# 板橋区子ども医療費助成 — 出典固定

**状態: VERIFIED（2026-06-21, 公式ページ全文読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 出生から18歳になった日以降の最初の3月31日まで |
| 助成内容 | 健康保険診療の範囲内の自己負担分の医療費を助成（in_kind） |
| 要件 | 板橋区住民登録 + 国内健康保険加入 |
| 所得制限 | なし（ページに所得制限の記載なし） |
| 除外 | 生活保護、児童福祉施設入所、里親委託 |
| 注意 | 入院時食事代は助成対象外（港区等と異なる） |

出典（公式ページ全文読み取り）:
- 板橋区公式: https://www.city.itabashi.tokyo.jp/kosodate/teate/iryohi/1053428/1053072.html
- 「出生から18歳になった日以降の最初の3月31日までの間」
- 「健康保険診療の範囲内の自己負担分の医療費を助成」
- 「入院時の食事療養標準負担額（食事代）は助成できません」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind(jiko_futan_josei)): ✓
- 所得制限なし: ✓

source_url: https://www.city.itabashi.tokyo.jp/kosodate/teate/iryohi/1053428/1053072.html
source_quote: "健康保険診療の範囲内の自己負担分の医療費を助成"
