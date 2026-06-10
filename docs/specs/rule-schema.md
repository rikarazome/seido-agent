# ルールスキーマ仕様（v1）

2026-06-11 改訂。設計レビューで発見した2つの重大欠陥（NAFによる未知/偽の混同・述語名前空間の衝突）を修正。
新方式は prolog-reasoner で再検証済み（下表）。全エージェントの契約となる最重要仕様。

## v0からの変更点

| # | 問題 | 修正 |
|---|---|---|
| 1 | `\+ jogai(C,_)` が「除外事由が偽」と「未質問」を区別できず、未質問のまま誤って decided を返す | **3値事実方式**: 可問事実は `known/2` で表現し、`yes/no/unknown` ヘルパー経由でのみ参照 |
| 2 | 10ルールファイルが `kettei_status/3` 等を重複定義し、同時ロードで節がマージ・補助述語が衝突 | **SWI-Prolog module化**: 1制度=1module。`Prog:kettei_status(P,C,S)` で制度別に照会 |
| 3 | 所得が点値前提で、フォームの「レンジ入力」を扱えない | `range(Lo,Hi)` 値と区間比較ヘルパー（`v_lt/v_geq/v_indet`）を導入 |

## 事実の2分類

**構造事実**（フォームから常に得られる。素のPrologファクト）

| 述語 | 意味 | 出所 |
|---|---|---|
| `claimant(P)` | 申請者 | フォーム |
| `child(C)` | 子 | フォーム（children配列） |
| `kango_by(C, P)` / `seikei_futan(P, C)` | 監護・生計費負担 | **フォームの既定値として注入**（申請者が監護・負担すると仮定）。対話で訂正可 |
| `age(C, A)` / `age_nendo_matsu(C, A)` | 基準日年齢 / 年度末年齢 | 誕生日からPython側が**JST基準で**決定的に計算 |
| `birth_nendo(C, Y)` | 出生年度（4月始まり） | 誕生日から決定的に計算（出生年度で金額が変わる制度用。例: バースデーサポート） |

構造事実は常に存在が保証されるため、これらに対するNAF（`\+`）は安全。

**可問事実**（未知がありうる。必ず `known/2` で表現）

```prolog
known(income(p1), 1500000).              % 点値
known(income(p1), range(1000000, 3000000)). % レンジ（フォームの所得帯選択）
known(income(p1), range(10000000, 999999999)). % 「1,000万円以上」は番兵上限で表現
                                         %（全制度の限度額 < 番兵 をCIで恒常検証）
known(hitorioya(p1), true).              % bool: true/false
known(hitorioya_jiyuu(p1), rikon).       % 列挙値: rikon/shibou/iki/mikon/...
known(seikei_douitsu_partner(c1), false).
known(fuyou_ninzu(p1), 2).
```

- **未知 = `known/2` 節が存在しない**こと。`null` をPrologに渡さない（Pythonのマッピング層が省略する）
- `hitorioya_jiyuu` はv1では**申請者単位**に簡略化（子ごとに事由が異なるケースは後続バージョン）
- **子ごとに値が異なる可問事実**（在学状況・学校区分等）は `children[].askable` から
  `known(koukou_zaigaku(c1), true)` の形で注入する（就学支援金で導入。世帯レベルのフラットaskableとは別経路）

## エンジンヘルパー（engine.pl、全moduleから利用）

```prolog
:- dynamic known/2.

yes(F)     :- known(F, true).
no(F)      :- known(F, false).
unknown(F) :- \+ known(F, _).
val(F, V)  :- known(F, V).

% 区間対応比較: レンジ全体が条件を満たすときのみ成功
v_lt(V, L)  :- number(V), V < L.
v_lt(range(_, Hi), L)  :- number(Hi), Hi < L.
v_geq(V, L) :- number(V), V >= L.
v_geq(range(Lo, _), L) :- number(Lo), Lo >= L.
% 型ガード: これが無いとゴミ値（アトム・逆転レンジ）が両比較に失敗して
% v_indet が偽成功し、型バグが「追加質問」に化けて隠れる
valid_val(V) :- number(V).
valid_val(range(Lo, Hi)) :- number(Lo), number(Hi), Lo =< Hi.
% レンジが閾値を跨ぐ → どちらとも言えない → 正確な値の質問を誘発
v_indet(V, L) :- valid_val(V), \+ v_lt(V, L), \+ v_geq(V, L).
```

engine.pl は非moduleで `user` にロードする。SWI-Prologのmoduleは既定で `user` を継承するため、
各制度moduleからヘルパーと `known/2` を修飾なしで参照できる（**Week 2の統合テストで多ファイル構成を実機確認。
不調時のフォールバック: 制度ごとに別swiplプロセス起動**）。

## NAF（失敗による否定）使用規則 — 形式化エージェントの生成制約

1. **可問事実への素の `\+` は禁止**。除外の否定は `no(F)`（false確認済み）でのみ表現
2. 除外規定は「確認済みのときだけ発火」する派生述語にする: `jogai_confirmed(C, Reason) :- yes(F).`
   `\+ jogai_confirmed(C, _)` は「確認済み除外なし」の意味になるため使用可（未知なら required_fact が拾う）
3. 構造事実・構造事実のみから導出される述語（findallランキング等）へのNAFは可

## 判定プロトコル（全制度共通）

```prolog
kettei_status(P, C, decided(Kubun))     % 確定（zenbu/ichibu/amount(Y)等）
kettei_status(P, C, blocked(Missing))   % 事実不足。Missing = 質問生成の入力
kettei_status(P, C, ineligible(Reason)) % 非該当。Reason = 違反規定
kettei_status(P, C, error(Why))         % ルール網羅漏れの検出（fail-safe）
```

**節の標準順序**（カットで先勝ち。検証済みパターン）:

```prolog
kettei_status(P, C, error(structural_facts_missing)) :-              % 構造ガード必須（先頭）
    claimant(P), child(C), \+ age_nendo_matsu(C, _), !.
kettei_status(..., ineligible(...)) :- <構造要件の不充足>, !.        % 例: 年齢超過
kettei_status(..., ineligible(...)) :- <要件のno()確認>, !.          % 例: ひとり親でないと確認
kettei_status(..., ineligible(R))   :- jogai_confirmed(_, R), !.     % 除外の確認
kettei_status(..., blocked(Missing)) :- \+ jogai_confirmed(_, _),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing), Missing \= [], !.
kettei_status(..., decided(K))      :- <全要件yes/val>, <支給区分>, !.
kettei_status(..., ineligible(...)) :- <所得超過等、値由来の非該当>, !.
kettei_status(_, _, error(no_rule_matched)).   % catch-all 必須（最終節・無条件）
```

**構造ガードは構造ineligibleより前に必須**（v1.1、実証済み）。構造要件のineligible節は構造事実への
NAFを使うため、事実が**欠落**していても成功してしまい、「年齢未知」（マッピング層のバグ）が
「年齢超過で非該当」という**誤判定**に化ける。マッピング層は birth_date 必須で欠落を防ぐが（一次防御）、
ガード節を先頭に置いて error として表面化させる（二次防御）。blockedではなくerrorなのは、
構造事実はフォーム由来でありユーザーに質問するものではないため。

**catch-all は全制度で必須**。どの節にもマッチしないケース（網羅漏れ）が結果から**黙って消える**ことを防ぎ、
「判定不能」カードとして表面化させる（Fail Safe: 沈黙よりエラー）。`once()` ドライバ前提のため、
中間の全節にカットを置くこと。万一 `once` が解なしで失敗した場合もランナーは error 扱いにする（二重の防御）。

**限度額・パラメータ表は加算式で書く**（網羅漏れの主要因のため）:

```prolog
% NG: 表形式は定義域に穴が出る（N=3で解なしになった実例 → 検証済み）
% zenbu_limit(0, 690000).  zenbu_limit(1, 1070000). ...
% OK: 式形式は全 N >= 0 で定義される
zenbu_limit(N, L) :- integer(N), N >= 0, L is 690000 + 380000 * N.
```

法令が実際に表（非線形）の場合は表で書いてよいが、**定義域の上限を超える入力を error ではなく
明示の節で受ける**こと（例: `kettei_status(..., error(fuyou_out_of_range)) :- val(fuyou_ninzu(P), N), N > 9, !.`）。

**金額のレンジ評価規約**: 逓減式など点値所得を要する金額計算で所得が `range(Lo,Hi)` のままの場合、
ランナーが **Lo / Hi をそれぞれ点値として2回評価**し、金額を「月◯〜◯円」のレンジで表示する。
ルール側に区間演算は持ち込まない（kubun判定は `v_lt/v_geq` で済み、金額はランナーの2点評価で済むため）。

- `required_fact(P, FactName, Description)` が blocked の中身を導出。`unknown/1` と `v_indet/2`（レンジが限度額を跨ぐ→ `income_exact` を要求）の両方から発生する

**証明木の取得は2段階再導出方式（検証済み）**。標準節順序はカット前提だが、素朴な証明木
メタインタプリタは `!` を正しく扱えない（true扱いすると節選択が変わり、静かに誤った結果を返しうる）:

1. **ステータス確定**: 通常照会 `once(Prog:kettei_status(P, C, S))` — カットは本来の意味で動く
2. **証明木再導出**: 確定した **ground項**（例: `kettei_status(p1, c1, decided(zenbu))`）をメタインタプリタで
   再導出する。状態項が接地していれば他の節の頭部とは単一化しないため、**cut=true扱いでも導出は健全**

検証: ground項 `decided(zenbu)` は再導出に成功し、誤った `decided(ichibu)`・`blocked([income])` は
cut無視のメタインタプリタでも導出**不能**であることを確認。さらに **直接照会とメタ解釈の結果一致を
goldenテストの恒常チェック項目**とする（メタインタプリタ改修時の回帰検知）。

**呼び出し規約（重要・検証済み）**: 節内のカットは `kettei_status` 全体の選択点を刈るため、
**`P`・`C` を未束縛で照会すると最初の1子の解しか返らない**。ランナーは必ず両引数を束縛して照会する:

```prolog
% subject: child の制度 — 子ごとに照会（子の列挙はkettei_statusの外で行う）
result(Prog, C, S) :- child(C), once(Prog:kettei_status(P, C, S)).
% subject: claimant の制度 — 第2引数はアトム self 固定
result(Prog, self, S) :- claimant(P), once(Prog:kettei_status(P, self, S)).
```

**判定対象（subject）の規約**: 制度には子単位の判定（児童手当等）と申請者単位の判定（住居確保給付金等）が
ある。programs.yaml の `subject: child | claimant` で宣言し、`claimant` の制度はルールの全 `kettei_status`
節の第2引数を**アトム `self`** にする（子IDと衝突しない明示マーカー。`C = P` の自己参照は採らない）。

検証: 3児世帯で c1=ineligible(年齢超過), c2=decided(10000), c3=decided(30000) を正しく列挙。
claimant制度（離職要件+所得、condensed）で `once(kettei_status(p1, self, S))` → `blocked([income])`。

## module構成

```prolog
:- module(jidou_fuyou_teate, [kettei_status/3, required_fact/3, teate_amount/2]).
```

- 1制度 = 1ファイル = 1module。module名 = ファイル名 = 制度ID（ローマ字）
- 必須エクスポート: `kettei_status/3`・`required_fact/3`（askableが無い制度は `required_fact(_,_,_) :- fail.`
  の明示空定義）。`unit: per_household` の制度は `teate_amount/2`（世帯月額）を追加エクスポート
- **ロードは空インポートで行う**: `use_module(File, [])`。照会は全てmodule修飾で行うため
  インポート不要であり、`use_module/1` だと複数制度の同名エクスポートが user へのインポートで
  衝突する（実機で確認: 「No permission to import ... already imported from ...」）
- ランナーは engine.pl → facts.pl（known/2 + 構造事実、user にロード）→ rules/*.pl の順にロードし、
  制度ごとに `Prog:kettei_status(P, C, S)` を全解照会
- 述語名はローマ字・コメントはASCII（SWI一時ファイルのエンコーディング問題回避）。表示名・条文リンク・金額種別は `data/programs.yaml`（静的メタデータ）が持つ

## 制度メタデータ（data/programs.yaml）

ルールが返すのは判定と区分のみ。表示に必要な情報はYAMLに分離する:

```yaml
- id: jidou_fuyou_teate
  name: 児童扶養手当
  amount_type: monthly        # monthly | oneoff | yearly | in_kind
  subject: child              # child | claimant（判定対象。claimant → self規約で照会）
  unit: per_household         # per_child | per_household（金額の集約単位。subject: claimant は常に per_household）
  layer: national             # national | municipal（rules/national/ または rules/municipal/<muni>/ に配置）
  municipality: null          # layer: municipal のとき自治体ID（例: shibuya）。municipal の id/module名は
                              # 自治体プレフィックス必須（shibuya_kodomo_iryouhi 等。CI全ロード時の衝突防止）
  potential_amount: 45500     # 最大支給額の目安（円、公式数値由来）。質問優先度のタイブレークと
                              # 「あとN問で最大+月◯円」表示に使う。作り話の数字を入れない（出典必須）
  statute:
    - { ref: "児童扶養手当法4条", url: "https://..." }
  status: supported           # supported | unsupported（⬜カードの出所）
```

## 検証済みパターン（2026-06-11 再スパイク）

| シナリオ | 結果 |
|---|---|
| 除外事由（事実婚）が**未知** + 他は全て確定 | ✅ `blocked([seikei_douitsu_partner])` — v0なら誤decidedだった回帰テスト |
| 所得レンジが全部支給限度額を**跨ぐ** | ✅ `blocked([income_exact])` |
| ひとり親=yes だが事由が未知 | ✅ `blocked([hitorioya_jiyuu])` |
| 全事実確定・レンジが限度内に収まる | ✅ `decided(zenbu)` |
| 除外確認済み（レンジ判定より優先） | ✅ `ineligible(partner_cohabit_art4_2)` |
| 所得レンジ全体が一部支給限度超 | ✅ `ineligible(income_over_ichibu_limit)` |
| 多子加算の順位計算（22歳年度末カウント） | ✅ v0スパイクで検証済み（構造事実のみ、v1でも有効） |
| 扶養3人（旧・表形式限度額の網羅漏れ） | ✅ 加算式化で `decided(zenbu)`（旧版は解なしで沈黙） |
| `kango_by` 欠落の子（網羅漏れ） | ✅ `error(no_rule_matched)` で表面化、他の子の判定に影響なし |
| 申請者単位制度の `self` 規約 | ✅ `once(kettei_status(p1, self, S))` → `blocked([income])` |
| 世帯単位制度で子の判定が混在 | ✅ c1=ineligible(年齢超過) と c2=decided(zenbu) が正しく共存（「全子同一判定」前提は誤りと実証） |
| 証明木の2段階再導出（cut=true扱い） | ✅ 真のground状態項のみ再導出可、誤kubun・誤ステータスは棄却 |
| `v_indet` 型ガード | ✅ アトム・逆転レンジは偽成功せず、正規の跨ぎ検出は維持 |
| 構造ガード（年齢欠落） | ✅ ガード無しだと誤ineligible（年齢超過）になることを実証 → `error(structural_facts_missing)` |
| `use_module/2` 空インポート | ✅ `use_module/1` は同名エクスポートのインポート衝突（on_error=halt導入で検出） |
| R8年度の金額・逓減式 | ✅ golden 5件（全部/一部×1〜2子、点値/上書き）で `teate_amount/2` を照合 |

## 所得定義ポリシー

- フォームが集めるのは**年収（額面）**のレンジまたは点値。ユーザーが知っているのはこれだけ
- Pythonマッピング層が給与所得控除等の**決定的計算**で各制度の所得定義（控除後所得等）に変換し、制度別の known 事実として注入する（例: `known(income(p1), ...)` は児童扶養手当の所得定義）
- 制度ごとに所得定義が違う場合は述語を分ける（`income_iryouhi(P)` 等）。**変換式と限度額はgolden case作成時に公式出典で固定**（statute_source.md）

## 既知の課題

- 公式数値: 児童手当・児童扶養手当は**検証済み**（限度額=施行令2条の4と一致、R8年度手当額・逓減式を
  `teate_amount/2` で形式化、goldenで金額照合）。残り8制度は形式化時に同様の検証が必須
- module + 多ファイルロードは実機（コンテナ内swipl）未検証。**証明木メタインタプリタが module 内静的述語を
  `clause/2` で展開できるかも併せて確認**（SWI実装依存の領域）。Week 2統合テストの最初の項目とする。
  フォールバック: 判定は module 照会のまま、証明木取得時のみ対象制度を単独プロセスでロード
- `:- discontiguous` 宣言を生成テンプレートに含めること
- 所得の定義: **入力設計決定済み（ハイブリッド、2026-06-11）** — 一次判定は年収レンジの概算変換
  （給与所得控除のみ）、限度額を跨いだら income_exact 質問で控除後所得の点値を聞く。
  factgen.py の概算変換（給与所得控除テーブル）実装はWeek 2
