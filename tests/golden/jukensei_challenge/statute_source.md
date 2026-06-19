# 受験生チャレンジ支援貸付事業（東京都） — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 貸付額 | 学習塾等受講料: 200,000円以内、受験料: 高校27,400円・大学80,000円以内 |
| 対象 | 都内在住、中学3年生または高校3年生相当の子がいる世帯 |
| 返済免除 | 入学した場合は返済免除（実質給付） |
| 所得制限 | あり（世帯収入基準。以下は公式公表の収入値を所得に換算した近似） |

**所得限度額（salary_to_shotokuによる近似、VERIFIED）**:
- 2人世帯(扶養0): 収入3,431,000 -> 所得2,321,700
- 3人世帯(扶養1): 収入4,073,000 -> 所得2,818,400
- 4人世帯(扶養2): 収入4,677,000 -> 所得3,301,600

近似式: L = 2,322,000 + 490,000 * N（扶養N人。収入基準からの所得変換による近似）

出典:
- 東京都社会福祉協議会: https://www.tcsw.tvac.or.jp/activity/jukensei.html
- 東京都福祉局: https://www.fukushi.metro.tokyo.lg.jp/seikatsu/teisyotokusyataisaku/jukenseichallenge.html

判定に使うaskable:
- `nenshu` / `shotoku_exact`: 所得
- `fuyou_ninzu`: 扶養人数

v1簡略化:
- 年齢判定: FY-end age 14-15（中3相当）or 17-18（高3相当）
- 金額: 一律200,000円（塾代上限）で表示
- 所得限度額は収入基準からの近似変換。レンジ跨ぎ時はincome_exactで正確値を聞く

source_url: https://www.fukushi.metro.tokyo.lg.jp/seikatsu/teisyotokusyataisaku/jukenseichallenge
source_quote: "受験生チャレンジ支援貸付事業"
