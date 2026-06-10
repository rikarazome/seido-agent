# アーキテクチャ設計書（v1.1）

2026-06-11 確定、同日レビュー指摘14件を反映して改訂。プロダクト形態の決定（Webアプリ + 同一コンテナでのサービス統合）に基づく技術設計。

## 決定事項サマリ

| 項目 | 決定 | 理由 |
|---|---|---|
| 形態 | ログイン不要のモバイル対応Webアプリ | とどける力・デモ体験が最強。審査員もProtoPedia訪問者もURLタップで完結 |
| 入力方式 | **最小限の基本情報フォーム → 即時一次判定 → 以降は一問一答**（3〜4択チップ+自由入力、Claude Code式） | フォームの手間を最小化しつつ、選択肢タップ経路はLLM不使用で0円・誤抽出ゼロ。質問の必然性（blocked由来）が見える |
| サーバー | **Cloud Run 1サービスのみ**（min=0, max=2） | scale-to-zeroで待機コスト0円。無料枠内で全運用が収まる見込み |
| DB | **なし**（完全ステートレス） | 世帯事実はクライアントが保持し毎回送る。「保存しません」が設計上の事実になる |
| LLM | Gemini（Vertex AI経由、クレジット消化） | ハッカソン要件 + 形式化はビルド時のみでランタイム消費は最小 |
| Prolog | SWI-Prologを**同一コンテナに同梱**、サブプロセス実行 | 別サービス化は過剰。コールドスタートも課金も1個で済む |
| フロント | ビルドレスの素のHTML/CSS/JS（FastAPIから静的配信） | ビルドパイプライン不要。CIが単純になる。複雑化したらViteへ移行 |
| ルール表現 | **3値事実 + module化**（docs/specs/rule-schema.md v1） | 未知/偽の混同バグと述語衝突を設計段階で排除（検証済み） |

## システム構成図

```
                        ┌──────────────────────────────────────────────┐
                        │  Cloud Run（1コンテナ, asia-northeast1）       │
                        │                                              │
 ブラウザ ──────────────▶│  FastAPI（get_fast_api_app + 自作ルート）      │
   │  GET  /            │   ├─ /            … 静的フロント配信           │
   │  POST /api/judge   │   ├─ /api/judge   … 一次判定（LLM不使用）      │
   │  POST /api/chat    │   ├─ /api/chat    … 対話1ターン（Gemini使用）  │
   │  GET  /ops         │   ├─ /api/programs… 制度メタデータ            │
   │                    │   └─ /ops         … opsダッシュボード(静的)    │
   │                    │                                              │
   │                    │  ADK Runner（ヒアリングエージェント）            │──▶ Vertex AI
   │                    │   └─ tools: run_judgment, extract_facts      │    (Gemini)
   │                    │                                              │
   │                    │  推論エンジン層（Python）                       │
   │                    │   ├─ facts JSON → known/2 + 構造事実（決定的） │
   │                    │   ├─ swipl サブプロセス実行                    │
   │                    │   └─ engine.pl + rules/*.pl（イメージ同梱）    │
                        └──────────────────────────────────────────────┘
   GET ops.json ───────▶ GCS公開バケット（CIが書き込み。nightly検証結果もここに反映）

        ビルド時（CI, GitHub Actions）:
        条文 → 形式化エージェント(Gemini) → rules/*.pl → goldenテスト → イメージ焼き込み → deploy
```

## LLM使用ポイント（コスト構造の根拠）とモデル固定

| 処理 | 実行タイミング | 担当 | モデル（環境変数でピン留め） |
|---|---|---|---|
| 法令の形式化（条文→Prologルール） | **ビルド時のみ** | Gemini | Pro系（精度優先。ユーザー数と無関係に償却） |
| フォーム/選択肢回答→全制度判定 | ランタイム | **Prologのみ** | —（**0円**、トークン不使用） |
| 質問文・選択肢の提示 | ランタイム | **静的メタデータ**（data/questions.yaml） | —（**0円**。LLM生成しない=誤選択肢ゼロ） |
| 自由文回答→事実抽出 / 証明木の日本語説明 | ランタイム | Gemini | Flash系 |
| adk eval（CI） | mainマージ時 | Gemini | Flash-Lite系 |

試算: 約2〜3円/セッション（Flash）。一次判定だけで離脱するユーザーは **0円**。

## facts JSONスキーマ（rule-schema.md v1 と1:1対応）

```jsonc
{
  "facts": {
    "claimant": { "birth_date": "1988-04-01" },
    "children": [ { "id": "c1", "birth_date": "2019-06-01" } ],
    "askable": {
      // 値の型: 数値（点値） | [lo, hi]（レンジ） | true/false | 列挙文字列
      //        | null（未質問） | "declined"（質問済み・回答なし。nullと区別必須 — 区別しないと
      //          「わからない」の直後に同じ質問が最優先で再計算され無限再質問になる）
      // 上限なしレンジの規約: 「1,000万円以上」等は番兵上限 [10000000, 999999999] で表現。
      // 全制度の限度額 < 番兵 であることをCIで恒常検証（番兵を超える限度額の出現＝即CI失敗）
      // 正規化規則: askable は常に全キーを持ち、未知は null（キー欠落を許さない。
      // 欠落とnullの扱い分岐によるバグを防ぐ。サーバーはスキーマ検証で欠落を拒否）
      // 名前空間規則: askable は世帯レベルのフラット集合。Prolog側で子ごとの述語になるもの
      // （seikei_douitsu_partner 等）は全子に同値で注入する（v1の決定。事実婚パートナーは
      // 世帯の状態なので実用上正しい）。子ごとに値が真に異なる事実（在学状況・学校区分）は
      // children[].askable に置く（就学支援金で導入済み。questions.yaml の scope: per_child）
      "nenshu": [3000000, 5000000],      // 年収（額面）。フォームはレンジ選択
      "shotoku_exact": null,             // income_exact質問の回答（控除後所得の点値）。
                                         // 存在すれば nenshu 由来の income を上書き（ハイブリッド方式）
      "hitorioya": true,
      "hitorioya_jiyuu": null,           // rikon | shibou | ...（未質問）
      "seikei_douitsu_partner": null,
      "fuyou_ninzu": 2
    }
  },
  "as_of": "2026-06-11"                  // 判定基準日（省略時はJSTの今日。goldenテストで固定可能）
}
```

マッピング層（Python、決定的・LLM不使用）の責務:
- `birth_date` → `age/2`・`age_nendo_matsu/2`（**JST基準**、基準日は `as_of`）
- `children` → `child/1` + `kango_by/2`・`seikei_futan/2` を既定値として注入（対話で訂正可）
- `nenshu` → **ハイブリッド方式（2026-06-11決定）**: 一次判定はフォームの年収レンジを給与所得控除のみで
  **概算変換**（養育費・諸控除は無視 → レンジが広がる方向の安全側誤差として扱い、限度額を跨げば自然に
  blocked(income_exact) になる）。**跨いだ場合のみ**一問一答で「源泉徴収票の給与所得控除後の金額 + 養育費」を
  聞き、回答を `shotoku_exact` に書く（**nenshuには書き戻さない** — 回答は控除後所得であり年収ではない。
  factgenは shotoku_exact 存在時に nenshu を無視する優先規則）。レンジは**端点のみ変換**
  （給与所得控除は単調非減少。**単調でない控除を導入する場合は要再設計**）。区間評価はProlog側
- `null` / `"declined"` は **known事実を生成しない**（= Prolog側ではどちらも unknown、判定はblockedのまま）。
  両者の違いは**質問選定エンジンだけ**が見る（declined は選定対象から除外）

## API設計

### POST /api/judge（一次判定、LLM不使用）

```jsonc
// Request: { "facts": {…上記…}, "as_of": "...", "municipality": "shibuya" }
// municipality はフォームの居住自治体。national + 当該自治体（+上位: shibuya→tokyo）の制度を判定
// Response:
{
  "headline": {                          // 金額種別ごとに分離集計（混ぜて合算しない）
    "monthly_yen": 25000,                // amount_type=monthly の decided 合計
    "oneoff_yen": 100000,                // 一時金の合計
    "yearly_yen": 0,
    "in_kind_count": 1                   // 現物給付（医療費助成等）の件数
  },
  "results": [
    { "program": "jidou_teate", "name": "児童手当",
      "status": "decided",                       // 制度レベルの集約ステータス（規則は下記）
      "amount": { "type": "monthly", "yen": 40000 },  // decided の子の合計
      "children": [                              // 子ごとの内訳（判定の実体は (P,C) 単位）
        { "subject": "c1", "status": "ineligible", "reason": "18歳年度末超" },
        { "subject": "c2", "status": "decided", "yen": 10000 },
        { "subject": "c3", "status": "decided", "yen": 30000 }
      ],
      // 証明木は judge レスポンスに含めない（遅延取得）。「なぜ？」タップ時に
      // POST /api/proof { facts, program, subject, status_term } → prove/3 の2段階再導出で返す。
      // レスポンス肥大とPrologの二重実行を避け、直接照会×メタ解釈の一致検証とも整合
      "statute": [ { "ref": "児童手当法…", "url": "…" } ] },
    { "program": "jidou_fuyou_teate", "name": "児童扶養手当",
      "status": "blocked", "missing": ["hitorioya_jiyuu"],
      "missing_label": "あと1問で確定します",
      "partial_amount": { "type": "monthly", "yen": 0 } },  // 確定済み分があれば部分合計を出す
    { "program": "...", "status": "ineligible", "reason": "...", "statute": [ … ] },
    { "program": "...", "status": "unsupported" },  // data/programs.yaml の status から生成
    { "program": "...", "status": "error" }         // catch-all / 解なし。「判定不能」カード
  ]
}
```

**判定対象→制度カードの集約規則**（判定は (P, 子) または (P, self) 単位、カードは制度単位のため必須）:

| 規則 | 内容 |
|---|---|
| 照会対象 | programs.yaml の `subject` に従う。`child` → 子ごとに照会、`claimant` → `self` 1件のみ照会（rule-schema.md の規約） |
| ステータス優先順位 | `error` > `blocked` > `decided` > `ineligible`。1件でもerrorなら制度カードはerror、errorなしで1件でもblockedならblocked（missingは全対象の和集合）、blockedなしで1件でもdecidedならdecided、全件ineligibleのときのみineligible。**判定の混在は正常**（年齢超過の子と受給対象の子は普通に共存する。検証済み） |
| 金額（`unit: per_child`） | 制度の `amount.yen` = decidedの子の合計。blocked制度でも確定済みの子があれば `partial_amount` で出す（「現時点で月◯円+あとN問」） |
| 金額（`unit: per_household`） | **子の合計ではなく世帯単位で1回導出**（本体額+第2子・第3子加算の式。`teate_amount/2` で形式化、rule-schema.md既知課題）。decidedの子の間でkubunが食い違う場合のみ error（kubunは申請者の所得のみに依存するため、不一致は真正のルールバグ） |
| 対象者ゼロ | subject: child の制度で子が0人 → 照会せず**ランナーが** `ineligible(no_eligible_subject)` を生成（「対象となるお子さんがいません」カード）。空集合の集約を未定義にしない |
| headline | 制度レベル `amount` を amount_type ごとに合算（monthly/oneoff/yearly別、in_kindは件数）。**金額がレンジの制度は下限で合算**し、レンジを1件でも含む種別は「月◯円以上」と表示（上限合算は誇大表示になり信頼設計と矛盾） |
| 解なし | `once()` が失敗した対象は `error` 扱い（catch-all節と二重の防御） |

- 見出しは「💰 月25,000円 ＋ 一時金10万円」のように**種別を分けて表示**。月額・一時金・年額・現物を雑に足さない
- 制度名・条文リンク・amount_type・subject・unit は `data/programs.yaml` から付与（ルールは判定と区分のみ返す）
- 全制度module（10個）×全対象（子 または self）に対して `Prog:kettei_status(P, C, S)` を**両引数束縛・`once/1`**で照会（呼び出し規約はrule-schema.md）
- **金額のレンジ評価**: 逓減式等で所得がレンジのまま確定（decided(ichibu)等）した場合、ランナーがLo/Hiの2点で金額式を評価し「月◯〜◯円」とレンジ表示する（rule-schema.md の規約）
- **レスポンスに `next_question` を含む**（下記・一問一答エンジン）。判定と次の質問が1リクエストで返るため、選択肢タップのループは /api/judge だけで回る

### 一問一答エンジン（基本情報フォーム後の対話設計）

フォームで聞くのは基本情報のみ（居住自治体・子の生年月・年収レンジ）。残りのaskableは
**1問ずつ・3〜4択チップ+自由入力**（Claude Code式）で聞く。

```jsonc
// /api/judge レスポンスに含まれる next_question（nullなら質問なし=全制度確定）
{ "next_question": {
    "fact": "hitorioya_jiyuu",
    "text": "ひとり親となった理由を教えてください",
    "why": ["jidou_fuyou_teate", "jidou_ikusei_teate"],   // この質問で確定に近づく制度（必然性の可視化）
    "choices": [
      { "value": "rikon",  "label": "離婚" },
      { "value": "shibou", "label": "死別" },
      { "value": "mikon",  "label": "未婚" },
      { "value": "__free_text__", "label": "その他" },           // 値を書かず自由文入力へ誘導
      { "value": "declined", "label": "わからない / 答えたくない" } // 常に最後に置く
    ],
    "allow_free_text": true } }
```

| 設計要素 | 規則 |
|---|---|
| 質問の選定 | **決定的**: declined以外の未知factについて、「その事実を要求しているblocked制度数」最大のものを選ぶ。同点は対象制度の `potential_amount`（programs.yaml）合計が大きい順、さらに同点は **questions.yaml のファイル順**（=自然なインタビュー順を編集で制御できる）。per-childのfactは「未回答の子が残っている」場合のみ候補（全子declinedなら除外=再質問ループ防止） |
| 選択肢の生成 | **静的**: data/questions.yaml にfactごとの質問文・選択肢を定義。LLM生成しないので誤った選択肢が出ない |
| タップ回答の処理 | クライアントが選択値をfactsに直接書いて **POST /api/judge**（LLM・/api/chat不使用、0円・誤抽出ゼロ） |
| 「わからない/答えたくない」 | factに **`"declined"`** を書く（nullのままにしない — ステートレス故にnullだと次の/api/judgeで同じ質問が最優先のまま再提示され**無限再質問**になる）。該当制度はblockedのまま、質問選定からは除外 |
| 「その他」（法定列挙外） | **値を書かず自由文入力へ誘導**（`__free_text__`）。Geminiが法定事由のいずれに該当するか分類し、どれにも該当しなければfactは未知のまま+「該当する事由が確認できませんでした」を表示。`sonota` のような**法定列挙にない値を有効値として書かない**（書くと `val(F,_)` の存在チェックを誤って通過し誤decidedになる） |
| 自由入力 | **POST /api/chat**（Gemini抽出）にフォールバック。「去年離婚して……」のような文から複数factを一度に抽出できるのが選択肢に対する付加価値 |
| 終了条件 | next_question = null または ユーザーの明示終了。**null には2状態がある**: (a) 全制度確定、(b) 残る未知factがすべてdeclined → blockedカードに「回答がなかったため確定できません（窓口で確認できます）」を表示。「ここまでで月◯円確定」を常時表示し、途中離脱でも価値が残る |

```yaml
# data/questions.yaml（静的メタデータ）
- fact: hitorioya_jiyuu
  text: ひとり親となった理由を教えてください
  type: enum
  choices: { rikon: 離婚, shibou: 死別, mikon: 未婚 }   # 法定列挙のみ。「その他」「わからない」は全質問に自動付与
  sensitive: true        # センシティブ質問は「答えたくない」を強調表示
- fact: fuyou_ninzu
  text: 税法上の扶養親族は何人ですか
  type: integer          # 限度額の式に入る数値は段階レンジ化禁止（式が正確なNを要求）
  choices: [0, 1, 2, 3, 4, 5]   # 6人以上は自由文へ（番兵不可: Nは式の入力）
```

**questions.yaml の設計規則**: (1) 列挙の choices は法定列挙のみ（「その他」「わからない」はエンジンが自動付与）、
(2) 式に入る数値fact（扶養人数等）は整数選択肢のみ・レンジ禁止、(3) 金額系レンジの最上段は番兵上限規約（facts JSON参照）、
(4) 型は `boolean | enum | integer`（チップ）と `integer_input`（数値入力欄+「わからない」。income_exact等の点値質問用）。

**正規化の責務分担**: 「askableは常に全キー存在・未知はnull」はAPI層（Pydantic）が強制する。
factgen（マッピング層）は欠落キーをnullと同一に扱う（この層に分岐は存在しない）。

### POST /api/chat（自由文入力専用、ステートレスラッパー）

選択肢タップは /api/judge だけで完結するため、このエンドポイントは**自由文回答の事実抽出専用**。

```jsonc
// Request
{ "facts": { /* 現在の全量 */ },
  "history": [                            // 直近の対話履歴（クライアント保持・毎回送る）
    { "role": "agent", "text": "ひとり親となった事由を教えてください" }
  ],
  "message": "離婚です" }
// Response
{ "facts": { /* 更新後の全量。クライアントが次回これを送る */ },
  "proposed_corrections": [              // 確認済み事実の変更はここに分離（自動適用しない）
    { "key": "hitorioya", "from": false, "to": true, "ask": "ひとり親世帯に変更しますか？" }
  ],
  "reply": "ありがとうございます。…",
  "next_question": "前年の所得（源泉徴収票の額）を教えてください",
  "judgment": { /* /api/judge と同形式の再判定結果 */ } }
```

**factsマージポリシー**（Geminiの抽出ミスがフォーム入力を壊さないための規則）:
- `extract_facts` の結果は **`null`（未知）のキーへの書き込みのみ自動適用**
- 既知の値と矛盾する抽出は `proposed_corrections` として返し、クライアントが確認UIを出して**ユーザー承認後に**factsへ反映
- 抽出結果はPydanticスキーマで検証してからマージ（型・列挙値・レンジの妥当性）

**会話履歴もクライアントが持つ**（factsと同じステートレス原則）:
- サーバーは毎回新規セッションのため、**直前に自分が何を質問したかを知らない**。履歴なしでは「いえ、ありません」等の省略応答が解釈不能になる
- クライアントが `history`（直近6往復・3KB上限）を保持して毎回送り、サーバーはプロンプトに前置してから `message` を処理する
- レスポンスの `reply`/`next_question` をクライアントが `history` に追記する

**ADKセッションの扱い**:
- `get_fast_api_app(session_service_uri=None)` → **InMemorySessionService を明示**（docsの例にあるsqlite URIは使わない。「DBなし」と矛盾しコンテナ内にファイルが残るため）
- リクエストごとに `create_session(state=facts)` → 履歴注入 → 1ターン実行 → **`delete_session`**（ウォームインスタンスのメモリ増加防止）。ADKの `/run` REST は直接公開しない
- インスタンスが消えても会話は壊れない（サーバーは何も覚えていない）

### GET /ops（「まわす」の見せ場）

- opsデータは **GCS公開バケット**に置き、フロントが直接フェッチ（Cache-Control: 300s）。ランタイム集計なし。コスト≒0円（GCS数KB）
- **書き込みジョブごとにファイルを分割**し、後勝ち上書きで相手のフィールドを消す競合を構造的に排除:
  - `ops/deploy.json` … デプロイCI（mainマージ）が書く: ルール更新履歴・golden合格率・デプロイ日時
  - `ops/verify.json` … nightly条文検証が書く: 最終検証日時・条文diff有無
  - フロントが2ファイルをフェッチして合成表示。これによりデプロイなしでも「最終検証: 昨日」が出せる
- **バケットにCORS設定が必須**（Cloud RunドメインからのフェッチはクロスオリジンHTTPのため）。
  `gcloud storage buckets update gs://<bucket> --cors-file=cors.json` をセットアップ手順に含める（origin = デプロイURL、method = GET）

## 推論エンジン層

- `rules/engine.pl`: 3値ヘルパー（`yes/no/unknown/val/v_lt/v_geq/v_indet` + 型ガード）+ 証明木メタインタプリタ（prolog-reasonerから移植）。非module、`user` にロード
- **証明木は2段階再導出**: 通常照会でステータス確定 → ground状態項をメタインタプリタで再導出（cut=true扱いで健全、rule-schema.md で検証済み）。直接照会との一致をgoldenテストで恒常検証
- `rules/<program>.pl`: 1制度=1module（`:- module(prog_id, [kettei_status/3, required_fact/3]).`）。rule-schema.md v1 準拠
- 実行: engine.pl → facts.pl（生成）→ rules/*.pl をロードし、制度×子ごとに `once(Prog:kettei_status(P, C, S))` を**両引数束縛で**照会（未束縛照会はカットが他の子の解を刈る。rule-schema.md 呼び出し規約）。サブプロセス、タイムアウト5秒
- 解なし（once失敗）は `error` 扱い。catch-all節（全制度必須）と合わせた二重の防御で「結果からの無言の欠落」を排除
- **多ファイル+module構成と、証明木メタインタプリタが module 内静的述語を `clause/2` で展開できるかは、Week 2統合テストの最初の項目**。不調時のフォールバック: 判定はmodule照会のまま、証明木取得時のみ対象制度を単独プロセスでロード（最終手段: 制度ごとに別プロセス、起動50ms×10で+0.5秒）
- ルールはイメージ焼き込み = ルール更新はデプロイ。二重ループ（法改正→再形式化→golden→再デプロイ）と一致し、`/ops` の更新履歴と連動

## フロントエンド画面フロー

```
[1] トップ: 基本情報フォームのみ（居住自治体・子の生年月・年収レンジ。30秒以内）
     │ POST /api/judge
[2] 結果一覧 + 一問一答パネル（同一画面。質問に答えるたびカードが更新される）
     ├─ 見出し: 「💰 月25,000円 + 一時金10万円（あと3問で最大+月◯円）」
     ├─ ✅ 該当カード: 金額（種別表示）+ 「なぜ？」→ 証明木を条文リンク付きで展開
     ├─ ❓ あとN問カード: 一問一答で確定に近づくと表示が減っていく
     ├─ ❌ 非該当カード: 理由 + 根拠条文
     ├─ ⚠️ 判定不能カード: error状態（ルール網羅漏れ等)。「窓口でご確認ください」+公式リンク
     ├─ ⬜ 未対応カード: programs.yaml の unsupported 制度を正直に表示
     └─ 質問パネル: next_question を1問ずつ表示
          [離婚] [死別] [未婚] [わからない/答えたくない]  ← タップ→ /api/judge（0円）
          （自由入力欄も常設 → /api/chat。「去年離婚して…」から複数fact一括抽出）
[3] 常時表示: 「法的助言ではありません」「入力情報は保存されません」公式窓口リンク
```

- 素のHTML/CSS/JS、1ページ構成。facts はJSの変数（メモリ上）にのみ存在し、リロードで消える
- 証明木はネストされた折りたたみリストで表現（木構造ライブラリ不要）
- 年収入力は「源泉徴収票の支払金額（額面）」と明記したレンジ選択。所得への変換はサーバー側

## コンテナとデプロイ

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends swi-prolog \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

| 設定 | 値 |
|---|---|
| region | asia-northeast1 |
| min-instances | 0（**審査期間中のみ1**に上げる。約1,500円/月、クレジット内） |
| max-instances | 2（コスト上限を物理的に確保） |
| concurrency / timeout | 8 / 60s（judge毎にswiplサブプロセスを起動するため、高concurrencyは1vCPU上でCPU競合する） |
| 環境変数 | `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, モデルID（`MODEL_CHAT` / `MODEL_FORMALIZE` / `MODEL_EVAL`） |
| 認証 | `--allow-unauthenticated`（公開デモ） |
| CORS | **設定しない**（フロントは同一オリジン配信。docsの例の `allow_origins=["*"]` はコピーしない） |
| 監視 | Cloud Trace（OTel）+ Billing予算アラート。**ログにfactsを出力しない** |

## コスト防御・入力ガード（多層）

| 層 | 内容 |
|---|---|
| 課金 | Billing予算アラート（日次500円目安）+ 超過通知での手動停止（Pub/Sub自動停止はストレッチ） |
| スケール | `max-instances=2` で物理上限 |
| クォータ | Vertex AI側のプロジェクトクォータを絞る（RPM/日次） |
| レート制限 | アプリ層トークンバケット: IPあたり毎分N回。IPはCloud Runが付与する `X-Forwarded-For` 末尾のクライアント値を使用。**インメモリ実装のためインスタンスごとに独立**（max=2なので実効上限は2倍。デモ規模では許容と明記） |
| 入力サイズ | `message` ≤ 500字 / facts JSON ≤ 10KB / `history` ≤ 6往復・3KB をサーバー側で検証（413）。超過分の履歴は古い側から切り捨て |
| 対話上限 | **自由文（/api/chat）のみ**フロントで10回まで（UX用）。選択肢タップは /api/judge のみでLLM不使用のため制限不要。**ステートレス故にサーバーはターン数を強制できない**ため、コスト防御の実効線は上記レート制限+クォータであることを明記 |

## CI/CD（docs/dev-methodology.md の段階パイプラインを具体化）

| トリガ | 内容 | LLM |
|---|---|---|
| PR | pytest（goldenテスト: swipl決定的実行）+ lint | 不使用 |
| main merge | adk eval（Flash-Lite）→ Docker build → `gcloud run deploy` → `ops/deploy.json` をGCSへ | 少量 |
| nightly / 手動 | 条文ソース再取得 → 形式化エージェント再実行 → golden照合 → diffあればPR起票 + **`ops/verify.json` を更新** | 使用 |

## スコープ拡大戦略（網羅性こそが売りであることへの設計上の備え）

「10制度しか判定できない」で終わらないために、ルールベースを**スケールする構造**で作る。

**レイヤ構造**: 制度は2層に分かれ、追加コストが本質的に違う。

```
rules/
├── engine.pl
├── national/        # 国の制度（児童手当・児童扶養手当・就学支援金…）
│   └── *.pl         #   → 一度形式化すれば全国どこでも有効
└── municipal/
    └── shibuya/     # 自治体上乗せ・独自制度
        └── *.pl     #   → 自治体追加 = このディレクトリの差分だけ
```

programs.yaml に `layer: national | municipal` と `municipality` を追加。判定時は national + 居住自治体の municipal をロードする。

**命名規約**: 自治体制度の id / module名は**自治体プレフィックス必須**（例: `shibuya_kodomo_iryouhi`）。
ランタイムは1自治体しかロードしないため衝突しないが、**CIは全自治体のルールを同時ロードしてテストする**ため、
プレフィックスなしだと第2自治体追加の時点でmodule名が衝突する（同名制度は普通にある: 子ども医療費助成等）。

**拡大フェーズ**（限界費用の逓減を `/ops` で実証する）:

| Phase | 内容 | 位置づけ |
|---|---|---|
| 1（Week 1-3） | コア10制度をgolden付きで検証済みに | 深さの証明。判定品質の土台 |
| 2（Week 4、ストレッチ） | **国制度を中心に15〜20制度へ拡大**。形式化エージェントの生産性（1制度あたりの追加時間の推移）を `/ops` に記録 | 広さの証明。「ルール追加の限界費用が下がる」というプロダクトの中心主張のデータ化 |
| 3（デモ） | **第2自治体の追加をパイプラインで実演**（municipal差分の形式化→golden→deploy） | 「まわす」の最強デモ。手作業のOpenFisca-Japanとの決定的な差別化 |

**品質ゲート（譲らない線）**: ユーザーに見せる判定は **golden検証済み制度のみ**。自動形式化しただけの制度は
`status: unsupported`（⬜カード）に留め、検証通過後に昇格させる。制度数を盛るために信頼を売らない。
網羅性の主張は「対応制度の**中で**は全解探索で取りこぼさない」+「対応制度を増やす限界費用が構造的に低い」の2段で語る。

## セキュリティ・プライバシー

- 個人情報の保存なし（Cloud Loggingにはステータスコードとレイテンシのみ。factsと自由文は記録しない）
- プロンプトインジェクション面: 自由文入力はStructured Outputで事実抽出に限定し、Pydanticスキーマ検証後にマージ。**ユーザー入力が直接Prologコードに混ざる経路を作らない**（known/2 事実の生成はPython側のテンプレートのみ。値は型検証済みの数値/真偽/列挙に限る）
- 免責表示を常時固定（「法的助言ではない」「最終判断は自治体窓口」）

## 未決事項

- プロダクト名（候補: モラエル / うけとりナビ / Todoke / 証明つき給付金チェッカー）
- MCPエンドポイント公開（案Gの+1日要素）: `/mcp` ルートに推論コアを露出。**Week 3の進捗を見てストレッチとして判断**
- 所得制限の公式数値・年収→所得変換式の検証（golden case作成と同時、statute_source.mdに出典固定）
- module + 多ファイルロードの実機確認（Week 2統合テスト先頭。フォールバック: 制度別プロセス）
