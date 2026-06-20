# 千代田区障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り）**

| 項目 | 確定値 |
|---|---|
| 対象1-6（身体1-2/愛の手帳1-3/精神1級/難病/脳性まひ/戦傷病者） | 月額15,500円 |
| 対象7-8（身体3/愛の手帳4） | 月額10,500円 |
| 65歳以上 | 新規申請不可 |
| 所得制限 | あり（本人3,661,000円+380,000×N） |

出典（公式ページ直接読み取り）:
- 千代田区公式: https://www.city.chiyoda.lg.jp/koho/kenko/shogaisha/techo/teate/shinshin.html
- 「上記1～6の人は、月額15,500円」
- 「上記7・8の人は、月額10,500円」
- 「精神障害者保健福祉手帳1級の人」→ 対象3（grade_a, 15,500円）

ルールの条文対応:
- monthly(15500): ✓
- monthly(10500): ✓
- seishin_1 → grade_a: ✓（千代田区は精神1級=15,500円。足立・荒川はgrade_b）
- age >= 65 → ineligible: ✓

source_url: https://www.city.chiyoda.lg.jp/koho/kenko/shogaisha/techo/teate/shinshin.html
source_quote: "障害者福祉手当 月額15,500円 月額10,500円"
