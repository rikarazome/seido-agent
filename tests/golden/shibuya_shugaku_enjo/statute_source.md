# 渋谷区就学援助 — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 援助内容 | 学用品費・給食費・修学旅行費等の実費助成（年額、学年により異なる） |
| 対象 | 区立小中学校に通う児童の保護者で、生活保護に準ずる程度に経済的に困窮 |
| 認定基準 | 住民税非課税世帯、または生活保護基準の1.2倍以内（渋谷区基準） |
| 金額 | 学用品費: 小学校約15,000円/年、中学校約27,000円/年（他に給食費等加算） |

出典:
- 渋谷区: https://www.city.shibuya.tokyo.jp/kodomo/gakkou/enjo/shugaku_enjo.html

判定に使うaskable:
- `hikazei`: 住民税非課税世帯か

v1簡略化:
- 生活保護基準の1.2倍判定は複雑なため、hikazei=trueを準ずる程度の代理条件とする
- 金額は小学校の学用品費年額15,000円で表示（実際は学年・費目により異なる）
- 区立小中学校在学の確認は省略（対象年齢の子がいれば案内）
- FY-end age 6-15を小中学生相当とする

source_url: https://www.city.shibuya.tokyo.jp/kodomo/gakko-kyoiku/nyugaku-tennyu-shugaku/tetsuduki_g.html
source_quote: "就学援助として学用品費・給食費等を援助"
