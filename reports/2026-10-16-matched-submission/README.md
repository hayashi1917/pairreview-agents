# 査読前の原稿を使った査読エージェントの再実行

対象は **Score-based Causal Discovery from Heterogeneous Data**（ICLR 2021投稿、Paper999）。
Common Corpusは初回査読時の原稿を確認できなかったため、比較対象を変更した。

## 原稿の版の確認

[ARIES](https://aclanthology.org/2024.acl-long.377/) Section 4.1は、初回査読より前に投稿された最後のPDFをsource、改訂後のPDFをtargetとして収集している。
[配布元の説明](https://github.com/allenai/aries)に従って `paper_edits.jsonl` を取得し、先頭レコード `lcNa5mQ-CSb` を選んだ。生成結果を見て対象を選び直していない。

- **使用した査読前PDF**: [ynuneF8WA0](https://openreview.net/references/pdf?id=ynuneF8WA0)。14ページ。PDFの作成日時は2020年10月2日。
- **使用しなかった改訂後PDF**: `mvQwFp1oTz`。現在のフォーラムがReviewed Versionとして表示するPDFとは区別する。
- [実際の査読・議論](https://openreview.net/forum?id=lcNa5mQ-CSb)。初回公式査読は2020年10月27日〜11月7日、著者の改訂報告は11月21日。
- ファイルのハッシュ、データセットのレコード、出典IDは [source_provenance.json](source_provenance.json) に記録した。

## 入力と再実行方法

Popplerで抽出した全文と、同じPDFの全14ページの画像（長辺1200ピクセル）を渡す。タイトル、図、表、参考文献、付録を含む。実際の査読と著者回答は入力しない。
既存の討論・関係抽出・グラフ構築・推論処理を使い、[実行用スクリプト](run_submission_review.py)でページ画像を追加入力する。査読の指示文や使用モデルは前回と同じ。

```bash
.venv/bin/python reports/2026-10-16-matched-submission/run_submission_review.py /path/to/source.pdf
```

PDFのハッシュを照合してから実行する。取得したPDF・ページ画像・本文・APIキーは共有しない。
採否判定部分の学習は実施していない。採否ラベル付きの論文データセットによる学習が必要で、今週は実施できなかったため、未学習モデルの確率や採否を評価に使わない。

## 比較の範囲

生成した初期査読3件を、実際の初期公式査読4件と論点ごとに比較する。査読者同士の一対一対応は付けない。著者回答・追記は初期査読の比較とは分ける。
実際の査読をすべて正解とみなさず、一般的な改善要求と、具体的な誤りの指摘を区別する。
古い公開論文なので、使用モデルの事前学習に論文や査読が含まれた可能性までは排除できない。

## 実行結果（2026年10月16日追記）

00:12:37〜00:16:15 JST、約3分38秒で6段階すべてが完了した。3名分・9発言、14ノード・23エッジのグラフを取得した。HTTP応答20件はすべて成功した。
3名とも初期査読で採択を支持したが、実際の初期査読にあった定理1の標本抽出の前提への具体的な疑問は出ていなかった。

- [査読ログ全文](review.md) / [整形前テキスト](review.txt) / [9発言のJSON](turns.json)
- [論点ごとの厳密な比較](comparison.md)
- [実行条件・検証結果](run_metadata.json) / [実行ログ](execution.txt)
- [討論ツリー](debate_tree.json) / [グラフ](graph.json) / [未学習の採否出力](prediction.json)

9発言の構造、グラフの全参照先、JSONの型、確率の総和と未学習フラグ、完了記録を確認した。
