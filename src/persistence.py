"""
中間生成物（議論ツリー・異種グラフ）をファイルに保存する処理
"""
import json
import logging
from pathlib import Path

from src.schemas import AcceptancePrediction, DebateLog, DebateSentence, HeterogeneousGraph

logger = logging.getLogger(__name__)


def _build_tree_node(sentence: DebateSentence, children_map: dict[str, list[DebateSentence]]) -> dict:
    """1発言とその子発言（反論・再評価）を再帰的にネストしたdictへ変換する"""
    return {
        "id": sentence.id,
        "speaker": sentence.speaker,
        "stage": sentence.stage,
        "text": sentence.text,
        "children": [
            _build_tree_node(child, children_map) for child in children_map.get(sentence.id, [])
        ],
    }


def build_debate_tree(debate_log: DebateLog) -> list[dict]:
    """
    討論ログ（フラットなsentencesのリスト）を、parent_idを使って
    レビュワーごとの木構造（初期コメント -> 著者反論 -> 再評価）に変換する。
    """
    children_map: dict[str, list[DebateSentence]] = {}
    for s in debate_log.sentences:
        if s.parent_id is not None:
            children_map.setdefault(s.parent_id, []).append(s)

    roots = [s for s in debate_log.sentences if s.parent_id is None]
    return [_build_tree_node(root, children_map) for root in roots]


def save_debate_tree(debate_log: DebateLog, output_path: str) -> None:
    """討論ツリーをJSONファイルに保存する。"""
    tree = build_debate_tree(debate_log)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("議論ツリーを保存しました: %s", path)


def save_graph(graph: HeterogeneousGraph, output_path: str) -> None:
    """異種グラフ（ノード・エッジ）をJSONファイルに保存する。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    logger.info("異種グラフを保存しました: %s", path)


def load_graph(input_path: str) -> HeterogeneousGraph:
    """save_graphで保存した異種グラフJSONを読み込む。"""
    return HeterogeneousGraph.model_validate_json(
        Path(input_path).read_text(encoding="utf-8")
    )


def save_prediction(prediction: AcceptancePrediction, output_path: str) -> None:
    """FFNによる採否判定結果をJSONファイルに保存する。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prediction.model_dump_json(indent=2), encoding="utf-8")
    logger.info("採否判定結果を保存しました: %s", path)
