# 中央区子ども医療費助成 — 出典固定

**状態: VERIFIED（2026-06-20, 公式ページ直接読み取り + page_snapshot保存）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 18歳到達後最初の3月31日まで |
| 助成内容 | 保険適用医療の保護者負担額を区が助成（in_kind） |
| 要件 | 中央区住民登録 + 健康保険加入 |
| 所得制限 | なし（「所得による制限はありません」と明記） |
| 除外 | 生活保護、児童福祉施設入所、里親委託 |

出典（公式ページ直接読み取り）:
- 中央区公式: https://www.city.chuo.lg.jp/a0020/kosodate/kosodate/teatejosei/iryohi/iryouhi.html
- 「所得による制限はありません」
- 「18歳到達後最初の3月31日まで」
- 「保護者の負担する額を区が助成」
- 証拠: page_snapshot_2026-06-20.txt

ルールの条文対応:
- age_nendo_matsu <= 18: ✓
- kenkou_hoken=true: ✓
- decided(in_kind): ✓
- 所得制限なし: ✓

source_url: https://www.city.chuo.lg.jp/a0020/kosodate/kosodate/teatejosei/iryohi/iryouhi.html
source_quote: "子ども医療費助成"
