# 江戸川区子ども医療費助成制度 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 18歳到達後の最初の3月31日まで |
| 助成内容 | 保険診療の自己負担分を助成（in_kind） |
| 要件 | 江戸川区住民登録 + 健康保険加入 |
| 所得制限 | なし（「保護者の所得制限はありません」と明記） |
| 除外 | 生活保護、児童福祉施設入所、里親委託 |

出典（公式ページ直接読み取り）:
- 江戸川区公式: https://www.city.edogawa.tokyo.jp/e049/kosodate/kosodate/teateshien/kodomoiryohi/iryouhi.html
- 「18歳到達後の最初の3月31日まで」
- 「保護者の所得制限はありません」
- 「保険診療の自己負担分を江戸川区が助成する制度」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind): ✓
- 所得制限なし: ✓

source_url: https://www.city.edogawa.tokyo.jp/e049/kosodate/kosodate/teateshien/kodomoiryohi/iryouhi.html
source_quote: "子ども医療費助成制度"
