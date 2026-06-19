# 自立支援医療（精神通院医療） — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 助成内容 | 精神疾患の通院医療費の自己負担を1割に軽減（通常3割）。所得に応じた月額上限あり |
| 対象 | 統合失調症、うつ病、てんかん等の精神疾患で継続的な通院が必要な者 |
| 所得制限 | **なし**（自己負担上限額は所得に応じるが、制度の対象判定自体に所得制限はない） |
| 申請 | 市区町村窓口（精神科医の診断書が必要） |
| 有効期間 | 1年（毎年更新） |

出典:
- 厚生労働省: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/jiritsu/
- 障害者総合支援法 第52条〜

判定に使うaskable:
- `shogai_techo`: 精神障害者保健福祉手帳の有無（seishin_1, seishin_2 → 対象。手帳なしでも申請可能だが、v1では手帳保持を前提に案内）

注: 実際は手帳がなくても精神科医の診断書で申請可能。v1では手帳保持（seishin_1 or seishin_2）を
対象の目安とし、「手帳がなくても通院中であれば申請可能です」と注記。

source_url: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/jiritsu/index.html
source_quote: "精神疾患で通院による精神医療を続ける必要がある病状の方に、通院のための医療費の自己負担を軽減する制度"
