# 江東区子ども医療費助成 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 18歳到達後の最初の3月31日まで |
| 助成内容 | 保険診療の自己負担分を助成（in_kind） |
| 要件 | 江東区住民登録 + 健康保険加入 |
| 所得制限 | なし（「保護者の所得制限はありません」と明記） |
| 除外 | 生活保護、児童福祉施設入所、里親委託 |

出典（公式ページ直接読み取り）:
- 江東区公式: https://www.city.koto.lg.jp/260502/kodomo/kosodate/teate/20120401.html
- 「保険診療の自己負担分を区が助成する制度」
- 「本制度に保護者の所得制限はありません」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind): ✓
- 所得制限なし: ✓

source_url: https://www.city.koto.lg.jp/260502/kodomo/kosodate/teate/20120401.html
source_quote: "子ども医療費助成"
