# 中央区心身障害者福祉手当 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象1-3（身体1-2/愛の手帳1-3/脳性麻痺） | 月額15,500円 |
| 対象4-6（身体3/愛の手帳4/精神1級） | 月額10,200円 |
| 65歳以上 | 新規申請不可 |
| 所得制限 | あり（本人3,661,000円+380,000×N） |

出典（公式ページ直接読み取り）:
- 中央区公式: https://www.city.chuo.lg.jp/a0023/kenkouiryou/shougaishafukushi/teate/sinsin.html
- 「月10,200円 「対象」の4、5、6にあたる方」
- 「月15,500円 「対象」の1、2、3にあたる方」
- 「精神障害者保健福祉手帳1級」→ 対象6（grade_b, 10,200円）
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- monthly(15500): ✓
- monthly(10200): ✓
- seishin_1 → grade_b: ✓（中央区は精神1級=10,200円）
- age >= 65 → ineligible: ✓

source_url: https://www.city.chuo.lg.jp/a0023/kenkouiryou/shougaishafukushi/teate/sinsin.html
source_quote: "心身障害者福祉手当（区の制度） 月10,200円 月15,500円"
