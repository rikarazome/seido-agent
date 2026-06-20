# 大田区心身障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 身体1-2/愛1-3/脳性まひ（20歳以上） | 月額17,500円 |
| 身体1-2/愛1-3/脳性まひ（20歳未満） | 月額4,500円 |
| 難病（20歳以上） | 月額12,000円 |
| 難病（20歳未満） | 月額4,500円 |
| 精神1級/身体3/愛4 | 月額4,500円 |
| 65歳以上 | 新規申請不可 |
| 所得制限 | あり |

出典（公式ページ直接読み取り）:
- 大田区公式: https://www.city.ota.tokyo.jp/seikatsu/fukushi/shougai/teate_nenkin/ootaku.html
- 「精神障害者保健福祉手帳1級(平成28年4月1日から対象となりました)」
- 「精神障害者保健福祉手帳1級 ・身体障害者手帳3級 ・愛の手帳4度 0歳～ 4,500円」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- monthly(17500): ✓
- monthly(4500): ✓
- seishin_1 → grade_b(4500): ✓
- age >= 65 → ineligible: ✓

source_url: https://www.city.ota.tokyo.jp/seikatsu/fukushi/shougai/teate_nenkin/ootaku.html
source_quote: "大田区心身障害者福祉手当 17,500円 4,500円 精神障害者保健福祉手帳1級"
