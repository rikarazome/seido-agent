# 国民健康保険料の軽減（7割・5割・2割）— 出典固定

**状態: VERIFIED（2026-06-21, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 7割軽減 | 所得 ≤ 430,000円 |
| 5割軽減 | 所得 ≤ 430,000 + 295,000 × (被保険者数+1) |
| 2割軽減 | 所得 ≤ 430,000 + 545,000 × (被保険者数+1) |

条文根拠:
- 国民健康保険法81条、施行令29条の7
- 計算式: keigen_limit_5(N, L) :- L is 430000 + 295000 * (N + 1) ✓
- 計算式: keigen_limit_2(N, L) :- L is 430000 + 545000 * (N + 1) ✓

出典:
- 厚労省: https://www.mhlw.go.jp/stf/newpage_21061.html
- 証拠: page_snapshot_2026-06-21.txt

source_url: https://www.mhlw.go.jp/stf/newpage_21061.html
source_quote: "国民健康保険料 軽減 7割 5割 2割"
