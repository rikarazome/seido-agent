# ルールスキーマ仕様（v0 ドラフト）

prolog-reasonerによる実現性検証（2026-06-10）で確立した述語設計。全エージェントの契約となる最重要仕様。

## 設計原則

1. **ルールと事実の分離** — 制度ルール（`rules/*.pl`）は世帯事実を含まない。世帯事実はヒアリングエージェントが生成
2. **述語名はローマ字** — SWI-Prologの一時ファイルエンコーディング問題を回避（日本語コメントはUTF-8問題が出るためASCIIで書く。表示名は別レイヤーで日本語化）
3. **すべての判定は3値プロトコルで返す** — `decided` / `blocked` / `ineligible`
4. **除外規定は理由付き** — `jogai(C, Reason)` の形で、違反した条文を理由として持つ

## 世帯モデル（事実述語）

| 述語 | 意味 |
|---|---|
| `claimant(P)` | 申請者 |
| `child(C)` | 子 |
| `kango_by(C, P)` | PがCを監護 |
| `seikei_futan(P, C)` | PがCの生計費を負担 |
| `age(C, A)` | 基準日時点の年齢 |
| `age_nendo_matsu(C, A)` | 年度末時点の年齢（18歳年度末等の判定用） |
| `income(P, I)` | 所得（円） |
| `fuyou_ninzu(P, N)` | 扶養親族数 |
| `hitorioya_jiyuu(C, Reason)` | ひとり親事由（rikon/shibou/...） |

※誕生日→年齢変換は本実装でPython側が行い、事実として注入する。

## 判定プロトコル（全制度共通）

```prolog
kettei_status(P, C, decided(Kubun))    % 判定確定（zenbu/ichibu/金額等）
kettei_status(P, C, blocked(Missing))  % 事実不足。Missing = 不足事実リスト → 質問生成の入力
kettei_status(P, C, ineligible(Reason)) % 非該当。Reason = 違反した規定
```

- `blocked` は `required_fact(P, FactName, Description)` の探索で導出。**ヒアリングエージェントはこのリストから次の質問を選ぶ**
- 証明木は `trace=true` で取得し、説明エージェントが条文参照付き自然言語に変換する

## 検証済みパターン（spike結果）

| パターン | 制度例 | 結果 |
|---|---|---|
| 多子加算の順位計算（22歳年度末カウント） | 児童手当 | ✅ findall+rankで正しく第3子3万円を導出、証明木出力 |
| 否定による除外規定 | 児童扶養手当（事実婚同居除外） | ✅ negation_as_failureが証明木に記録される |
| 事実不足→質問リスト | 児童扶養手当（所得未聴取） | ✅ `blocked([income, fuyou_ninzu])` |
| 非該当理由の提示 | 児童扶養手当 | ✅ `ineligible('...(Art.4(2))')` |

## 既知の課題

- 所得制限の限度額はプレースホルダ。**公式数値の検証が全制度で必須**（golden caseのstatute_source.mdに出典を固定）
- 所得の定義（収入/所得/控除後）が制度ごとに違う。述語を分ける必要あり（`income_kazei/2` 等）— 形式化エージェントの主要な誤りポイントになる見込み
- `:- discontiguous` 宣言を生成テンプレートに含めること
