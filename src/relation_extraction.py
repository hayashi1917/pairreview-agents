"""
Stage3: 討論ログからの関係抽出

討論ログ（DebateLog）をgpt-4.1-miniに与え、論文 Table5
「Prompt template for triple extraction」のプロンプト文言を変更せずに使用して、
査読者-著者関係・査読者間関係を抽出する。
LangChainのwith_structured_outputによりPydanticモデルとして構造化出力させる。
"""
import functools
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.schemas import (
    DebateLog,
    DebateSentence,
    InterReviewerRelation,
    RelationExtractionResult,
    ReviewerAuthorRelation,
)

logger = logging.getLogger(__name__)

@functools.cache
def _get_structured_llm():
    # OPENAI_API_KEYの読み込み（load_dotenv）より先にimportされても動くよう、
    # クライアントは初回使用時に生成する
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    return llm.with_structured_output(RelationExtractionResult)

# ============================================================
# 論文 Table5 のプロンプト文言（原文のまま使用）
# ============================================================

_SYSTEM_PROMPT = (
    "You are an expert in argument mining and peer review analysis.\n\n"
    "You are given a review file that contains:\n\n"
    "- The initial review comments from three reviewers.\n\n"
    "- The author’s responses to each reviewer.\n\n"
    "- The reviewers’ subsequent responses to the author’s replies."
)

_ACK_MESSAGE = "Received the review contents."

_TASK_INSTRUCTION = (
    "### Task:\n\n"
    "Please carefully read the provided text and extract the argumentative "
    "relationships in the following two categories:\n\n"
    "1. **Reviewer-Author Relationships:**\n\n"
    "Identify the relationships between each reviewer’s argument sentence and "
    "the corresponding author’s response.\n\n"
    "Use the following relation types:\n\n"
    "- Accept: The author fully accepts or agrees with the reviewer’s comment.\n\n"
    "- Reject: The author disagrees with or does not adopt the reviewer’s comment.\n\n"
    "- Clarify: The author provides additional explanations or clarifications.\n\n"
    "- Compromise: The author partially accepts the reviewer’s comment and "
    "proposes a middle-ground solution.\n\n"
    "- Extend: The author expands or supplements their response based on the "
    "reviewer’s comment.\n\n"
    "- Neutral: The author’s response does not clearly express an attitude or is "
    "neutral.\n\n"
    "2. **Inter-Reviewer Relationships:**\n\n"
    "Identify the relationships between argument sentences from different "
    "reviewers.\n\n"
    "Use the following relation types:\n\n"
    "- Agree: The reviewers hold consistent viewpoints or mutually support each "
    "other’s comments.\n\n"
    "- Disagree: The reviewers present conflicting viewpoints or directly refute "
    "each other.\n\n"
    "- Complement: Reviewers’ comments are complementary and cover different but "
    "related aspects.\n\n"
    "- Progressive: One reviewer’s comment builds upon or deepens another’s.\n\n"
    "- Independent: Reviewers’ comments are unrelated and focus on different "
    "issues independently.\n\n"
    "### Output Format:\n\n"
    "Please provide the extracted triples in the following format:\n\n"
    "- (Reviewer X: [argument sentence], Author: [argument sentence], [relation type])\n\n"
    "- (Reviewer X: [argument sentence], Reviewer Y: [argument sentence], [relation type])\n\n"
    "### Notes:\n\n"
    "- “Argument sentence” refers to a concise sentence that clearly expresses "
    "a viewpoint, criticism, suggestion, or justification.\n\n"
    "- Please focus on argument sentences and ignore background descriptions or "
    "non-argumentative text.\n\n"
    "- If no clear relation exists, skip that pair.\n\n"
    "### Example Output:\n\n"
    "{“Reviewer_Author_Relations”: [“(Reviewer 1: ‘The experiment settings lack "
    "sufficient diversity to fully validate the generalizability of the proposed "
    "method.’, Author: ‘We have added new experiments on additional datasets "
    "from different domains to enhance diversity and support generalization.’, "
    "Accept)”,\n\n"
    "…],\n\n"
    "“Inter_Reviewer_Relations”: [“(Reviewer 1: ‘The proposed model demonstrates "
    "significant novelty in its hierarchical reasoning structure.’, Reviewer 2: "
    "‘The hierarchical reasoning structure introduced is indeed novel and "
    "well-motivated.’, Agree)”,\n\n"
    "…]}\n\n"
    "Please extract all relevant triples from the provided text. Each triple must "
    "directly quote the original sentences without any paraphrasing, summarizing, "
    "or abbreviation. Ensure that the wording is fully preserved as in the "
    "original text. Follow the example and provide the final output in a single "
    "JSON object. Please strive to cover the full diversity of relationship types "
    "as comprehensively as possible. The extracted relationships should be "
    "complete, diverse, and richly capture the different types of interactions "
    "present in the text."
)


def _build_review_file(debate_log: DebateLog) -> str:
    """討論ログをTable5が想定する「review file」形式のテキストに整形する"""
    lines: list[str] = ["### Initial Review Comments:"]
    for s in debate_log.sentences:
        if s.stage == "initial_review":
            lines.append(f"\n##{s.speaker}: \n{s.text}")

    lines.append("\n### Author's Responses:")
    for s in debate_log.sentences:
        if s.stage == "author_response":
            lines.append(f"\n##{s.speaker}: \n{s.text}")

    lines.append("\n### Reviewers' Responses:")
    for s in debate_log.sentences:
        if s.stage == "reviewer_reevaluation":
            lines.append(f"\n##{s.speaker}:\n\n{s.text}")

    return "\n".join(lines)


# ============================================================
# LLM出力（引用文）から討論ログ発言idへの解決
#
# Table5のプロンプトはidではなく「発言の引用文」を出力させる形式のため、
# LLMは reviewer_sentence_id 等のフィールドに「Reviewer 1: <引用文>」の
# ような文字列を返す。これを討論ログの実在する発言idへ照合・解決する。
# ============================================================


def _normalize(text: str) -> str:
    """引用照合用にテキストを正規化する（空白圧縮・引用符/大文字小文字の統一）"""
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    return re.sub(r"\s+", " ", text).strip().lower()


def _parse_reference(ref: str) -> tuple[str | None, str]:
    """「Reviewer 1: 引用文」形式の文字列から (話者名, 引用文) を取り出す"""
    m = re.match(r"\s*\(?\s*(reviewer\s*(\d+)|author)\s*:\s*(.*)", ref, re.IGNORECASE | re.DOTALL)
    if m is None:
        return None, ref
    speaker = "Author" if m.group(2) is None else f"Reviewer {m.group(2)}"
    return speaker, m.group(3).strip().strip("'\"“”‘’")


def _resolve_sentence_id(
    ref: str, candidates: list[DebateSentence], known_ids: set[str]
) -> str | None:
    """LLMが返した参照（idまたは引用文）を実在する発言idへ解決する。
    解決できない場合はNoneを返す。"""
    if ref in known_ids:
        return ref

    speaker, quote = _parse_reference(ref)
    pool = [s for s in candidates if s.speaker == speaker] or candidates
    quote_norm = _normalize(quote)
    if not quote_norm:
        return None

    # まず完全包含（引用文が発言本文にそのまま含まれる）を探す
    for s in pool:
        if quote_norm in _normalize(s.text):
            return s.id

    # 引用が多少変形されている場合は、引用文の単語が最も多く含まれる発言を選ぶ
    quote_words = set(quote_norm.split())
    best_id, best_coverage = None, 0.0
    for s in pool:
        sentence_words = set(_normalize(s.text).split())
        coverage = len(quote_words & sentence_words) / len(quote_words)
        if coverage > best_coverage:
            best_id, best_coverage = s.id, coverage
    return best_id if best_coverage >= 0.5 else None


def _resolve_relations(
    result: RelationExtractionResult, debate_log: DebateLog
) -> RelationExtractionResult:
    """抽出結果内の参照をすべて実在する発言idへ解決し、
    解決できない関係は警告を出して除外する。重複関係も除去する。"""
    known_ids = {s.id for s in debate_log.sentences}
    reviewer_sentences = [s for s in debate_log.sentences if s.speaker.startswith("Reviewer")]
    author_sentences = [s for s in debate_log.sentences if s.speaker == "Author"]

    reviewer_author: list[ReviewerAuthorRelation] = []
    seen_ra: set[tuple[str, str, str]] = set()
    for rel in result.reviewer_author_relations:
        rid = _resolve_sentence_id(rel.reviewer_sentence_id, reviewer_sentences, known_ids)
        aid = _resolve_sentence_id(rel.author_sentence_id, author_sentences, known_ids)
        if rid is None or aid is None:
            logger.warning(
                "査読者-著者関係の参照先を特定できないためスキップ: %.60s... -> %.60s...",
                rel.reviewer_sentence_id, rel.author_sentence_id,
            )
            continue
        key = (rid, aid, rel.relation)
        if key not in seen_ra:
            seen_ra.add(key)
            reviewer_author.append(
                ReviewerAuthorRelation(reviewer_sentence_id=rid, author_sentence_id=aid, relation=rel.relation)
            )

    inter_reviewer: list[InterReviewerRelation] = []
    seen_ir: set[tuple[str, str, str]] = set()
    for rel in result.inter_reviewer_relations:
        sid = _resolve_sentence_id(rel.source_sentence_id, reviewer_sentences, known_ids)
        tid = _resolve_sentence_id(rel.target_sentence_id, reviewer_sentences, known_ids)
        if sid is None or tid is None:
            logger.warning(
                "査読者間関係の参照先を特定できないためスキップ: %.60s... -> %.60s...",
                rel.source_sentence_id, rel.target_sentence_id,
            )
            continue
        if sid == tid:
            # 同一発言への自己ループは意味を持たないため除外
            continue
        key = (sid, tid, rel.relation)
        if key not in seen_ir:
            seen_ir.add(key)
            inter_reviewer.append(
                InterReviewerRelation(source_sentence_id=sid, target_sentence_id=tid, relation=rel.relation)
            )

    return RelationExtractionResult(
        reviewer_author_relations=reviewer_author,
        inter_reviewer_relations=inter_reviewer,
    )


def extract_relations(debate_log: DebateLog) -> RelationExtractionResult:
    """討論ログから査読者-著者関係・査読者間関係を抽出する（Table5のプロンプトを使用）。"""
    logger.info("討論ログから関係を抽出中... (gpt-4.1-mini)")
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_build_review_file(debate_log)),
        AIMessage(content=_ACK_MESSAGE),
        HumanMessage(content=_TASK_INSTRUCTION),
    ]
    raw_result = _get_structured_llm().invoke(messages)
    # LLMが返す参照は引用文の形式（Table5準拠）のため、実在する発言idへ解決する
    result = _resolve_relations(raw_result, debate_log)
    logger.info(
        "関係抽出完了: reviewer_author=%d件, inter_reviewer=%d件（抽出%d件から解決）",
        len(result.reviewer_author_relations),
        len(result.inter_reviewer_relations),
        len(raw_result.reviewer_author_relations) + len(raw_result.inter_reviewer_relations),
    )
    return result
