# 子ども医療費助成（豊島区） — 出典固定

**状態: VERIFIED（2026-06-12、並列リサーチエージェントによる公式一次情報調査）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 0歳〜18歳年度末（マル乳/マル子/マル青で連続カバー） |
| 助成内容 | 保険診療の自己負担分を助成 |
| 要件 | 区内在住 + 日本の健康保険加入 |
| 所得制限 | なし |

出典:
- 豊島区 子どもの医療費助成: https://www.city.toshima.lg.jp/261/kosodate/kosodate/teate-jose/015729.html

注意: 「保護者の所得制限はありません」と公式ページに明示。

意味論は渋谷区テンプレート（tests/golden/shibuya_kodomo_iryouhi/）と同一。
このファイルと cases.yaml・ルールは scripts/gen_ward_iryouhi.py が
data/ward_iryouhi_sources.yaml から生成する（手編集しない）。
区内在住はフォームの居住自治体選択から暗黙に充足。

source_url: https://www.city.toshima.lg.jp/261/kosodate/kosodate/teate-jose/015729.html
source_quote: "こどもの医療費の自己負担分を助成"
