# 江戸川区心身障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 身体1-2/愛の手帳1-3/脳性まひ/進行性筋萎縮 | 月額15,500円 |
| 精神1級（R8.4新規追加） | 月額15,500円 |
| 身体3 | 月額7,750円 |
| 愛の手帳4度（R8.4以降新規） | 月額7,750円 |
| 65歳以上 | 新規申請不可（原則） |
| 所得制限 | あり（本人3,661,000円+380,000×N） |

出典（公式ページ直接読み取り）:
- 江戸川区公式: https://www.city.edogawa.tokyo.jp/e041/kenko/fukushikaigo/shogaisha/teate/teate/shinshin.html
- 「令和8年4月分から手当の対象者と月額が変更」
- 「精神障害者保健福祉手帳1級の方 15,500円」
- 「身体障害者手帳3級の方 7,750円」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- monthly(15500): ✓
- monthly(7750): ✓
- seishin_1 → grade_a(15500): ✓（R8.4新規追加を反映）
- age >= 65 → ineligible: ✓

source_url: https://www.city.edogawa.tokyo.jp/e041/kenko/fukushikaigo/shogaisha/teate/teate/shinshin.html
source_quote: "心身障害者福祉手当 精神障害者保健福祉手帳1級の方 15,500円"
