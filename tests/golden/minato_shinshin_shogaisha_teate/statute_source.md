# 港区心身障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 身体1-2/愛1-3/精神1級/脳性麻痺/進行性筋萎縮/難病 | 月額15,500円 |
| 身体3/愛4 | 月額7,750円 |
| 65歳以上 | 新規申請不可 |
| 所得制限 | あり |

出典（公式ページ直接読み取り）:
- 港区公式: https://www.city.minato.tokyo.jp/kenko/fukushi/shogaisha/teate/shinshinshogai.html
- 「月額 15,500円の手当てを受けられる人」「精神障害者保健福祉手帳1級の人」
- 「月額 7,750円の手当てを受けられる人」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- monthly(15500): ✓
- monthly(7750): ✓
- seishin_1 → grade_a(15500): ✓
- age >= 65 → ineligible: ✓

source_url: https://www.city.minato.tokyo.jp/kenko/fukushi/shogaisha/teate/shinshinshogai.html
source_quote: "心身障害者福祉手当（区の制度）15,500円 精神障害者保健福祉手帳1級"
