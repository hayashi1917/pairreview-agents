# 同じ査読前原稿による比較

対象: *Score-based Causal Discovery from Heterogeneous Data*（ICLR 2021投稿）。[公式フォーラム](https://openreview.net/forum?id=lcNa5mQ-CSb)。
使用原稿はARIESのsource_pdf_id `ynuneF8WA0`。版の根拠は [source_provenance.json](source_provenance.json)。
生成側は [review.md](review.md) の初期査読3件。著者役の返答・再評価は初期査読の照合から除いた。
以下は筆者による論点の照合であり、複数評価者による採点や精度測定ではない。

## 公式査読

| 査読者 | 評点 | 参照 |
|---|---:|---|
| AnonReviewer5 | 7 | [7jGBt5Gh-4f](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=7jGBt5Gh-4f) |
| AnonReviewer2 | 3 | [TO6pqnJEM6c](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=TO6pqnJEM6c) |
| AnonReviewer3 | 5 | [3njY0I1L9pk](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=3njY0I1L9pk) |
| AnonReviewer4 | 6 | [FcdQcUHhHkZ](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=FcdQcUHhHkZ) |

全員の表示信頼度は4。公式査読者と生成側Reviewer 1〜3には対応関係がない。

## 初期査読の具体的な指摘

| 論点 | 公式査読の指摘 | 生成側の根拠・対応 | 照合結果 |
|---|---|---|---|
| 定理1と標本抽出の前提 | AnonReviewer2: 固定されたドメインのデータをまとめただけで、P(V,C)から独立同分布の標本と扱えるのか。定理の成立に疑問 | R1-I-001「Theoretical Guarantees」は証明を厳密と評価。R2-I-001「Writing and Presentation」、R3-I-001「Theoretical Guarantees」も理論を肯定 | 該当する具体的な疑問なし。仮定が強いという一般論とは異なる |
| MDSの各項・構成要素の寄与 | AnonReviewer3/4: 構成要素や式3・4の項を分けた検証 | R2-I-001「Ablation and Analysis」、R3-I-001「Ablation Studies」がMDSの項や二段階探索の比較を要求 | 対応あり。R1のカーネル・正則化係数の感度分析要求とは分ける |
| 分布変化の難しさ | AnonReviewer3: 偽の辺の数や分布差の大きさを示し、複数ドメインの難しさを説明してほしい | R1/R2はドメイン指標の誤指定や仮定違反での頑健性を要求 | 関連するが部分対応。分布差と偽の辺を具体的に問う指摘とは同一ではない |
| 専門用語の説明 | AnonReviewer3: causal sufficiency、causal modulesの初出説明 | R1/R2/R3は記法の密度、カーネル、HSICなどの説明改善を要求 | 読みやすさという大枠は共通。指定した用語の照合では同一ではない |
| 新規性と先行研究 | AnonReviewer4: Huangらの研究からの改善は小さいのではないか | R3-I-001「Positioning Among Recent Work」はCD-NOD等との差を明確にするよう要求。3件とも手法の新規性自体は肯定 | 差の説明要求は部分対応。改善が小さいとの評価は出ていない |
| 共分散と因果方向の根拠 | AnonReviewer4: 共分散から因果方向へ結び付ける根拠、θを別ノードとする理由を質問 | 初期査読3件に同じ問いなし。仮定の強さやカーネルの難しさには触れる | 具体的対応なし |
| 探索手順との接続 | AnonReviewer4: Algorithm 2や方策勾配探索へMDSを組み込む説明が不足 | R2-I-001は探索戦略の比較・分析を要求 | 部分対応。実装手順の説明不足と実験比較は区別する |
| ベイジアンネットワークの混合 | AnonReviewer5: 混合モデルの関連研究を引用してほしい | 初期査読3件に該当する引用要求なし | 対応なし |
| ドメイン間の変数集合 | AnonReviewer5: 全ドメインで同じ変数が観測される必要があるのか | R3-I-001は構造変化を扱わないと述べるが、変数集合が異なる場合を問わない | 同一の問いではない |
| 骨格推定の誤りと退化 | AnonReviewer5: 骨格推定を誤ったときも退化の問題が起きるのか | R1/R2は退化の説明を分かりやすくするよう要求するが、骨格推定の誤りとの関係を問わない | 具体的対応なし |

生成側独自の指摘として、計算時間・メモリ、追加の実データ、カーネルや正則化係数の感度分析がある。これらは今回の4件の初期査読との一致だけで有用性を判断できない。
また、公式査読のすべてを正解とみなしていない。例えばAnonReviewer4が定義を質問した関数hは、元原稿の付録A.2・式5に定義がある。「公式査読と違う」だけで誤りと判定しない。

## 著者回答後と最終決定

初期査読とは別に、[11月23日の追加質問](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=ibBO2ftZHbA)では、AnonReviewer2が定理1の一方向を反例で問題にしている。[回答後の追記](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=biExnJ72bO)にも疑問が残る。
これは初回査読に含まれた反例として数えない。著者の[改訂報告](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=rtHp13sc2JU)には、定理1と証明の修正、説明の追加、アブレーション結果の追加が記されている。
[最終決定](https://openreview.net/forum?id=lcNa5mQ-CSb&noteId=BfiTNTAh2MZ)はRejectで、正しさと説明への懸念を理由として挙げる。

生成側は3名とも初期査読で軽微な修正を伴う採択を推薦した。数値を出したのはR2のみ（8/10）で、公式評点の平均と同じ尺度だと仮定して差を計算しない。
模擬著者は追加実験を約束し、A-R2-001では未確認の予備結果にも言及するが、これは実際の実験結果ではない。
R1-RE-001は各点をResolved、R2-RE-001も懸念が解消したとし、R3-RE-001も採択支持を維持する。実際の議論とは、争点も与えた著者回答も異なるので、再評価性能の比較にはならない。

## 今回の結論と限界

同じ査読前の版にそろえても、今回の3件の生成査読には、定理の前提を疑う具体的な問いが出ず、理論面を肯定していた。改善案は出るが、論文の重要な問題を点検できているかは別に確かめる必要がある。
原稿の版はそろえたが、単一論文・単一実行・単独の照合であり、性能の一般化や数値的な精度評価はしていない。公開済みの古い論文・査読なので事前学習への混入も排除できない。ページ画像は長辺1200ピクセルに縮小している。
Common Corpusの前回結果との違いを、版合わせや画像入力による改善・悪化の効果とは解釈しない。
