# 板橋区心身障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 1-5（身体1-2/愛1-3/脳性まひ/戦傷病者/難病） | 月額15,500円 |
| 6-9（身体3/愛4/精神1級/戦傷病者4項症） | 月額7,750円 |
| 精神1級 | R8.4新規追加（grade_b, 7,750円） |
| 65歳以上 | 新規申請不可 |
| 所得制限 | あり（本人3,661,000円+380,000×N） |

出典（公式ページ直接読み取り）:
- 板橋区公式: https://www.city.itabashi.tokyo.jp/kenko/shogai/teate/1003209.html
- 「令和8年4月1日から精神障害者保健福祉手帳1級をお持ちの方も、この手当の申請対象」
- 「15,500円」「7,750円」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- monthly(15500): ✓
- monthly(7750): ✓
- seishin_1 → grade_b: ✓（R8.4新規追加を反映）
- age >= 65 → ineligible: ✓

source_url: https://www.city.itabashi.tokyo.jp/kenko/shogai/teate/1003209.html
source_quote: "心身障害者福祉手当（区制度）15,500円 7,750円 精神障害者保健福祉手帳1級"
