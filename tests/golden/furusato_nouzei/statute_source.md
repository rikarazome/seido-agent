# ふるさと納税（寄附金控除）— 出典固定

**状態: VERIFIED（2026-06-21, 総務省ポータル全文読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 自己負担 | 実質2,000円（特例分が住民税所得割額20%以内の場合） |
| 所得税控除 | （寄附額−2,000円）×所得税率（上限: 総所得金額等の40%） |
| 住民税基本分 | （寄附額−2,000円）×10%（上限: 総所得金額等の30%） |
| 住民税特例分 | （寄附額−2,000円）×（100%−10%−所得税率） |
| ワンストップ特例 | 5団体以内なら確定申告不要 |
| 手続き | 確定申告またはワンストップ特例 |

出典（総務省ポータル全文読み取り）:
- 総務省: https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/mechanism/deduction.html
- 「（ふるさと納税額−2,000円）×所得税の税率」
- 「特例分が住民税所得割額の2割を超えない場合」
- 証拠: page_snapshot_2026-06-21.txt

ルールの条文対応:
- kubun(furusato_nouzei): 控除額が所得・寄附額で変動 ✓

source_url: https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/mechanism/deduction.html
source_quote: "ふるさと納税 自己負担2,000円 所得税率×寄附額"
