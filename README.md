# pairreview-agents

査読討論グラフを用いた論文採否推論システム。

既存環境での起動方法・前回の解析キャッシュの再利用・再開時の確認事項は
[査読エージェントの再実行](docs/restart.md)を参照。

論文PDF（またはMinerU抽出済みjson）を入力とし、LLMによるマルチエージェント査読討論を生成、
その討論から異種グラフを構築してHGT（Heterogeneous Graph Transformer）で推論する。

## 処理の流れ

1. **論文前処理** — PDF入力ならMinerU公式APIで解析、json入力なら読み込みのみ
2. **マルチエージェント討論** — 査読者3名+著者によるLLM討論ログ生成
3. **関係抽出** — 討論ログから査読者-著者関係・査読者間関係を抽出
4. **異種グラフ構築** — Title / EvaluationDimension / ReviewerOpinion / AuthorOpinion のグラフ構築
5. **HGTによるグラフ推論** — 異種グラフから特徴量 h_concat を取得
6. **採否判定(FFN)** — h_concat をFFN（2層NN + Softmax）に通して accept/reject を判定。
   学習済みモデル（`models/acceptance_model.pt`）があれば自動で読み込み、
   無ければ未学習の重みで動作し警告を出す（学習方法は後述）

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`.env.example` をコピーして `.env` を作成し、APIキーを設定する:

```bash
cp .env.example .env
```

- `OPENAI_API_KEY` — LLM討論・関係抽出に使用
- `MINERU_API_KEY` — PDF解析に使用（[mineru.netのAPI管理ページ](https://mineru.net/apiManage)で発行）。
  抽出済みjsonを入力する場合は不要

## 使い方

```bash
# 論文PDFから実行（MinerU APIで解析）
python main.py paper.pdf

# 抽出済みjsonから実行
python main.py data/sample_mineru_output.json

# 出力先の変更（デフォルト: output/）
python main.py paper.pdf --output-dir results

# 学習済みモデルの指定（デフォルト: models/acceptance_model.pt）
python main.py paper.pdf --model-path models/acceptance_model.pt
```

## 採否判定モデル（HGT+FFN）の学習

学習に必要なのは **論文** と **学会への採否結果（accept/reject）** のペアのみ。
以下の形式のJSONファイルを用意する（`data/train_dataset.example.json` 参照）:

```json
[
  {"paper": "papers/example1.pdf", "label": "accept"},
  {"paper": "data/example2_mineru_output.json", "label": "reject"},
  {"paper": "output/example3/graph.json", "label": "accept"}
]
```

`paper` には PDF / MinerU抽出済みjson / `main.py` が出力した構築済み `graph.json` の
いずれも指定できる。PDF・MinerU json の場合は討論生成〜グラフ構築（Stage2-4）を
自動実行し、結果を `train_cache/` にキャッシュするため、2回目以降の学習では
LLM・Embedding APIを呼ばずに再学習できる。

```bash
# 学習（HGTとFFNをend-to-endにクロスエントロピー学習）
python train_fnn.py dataset.json

# エポック数・学習率・検証分割を指定する場合
python train_fnn.py dataset.json --epochs 100 --lr 1e-3 --val-ratio 0.2
```

チェックポイントは `models/acceptance_model.pt` に保存され、
次回以降の `python main.py ...` が自動で読み込んで採否判定に使用する。

## 出力

- `output/debate_tree.json` — 討論ツリー
- `output/graph.json` — 異種グラフ
- `output/prediction.json` — FFNによる採否判定結果（label / 確率 / 学習済み重み使用の有無）
- `output/mineru/` — MinerUの生出力（full.md, content_list.json）。PDF入力時のみ
- `logs/run_*.log` — 実行ログ

## ディレクトリ構成

```
main.py                     # メインスクリプト
train_fnn.py                # 採否判定モデル（HGT+FFN）の学習スクリプト
src/
  preprocess.py             # Stage1: 論文前処理（PDF/json → PaperContent）
  mineru_client.py          # MinerU公式APIクライアント
  debate.py                 # Stage2: マルチエージェント討論
  relation_extraction.py    # Stage3: 討論からの関係抽出
  graph_builder.py          # Stage4: 異種グラフ構築
  hgt_reasoning.py          # Stage5: HGTによるグラフ推論 / Stage6: FFNによる採否判定
  schemas.py                # 全ステージ共通のPydanticデータモデル
  persistence.py            # 討論ツリー・グラフ・判定結果のJSON保存
  logging_config.py         # ロギング設定
data/
  sample_mineru_output.json      # 抽出済みjsonのサンプル
  train_dataset.example.json     # 学習データセットの記述例
models/                     # 学習済みチェックポイント（train_fnn.pyが生成）
train_cache/                # 学習用の討論グラフ・Embeddingキャッシュ（同上）
```
