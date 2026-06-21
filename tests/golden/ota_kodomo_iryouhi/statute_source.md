# 大田区児童医療費助成制度 — 出典固定

**状態: VERIFIED（2026-06-21, 公式ページ全文読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 0歳から18歳到達後最初の3月31日まで |
| 助成内容 | 保険診療の自己負担分 + 入院時食事代 + 治療用装具（in_kind） |
| 要件 | 大田区住民登録 + 健康保険加入 |
| 所得制限 | なし（ページに記載なし） |
| 除外 | 生活保護、児童福祉施設措置入所、里親委託 |
| 特記 | 入院時の食事療養標準負担額も助成対象（板橋・葛飾は対象外） |

出典（公式ページ全文読み取り）:
- 大田区公式: https://www.city.ota.tokyo.jp/seikatsu/kodomo/teate/kodomonyuui.html
- 「保険診療の対象となる医療費、薬剤費等の自己負担分」
- 「入院時の食事療養標準負担額、治療用装具（健康保険組合から支給決定された場合のみ）」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind(jiko_futan_josei)): ✓
- 所得制限なし: ✓

source_url: https://www.city.ota.tokyo.jp/seikatsu/kodomo/teate/kodomonyuui.html
source_quote: "保険診療の自己負担分 入院時の食事療養標準負担額も助成"
