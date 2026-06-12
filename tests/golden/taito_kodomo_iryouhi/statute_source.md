# 子ども医療費助成（台東区） — 出典固定

**状態: VERIFIED（2026-06-12、並列リサーチエージェントによる公式一次情報調査）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 0歳〜18歳年度末（マル乳/マル子/マル青で連続カバー） |
| 助成内容 | 保険診療の自己負担分を助成 |
| 要件 | 区内在住 + 日本の健康保険加入 |
| 所得制限 | なし |

出典:
- 台東区 子ども医療費助成: https://www.city.taito.lg.jp/kosodatekyouiku/kosodate/mokutei/teate_josei/iryohijosei/annai.html

注意: 重要な相違: 台東区は償還払い方式（医療機関で一旦全額支払い、後日区に申請して 口座振込で助成。公式に明記）。助成範囲（保険診療自己負担分）は他区と同一のため decided 詳細は共通の in_kind(jiko_futan_josei) とし、支払い方式の相違は本ノートで 固定。所得制限は消極的確認（対象要件に所得条項なし）。

意味論は渋谷区テンプレート（tests/golden/shibuya_kodomo_iryouhi/）と同一。
このファイルと cases.yaml・ルールは scripts/gen_ward_iryouhi.py が
data/ward_iryouhi_sources.yaml から生成する（手編集しない）。
区内在住はフォームの居住自治体選択から暗黙に充足。
