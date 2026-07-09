"""
Stage4: 異種グラフ構築

討論ログと関係抽出結果から、以下4種類のノードと5種類のエッジからなる異種グラフを構築する。

ノード: Title / EvaluationDimension / ReviewerOpinion / AuthorOpinion
エッジ:
  Title -> EvaluationDimension            : has_aspect
  ReviewerOpinion -> EvaluationDimension  : reviewed_by
  ReviewerOpinion -> AuthorOpinion        : accept/reject/clarify/compromise/extend/neutral
  ReviewerOpinion -> ReviewerOpinion      : agree/disagree/complement/progressive/independent

ReviewerOpinion -> EvaluationDimension の分類には、論文 Table8
「Prompt template for argumentative sentence classification」のプロンプト文言を
変更せずに使用する。Table8はコメント1件ずつを分類する形式のため、
査読者コメントごとにLLM呼び出しを行う。
"""
import functools
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from src.schemas import (
    DebateLog,
    DebateSentence,
    GraphEdge,
    GraphNode,
    HeterogeneousGraph,
    RelationExtractionResult,
)

logger = logging.getLogger(__name__)

# Table8の番号付けに合わせた評価次元の並び
EVALUATION_DIMENSIONS: list[str] = [
    "Methodological Novelty",
    "Motivation Clarity",
    "Experimental Completeness",
    "Writing Fluency",
]

# ============================================================
# 論文 Table8 のプロンプト文言（原文のまま使用）
# ============================================================

_SYSTEM_PROMPT = (
    "### Task:\n\n"
    "Your task is to classify the given comment into one of the following "
    "categories based on their primary evaluation focus:\n\n"
    "1. Methodological Novelty — Is the comment evaluating whether the proposed "
    "method is novel, creative, or technically original?\n\n"
    "2. Motivation Clarity — Is the comment assessing whether the motivation or "
    "problem statement is clear and compelling?\n\n"
    "3. Experimental Completeness — Is the comment about the quality, "
    "completeness, or reliability of the experiments and empirical evaluation?\n\n"
    "4. Writing Fluency — Is the comment about the writing quality, fluency, or "
    "readability of the paper?\n\n"
    "Return your answer as JSON in the format: “category”: “category_name”"
)


class _DimensionClassification(BaseModel):
    category: str


@functools.cache
def _get_structured_llm():
    # OPENAI_API_KEYの読み込み（load_dotenv）より先にimportされても動くよう、
    # クライアントは初回使用時に生成する
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    return llm.with_structured_output(_DimensionClassification)


def _classify_reviewer_opinions(reviewer_sentences: list[DebateSentence]) -> dict[str, str]:
    """各ReviewerOpinionをEvaluationDimensionに分類し、sentence_id -> dimensionの辞書を返す。
    Table8の形式に合わせ、コメント1件ずつLLMへ問い合わせる。"""
    sentence_to_dimension: dict[str, str] = {}
    logger.info("%d件のReviewerOpinionをEvaluationDimensionに分類中...", len(reviewer_sentences))
    for i, s in enumerate(reviewer_sentences, start=1):
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"Comment to classify: \n{s.text}"),
        ]
        classification = _get_structured_llm().invoke(messages)
        sentence_to_dimension[s.id] = classification.category
        logger.info("  (%d/%d) %s -> %s", i, len(reviewer_sentences), s.id, classification.category)
    return sentence_to_dimension


def build_heterogeneous_graph(
    paper_title: str,
    debate_log: DebateLog,
    relations: RelationExtractionResult,
) -> HeterogeneousGraph:
    """討論ログと抽出済み関係から異種グラフ（ノード・エッジ）を構築する。"""
    logger.info("異種グラフの構築を開始します。")
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # --- Titleノード ---
    title_id = "title-0"
    nodes.append(GraphNode(id=title_id, node_type="title", text=paper_title))

    # --- EvaluationDimensionノード + Title -> EvaluationDimension ---
    dimension_ids: dict[str, str] = {}
    for i, dim in enumerate(EVALUATION_DIMENSIONS):
        dim_id = f"dim-{i}"
        dimension_ids[dim] = dim_id
        nodes.append(GraphNode(id=dim_id, node_type="evaluation_dimension", text=dim))
        edges.append(GraphEdge(source_id=title_id, target_id=dim_id, relation="has_aspect"))

    # --- ReviewerOpinion / AuthorOpinionノード ---
    reviewer_sentences = [s for s in debate_log.sentences if s.speaker.startswith("Reviewer")]
    author_sentences = [s for s in debate_log.sentences if s.speaker == "Author"]

    for s in reviewer_sentences:
        nodes.append(GraphNode(id=s.id, node_type="reviewer_opinion", text=s.text))
    for s in author_sentences:
        nodes.append(GraphNode(id=s.id, node_type="author_opinion", text=s.text))

    # --- ReviewerOpinion -> EvaluationDimension (reviewed_by) ---
    sentence_to_dimension = _classify_reviewer_opinions(reviewer_sentences)
    for sentence_id, dimension in sentence_to_dimension.items():
        dim_id = dimension_ids.get(dimension)
        if dim_id is not None:
            edges.append(GraphEdge(source_id=sentence_id, target_id=dim_id, relation="reviewed_by"))

    # 関係抽出結果が実在しない発言idを参照している場合はエッジにせずスキップする
    node_ids = {n.id for n in nodes}

    # --- ReviewerOpinion -> AuthorOpinion ---
    for rel in relations.reviewer_author_relations:
        if rel.reviewer_sentence_id not in node_ids or rel.author_sentence_id not in node_ids:
            logger.warning(
                "実在しない発言idを参照する査読者-著者関係をスキップ: %s -> %s",
                rel.reviewer_sentence_id, rel.author_sentence_id,
            )
            continue
        edges.append(
            GraphEdge(
                source_id=rel.reviewer_sentence_id,
                target_id=rel.author_sentence_id,
                relation=rel.relation,
            )
        )

    # --- ReviewerOpinion -> ReviewerOpinion ---
    for rel in relations.inter_reviewer_relations:
        if rel.source_sentence_id not in node_ids or rel.target_sentence_id not in node_ids:
            logger.warning(
                "実在しない発言idを参照する査読者間関係をスキップ: %s -> %s",
                rel.source_sentence_id, rel.target_sentence_id,
            )
            continue
        edges.append(
            GraphEdge(
                source_id=rel.source_sentence_id,
                target_id=rel.target_sentence_id,
                relation=rel.relation,
            )
        )

    logger.info("異種グラフ構築完了: ノード%d件, エッジ%d件", len(nodes), len(edges))
    return HeterogeneousGraph(nodes=nodes, edges=edges)
