# 足立区心身障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り）**

| 項目 | 確定値 |
|---|---|
| grade_a（身体1-2級/愛の手帳1-3度） | 月額15,500円、20歳以上65歳未満 |
| grade_b（身体3級/愛の手帳4度） | 月額7,750円、65歳未満 |
| 所得制限 | あり（v1では省略） |
| 除外 | 施設入所中、65歳以上の新規申請 |

出典（公式ページ直接読み取り）:
- 足立区公式: https://www.city.adachi.tokyo.jp/shogai/fukushi-kenko/shinshin/teate-s-shogaisha.html
- 「（１）支給月額１５,５００円の対象者 申請日において２０歳以上６５歳未満」
- 「（２）支給月額７,７５０円の対象者 申請日において６５歳未満」

ルールの条文対応:
- monthly(15500): 条文の15,500円に対応 ✓
- monthly(7750): 条文の7,750円に対応 ✓
- age >= 65 → ineligible: 条文の65歳未満に対応 ✓
- grade_a の20歳下限: ルールに未実装（v1簡略化。20歳未満は児童育成手当対象）

source_url: https://www.city.adachi.tokyo.jp/shogai/fukushi-kenko/shinshin/teate-s-shogaisha.html
source_quote: "障がい者福祉手当（区の制度） 支給月額15,500円 支給月額7,750円"
