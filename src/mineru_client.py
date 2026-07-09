"""
MinerU公式API (https://mineru.net/api/v4) クライアント

ローカルのPDFをMinerU APIにアップロードして解析し、
結果ZIPに含まれる full.md / content_list.json を取得する。

処理の流れ:
  1. POST /file-urls/batch      : アップロード用の署名付きURLとbatch_idを発行
  2. PUT  {file_url}            : PDF本体をアップロード（完了すると解析タスクが自動投入される）
  3. GET  /extract-results/batch/{batch_id} : 解析完了までポーリング
  4. full_zip_url からZIPをダウンロードし、full.md / content_list.json を展開

利用にはmineru.netのAPI管理ページで発行したトークンを
環境変数 MINERU_API_KEY に設定しておく必要がある。
"""
import io
import json
import logging
import os
import time
import zipfile
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://mineru.net/api/v4"
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 900
REQUEST_TIMEOUT_SECONDS = 60


class MinerUAPIError(RuntimeError):
    """MinerU APIの呼び出し失敗を表す例外"""


class MinerUParseResult:
    """MinerU APIの解析結果（結果ZIPの主要ファイル）"""

    def __init__(self, full_md: str, content_list: list[dict]):
        self.full_md = full_md
        self.content_list = content_list


def _auth_headers() -> dict[str, str]:
    token = os.environ.get("MINERU_API_KEY", "").strip()
    if not token:
        raise MinerUAPIError(
            "環境変数 MINERU_API_KEY が設定されていません。"
            "mineru.netのAPI管理ページでトークンを発行し、.envに設定してください。"
        )
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _check_api_response(res: requests.Response) -> dict:
    """HTTPステータスとAPIレスポンスのcodeを検証し、dataフィールドを返す"""
    res.raise_for_status()
    body = res.json()
    if body.get("code") != 0:
        raise MinerUAPIError(f"MinerU APIがエラーを返しました: {body}")
    return body["data"]


def _request_upload_url(pdf_path: Path, language: str, model_version: str) -> tuple[str, str]:
    """アップロード用URLを発行し、(batch_id, file_url) を返す"""
    payload = {
        "language": language,
        "model_version": model_version,
        "enable_formula": True,
        "enable_table": True,
        "files": [{"name": pdf_path.name, "is_ocr": False}],
    }
    res = requests.post(
        f"{BASE_URL}/file-urls/batch",
        headers=_auth_headers(),
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    data = _check_api_response(res)
    return data["batch_id"], data["file_urls"][0]


def _upload_file(pdf_path: Path, file_url: str) -> None:
    # 署名付きURLへのPUTではContent-Typeヘッダを付けないこと（MinerU仕様）
    with pdf_path.open("rb") as f:
        res = requests.put(file_url, data=f, timeout=REQUEST_TIMEOUT_SECONDS * 5)
    res.raise_for_status()


def _poll_until_done(batch_id: str, file_name: str) -> str:
    """解析完了までポーリングし、結果ZIPのURLを返す"""
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        res = requests.get(
            f"{BASE_URL}/extract-results/batch/{batch_id}",
            headers=_auth_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        data = _check_api_response(res)
        results = [r for r in data.get("extract_result", []) if r.get("file_name") == file_name]
        result = results[0] if results else None
        if result is None:
            raise MinerUAPIError(f"batch {batch_id} に {file_name} の結果が見つかりません。")

        state = result.get("state")
        if state == "done":
            return result["full_zip_url"]
        if state == "failed":
            raise MinerUAPIError(f"MinerUの解析に失敗しました: {result.get('err_msg')}")

        progress = result.get("extract_progress") or {}
        logger.info(
            "MinerU解析中... state=%s (%s/%sページ)",
            state,
            progress.get("extracted_pages", "-"),
            progress.get("total_pages", "-"),
        )
        time.sleep(POLL_INTERVAL_SECONDS)

    raise MinerUAPIError(
        f"MinerUの解析が{POLL_TIMEOUT_SECONDS}秒以内に完了しませんでした (batch_id={batch_id})。"
    )


def _download_and_extract_zip(zip_url: str, save_dir: Path | None) -> MinerUParseResult:
    """結果ZIPをダウンロードし、full.md / content_list.json を取り出す"""
    res = requests.get(zip_url, timeout=REQUEST_TIMEOUT_SECONDS * 5)
    res.raise_for_status()

    full_md = ""
    content_list: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
        for name in zf.namelist():
            basename = Path(name).name
            if basename == "full.md":
                full_md = zf.read(name).decode("utf-8")
            elif basename.endswith("content_list.json"):
                content_list = json.loads(zf.read(name).decode("utf-8"))

    if not content_list:
        raise MinerUAPIError("結果ZIPに content_list.json が含まれていませんでした。")

    # デバッグ・再利用のために生の解析結果を保存しておく
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / "full.md").write_text(full_md, encoding="utf-8")
        (save_dir / "content_list.json").write_text(
            json.dumps(content_list, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("MinerUの生出力を保存しました: %s", save_dir)

    return MinerUParseResult(full_md=full_md, content_list=content_list)


def parse_pdf(
    pdf_path: str,
    language: str = "en",
    model_version: str = "vlm",
    save_dir: str | None = None,
) -> MinerUParseResult:
    """
    PDFをMinerU APIで解析し、full.md / content_list.json を返す。

    Args:
        pdf_path: 解析対象のPDFファイルパス
        language: 文書の言語（英語論文なら"en"）
        model_version: "pipeline" / "vlm" / "MinerU-HTML"
        save_dir: 指定するとMinerUの生出力(full.md, content_list.json)を保存する
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDFファイルが見つかりません: {pdf_path}")

    logger.info("MinerU API: アップロードURLを発行中...")
    batch_id, file_url = _request_upload_url(path, language, model_version)

    logger.info("MinerU API: PDFをアップロード中: %s", path.name)
    _upload_file(path, file_url)

    logger.info("MinerU API: 解析完了を待機中 (batch_id=%s)...", batch_id)
    zip_url = _poll_until_done(batch_id, path.name)

    logger.info("MinerU API: 結果ZIPをダウンロード中...")
    return _download_and_extract_zip(zip_url, Path(save_dir) if save_dir else None)
