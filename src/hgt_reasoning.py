"""
Stage5: HGTによるグラフ推論 / Stage6: FFNによる採否判定

異種グラフ（HeterogeneousGraph）をtorch_geometricのHeteroData形式に変換し、
HGTConvでノード種別ごとの埋め込みを更新する。ノード種別ごとに平均を取り、
4種類の平均ベクトルを連結したh_concatを得る（Stage5）。
h_concatをFFN（Linear(512->128) -> ReLU -> Linear(128->2) -> Softmax）に通して
採否(reject/accept)を判定する（Stage6）。

参考: https://pytorch-geometric.readthedocs.io/en/2.7.0/generated/torch_geometric.nn.conv.HGTConv.html

HGTとFFNはAcceptanceModelとしてまとめて扱い、train_fnn.pyでend-to-endに学習する。
学習済みチェックポイント（デフォルト: models/acceptance_model.pt）があれば読み込み、
無ければ初期化直後の重みで動作する（判定結果は無意味なので警告を出す）。
"""
import functools
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import get_args

import openai
import torch
from langchain_openai import OpenAIEmbeddings
from torch_geometric.data import HeteroData
from torch_geometric.nn import HGTConv

from src.schemas import (
    AcceptancePrediction,
    HeterogeneousGraph,
    HGTReasoningResult,
    InterReviewerRelationType,
    ReviewerAuthorRelationType,
)

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 1536
_HIDDEN_CHANNELS = 128
_NUM_HEADS = 2
_NUM_LAYERS = 1
_FFN_HIDDEN_DIM = 128
_NUM_CLASSES = 2  # 0: reject, 1: accept

# 学習済みモデル（HGT+FFN）チェックポイントのデフォルト保存先
DEFAULT_MODEL_PATH = "models/acceptance_model.pt"

# グラフごとに実際に出現するエッジ種別が異なってもモデル構造（state_dict）が
# 常に同一になるよう、スキーマ上あり得る全ノード種別・全エッジ種別を固定のmetadataとする
NODE_TYPES: list[str] = ["title", "evaluation_dimension", "reviewer_opinion", "author_opinion"]
EDGE_TYPES: list[tuple[str, str, str]] = (
    [
        ("title", "has_aspect", "evaluation_dimension"),
        ("reviewer_opinion", "reviewed_by", "evaluation_dimension"),
    ]
    + [("reviewer_opinion", rel, "author_opinion") for rel in get_args(ReviewerAuthorRelationType)]
    + [("reviewer_opinion", rel, "reviewer_opinion") for rel in get_args(InterReviewerRelationType)]
)
FULL_METADATA: tuple[list[str], list[tuple[str, str, str]]] = (NODE_TYPES, EDGE_TYPES)


@functools.cache
def _get_embedding_model() -> OpenAIEmbeddings:
    """ノードのテキストをベクトル化するためのEmbeddingモデル（LangChain経由）。
    OPENAI_API_KEYの読み込み（load_dotenv）より先にimportされても動くよう、
    クライアントは初回使用時に生成する。"""
    return OpenAIEmbeddings(model="text-embedding-3-small")


_EMBED_MAX_ATTEMPTS = 8


def _embed_with_retry(texts: list[str]) -> list[list[float]]:
    """embed_documentsを間欠的なAPIエラーに耐えるよう再試行付きで呼ぶ。

    モデル有効化直後はOpenAI側の設定伝播が不安定で、有効化済みでも一部の
    リクエストだけ403(model_not_found)が返ることがあるため、
    403もレート制限と同様に指数バックオフで再試行する。
    """
    delay = 2.0
    for attempt in range(1, _EMBED_MAX_ATTEMPTS + 1):
        try:
            return _get_embedding_model().embed_documents(texts)
        except (openai.PermissionDeniedError, openai.RateLimitError) as e:
            if attempt == _EMBED_MAX_ATTEMPTS:
                raise
            logger.warning(
                "Embedding APIが一時的に拒否されました（%s）。%.0f秒後に再試行します (%d/%d)",
                type(e).__name__, delay, attempt, _EMBED_MAX_ATTEMPTS,
            )
            time.sleep(delay)
            delay = min(delay * 2, 60.0)
    raise RuntimeError("unreachable")


class _HGT(torch.nn.Module):
    """torch_geometric公式ドキュメントのHGTConv使用例に基づく最小構成のHGTモデル"""

    def __init__(self, hidden_channels: int, num_heads: int, num_layers: int, metadata) -> None:
        super().__init__()
        # ノード種別ごとにEmbedding次元からhidden_channelsへ射影する層
        self.lin_dict = torch.nn.ModuleDict()
        for node_type in metadata[0]:
            self.lin_dict[node_type] = torch.nn.Linear(_EMBEDDING_DIM, hidden_channels)

        # HGTConv層を積み重ねる
        self.convs = torch.nn.ModuleList()
        for _ in range(num_layers):
            self.convs.append(HGTConv(hidden_channels, hidden_channels, metadata, num_heads))

    def forward(self, x_dict, edge_index_dict):
        x_dict = {node_type: self.lin_dict[node_type](x).relu() for node_type, x in x_dict.items()}
        for conv in self.convs:
            out_dict = conv(x_dict, edge_index_dict)
            # 入力エッジが1本も無いノード種別（titleなど）はHGTConvの出力に含まれない
            # （またはNoneになる）ため、射影後の入力特徴をそのまま引き継ぐ
            x_dict = {
                node_type: out_dict[node_type]
                if out_dict.get(node_type) is not None
                else x_dict[node_type]
                for node_type in x_dict
            }
        return x_dict


class _FFN(torch.nn.Module):
    """h_concatから採否2クラスのロジットを出す2層NN（Linear -> ReLU -> Linear）"""

    def __init__(self, in_dim: int, hidden_dim: int, num_classes: int) -> None:
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(in_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, h_concat: torch.Tensor) -> torch.Tensor:
        return self.net(h_concat)


class AcceptanceModel(torch.nn.Module):
    """HGT（Stage5）とFFN（Stage6）をまとめた採否判定モデル。学習・チェックポイント保存の単位。"""

    def __init__(self) -> None:
        super().__init__()
        self.hgt = _HGT(_HIDDEN_CHANNELS, _NUM_HEADS, _NUM_LAYERS, FULL_METADATA)
        self.ffn = _FFN(_HIDDEN_CHANNELS * len(NODE_TYPES), _FFN_HIDDEN_DIM, _NUM_CLASSES)
        # 学習済みチェックポイントから読み込まれたかどうか（load_or_init_modelが設定）
        self.is_trained = False

    def node_type_means(self, data: HeteroData) -> dict[str, torch.Tensor]:
        """HGTを適用し、ノード種別ごとの平均埋め込みを返す。"""
        out_dict = self.hgt(data.x_dict, data.edge_index_dict)
        return {node_type: out_dict[node_type].mean(dim=0) for node_type in NODE_TYPES}

    def forward(self, data: HeteroData) -> torch.Tensor:
        """異種グラフから採否2クラスのロジットを返す。"""
        means = self.node_type_means(data)
        h_concat = torch.cat([means[node_type] for node_type in NODE_TYPES])
        return self.ffn(h_concat)


def load_or_init_model(model_path: str | None = DEFAULT_MODEL_PATH) -> AcceptanceModel:
    """学習済みチェックポイントがあれば読み込み、無ければ初期化直後のモデルを返す。"""
    model = AcceptanceModel()
    if model_path and Path(model_path).exists():
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.is_trained = True
        logger.info("学習済みモデルを読み込みました: %s", model_path)
    else:
        logger.warning(
            "学習済みモデルが見つかりません（%s）。初期化直後の重みで動作するため、"
            "採否判定の結果は参考になりません。train_fnn.py で学習してください。",
            model_path,
        )
    return model


def build_hetero_data(graph: HeterogeneousGraph) -> HeteroData:
    """HeterogeneousGraph(Pydantic)をtorch_geometricのHeteroDataに変換する"""
    # ノード種別ごとにテキストとidをまとめる
    node_texts_by_type: dict[str, list[str]] = defaultdict(list)
    node_ids_by_type: dict[str, list[str]] = defaultdict(list)
    for node in graph.nodes:
        node_texts_by_type[node.node_type].append(node.text)
        node_ids_by_type[node.node_type].append(node.id)

    data = HeteroData()

    # ノードテキストをベクトル化してx_dictを構築
    for node_type, texts in node_texts_by_type.items():
        vectors = _embed_with_retry(texts)
        data[node_type].x = torch.tensor(vectors, dtype=torch.float)

    # id -> (ノード種別, その種別内でのindex) の対応表を作成
    id_to_index: dict[str, tuple[str, int]] = {}
    for node_type, ids in node_ids_by_type.items():
        for i, node_id in enumerate(ids):
            id_to_index[node_id] = (node_type, i)

    # エッジをrelation種別ごとに(src_type, relation, dst_type)のedge_indexへ変換
    edges_by_key: dict[tuple[str, str, str], list[list[int]]] = defaultdict(lambda: [[], []])
    for edge in graph.edges:
        if edge.source_id not in id_to_index or edge.target_id not in id_to_index:
            # 古いキャッシュ等で実在しないノードidを参照するエッジが混ざっていても落ちないようにする
            logger.warning(
                "実在しないノードidを参照するエッジをスキップ: %.60s -> %.60s",
                edge.source_id, edge.target_id,
            )
            continue
        src_type, src_idx = id_to_index[edge.source_id]
        dst_type, dst_idx = id_to_index[edge.target_id]
        key = (src_type, edge.relation, dst_type)
        edges_by_key[key][0].append(src_idx)
        edges_by_key[key][1].append(dst_idx)

    for (src_type, relation, dst_type), (src_list, dst_list) in edges_by_key.items():
        data[src_type, relation, dst_type].edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)

    return data


def run_hgt_reasoning(graph: HeterogeneousGraph, model: AcceptanceModel | None = None) -> HGTReasoningResult:
    """異種グラフをHGTに入力し、ノード種別ごとの平均埋め込みを連結したh_concatを返す。"""
    logger.info("ノードのベクトル化とHeteroDataへの変換中... (text-embedding-3-small)")
    data = build_hetero_data(graph)

    if model is None:
        model = load_or_init_model()

    logger.info("HGTConvによるグラフ推論を実行中...")
    model.eval()
    with torch.no_grad():
        means = model.node_type_means(data)

    h_title = means["title"]
    h_dim = means["evaluation_dimension"]
    h_reviewer = means["reviewer_opinion"]
    h_author = means["author_opinion"]

    # 4種類の平均ベクトルを連結
    h_concat = torch.cat([h_title, h_dim, h_reviewer, h_author])
    logger.info("HGT推論完了: h_concat次元=%d", h_concat.shape[0])

    return HGTReasoningResult(
        h_title=h_title.tolist(),
        h_dim=h_dim.tolist(),
        h_reviewer=h_reviewer.tolist(),
        h_author=h_author.tolist(),
        h_concat=h_concat.tolist(),
    )


def classify_accept_reject(
    h_concat: list[float], model: AcceptanceModel | None = None
) -> AcceptancePrediction:
    """
    Stage6: h_concatをLinear(512->128) -> ReLU -> Linear(128->2) -> Softmaxに通し、
    採否(0: reject, 1: accept)を判定する。

    modelを省略した場合はDEFAULT_MODEL_PATHのチェックポイントを読み込む
    （無ければ未学習の重みで判定し、used_trained_weights=False を返す）。
    """
    if model is None:
        model = load_or_init_model()

    model.eval()
    with torch.no_grad():
        logits = model.ffn(torch.tensor(h_concat, dtype=torch.float))
        probs = torch.softmax(logits, dim=-1)

    reject_prob = probs[0].item()
    accept_prob = probs[1].item()
    label = "accept" if accept_prob >= reject_prob else "reject"
    logger.info(
        "採否判定結果: %s (reject=%.3f, accept=%.3f)%s",
        label,
        reject_prob,
        accept_prob,
        "" if model.is_trained else " ※未学習の重みによる判定",
    )

    return AcceptancePrediction(
        label=label,
        reject_probability=reject_prob,
        accept_probability=accept_prob,
        used_trained_weights=model.is_trained,
    )
