# 子ども医療費助成（世田谷区） — 出典固定

**状態: VERIFIED（2026-06-12、並列リサーチエージェントによる公式一次情報調査）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 0歳〜18歳年度末（マル乳/マル子/マル青で連続カバー） |
| 助成内容 | 保険診療の自己負担分を助成 |
| 要件 | 区内在住 + 日本の健康保険加入 |
| 所得制限 | なし |

出典:
- 世田谷区 子ども等医療費助成制度: https://www.city.setagaya.lg.jp/02413/1305.html

注意: 所得制限は消極的確認（公式ページ・案内PDF・対象外者リストのいずれにも所得要件の記載なし。渋谷区と同じ確認水準）。条例本文の明示条文は未確認。

意味論は渋谷区テンプレート（tests/golden/shibuya_kodomo_iryouhi/）と同一。
このファイルと cases.yaml・ルールは scripts/gen_ward_iryouhi.py が
data/ward_iryouhi_sources.yaml から生成する（手編集しない）。
区内在住はフォームの居住自治体選択から暗黙に充足。

source_url: https://www.city.setagaya.lg.jp/02413/1305.html
source_quote: "子ども等医療費助成制度"
