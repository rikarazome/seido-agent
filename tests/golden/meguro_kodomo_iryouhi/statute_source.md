# 目黒区子ども医療費助成制度 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 18歳到達後最初の3月31日まで |
| 助成内容 | 保険診療の自己負担額を助成 + 入院時食事代（in_kind） |
| 要件 | 目黒区住民登録 + 国内健康保険加入 |
| 所得制限 | なし |
| 除外 | 生活保護、児童福祉施設措置入所、里親委託 |

出典（公式ページ直接読み取り）:
- 目黒区公式: https://www.city.meguro.tokyo.jp/kosodateshien/kosodatekyouiku/kosodate/toha.html
- 「18歳到達後最初の3月31日までのかたが受給対象者」
- 「保険診療でかかった医療費の自己負担額を区が助成する制度」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind): ✓
- 所得制限なし: ✓

source_url: https://www.city.meguro.tokyo.jp/kosodateshien/kosodatekyouiku/kosodate/toha.html
source_quote: "子ども医療費助成制度とは"
