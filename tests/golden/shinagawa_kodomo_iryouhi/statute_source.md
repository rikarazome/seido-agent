# 品川区子どもすこやか医療費助成 — 出典固定

**状態: VERIFIED（2026-06-21, 公式ページ全文読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 制度名 | 子どもすこやか医療費助成（品川区独自名称） |
| 対象年齢 | 0歳～18歳到達後最初の3月31日まで |
| 助成内容 | 保険適用の自己負担分 + 入院時食事代 + 治療用装具（in_kind） |
| 要件 | 品川区住民登録 + 健康保険加入 |
| 所得制限 | なし（ページに記載なし） |
| 除外 | 生活保護、児童福祉施設入所、里親委託 |
| 特記 | 食事代・治療用装具も対象（ただし窓口提示では使えず後日申請） |

出典（公式ページ全文読み取り）:
- 品川区公式: http://www.city.shinagawa.tokyo.jp/PC/kodomo/kodomo-iryohizyosei/hpg000017744.html
- 「保険適用の医療費の自己負担分」
- 「入院時の食事療養費標準負担額（食事代）」も助成対象
- 「治療用装具（補装具・治療用メガネなど）」も助成対象
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind(jiko_futan_josei)): ✓
- 所得制限なし: ✓

source_url: http://www.city.shinagawa.tokyo.jp/PC/kodomo/kodomo-iryohizyosei/hpg000017744.html
source_quote: "保険適用の医療費の自己負担分 入院時の食事療養費標準負担額も助成"
