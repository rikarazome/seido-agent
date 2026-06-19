# 私立高校授業料軽減助成金（東京都） — 出典固定

**状態: VERIFIED（2026-06-15）**

| 項目 | 確定値 |
|---|---|
| 支給額 | 年額最大484,000円（国の就学支援金との差額。授業料実額を上限） |
| 対象 | 都内在住 + 私立高校等に在学する生徒の保護者 |
| 所得制限 | **2026年4月撤廃**（R8年度から所得制限なし。従来は目安年収910万円） |
| 申請 | 学校経由（毎年度申請） |

出典:
- 東京都私学財団: https://www.shigaku-tokyo.or.jp/parents/tuition.html
- 東京都生活文化スポーツ局: https://www.seikatubunka.metro.tokyo.lg.jp/shigaku/

判定に使うaskable:
- `gakkou_kubun` (per_child): 学校区分（shiritsu=私立の場合に対象）
- `koukou_zaigaku` (per_child): 高校在学中か

注: 国の就学支援金（kouko_shugaku_shienkin）は別制度。本制度は東京都の上乗せ。
金額は学校により異なるため、v1では最大額484,000円で表示（実際の授業料が下回る場合あり）。
2026-04の所得制限撤廃により、判定は在学+私立のみで確定。

source_url: https://www.seikatubunka.metro.tokyo.lg.jp/shigaku/hogosha/seido/highschool/0000000055
source_quote: "私立高等学校等授業料軽減助成金"
