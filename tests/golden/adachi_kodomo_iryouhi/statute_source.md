# 子ども医療費助成（足立区） — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 出生〜18歳年度末（マル乳/マル子/マル青で連続カバー） |
| 助成内容 | 保険診療の自己負担分を助成（in_kind） |
| 要件 | 足立区内住民登録 + 健康保険加入 |
| 所得制限 | なし（「保護者の所得制限はありません」と明記） |

出典（公式ページ直接読み取り）:
- 足立区公式: https://www.city.adachi.tokyo.jp/oyako/k-kyoiku/kosodate/teate-iryohijose.html
- 「出生から高校生相当の（18歳に達した日以降の最初の3月31日まで）お子さま」
- 「保護者の所得制限はありません」
- 「医療費のうち保険診療の自己負担分を助成します」

ルールの条文対応:
- age_nendo_matsu <= 18: 「18歳に達した日以降の最初の3月31日まで」に対応
- kenkou_hoken=true: 「健康保険に加入している」に対応
- decided(in_kind): 「自己負担分を助成」に対応（金額は受診内容により変動）

source_url: https://www.city.adachi.tokyo.jp/oyako/k-kyoiku/kosodate/teate-iryohijose.html
source_quote: "子ども医療費助成制度（マル乳・マル子・マル青医療証） 18歳に達した日以降の最初の3月31日まで 所得制限はありません"
