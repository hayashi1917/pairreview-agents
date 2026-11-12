# SciAudit（ICLR 2027 投稿）での査読エージェント実行（2026年11月12日）

査読者が実際に読んだ版の原稿で、このエージェントの査読と実際の査読を比べるための実行。Google の Deep Review との比較の一部でもある。Deep Review の出力は [deep_review.md](deep_review.md)（2026-11-13 追加）。

## 入力の版

**査読者が読んだ版と同じ。** [SciAudit: Benchmarking MLLMs for Scientific Error Detection](https://openreview.net/forum?id=xagiYitqc0)（ICLR 2027 Submission 42373）の PDF を、著者の回答や改訂が出る前の 2026-11-12 に OpenReview から保存した。

- PDF の作成日時は 2026-09-25（投稿の締め切り日）で、46ページ。冒頭に「Under review as a conference paper at ICLR 2027」「Anonymous authors」とある。
- 投稿の最終更新は 2026-10-05。査読の公開は 2026-11-05 で、保存の時点で著者の回答はなかった。
- OpenReview の PDF の SHA-1 は `878e5f236b500b2fb2fc989b84c091f9e33fa52c`、SHA-256 は `0fc360d7fb45b23c150eda7e1ab181c5b63ac9b5bb837268237f4a1157306a53`。取得した PDF は共有しない。

APRES・Common Corpus では査読前の版が手に入らなかったが、今回はこの問題がない。

## 実行方法

APRES のときと同じ方法。タイトルを含む全文140,365文字と、全46ページの画像（長辺1,200ピクセル）を入力した。OpenReview の査読は入力していない。

```bash
.venv/bin/python reports/2026-11-12-sciaudit/run_submission_review.py /path/to/SciAudit.pdf
```

査読・著者役・再評価は gpt-4.1、関係抽出・分類は gpt-4.1-mini、埋め込みは text-embedding-3-small。採否判定の部分は未学習で、`prediction.json` の値（accept、0.52）は性能の根拠に使わない。著者役の回答は LLM による模擬応答。

1回目（16:01開始）は、開始直後に Mac がスリープしたため API の接続が切れ、5発言目のあとで止まった（[記録](execution_failed_sleep_1601.txt)）。スリープを止めて実行し直した2回目（22:54〜22:59、約5分）で6段階すべてが完了し、9発言、14ノード・20エッジを得た。

## 出力

- [9発言の全文](review.md) / [発言 JSON](turns.json)
- [実際の査読・Deep Review との比較](comparison.md)
- [Deep Review の出力](deep_review.md)
- [実行条件](run_metadata.json) / [実行記録](execution.txt)
- [討論ツリー](debate_tree.json) / [グラフ](graph.json) / [未学習の採否出力](prediction.json)

## 結果の要点

生成された3人の推薦は Accept with Minor Revisions、Strong Accept、Strong Accept で、再評価では3人とも「著者の回答で懸念はすべて解消した」とした。実際の査読者3人は評点3で、そのうち1人は弱い採択と書いている。

実際の査読者が挙げた具体的な指摘（Gold の候補を出したモデルの偏り、LLM による照合の妥当性、Table 4 に誤りのない箇所の対照がない、評価式で根拠を分けると点が下がる、など）は、生成された査読にはほぼ出なかった。重なったのは、Gold を専門家1人が確認していることと、Gold で見落とされた誤りがありうることの1点だけ。詳しくは[比較](comparison.md)。

比較は1名による読み合わせで、複数人による評価ではない。

## 追記（2026-11-13）：Deep Review との比較

Deep Review は評点や採否を出さないが、実際の査読者が挙げた具体的な論点11個のうち4個をはっきり、4個を一部拾った（このエージェントは一部が1個）。表の数値を再計算した指摘（表10の評価が思考なしの出力らしい、など）もあり、確かめた範囲では正しかった。一方、図4の分野別の論文数のうち3つを誤って記していた。詳しくは[比較](comparison.md)。
