# 荒川区心身障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り）**

| 項目 | 確定値 |
|---|---|
| grade_a（身体1-2/愛の手帳1-3/脳性まひ/難病） | 月額15,500円 |
| grade_b（身体3/愛の手帳4/精神1級） | 月額9,500円 |
| 65歳以上 | 新規申請不可 |
| 所得制限 | あり |

出典（公式ページ直接読み取り）:
- 荒川区公式: https://www.city.arakawa.tokyo.jp/a030/shougaisha/teate/sinsinsyougaisyateat.html
- 「月額15,500円」「月額9,500円」
- 「精神障害者保健福祉手帳１級の方は、月額9,500円」
- 「障がい者となった年齢が65歳以上の方は新規申請ができません」

ルールの条文対応:
- monthly(15500): ✓
- monthly(9500): ✓
- seishin_1 → grade_b: ✓（条文で精神1級が明記）
- age >= 65 → ineligible: ✓

source_url: https://www.city.arakawa.tokyo.jp/a030/shougaisha/teate/sinsinsyougaisyateat.html
source_quote: "心身障害者福祉手当（区の制度） 月額15,500円 月額9,500円"
