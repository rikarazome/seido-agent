# 品川区障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 第1種（身体1-2/愛1-3/脳性まひ） | 月額15,500円 |
| 第2種 難病 | 月額15,500円 |
| 第2種（身体3/愛4/精神1級/戦傷病者） | 月額8,500円 |
| 精神1級 | R2.4.1から対象。第2種(8,500円) |
| 65歳以上 | 新規申請不可 |
| 所得制限 | あり |

出典（公式ページ直接読み取り）:
- 品川区公式: http://www.city.shinagawa.tokyo.jp/PC/kenkou/kenkou-syogai/kenkou-syogai-teate/hpg000024970.html
- 「第1種手当 月額 15,500円」「第2種手当 月額 8,500円」
- 「精神障害者保健福祉手帳1級を所持している方（令和2年4月1日より）」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- monthly(15500): ✓
- monthly(8500): ✓
- seishin_1 → grade_b(8500): ✓
- age >= 65 → ineligible: ✓

source_url: http://www.city.shinagawa.tokyo.jp/PC/kenkou/kenkou-syogai/kenkou-syogai-teate/hpg000024970.html
source_quote: "障害者福祉手当（区制度）15,500円 8,500円 精神障害者保健福祉手帳1級"
