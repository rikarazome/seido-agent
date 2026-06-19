# 自立支援医療（育成医療） — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 助成内容 | 18歳未満の身体障害児の手術等の医療費自己負担を軽減（1割負担、所得に応じた上限） |
| 対象 | 18歳未満で身体障害があり、確実な治療効果が期待できる者 |
| 所得制限 | **なし**（自己負担上限は所得で変動するが、対象判定に所得制限はない） |

出典:
- 厚生労働省: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/jiritsu/
- 障害者総合支援法 第52条

判定に使うaskable:
- `shogai_techo_child` (per_child): 子の障害者手帳（shintai_1, shintai_2, shintai_3 -> 対象）

v1簡略化: 身体障害者手帳保持を対象の目安とする。実際は手帳なしでも医師の判断で対象になりうる。

source_url: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/jiritsu/index.html
source_quote: "自立支援医療費の支給対象 育成医療 利用者負担 自己負担を軽減する制度"
