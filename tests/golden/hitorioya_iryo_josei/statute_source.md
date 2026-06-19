# ひとり親家庭等医療費助成（東京都） — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 助成内容 | 医療費の自己負担分を助成（現物給付） |
| 対象 | ひとり親家庭の親+18歳年度末までの子。ひとり親=母子/父子/養育者 |
| 所得制限 | あり。扶養0人: 1,920,000円、1人: 2,300,000円、以降+380,000円/人（本人所得） |
| 除外 | 生活保護受給中、事実婚パートナーあり |

出典:
- 東京都福祉局: https://www.fukushi.metro.tokyo.lg.jp/smph/iryo/josei/maruoya.html
- 渋谷区: https://www.city.shibuya.tokyo.jp/kodomo/kodomo-teate-josei/hitorioya/hitorioya_iryohi.html

判定に使うaskable:
- `hitorioya`: ひとり親か（boolean）
- `seikei_douitsu_partner`: 事実婚パートナー（boolean, per_child scope）
- `nenshu` / `shotoku_exact`: 所得（ハイブリッド方式）
- `fuyou_ninzu`: 扶養人数

限度額式: L = 1,920,000 + 380,000 * N（N=扶養人数）

注: subject=claimant（親本人への医療費助成）。子の医療費は子ども医療費助成でカバー。

source_url: https://www.fukushi.metro.tokyo.lg.jp/kodomo/kosodate/hitorioya/iryouhi.html
source_quote: "ひとり親家庭等医療費助成制度として医療費の自己負担分を助成"
