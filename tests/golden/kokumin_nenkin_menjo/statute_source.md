# 国民年金保険料の免除・猶予 — 出典固定

**状態: VERIFIED（2026-06-21, 公式ページ直接読み取り + page_snapshot保存）**

| 区分 | 所得基準 |
|---|---|
| 全額免除 | (扶養親族等の数+1)×35万円+32万円以下 |
| 3/4免除 | 88万円+38万円×扶養親族等の数以下 |
| 半額免除 | 128万円+38万円×扶養親族等の数以下 |
| 1/4免除 | 168万円+38万円×扶養親族等の数以下 |

条文根拠: 国民年金法90条・90条の2

計算式照合:
- zenmen_limit(N, L) :- L is (N + 1) * 350000 + 320000 ✓
- menjo34_limit(N, L) :- L is 880000 + 380000 * N ✓

出典:
- 日本年金機構: https://www.nenkin.go.jp/service/kokunen/menjo/20150428.html
- 「全額免除 (扶養親族等の数+1)×35万円+32万円以下」
- 証拠: page_snapshot_2026-06-21.txt

source_url: https://www.nenkin.go.jp/service/kokunen/menjo/20150428.html
source_quote: "国民年金保険料の免除制度"
