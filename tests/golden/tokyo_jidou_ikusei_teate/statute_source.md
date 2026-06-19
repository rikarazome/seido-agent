# 児童育成手当（東京都制度・渋谷区実施） — 出典固定

**状態: VERIFIED（2026-06-11）**

| 項目 | 確定値 |
|---|---|
| 月額 | 児童1人あたり**13,500円**（年3回: 2月/6月/10月） |
| 対象 | 18歳年度末までの児童を養育するひとり親等（事由は児童扶養手当とほぼ同一: 離婚/死亡/重度障害/生死不明/1年以上遺棄/DV保護命令/1年以上拘禁/未婚） |
| 除外 | 事実婚（事実上の婚姻関係）の場合は不支給 |
| 所得制限 | **本人所得のみ**（扶養義務者の所得は見ない）。限度額 = **3,604,000 + 380,000×扶養親族数**（線形、0〜5人で確認） |
| 児童扶養手当との差 | 限度額が緩い / 養育費の8割算入**なし** / 年金併給制限なし / 逓減なし（全額or不支給） |

出典:
- 渋谷区: https://www.city.shibuya.tokyo.jp/kodomo/kodomo-teate-josei/hitorioya/hitorioya_teate.html
- 東京都児童育成手当に関する条例施行規則: https://www.reiki.metro.tokyo.lg.jp/reiki/reiki_honbun/g101RG00000745.html

v1スコープの簡略化:
- 老人扶養（+480,000円）・特定扶養（+630,000円）の加算特例は未モデル化（goldenは該当しない世帯のみ。
  形式化時の既知の縮小として明記）
- 所得は児童扶養手当と同じ `income(P)` を流用（養育費algorithm差は所得変換実装時に分離する）

source_url: https://www.city.chiyoda.lg.jp/koho/kosodate/kosodate/hitorioya/teate/jidoikuse.html
source_quote: "児童育成手当（育成手当・障害手当）"
