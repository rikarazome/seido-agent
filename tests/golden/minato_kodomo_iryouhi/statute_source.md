# 港区子ども医療費助成 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 18歳到達後最初の3月31日まで |
| 助成内容 | 自己負担分 + 入院時食事代（in_kind） |
| 要件 | 港区住民登録 + 日本の公的健康保険加入 |
| 所得制限 | なし |
| 除外 | 生活保護、児童福祉施設入所、里親委託 |

出典（公式ページ直接読み取り）:
- 港区公式: https://www.city.minato.tokyo.jp/kosodatesien/kodomo/kate/kodomoiryo.html
- 「18歳に達する日以後の最初の3月31日までの子ども」
- 「医療費の自己負担分を港区が助成する制度」
- 「入院時の食事療養標準負担額も助成の対象」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind): ✓
- 所得制限なし: ✓

source_url: https://www.city.minato.tokyo.jp/kosodatesien/kodomo/kate/kodomoiryo.html
source_quote: "子ども医療費助成"
