"""
Stage2: マルチエージェント討論

論文 Table4「Prompt template for LLM-simulated reviewer-author debate」の
プロンプト文言を変更せずに使用する。論文中ではQwen2.5-VL-72B-Instructを使用しているが、
本実装ではLangChain経由でgpt-4.1を使用する。

会話の流れ（Table4準拠）:
  1. system: 論文内容を理解する参加者であることを指示
  2. 論文のテキスト・図・表を順番に投入し、受領確認させる（固定のack応答）
  3. reviewerロール + Review Guidelinesを与え、査読者コメントを生成させる（3名分）
  4. authorロール + Author Guidelinesを与え、各コメントへの反論を生成させる
  5. 著者の反論を踏まえ、reviewerロールで再度評価させ、再評価コメントを生成させる

※ Table4にはarea chair（メタレビュー）ロールも記載されているが、
   本システムのグラフスキーマにはAreaChairOpinionに相当するノードが存在しないため、
   討論ログの生成では使用しない（参考として定数のみ残す）。
"""
import functools
import logging

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.schemas import DebateLog, DebateSentence, PaperContent

logger = logging.getLogger(__name__)

REVIEWER_NAMES: list[str] = ["Reviewer 1", "Reviewer 2", "Reviewer 3"]


@functools.cache
def _get_llm() -> ChatOpenAI:
    # OPENAI_API_KEYの読み込み（load_dotenv）より先にimportされても動くよう、
    # クライアントは初回使用時に生成する
    return ChatOpenAI(model="gpt-4.1", temperature=0.7)

# ============================================================
# 論文 Table4 のプロンプト文言（原文のまま使用）
# ============================================================

_SYSTEM_PROMPT = (
    "You are a participant in the paper review and you need to fully understand "
    "the content of the paper."
)

_REVIEWER_ROLE_TEMPLATE = (
    "You are a helpful assistant. Your role:\n\n"
    "You are a reviewer. You write peer review of academic papers by evaluating "
    "their technical quality, originality, and clarity.\n\n"
    "## Review Guidelines\n\n{review_guidelines}"
)

_AUTHOR_ROLE_TEMPLATE = (
    "You are a helpful assistant. Your role:\n\n"
    "You are an author. You write research papers and submit them to conferences. "
    "During the rebuttal phase, you carefully read the reviews from the reviewers "
    "and respond to each of them.\n\n"
    "## Author Guidelines\n\n{author_guidelines}"
)

# Table4に記載されているが、討論ログの生成では使用しないロール（参考として保持）
_AREA_CHAIR_ROLE_TEMPLATE = (
    "You are a helpful assistant. Your role:\n\n"
    "You are a very knowledgeable and experienced area chair in a top-tier "
    "machine learning conference.\n\n"
    "You evaluate the reviews provided by reviewers and write metareviews.\n\n"
    "## Area Chair Guidelines\n\n{area_chair_guidelines}"
)

# Review Guidelines / Author Guidelines はTable4中では {{review guidelines}} /
# {{author guidelines}} というプレースホルダのままであり、具体的な文言の記載はないため、
# 評価次元（EvaluationDimension）に基づく最小限のガイドラインを別途定義して埋め込む。
_DEFAULT_REVIEW_GUIDELINES = (
    "Evaluate the paper in terms of methodological novelty, motivation clarity, "
    "experimental completeness, and writing fluency. Point out concrete strengths "
    "and weaknesses."
)
_DEFAULT_AUTHOR_GUIDELINES = (
    "Address the reviewer's concern directly. Where the concern is valid, "
    "acknowledge it and describe the specific action you will take; where you "
    "disagree, explain your reasoning."
)
# Table4には再評価ロールの記載が無いため、reviewerロールを再利用し、
# 著者の反論を踏まえて再評価するよう指示する文言を独自に補う。
_REEVALUATION_GUIDELINES = (
    "Reconsider your original comment in light of the author's rebuttal above, "
    "and state whether it resolves your concern."
)


def _build_paper_ingestion_messages(paper: PaperContent) -> list[BaseMessage]:
    """論文のテキスト・図・表を投入し、受領確認させる固定の会話履歴を構築する（Table4準拠）"""
    messages: list[BaseMessage] = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content="The following is the text content, figures and tables of a research paper."),
        AIMessage(content="Okay, please provide the content of the research paper."),
        HumanMessage(content=paper.main_text),
        AIMessage(content="Received the text content of the research paper."),
    ]
    for image_description in paper.image_descriptions:
        messages.append(HumanMessage(content=image_description))
        messages.append(AIMessage(content="Received the figure of the research paper."))
    for table in paper.tables:
        messages.append(HumanMessage(content=table))
        messages.append(AIMessage(content="Received the table of the research paper."))
    return messages


def run_multi_agent_debate(paper: PaperContent) -> DebateLog:
    """
    論文Table4のプロンプト構造に従い、3名のレビュワーによる初期コメント生成
    -> 著者の反論 -> レビュワーの再評価、という流れで討論ログを作成する。
    """
    sentences: list[DebateSentence] = []
    base_messages = _build_paper_ingestion_messages(paper)
    logger.info("論文コンテンツの投入完了。%d名のレビュワーによる討論を開始します。", len(REVIEWER_NAMES))

    for idx, reviewer_name in enumerate(REVIEWER_NAMES, start=1):
        history = list(base_messages)

        # 1. reviewerロールで初期コメントを生成
        logger.info("[%s] 初期コメントを生成中...", reviewer_name)
        history.append(
            HumanMessage(content=_REVIEWER_ROLE_TEMPLATE.format(review_guidelines=_DEFAULT_REVIEW_GUIDELINES))
        )
        initial_comment = _get_llm().invoke(history).content
        history.append(AIMessage(content=initial_comment))
        initial_id = f"R{idx}-I-001"
        sentences.append(
            DebateSentence(
                id=initial_id,
                speaker=reviewer_name,
                stage="initial_review",
                text=initial_comment,
                parent_id=None,
            )
        )
        logger.info("[%s] 初期コメント生成完了 (id=%s)", reviewer_name, initial_id)

        # 2. authorロールでコメントに反論
        logger.info("[Author] %s へのコメントに反論を生成中...", reviewer_name)
        history.append(
            HumanMessage(content=_AUTHOR_ROLE_TEMPLATE.format(author_guidelines=_DEFAULT_AUTHOR_GUIDELINES))
        )
        author_response = _get_llm().invoke(history).content
        history.append(AIMessage(content=author_response))
        author_id = f"A-R{idx}-001"
        sentences.append(
            DebateSentence(
                id=author_id,
                speaker="Author",
                stage="author_response",
                text=author_response,
                parent_id=initial_id,
            )
        )
        logger.info("[Author] 反論生成完了 (id=%s)", author_id)

        # 3. reviewerロールに戻り、著者の反論を踏まえて再評価
        logger.info("[%s] 著者の反論を踏まえた再評価を生成中...", reviewer_name)
        history.append(
            HumanMessage(content=_REVIEWER_ROLE_TEMPLATE.format(review_guidelines=_REEVALUATION_GUIDELINES))
        )
        reeval_comment = _get_llm().invoke(history).content
        reeval_id = f"R{idx}-RE-001"
        sentences.append(
            DebateSentence(
                id=reeval_id,
                speaker=reviewer_name,
                stage="reviewer_reevaluation",
                text=reeval_comment,
                parent_id=author_id,
            )
        )
        logger.info("[%s] 再評価生成完了 (id=%s)", reviewer_name, reeval_id)

    logger.info("討論ログ生成完了: 合計%d件の発言", len(sentences))
    return DebateLog(sentences=sentences)
