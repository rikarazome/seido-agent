# 荒川区 乳幼児・子ども・高校生等医療費助成 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 18歳に達する日以後の最初の3月31日まで |
| 助成内容 | 自己負担分を助成（in_kind） |
| 要件 | 荒川区住民登録 + 健康保険加入 |
| 所得制限 | なし（「荒川区では所得制限を設けていません」と明記） |

出典（公式ページ直接読み取り）:
- 荒川区公式: https://www.city.arakawa.tokyo.jp/a033/kosodate/iryouhi/iryouhijosei.html
- 「18歳になった日の最初の3月31日までの子ども」
- 「荒川区では所得制限を設けていません」
- 「窓口で支払う医療費の一部（自己負担分）を助成します」

ルールの条文対応:
- age_nendo_matsu <= 18: 条文に対応 ✓
- kenkou_hoken=true: 「健康保険を使って」に対応 ✓
- decided(in_kind): 「自己負担分を助成」に対応 ✓
- 所得制限なし: 条文と一致 ✓

source_url: https://www.city.arakawa.tokyo.jp/a033/kosodate/iryouhi/iryouhijosei.html
source_quote: "乳幼児・子ども・高校生等医療費助成"
