# 査読エージェントの再実行

確認日: 2026-10-15

Common Corpusで全6工程を実行した記録と査読ログは
[2026-10-15の実行結果](../reports/2026-10-15-common-corpus/README.md)を参照。

## 場所と役割

- ローカル: `/Users/haya/research/program/pairreview-agents`
- リポジトリ: https://github.com/hayashi1917/pairreview-agents
- 入口: `main.py`
- 査読者3名の初期査読 → 著者の反論 → 査読者の再評価を生成する。
- 使用モデル: 討論は `gpt-4.1`、関係抽出・評価次元の分類は `gpt-4.1-mini`、埋め込みは `text-embedding-3-small`。
- 「著者」の応答もLLMによる模擬応答であり、実際の著者の回答・追加実験の実施を意味しない。

## 既存の環境で動かす

仮想環境と `.env` は残っているため、通常は再インストール不要。

```bash
cd /Users/haya/research/program/pairreview-agents
.venv/bin/python main.py --help
```

PDFを入力する場合:

```bash
.venv/bin/python main.py "/absolute/path/to/paper.pdf" \
  --output-dir output/my-paper
```

`OPENAI_API_KEY` と `MINERU_API_KEY` をこのフォルダの `.env` に設定する。
2026-10-15の確認では、OpenAIの3モデルへのアクセスは成功した。
既存のMinerUトークン内の有効期限は2026-10-07 22:04:45 JSTで、更新が必要。
APIキーはGitに追加しない。

## 前回のCommon Corpusを、PDFを再解析せずに動かす

前回の解析結果が `train_cache/` に残っている。次の操作で `main.py` 用の入力形式へ変換できる。
出力先を変えれば過去の実行結果も保存できる。

```bash
cd /Users/haya/research/program/pairreview-agents
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from src.preprocess import _content_list_to_paper_content

source = Path("train_cache/25369_Common_Corpus_The_Larges-8f67f8a2/mineru/content_list.json")
destination = Path("output/common-corpus-input.json")
paper = _content_list_to_paper_content(
    json.loads(source.read_text(encoding="utf-8")), "Common Corpus"
)
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(paper.model_dump_json(indent=2), encoding="utf-8")
PY
.venv/bin/python main.py output/common-corpus-input.json \
  --output-dir output/common-corpus-rerun
```

この方法ではMinerUを呼ばないため、`OPENAI_API_KEY` だけで実行できる。
`train_cache/` はGit管理外のため、別の端末ではPDFを解析し直すか、解析済み入力を別途用意する。

最小サンプルで確認する場合（架空の短い論文データ）:

```bash
.venv/bin/python main.py data/sample_mineru_output.json \
  --output-dir output/sample-rerun
```

## 出力と制限

- `debate_tree.json`: 査読者ごとの初期査読・模擬著者反論・再評価。
- `graph.json`: 討論から構築した異種グラフ。
- `prediction.json`: 採否判定と `used_trained_weights`。
- `logs/run_*.log`: 進行状況。

**2026-10-15の再開時点では `models/acceptance_model.pt` は存在しない。**
その状態でも最後まで動くが、採否は未学習のランダム初期重みによるため、
label・確率を論文の品質評価や採否予測として解釈しない。
査読コメントの生成は採否判定モデルとは独立して動作する。

前回（2026-07-09）の最新ログでは、10論文の学習用データ準備中、
2本目のQ-RAGの討論でHTTP 429が繰り返され、学習完了には至っていなかった。
今回も429が出た場合は、APIプロジェクトの利用制限を確認する。
実行にはOpenAI APIの料金が発生する。
