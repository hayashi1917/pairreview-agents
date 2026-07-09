"""
システム全体で使用するデータモデル定義。
各ステージ（前処理・討論・関係抽出・グラフ構築・HGT推論）間の
入出力は、すべてこのファイルのPydanticモデルを介してやり取りする。
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ============================================================
# Stage1: 論文前処理
# ============================================================


class PaperContent(BaseModel):
    """MinerUで抽出した論文コンテンツ（テキスト・画像・表）"""

    title: str = Field(..., description="論文タイトル")
    main_text: str = Field(..., description="本文（付録を除くメイン部分）のテキスト")
    references: str = Field(default="", description="参考文献リストのテキスト")
    image_descriptions: list[str] = Field(
        default_factory=list, description="抽出された図表画像のキャプション・説明"
    )
    tables: list[str] = Field(default_factory=list, description="抽出された表（markdown形式など）")


# ============================================================
# Stage2: マルチエージェント討論
# ============================================================

DebateStage = Literal["initial_review", "author_response", "reviewer_reevaluation"]
Speaker = Literal["Reviewer 1", "Reviewer 2", "Reviewer 3", "Author"]


class DebateSentence(BaseModel):
    """討論ログ中の1発言"""

    id: str
    speaker: Speaker
    stage: DebateStage
    text: str
    # 議論ツリーを構築するための親発言id（初期コメントはNone、
    # 著者反論の親は対応する初期コメント、再評価の親は対応する著者反論）
    parent_id: str | None = None


class DebateLog(BaseModel):
    """討論ログ全体（発言のリスト）"""

    sentences: list[DebateSentence] = Field(default_factory=list)


# ============================================================
# Stage3: 討論からの関係抽出
# ============================================================

ReviewerAuthorRelationType = Literal[
    "accept", "reject", "clarify", "compromise", "extend", "neutral"
]
InterReviewerRelationType = Literal[
    "agree", "disagree", "complement", "progressive", "independent"
]


class ReviewerAuthorRelation(BaseModel):
    """査読者発言 -> 著者発言 の関係"""

    reviewer_sentence_id: str
    author_sentence_id: str
    relation: ReviewerAuthorRelationType


class InterReviewerRelation(BaseModel):
    """査読者発言 -> 査読者発言 の関係"""

    source_sentence_id: str
    target_sentence_id: str
    relation: InterReviewerRelationType


class RelationExtractionResult(BaseModel):
    """討論ログから抽出された関係一式"""

    reviewer_author_relations: list[ReviewerAuthorRelation] = Field(default_factory=list)
    inter_reviewer_relations: list[InterReviewerRelation] = Field(default_factory=list)


# ============================================================
# Stage4: 異種グラフ構築
# ============================================================

NodeType = Literal["title", "evaluation_dimension", "reviewer_opinion", "author_opinion"]

EdgeRelation = Literal[
    "has_aspect",
    "reviewed_by",
    "accept", "reject", "clarify", "compromise", "extend", "neutral",
    "agree", "disagree", "complement", "progressive", "independent",
]


class GraphNode(BaseModel):
    id: str
    node_type: NodeType
    text: str


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation: EdgeRelation


class HeterogeneousGraph(BaseModel):
    """Title/EvaluationDimension/ReviewerOpinion/AuthorOpinionからなる異種グラフ"""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


# ============================================================
# Stage5: HGTによるグラフ推論
# ============================================================


class HGTReasoningResult(BaseModel):
    """HGTの出力をノード種別ごとに平均・連結した特徴量（採否判定FFNへの入力）"""

    h_title: list[float]
    h_dim: list[float]
    h_reviewer: list[float]
    h_author: list[float]
    h_concat: list[float]


# ============================================================
# Stage6: FFNによる採否判定
# ============================================================

AcceptanceLabel = Literal["reject", "accept"]


class AcceptancePrediction(BaseModel):
    """FFNによる採否判定結果"""

    label: AcceptanceLabel
    reject_probability: float
    accept_probability: float
    used_trained_weights: bool = Field(
        ..., description="学習済みチェックポイントを読み込んで判定したか（Falseなら未学習の重み）"
    )
