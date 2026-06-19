# 子ども医療費助成（港区） — 出典固定

**状態: VERIFIED（2026-06-12、並列リサーチエージェントによる公式一次情報調査）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 0歳〜18歳年度末（マル乳/マル子/マル青で連続カバー） |
| 助成内容 | 保険診療の自己負担分を助成 |
| 要件 | 区内在住 + 日本の健康保険加入 |
| 所得制限 | なし |

出典:
- 港区 子ども医療費助成: https://www.city.minato.tokyo.jp/kosodatesien/kodomo/kate/kodomoiryo.html

注意: 所得制限は消極的確認（公式ページに所得要件の記載なし、条例 https://www.city.minato.tokyo.jp/reiki/reiki_honbun/g104RG00000448.html にも所得要件条項なし。2023年撤廃の報道とも整合）。

意味論は渋谷区テンプレート（tests/golden/shibuya_kodomo_iryouhi/）と同一。
このファイルと cases.yaml・ルールは scripts/gen_ward_iryouhi.py が
data/ward_iryouhi_sources.yaml から生成する（手編集しない）。
区内在住はフォームの居住自治体選択から暗黙に充足。

source_url: https://www.city.minato.tokyo.jp/kosodatesien/kodomo/kate/kodomoiryo.html
source_quote: "こどもの医療費の自己負担分を助成"
