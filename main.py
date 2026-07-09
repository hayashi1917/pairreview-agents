"""
査読討論グラフを用いた論文採否推論システム メインスクリプト

処理の流れ:
  1. 論文前処理        : PDF入力ならMinerU APIで解析、json入力なら読み込みのみ
  2. マルチエージェント討論: 3名の査読者と著者によるLLM討論ログ生成
  3. 関係抽出          : 討論ログから査読者-著者関係/査読者間関係を抽出
  4. 異種グラフ構築     : Title/EvaluationDimension/ReviewerOpinion/AuthorOpinionのグラフ構築
  5. HGTによるグラフ推論 : 異種グラフをHGTに入力し特徴量h_concatを得る
  6. 採否判定(FFN)     : h_concatをFFNに通してaccept/rejectを判定

処理の進行状況は標準出力とログファイル(logs/run_*.log)の両方に出力され、
討論ツリー・異種グラフ・採否判定結果は output/ 以下にJSONとして保存される。
"""
import argparse
import logging

from dotenv import load_dotenv

from src.debate import run_multi_agent_debate
from src.graph_builder import build_heterogeneous_graph
from src.hgt_reasoning import (
    DEFAULT_MODEL_PATH,
    classify_accept_reject,
    load_or_init_model,
    run_hgt_reasoning,
)
from src.logging_config import setup_logging
from src.persistence import save_debate_tree, save_graph, save_prediction
from src.preprocess import load_paper_content, load_paper_content_from_pdf
from src.relation_extraction import extract_relations

logger = logging.getLogger(__name__)


def main(input_path: str, output_dir: str, model_path: str) -> None:
    # .env / .env.local からOPENAI_API_KEY・MINERU_API_KEY等を読み込む
    # （シェルに古いキーがexportされていても.envの値を優先する）
    load_dotenv(override=True)
    load_dotenv(".env.local", override=True)

    # 標準出力とログファイルの両方に進行状況を出力する
    setup_logging()

    # 1. 論文前処理: PDFならMinerU APIで解析、jsonなら読み込みのみでPaperContentへ変換
    logger.info("[1/6] 論文前処理を開始します。")
    if input_path.lower().endswith(".pdf"):
        # MinerUの生出力(full.md, content_list.json)もoutput_dir以下に保存する
        paper = load_paper_content_from_pdf(input_path, save_dir=f"{output_dir}/mineru")
    else:
        paper = load_paper_content(input_path)

    # 2. マルチエージェント討論: 査読者3名+著者による討論ログを生成
    logger.info("[2/6] マルチエージェント討論を開始します。")
    debate_log = run_multi_agent_debate(paper)
    save_debate_tree(debate_log, f"{output_dir}/debate_tree.json")

    # 3. 討論からの関係抽出: 査読者-著者関係・査読者間関係を推論
    logger.info("[3/6] 討論からの関係抽出を開始します。")
    relations = extract_relations(debate_log)

    # 4. 異種グラフ構築: Title/EvaluationDimension/ReviewerOpinion/AuthorOpinionのグラフを構築
    logger.info("[4/6] 異種グラフ構築を開始します。")
    graph = build_heterogeneous_graph(paper.title, debate_log, relations)
    save_graph(graph, f"{output_dir}/graph.json")

    # 5. HGTによるグラフ推論: 異種グラフをHGTに入力し特徴量h_concatを得る
    #    学習済みチェックポイントがあればHGT・FFNの重みを読み込む
    logger.info("[5/6] HGTによるグラフ推論を開始します。")
    model = load_or_init_model(model_path)
    hgt_result = run_hgt_reasoning(graph, model)

    # 6. 採否判定(FFN): h_concatをFFNに通してaccept/rejectを判定
    logger.info("[6/6] FFNによる採否判定を開始します。")
    prediction = classify_accept_reject(hgt_result.h_concat, model)
    save_prediction(prediction, f"{output_dir}/prediction.json")

    logger.info("全ステージが完了しました。出力先: %s", output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="査読討論グラフを用いた論文採否推論システム")
    parser.add_argument(
        "input_path",
        help="論文PDFのパス（MinerU APIで解析）、またはMinerUで抽出済みのjsonファイルのパス",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="討論ツリー・異種グラフ・採否判定結果の保存先ディレクトリ（デフォルト: output）",
    )
    parser.add_argument(
        "--model-path",
        default=DEFAULT_MODEL_PATH,
        help=f"train_fnn.pyで学習したモデルのパス（デフォルト: {DEFAULT_MODEL_PATH}）",
    )
    args = parser.parse_args()
    main(args.input_path, args.output_dir, args.model_path)
