# 千代田区こども・高校生等医療費助成制度 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 18歳に達した日以降最初の3月31日まで |
| 助成内容 | 保険診療の自己負担分を助成（in_kind） |
| 要件 | 千代田区住民登録 + 国内健康保険加入 |
| 所得制限 | なし |
| 除外 | 生活保護、児童福祉施設入所、里親委託 |

出典（公式ページ直接読み取り）:
- 千代田区公式: https://www.city.chiyoda.lg.jp/koho/kosodate/teate/kodomoiryo.html
- 「18歳に達した日以降最初の3月31日までの間にある子ども」
- 「保険診療の自己負担分を助成」

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind): ✓
- 所得制限なし: ✓

source_url: https://www.city.chiyoda.lg.jp/koho/kosodate/teate/kodomoiryo.html
source_quote: "こども・高校生等医療費助成制度（乳幼児～高校生等）"
