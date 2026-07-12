# 国制度ルール監査（2026-07-12） — 既知の過剰/過少判定

self_medication の過剰判定バグ（ユーザー報告→修正済み 1543fb2）を契機に、
国制度79本すべてについて「ルールの判定条件 vs statute_source.md に記録済みの
要件」を突き合わせた。**同型の問題（decided/ineligible に到達するのに、
証拠ファイルに記録済みの実体要件を確認していない）が約25本で確認された。**
大半は初期のバッチ生成（scripts/archive/gen_tax_deductions.py 等）由来の
簡易ルールで、個別の statute-first ループを通した主力制度（児童手当・
児童扶養手当・自治体制度群など）はこの問題を持たない。

## 分類

- **A: 過剰判定（実害大）** — 記録済みの実体ゲート（所得・期間・イベント）を
  確認せず「受給見込み」を出す
- **B: 過少判定** — 記録済みの例外を無視して「対象外」と誤断定
- **C: 資格枠グレー** — 「制度の対象者である」ことの提示としては成立するが、
  給付発生条件（高額な医療費が実際に生じた等）を注記していない
- **D: 証拠不備** — statute_source が別制度/リンク集のみで要件を検証できない

## findings（優先度順）

| # | program | 分類 | 欠落している記録済み要件 |
|---|---|---|---|
| 1 | sousaihi | A | **死亡イベント**。国保加入だけで7万円decided |
| 2 | maisouryou | A | 死亡イベント・請求者との関係（3類型） |
| 3 | hikazei_setai_kyufukin | A | **申請受付終了**が記録済み。非課税/均等割のみの金額区分も未実装 |
| 4 | shounimansei_iryo_josei | A | 小児慢性特定疾病の**指定**。子の年齢のみでdecided |
| 5 | izoku_kiso_nenkin | A | 子の存在/年齢・納付要件(2/3)。死別のみでdecided |
| 6 | izoku_kousei_nenkin | A | 受給順位・子なし妻30歳未満5年等。死別のみでdecided |
| 7 | hitorioya_koujo | A | 本人所得500万以下・生計同一の子(子所得58万以下)・事実婚なし |
| 8 | haiguusha_koujo | A | 配偶者所得58万以下・本人所得1,000万以下 |
| 9 | shitsugyo_kyufu | A | 被保険者期間12ヶ月(離職前2年) |
| 10 | shougai_kiso_nenkin | A | 保険料納付要件(2/3 or 直近1年) |
| 11 | ikuji_kyuugyou_kyufu | A | 賃金支払基礎日数11日以上×12ヶ月 |
| 12 | kaigo_kyuugyou_kyufu | A | 同上(12ヶ月要件) |
| 13 | jutaku_loan_koujo | A | 床面積50㎡・合計所得2,000万以下・10年以上返済 |
| 14 | juutaku_reform_zeisei | A | 所得2,000万以下・床面積50㎡・工事費50万超 |
| 15 | kinrou_gakusei_koujo | A | 合計所得75万以下・勤労外所得10万以下 |
| 16 | boshi_koutou_kunren | A | 所得制限(児扶手相当)・6月以上修業・対象資格 |
| 17 | boshi_jiritsu_kyouiku | A | 20歳未満の児童扶養・支援プログラム策定・講座指定 |
| 18 | kyushokusha_shien_kunren | A | 本人収入月8万以下・世帯収入30万以下・資産300万以下等 |
| 19 | kyouiku_kunren_kyufu | A | 講座区分(一般20%/特定一般40%/専門実践50%)の別 |
| 20 | kourei_sai_shushoku / sai_shushoku_teate | A | 基本手当の支給残日数要件 |
| 21 | nenkin_seikatsusha_shien | A | 年金+所得909,000円以下 |
| 22 | sanzen_sango_nenkin_menjo | A | 国民年金第1号被保険者であること |
| 23 | nisa_hikazei | A | 18歳以上。現状**無条件でdecided** |
| 24 | aoiro_shinkoku | A | 記帳方式による控除区分(65/55/10万) |
| 25 | jukyo_kakuho_kyufukin | A | 求職活動要件 |
| 26 | shoubyou_teatekin | A | 連続4日以上の休業・給与支払なし |
| 27 | tokubetsu_jidou_fuyou_teate / shogaiji_fukushi_teate / tokubetsu_shogaisha_teate | A(除外) | 施設入所・障害年金受給・長期入院の除外条件 |
| 28 | hosougubi_shikyuu | A | 所得割46万以上は対象外 |
| 29 | iryouhi_koujo | **B** | 所得200万未満は基準が「所得の5%」（10万未満でも該当しうるのに対象外と断定） |
| 30 | kougaku_ryouyouhi / 一部の資格枠系 | C | 給付発生条件（実際の高額支出）の注記なし |
| 31 | bukka_kodomo_teate / boshi_fukushi_shikin / shoukibo_kigyou_kyousai | D | statute_source が別制度ページ/リンク集のみ |

## 対応方針

1. **提出（7/12）はこのドキュメントの公開をもって行う**（既知の制限の明示）。
   判定カードは従来から「受給見込み」表記＋法的助言でない旨＋窓口誘導を常時表示。
2. 7/30のファイナリスト発表までに、A分類を優先して statute-first ループ
   （1コミット1制度）で修正する。イベント事実（死亡・受講等）が必要な制度は
   askable を追加、資格枠系（C）は説明文に給付発生条件を注記する。
3. 修正のたびに golden を要件網羅形（self_medication の 6 ケース構成を参照）に
   拡張する。「booleanが1つ真ならdecided」のルールを新規に書くことを禁止し、
   rule-schema.md にレビュー観点として追記する。

監査手法: 読み取り専用エージェント4体で79本を分担し、decided到達条件と
statute_source記録要件を突合。フラグ全件から、資格枠として妥当なもの・
記録済み簡略化注記があるものを除外し、代表例（jutaku_loan, sousaihi,
hitorioya_koujo, kougaku_ryouyouhi）は人手で原文確認した。
