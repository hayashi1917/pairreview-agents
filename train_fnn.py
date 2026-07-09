"""
採否判定モデル（HGT+FFN）の学習スクリプト

学習に必要なのは「論文」と「学会への採否結果（accept/reject）」のペアのみ。
データセットは以下の形式のJSONファイルで指定する（paperは3形式のいずれでも可）:

[
  {"paper": "papers/example1.pdf", "label": "accept"},
  {"paper": "data/example2_mineru_output.json", "label": "reject"},
  {"paper": "output/example3/graph.json", "label": "accept"}
]

  - PDF               : MinerU APIで解析後、Stage2-4（討論生成・関係抽出・グラフ構築）を実行
  - MinerU抽出済みjson : Stage2-4を実行
  - 構築済みgraph.json : main.pyの出力（output/graph.json）をそのまま流用

PDF/MinerU json入力時のLLM討論・グラフ構築の結果、およびノードEmbeddingは
cache_dir（デフォルト: train_cache/）にキャッシュされるため、
2回目以降の学習ではLLM・Embedding APIを呼ばずに再学習できる。

学習はHGTとFFNをend-to-endにクロスエントロピー損失で行い、
チェックポイントを models/acceptance_model.pt に保存する。
main.py は次回実行時からこのチェックポイントを自動で読み込む。

使い方:
  python train_fnn.py dataset.json
  python train_fnn.py dataset.json --epochs 100 --lr 1e-3 --val-ratio 0.2
"""
import argparse
import hashlib
import json
import logging
import random
from pathlib import Path

import torch
from dotenv import load_dotenv

from src.hgt_reasoning import AcceptanceModel, DEFAULT_MODEL_PATH, build_hetero_data
from src.logging_config import setup_logging
from src.persistence import load_graph, save_debate_tree, save_graph
from src.schemas import HeterogeneousGraph

logger = logging.getLogger(__name__)

_LABEL_TO_INDEX = {"reject": 0, "accept": 1}


def _cache_key(paper_path: Path) -> str:
    """キャッシュファイル名の衝突を避けるため、ファイル名にパスのハッシュを付ける"""
    digest = hashlib.md5(str(paper_path.resolve()).encode("utf-8")).hexdigest()[:8]
    return f"{paper_path.stem}-{digest}"


def _is_graph_json(path: Path) -> bool:
    """jsonファイルが構築済み異種グラフ（graph.json）かどうかを中身で判定する"""
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    return isinstance(obj, dict) and "nodes" in obj and "edges" in obj


def _build_graph_for_paper(paper_path: Path, cache_dir: Path) -> HeterogeneousGraph:
    """論文（PDF/MinerU json/graph.json）を異種グラフへ変換する。
    Stage2-4のLLM呼び出しを伴う場合、結果をcache_dirへ保存し2回目以降は再利用する。"""
    if paper_path.suffix == ".json" and _is_graph_json(paper_path):
        return load_graph(str(paper_path))

    key = _cache_key(paper_path)
    graph_cache = cache_dir / f"{key}.graph.json"
    if graph_cache.exists():
        logger.info("キャッシュ済みグラフを使用: %s", graph_cache)
        return load_graph(str(graph_cache))

    # Stage1-4はLLM/MinerU APIを使うため、必要になった時点でimportする
    from src.debate import run_multi_agent_debate
    from src.graph_builder import build_heterogeneous_graph
    from src.preprocess import load_paper_content, load_paper_content_from_pdf
    from src.relation_extraction import extract_relations

    if paper_path.suffix.lower() == ".pdf":
        paper = load_paper_content_from_pdf(str(paper_path), save_dir=str(cache_dir / key / "mineru"))
    else:
        paper = load_paper_content(str(paper_path))

    debate_log = run_multi_agent_debate(paper)
    save_debate_tree(debate_log, str(cache_dir / f"{key}.debate_tree.json"))
    relations = extract_relations(debate_log)
    graph = build_heterogeneous_graph(paper.title, debate_log, relations)
    save_graph(graph, str(graph_cache))
    return graph


def _load_hetero_data(paper_path: Path, cache_dir: Path):
    """論文をHeteroData（Embedding済み）へ変換する。Embedding結果も.ptでキャッシュする。"""
    hetero_cache = cache_dir / f"{_cache_key(paper_path)}.hetero.pt"
    if hetero_cache.exists():
        return torch.load(hetero_cache, weights_only=False)

    graph = _build_graph_for_paper(paper_path, cache_dir)
    data = build_hetero_data(graph)
    cache_dir.mkdir(parents=True, exist_ok=True)
    torch.save(data, hetero_cache)
    return data


def load_dataset(dataset_path: str, cache_dir: Path) -> list[tuple[object, int]]:
    """データセットJSONを読み込み、(HeteroData, ラベルindex) のリストへ変換する。"""
    entries = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"データセットが空か、リスト形式ではありません: {dataset_path}")

    samples: list[tuple[object, int]] = []
    for i, entry in enumerate(entries, start=1):
        label = str(entry["label"]).lower()
        if label not in _LABEL_TO_INDEX:
            raise ValueError(f"labelは accept / reject のいずれかにしてください: {entry}")
        paper_path = Path(entry["paper"])
        if not paper_path.exists():
            raise FileNotFoundError(f"論文ファイルが見つかりません: {paper_path}")
        logger.info("(%d/%d) 学習データを準備中: %s [%s]", i, len(entries), paper_path, label)
        data = _load_hetero_data(paper_path, cache_dir)
        samples.append((data, _LABEL_TO_INDEX[label]))
    return samples


def _evaluate(model: AcceptanceModel, samples: list[tuple[object, int]]) -> tuple[float, float]:
    """損失と正解率を返す。"""
    loss_fn = torch.nn.CrossEntropyLoss()
    model.eval()
    total_loss = 0.0
    correct = 0
    with torch.no_grad():
        for data, label in samples:
            logits = model(data)
            total_loss += loss_fn(logits.unsqueeze(0), torch.tensor([label])).item()
            correct += int(logits.argmax().item() == label)
    return total_loss / len(samples), correct / len(samples)


def train(
    dataset_path: str,
    model_out: str,
    cache_dir: str,
    epochs: int,
    lr: float,
    val_ratio: float,
    seed: int,
) -> None:
    random.seed(seed)
    torch.manual_seed(seed)

    samples = load_dataset(dataset_path, Path(cache_dir))
    logger.info("学習データの準備が完了しました: %d件", len(samples))

    # 検証データの分割（val_ratio > 0 の場合のみ）
    random.shuffle(samples)
    num_val = int(len(samples) * val_ratio)
    val_samples = samples[:num_val]
    train_samples = samples[num_val:]
    if not train_samples:
        raise ValueError("学習データが0件になりました。val_ratioを下げてください。")
    if val_samples:
        logger.info("学習 %d件 / 検証 %d件 に分割しました。", len(train_samples), len(val_samples))

    model = AcceptanceModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = torch.nn.CrossEntropyLoss()

    for epoch in range(1, epochs + 1):
        model.train()
        random.shuffle(train_samples)
        total_loss = 0.0
        correct = 0
        for data, label in train_samples:
            optimizer.zero_grad()
            logits = model(data)
            loss = loss_fn(logits.unsqueeze(0), torch.tensor([label]))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += int(logits.argmax().item() == label)

        train_loss = total_loss / len(train_samples)
        train_acc = correct / len(train_samples)
        if val_samples:
            val_loss, val_acc = _evaluate(model, val_samples)
            logger.info(
                "epoch %3d/%d  train: loss=%.4f acc=%.3f  val: loss=%.4f acc=%.3f",
                epoch, epochs, train_loss, train_acc, val_loss, val_acc,
            )
        else:
            logger.info("epoch %3d/%d  train: loss=%.4f acc=%.3f", epoch, epochs, train_loss, train_acc)

    out_path = Path(model_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_path)
    logger.info("学習済みモデルを保存しました: %s（main.pyが自動で読み込みます）", out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="採否判定モデル（HGT+FFN）の学習")
    parser.add_argument(
        "dataset_path",
        help='学習データセットのJSONパス（[{"paper": "...", "label": "accept|reject"}, ...]）',
    )
    parser.add_argument(
        "--model-out",
        default=DEFAULT_MODEL_PATH,
        help=f"チェックポイントの保存先（デフォルト: {DEFAULT_MODEL_PATH}）",
    )
    parser.add_argument(
        "--cache-dir",
        default="train_cache",
        help="討論グラフ・Embeddingのキャッシュディレクトリ（デフォルト: train_cache）",
    )
    parser.add_argument("--epochs", type=int, default=50, help="エポック数（デフォルト: 50）")
    parser.add_argument("--lr", type=float, default=1e-3, help="学習率（デフォルト: 1e-3）")
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.0,
        help="検証データの割合（デフォルト: 0.0 = 分割なし）",
    )
    parser.add_argument("--seed", type=int, default=42, help="乱数シード（デフォルト: 42）")
    args = parser.parse_args()

    # .env / .env.local からOPENAI_API_KEY・MINERU_API_KEY等を読み込む
    # （シェルに古いキーがexportされていても.envの値を優先する）
    load_dotenv(override=True)
    load_dotenv(".env.local", override=True)
    setup_logging()
    train(
        dataset_path=args.dataset_path,
        model_out=args.model_out,
        cache_dir=args.cache_dir,
        epochs=args.epochs,
        lr=args.lr,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )
