"""
Stage1: 論文前処理

論文コンテンツの入力方法は2通り:
  1. PDFを入力とし、MinerU公式APIで解析してPaperContentへ変換する（load_paper_content_from_pdf）
  2. 抽出済みのjsonファイル（本文・参考文献・画像説明・表）を読み込む（load_paper_content）
"""
import json
import logging
import re
from pathlib import Path

from src.mineru_client import parse_pdf
from src.schemas import PaperContent

logger = logging.getLogger(__name__)

# 参考文献・付録セクションの見出し判定（本文はここまでとする）
_REFERENCES_HEADING = re.compile(r"^(references|bibliography|参考文献)\b", re.IGNORECASE)
_APPENDIX_HEADING = re.compile(r"^(appendix|appendices|supplementary|付録)\b", re.IGNORECASE)


def load_paper_content(mineru_output_path: str) -> PaperContent:
    """
    抽出済みの論文コンテンツjsonを読み込み、PaperContentに変換する。

    想定するjsonの形式（付録は含まれない前提）:
    {
        "title": "...",
        "main_text": "...",
        "references": "...",
        "image_descriptions": ["...", ...],
        "tables": ["...", ...]
    }
    """
    logger.info("抽出済みjsonを読み込み中: %s", mineru_output_path)
    path = Path(mineru_output_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    paper = PaperContent(**data)
    logger.info("論文前処理完了: title=%s", paper.title)
    return paper


def load_paper_content_from_pdf(pdf_path: str, save_dir: str | None = None) -> PaperContent:
    """
    PDFをMinerU APIで解析し、PaperContentに変換する。

    Args:
        pdf_path: 論文PDFのパス
        save_dir: 指定するとMinerUの生出力(full.md, content_list.json)を保存する
    """
    logger.info("MinerU APIでPDFを解析中: %s", pdf_path)
    result = parse_pdf(pdf_path, save_dir=save_dir)
    paper = _content_list_to_paper_content(result.content_list, fallback_title=Path(pdf_path).stem)
    logger.info("論文前処理完了: title=%s", paper.title)
    return paper


def _content_list_to_paper_content(content_list: list[dict], fallback_title: str) -> PaperContent:
    """
    MinerUのcontent_list.json（ブロック単位の抽出結果）をPaperContentへ変換する。

    - 最初のレベル1見出しをタイトルとみなす
    - References見出し以降は参考文献、Appendix見出し以降は本文から除外
    - image/tableブロックはキャプションと表本体をそれぞれ抽出する
    """
    title = ""
    main_parts: list[str] = []
    reference_parts: list[str] = []
    image_descriptions: list[str] = []
    tables: list[str] = []
    section = "main"

    for item in content_list:
        item_type = item.get("type")

        if item_type in ("text", "equation"):
            text = (item.get("text") or "").strip()
            if not text:
                continue
            if item.get("text_level") == 1:
                if not title:
                    title = text
                    continue
                if _REFERENCES_HEADING.match(text):
                    section = "references"
                    continue
                if _APPENDIX_HEADING.match(text):
                    section = "appendix"
                    continue
            if section == "main":
                main_parts.append(text)
            elif section == "references":
                reference_parts.append(text)

        elif item_type == "image":
            caption = " ".join(item.get("img_caption") or []).strip()
            if caption:
                image_descriptions.append(caption)

        elif item_type == "table":
            caption = " ".join(item.get("table_caption") or []).strip()
            body = (item.get("table_body") or "").strip()
            table_text = "\n".join(part for part in (caption, body) if part)
            if table_text:
                tables.append(table_text)

    return PaperContent(
        title=title or fallback_title,
        main_text="\n\n".join(main_parts),
        references="\n".join(reference_parts),
        image_descriptions=image_descriptions,
        tables=tables,
    )
