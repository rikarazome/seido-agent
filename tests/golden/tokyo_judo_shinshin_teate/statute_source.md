# 東京都重度心身障害者手当 — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 支給額 | 月額60,000円 |
| 対象 | 都内在住、重度の心身障害者（身体1級+知的重度の重複、身体1級で常時介護等）。65歳以上の新規は対象外 |
| 所得制限 | あり。本人: 扶養0人 3,604,000円、以降+380,000円 |
| 除外 | 施設入所中、生活保護受給中ではないが施設入所は除外 |

出典:
- 東京都福祉局: https://www.fukushi.metro.tokyo.lg.jp/shinsho/teate/juudo.html

判定に使うaskable:
- `shogai_techo`: 障害者手帳（v1: shintai_1のみ対象として簡略化。実際は重複障害等の詳細判定）
- `nenshu` / `shotoku_exact`: 所得
- `fuyou_ninzu`: 扶養人数
- `seikatsu_hogo`: 生活保護（除外ではないが確認）

限度額式: L = 3,604,000 + 380,000 * N

注: 本手当は東京都独自。「重度心身障害」の判定は実際は都の認定が必要。
v1ではshintai_1を目安とし、「都の認定が必要です」と案内。

source_url: https://www.fukushi.metro.tokyo.lg.jp/shisetsu/jigyosyo/shinsho/teate/juudo
source_quote: "東京都重度心身障害者手当として月額60,000円を支給"
