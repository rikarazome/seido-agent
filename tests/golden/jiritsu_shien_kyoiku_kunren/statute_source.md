# 自立支援教育訓練給付金 — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 支給額 | 受講費用の60%（上限200,000円、下限12,001円）。専門実践は修学年数×200,000円（上限800,000円） |
| 対象 | ひとり親家庭の親で、雇用保険の教育訓練給付の指定教育訓練講座を受講 |
| 所得制限 | 児童扶養手当の所得制限に準じる（全部支給限度額: 1,490,000 + 380,000*N） |

出典:
- こども家庭庁: https://www.cfa.go.jp/policies/hitori-oya/jiritsu-shien-kyouiku
- 母子及び父子並びに寡婦福祉法 第31条

判定に使うaskable:
- `hitorioya`: ひとり親か
- `nenshu` / `shotoku_exact`: 所得
- `fuyou_ninzu`: 扶養人数

v1簡略化: 受講中の判定なし。ひとり親+所得制限内なら「対象の可能性あり（指定講座受講が条件）」として案内。
金額は上限200,000円（一般教育訓練）で表示。

source_url: https://www.city.edogawa.tokyo.jp/e090/kosodate/kosodate/teateshien/shisaku/kyufukin.html
source_quote: "支給額の上限は200,000円です"
