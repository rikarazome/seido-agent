# アーキテクチャ設計書（v2.0）

2026-06-13 改訂。v1.1（2026-06-11）からの主要変更: (1) フォーム＋一問一答 → 対話型AIチャットUI、(2) 子育て世帯限定 → 全カテゴリ給付制度、(3) 全制度Prolog統一判定（ハルシネーション防止）。

### v1→v2 変更サマリ

| 項目 | v1 | v2 | 理由 |
|---|---|---|---|
| UX | フォーム入力 → 一問一答チップ | **対話型チャットUI** | AIエージェントとしての体裁。チェッカーではなくエージェント |
| 対象制度 | 子育て世帯×10制度 | **全カテゴリ×30+制度** | 子育て限定では「ただのチェッカー」。網羅性が価値 |
| 判定方式 | Prolog（複雑制度）+ 情報提供のみ（単純制度） | **全制度Prolog統一** | 単純制度でもLLMハルシネーション防止。パイプライン一本化 |
| Gemini役割 | 自由文抽出のみ | **対話進行 + 事実抽出 + 判定説明** | チャットUXの中核 |
| メインAPI | POST /api/judge | **POST /api/chat**（実装予定） | 対話型UIの中核エンドポイント |

## 設計思想

```
「AIが対話で状況を聞き取り、形式推論エンジンが検証可能な判定を返す」
  — LLMの自然言語力 × Prologの論理的正確性
```

- **Geminiは判定しない**。対話の進行・事実の抽出・結果の説明だけを担う
- **Prologは対話しない**。判定・金額算出・根拠証明だけを担う
- **判定結果は全てProlog由来**。LLMが「もらえます」と言うことはない。Prologの判定結果をGeminiが自然言語で説明する

## 決定事項サマリ

| 項目 | 決定 | 理由 |
|---|---|---|
| 形態 | ログイン不要のモバイル対応Webアプリ | とどける力・デモ体験が最強。審査員もProtoPedia訪問者もURLタップで完結 |
| 入力方式 | **対話型チャットUI**（実装予定）。Geminiが対話で状況を聞き取り → JSON事実抽出 | 自然な対話で複数事実を同時取得。選択肢チップもチャット内に埋め込み |
| 対象制度 | **全カテゴリ×30+制度**（v1: 子育て×10制度） | 子育て限定では「ただのチェッカー」。網羅性が価値 |
| 判定方式 | **全制度Prolog統一**（ハルシネーション防止） | 単純制度でもLLM判定は使わない。パイプライン一本化 |
| サーバー | **Cloud Run 1サービスのみ**（min=0, max=2） | scale-to-zeroで待機コスト0円。無料枠内で全運用が収まる見込み |
| DB | **なし**（完全ステートレス） | 世帯事実はクライアントが保持し毎回送る。「保存しません」が設計上の事実になる |
| LLM | Gemini（Vertex AI経由、クレジット消化） | ハッカソン要件 + 形式化はビルド時のみでランタイム消費は最小 |
| Prolog | SWI-Prologを**同一コンテナに同梱**、サブプロセス実行 | 別サービス化は過剰。コールドスタートも課金も1個で済む |
| フロント | ビルドレスの素のHTML/CSS/JS（FastAPIから静的配信） | ビルドパイプライン不要。CIが単純になる。複雑化したらViteへ移行 |
| ルール表現 | **3値事実 + module化**（docs/specs/rule-schema.md v1） | 未知/偽の混同バグと述語衝突を設計段階で排除（検証済み） |

## システム構成図

```
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Run（1コンテナ, asia-northeast1）                          │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │ FastAPI   │    │ Chat Engine  │    │ Prolog推論エンジン      │  │
│  │          │    │ (Gemini)     │    │                       │  │
│  │ /api/chat├───▶│ 1. 対話理解   │    │ engine.pl             │  │
│  │ (実装予定) │    │ 2. 事実抽出   │    │ rules/national/*.pl   │  │
│  │          │◀───│ 3. 応答生成   │    │ rules/municipal/**/.pl│  │
│  │          │    │              │    │                       │  │
│  │ /api/judge────┼──────────────┼───▶│ swipl subprocess      │  │
│  │ (実装済み) │    │              │    │ facts → known/2       │  │
│  │ /api/proof────┼──────────────┼───▶│ prove/3 (proof tree)  │  │
│  │ (実装済み) │    │              │    │                       │  │
│  └──────────┘    └──────────────┘    └───────────────────────┘  │
│                         │                                       │
│                         ▼                                       │
│                  Vertex AI (Gemini)                              │
└─────────────────────────────────────────────────────────────────┘

ブラウザ（チャットUI）
 │
 ├─ POST /api/chat    … 対話1ターン（Gemini + Prolog判定）【実装予定】
 ├─ POST /api/judge   … 直接判定（LLM不使用、事実JSON直接送信）【実装済み】
 ├─ POST /api/proof   … 判定根拠の証明木取得【実装済み】
 ├─ GET  /api/municipalities … 自治体メタデータ【実装済み】
 ├─ GET  /healthz     … ヘルスチェック【実装済み】
 ├─ GET  /ops         … opsダッシュボード(静的)【実装予定】
 └─ GET  /            … 静的フロント配信【実装済み】

    ビルド時（CI, GitHub Actions）:
    条文 → 形式化エージェント(Gemini) → rules/*.pl → goldenテスト → イメージ焼き込み → deploy
```

## 対話パイプライン（/api/chat の処理フロー）【実装予定】

```
ユーザー発話
    │
    ▼
[Step 1] Gemini: 事実抽出（Structured Output → JSON）
    │  入力: ユーザー発話 + 対話履歴 + 現在の事実JSON
    │  出力: 更新された事実JSON（型検証済みの値のみ）
    │  制約: Geminiが出力するのはJSONのみ。Prologコードは絶対に生成しない
    │
    ▼
[Step 2] factgen.py: JSON → Prolog事実テキスト（決定的、LLM不使用）
    │  唯一のProlog生成ゲートウェイ。ユーザー入力は到達しない
    │
    ▼
[Step 3] Prolog判定: 全制度 × 全対象に kettei_status/3 を照会
    │  出力: 制度ごとの判定結果（decided/blocked/ineligible/error）
    │
    ▼
[Step 4] Gemini: 応答生成
    │  入力: 判定結果JSON + 対話履歴 + blocked制度のmissing facts
    │  出力: 自然言語の応答 + 次に聞くべきことの提案
    │  制約: 「確実にもらえます」等の断定表現を使わない（システムプロンプトで強制）
    │  次の質問の選定: 質問選定アルゴリズム（後述）を内部で使用
    │
    ▼
チャット応答（判定カード + 自然言語説明）
```

### Step 1: 事実抽出の詳細

Gemini Structured Outputで以下のスキーマに従うJSONを生成:

```jsonc
{
  "extracted_facts": {
    // askableキーと値のペア。抽出できなかったキーは含めない
    "hitorioya": true,
    "hitorioya_jiyuu": "rikon",
    "nenshu": [3000000, 5000000]
  },
  "extracted_profile": {
    // 初回の自己紹介から抽出する基本情報
    "municipality": "shibuya",
    "claimant_birthday": "1988-04-01",
    "children_birthdays": ["2019-06-01", "2022-03-15"]
  },
  "confidence": "high",  // high/medium/low
  "ambiguous_points": []
}
```

**マージポリシー**:
- `null`（未知）のキーへの書き込みのみ自動適用
- 既知の値と矛盾する抽出は `proposed_corrections` として返し、ユーザー確認後に反映
- Pydanticスキーマで型・列挙値・レンジの妥当性を検証してからマージ
- **confidence: low の抽出は自動適用しない**（確認質問を生成）

### Step 4: 応答生成のシステムプロンプト要点

```
あなたは制度案内エージェントです。ユーザーの状況を聞き取り、該当する給付制度を案内します。

【絶対に守ること】
- 判定結果はProlog推論エンジンの出力のみに基づく。自分で判定しない
- 「確実にもらえます」「必ず受給できます」と断定しない
- 判定結果を伝える際は「条件に該当する可能性があります」「申請により受給できる見込みです」等の表現を使う
- 最終判断は自治体窓口での確認を促す
- ユーザーのプライバシーに配慮し、センシティブな質問は選択肢を提示する

【対話の進め方】
- 初回: 居住区・家族構成・大まかな状況を聞く
- 判定結果が出たら: 該当制度を金額とともに案内し、blocked制度の追加質問をする
- blocked制度がなくなったら: 全判定結果のサマリーを提示
- 常に「他に気になることはありますか？」で終える
```

## LLM使用ポイント（コスト構造の根拠）とモデル固定

| 処理 | 実行タイミング | 担当 | モデル（環境変数でピン留め） | コスト |
|---|---|---|---|---|
| 法令の形式化（条文→Prologルール） | **ビルド時のみ** | Gemini | Pro系（精度優先。ユーザー数と無関係に償却） | 償却 |
| 全制度Prolog判定 | ランタイム（全エンドポイント） | **Prologのみ** | —（**swipl、0円**） | 0円 |
| 選択肢タップ処理 | ランタイム（/api/judge） | **Prologのみ** | —（**LLM不使用、0円**） | 0円 |
| 対話からの事実抽出 | ランタイム（/api/chat Step 1）【実装予定】 | Gemini | Flash系 | ~0.5円/ターン |
| 判定結果の説明生成 | ランタイム（/api/chat Step 4）【実装予定】 | Gemini | Flash系 | ~0.5円/ターン |
| 質問文・選択肢の提示 | ランタイム | **静的メタデータ**（data/questions.yaml） | —（**0円**。LLM生成しない=誤選択肢ゼロ） | 0円 |
| adk eval（CI） | mainマージ時 | Gemini | Flash-Lite系 | 少量 |

試算: /api/chat利用時 平均5ターンで約5円/セッション（Flash）。選択肢タップのみ（/api/judge直接利用）は **0円**。

## facts JSONスキーマ（rule-schema.md v1 と1:1対応）

```jsonc
{
  "facts": {
    "claimant": {
      "birth_date": "1988-04-01"    // 申請者自身の生年月日（高齢者・障害者制度に必要）
    },
    "children": [
      { "id": "c1", "birth_date": "2019-06-01",
        "askable": { "koukou_zaigaku": null, "gakkou_kubun": null } }
    ],
    "askable": {
      // 値の型: 数値（点値） | [lo, hi]（レンジ） | true/false | 列挙文字列
      //        | null（未質問） | "declined"（質問済み・回答なし。nullと区別必須 — 区別しないと
      //          「わからない」の直後に同じ質問が最優先で再計算され無限再質問になる）
      // 上限なしレンジの規約: 「1,000万円以上」等は番兵上限 [10000000, 999999999] で表現。
      // 全制度の限度額 < 番兵 であることをCIで恒常検証（番兵を超える限度額の出現＝即CI失敗）
      // 正規化規則: askable は常に全キーを持ち、未知は null（キー欠落を許さない。
      // 欠落とnullの扱い分岐によるバグを防ぐ）。現v1実装では factgen.py が未知キーに
      // ValueError を返す（Pydanticスキーマでの強制はv2で実装予定）
      // 名前空間規則: askable は世帯レベルのフラット集合。一部キー（seikei_douitsu_partner 等）は
      // ASKABLE_MAPで scope="per_child" として全子に同値で注入する（JSON上は世帯レベルの1キー、
      // Prolog上は子ごとの述語。事実婚パートナーは世帯の状態なので同値注入が正しい）。
      // 子ごとに値が真に異なる事実（在学状況・学校区分）は children[].askable に置く
      // （就学支援金で導入済み。questions.yaml の scope: per_child）

      // === v1実装済みキー ===
      "nenshu": [3000000, 5000000],      // 年収（額面）。フォームはレンジ選択
      "shotoku_exact": null,             // income_exact質問の回答（控除後所得の点値）。
                                         // 存在すれば nenshu 由来の income を上書き（ハイブリッド方式）
      "hitorioya": true,
      "hitorioya_jiyuu": "declined",     // ← 質問済み・回答拒否。"declined" 文字列を書く
                                         //    （nullのままにするとステートレス故に同じ質問が再提示される）
      "seikei_douitsu_partner": null,    // ← 未質問。null
      "fuyou_ninzu": 2,
      "kenkou_hoken": null,

      // === v2追加キー（実装予定）===
      "shogai_techo": null,              // 障害者手帳の種類・等級
                                         // null | "shintai_1" | "shintai_2" | ... | "ryoiku" | "seishin_1" | ...
      "shogai_teido": null,              // 障害の程度（重度/中度/軽度）
      "kaigo_nintei": null,              // 介護認定 null | "youshien_1" | ... | "youkaigo_5" | false
      "ninshin": null,                   // 妊娠中か（出産関連制度）
      "shussan_yoteibi": null,           // 出産予定日
      "juutaku_type": null,              // 住居種別: "chintai" | "jitaku" | "nashi"
      "hikazei": null,                   // 住民税非課税世帯か
      "koyou_hoken": null,              // 雇用保険加入
      "rishoku": null,                   // 離職中か（住居確保給付金）
      "rishoku_jiyuu": null,             // 離職理由
      "seikatsu_hogo": null,            // 生活保護受給中か（排他条件）
      "nanbyo_nintei": null,            // 難病認定
      "jido_yougo_shisetsu": null       // 児童養護施設入所（除外条件）
    }
  },
  "municipality": "shibuya",
  "as_of": "2026-06-13"                  // 判定基準日（省略時はJSTの今日。goldenテストで固定可能）
}
```

**データ型契約**:
- **日付**: ISO 8601 (`YYYY-MM-DD`、ゼロ埋め必須)。`2026/6/13` や `2026-6-1` は 422。`as_of` の有効範囲は `2020-01-01` 〜 `2100-12-31`（app.py で検証）
- **children配列**: `id` は省略可（省略時は `c1, c2, ...` を自動採番）。指定する場合は `/^[a-z][a-z0-9_]*$/` に一致する必要がある（Prolog atom安全性）。`birth_date` は必須。`askable` は省略可（省略時は `{}`）。重複IDの検出は未実装（v2で追加予定）
- **askable値の型**: `null`（未質問）| `"declined"`（回答拒否）| `true`/`false` | 整数 | `[lo, hi]`（レンジ、整数2要素、lo ≤ hi）| 列挙文字列（小文字英数_）

マッピング層（Python、決定的・LLM不使用）の責務:
- `birth_date` → `age/2`・`age_nendo_matsu/2`（**JST基準**、基準日は `as_of`）
- `claimant.birth_date` → `age(p1, Age)` を生成【v2追加・実装予定】（高齢者・障害者制度の年齢条件に必要）
- `children` → `child/1` + `kango_by/2`・`seikei_futan/2` を既定値として注入（対話で訂正可）
- `nenshu` → **ハイブリッド方式（2026-06-11決定）**: 一次判定はフォームの年収レンジを給与所得控除のみで
  **概算変換**（養育費・諸控除は無視 → レンジが広がる方向の安全側誤差として扱い、限度額を跨げば自然に
  blocked(income_exact) になる）。**跨いだ場合のみ**「源泉徴収票の給与所得控除後の金額 + 養育費」を
  聞き、回答を `shotoku_exact` に書く（**nenshuには書き戻さない** — 回答は控除後所得であり年収ではない。
  factgenは shotoku_exact 存在時に nenshu を無視する優先規則）。レンジは**端点のみ変換**
  （給与所得控除は単調非減少。**単調でない控除を導入する場合は要再設計**）。区間評価はProlog側
- `null` / `"declined"` は **known事実を生成しない**（= Prolog側ではどちらも unknown、判定はblockedのまま）。
  両者の違いは**質問選定アルゴリズムだけ**が見る（declined は選定対象から除外）

### factgen.py の拡張（v2、実装予定）

```python
ASKABLE_MAP = {
    # v1（実装済み）
    "nenshu": ("income", "claimant"),
    "shotoku_exact": ("income", "claimant"),
    "hitorioya": ("hitorioya", "claimant"),
    "hitorioya_jiyuu": ("hitorioya_jiyuu", "claimant"),
    "fuyou_ninzu": ("fuyou_ninzu", "claimant"),
    "seikei_douitsu_partner": ("seikei_douitsu_partner", "per_child"),
    "kenkou_hoken": ("kenkou_hoken", "claimant"),

    # v2（実装予定）
    "shogai_techo": ("shogai_techo", "claimant"),
    "shogai_teido": ("shogai_teido", "claimant"),
    "kaigo_nintei": ("kaigo_nintei", "claimant"),
    "ninshin": ("ninshin", "claimant"),
    "shussan_yoteibi": ("shussan_yoteibi", "claimant"),
    "juutaku_type": ("juutaku_type", "claimant"),
    "hikazei": ("hikazei", "claimant"),
    "koyou_hoken": ("koyou_hoken", "claimant"),
    "rishoku": ("rishoku", "claimant"),
    "rishoku_jiyuu": ("rishoku_jiyuu", "claimant"),
    "seikatsu_hogo": ("seikatsu_hogo", "claimant"),
    "nanbyo_nintei": ("nanbyo_nintei", "claimant"),
    "jido_yougo_shisetsu": ("jido_yougo_shisetsu", "per_child"),
}
```

## API設計

### エンドポイント一覧

| エンドポイント | 役割 | 実装状況 |
|---|---|---|
| POST /api/chat | メイン（対話1ターン、Gemini+Prolog） | 実装予定 |
| POST /api/judge | 直接判定（LLM不使用、テスト/選択肢タップ） | 実装済み |
| POST /api/proof | 証明木取得 | 実装済み |
| GET /api/municipalities | 自治体メタデータ | 実装済み |
| GET /healthz | ヘルスチェック（Cloud Run用） | 実装済み |
| GET /ops | 運用ダッシュボード | 実装予定 |

### POST /api/chat（メインエンドポイント）【実装予定】

チャットUIからの全対話はここを通る。

```jsonc
// Request
{
  "facts": { /* 現在の事実JSON全量 */ },
  "history": [
    { "role": "user", "text": "渋谷区在住で、3歳の子供がいます。離婚してひとり親です。" },
    { "role": "agent", "text": "..." }
  ],
  "message": "年収は300万円くらいです",
  "municipality": "shibuya"
}

// Response
{
  "facts": { /* 更新後の事実JSON全量 */ },
  "proposed_corrections": [],
  "reply": "ありがとうございます。現在の情報をもとに判定しました。...",
  "judgment": {
    "headline": {
      "monthly_yen": 57500,
      "oneoff_yen": 100000,
      "yearly_yen": 0,
      "in_kind_count": 1
    },
    "results": [ /* /api/judge と同形式 */ ]
  },
  "blocked_count": 3,
  "suggested_question": "税法上の扶養親族は何人ですか？"
}
```

**処理フロー**:
1. Gemini Structured Output で事実抽出 → facts更新
2. factgen.py で Prolog事実テキスト生成
3. 全制度判定（/api/judge と同じロジック）
4. Gemini で応答生成（判定結果 + blocked制度情報を入力）
5. レスポンス返却

**ADKセッションの扱い**:
- `get_fast_api_app(session_service_uri=None)` → **InMemorySessionService を明示**（docsの例にあるsqlite URIは使わない。「DBなし」と矛盾しコンテナ内にファイルが残るため）
- リクエストごとに `create_session(state=facts)` → 履歴注入 → 1ターン実行 → **`delete_session`**（ウォームインスタンスのメモリ増加防止）。ADKの `/run` REST は直接公開しない
- インスタンスが消えても会話は壊れない（サーバーは何も覚えていない）

### POST /api/judge（直接判定、LLM不使用）【実装済み】

テスト・デバッグ・CI用の直接判定エンドポイント。LLM不使用。チャットUI内の選択肢チップタップ時にも使用可能（0円）。

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
      "children": [                              // 対象ごとの内訳（subject=claimant制度では [{"subject":"self",...}]）
        { "subject": "c1", "status": "ineligible", "reason": "18歳年度末超" },
        { "subject": "c2", "status": "decided", "yen": 10000 },
        { "subject": "c3", "status": "decided", "yen": 30000 }
      ],
      // 証明木は judge レスポンスに含めない（遅延取得）。「なぜ？」タップ時に
      // POST /api/proof { facts, municipality, program, subject } → サーバー側で status 再計算 → prove/3 の2段階再導出で返す。
      // レスポンス肥大とPrologの二重実行を避け、直接照会×メタ解釈の一致検証とも整合
      },                                               // statute は未実装（v2で programs.yaml から付与予定）
    { "program": "jidou_fuyou_teate", "name": "児童扶養手当",
      "status": "blocked", "missing": ["hitorioya_jiyuu"],
      "partial_amount": { "type": "monthly", "yen": 0 } },  // 確定済み分があれば部分合計を出す
    { "program": "...", "status": "ineligible", "reason": "..." },
    { "program": "...", "status": "unsupported" },  // data/programs.yaml の status から生成
    { "program": "...", "status": "error" }         // catch-all / 解なし。「判定不能」カード
  ],
  "next_question": { ... }  // 質問選定アルゴリズム（後述）。/api/chat内部でも使用
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

- 見出しは「月25,000円 ＋ 一時金10万円」のように**種別を分けて表示**。月額・一時金・年額・現物を雑に足さない
- 制度名・条文リンク・amount_type・subject・unit は `data/programs.yaml` から付与（ルールは判定と区分のみ返す）
- 全制度module×全対象（子 または self）に対して `Prog:kettei_status(P, C, S)` を**両引数束縛・`once/1`**で照会（呼び出し規約はrule-schema.md）
- **金額のレンジ評価**: 逓減式等で所得がレンジのまま確定（decided(ichibu)等）した場合、ランナーがLo/Hiの2点で金額式を評価し「月◯〜◯円」とレンジ表示する（rule-schema.md の規約）
- **レスポンスに `next_question` を含む**（下記・質問選定アルゴリズム）。判定と次の質問が1リクエストで返るため、選択肢タップのループは /api/judge だけで回る

### 用語: fact / askable_key / askable

| 用語 | 意味 | 例 |
|---|---|---|
| **fact** | Prologの述語名。questions.yamlの`fact`フィールド | `income`, `hitorioya` |
| **askable_key** | facts JSONの`askable`内のキー名。questions.yamlの`askable_key`で上書き可能 | `nenshu`（fact `income` に対応） |
| **askable** | facts JSON内の世帯レベルの事実集合（`facts.askable`）。子ごとの事実は `children[].askable` | — |

通常は `fact == askable_key`。`income`→`nenshu` のように異なるのは、Prolog述語名（`income/2`）と ユーザー向けの質問（年収レンジ）で粒度が異なる場合。`_fact_to_askable()` が questions.yaml からマッピングを導出する。

### 質問選定アルゴリズム（内部ロジック、/api/judge・/api/chat 共通）

blocked制度を効率的に確定に導くための質問順序を決定する内部ロジック。/api/judge では `next_question` フィールドとして直接返し、/api/chat では Step 4 の「次に聞くべきこと」の決定に使用する。

```jsonc
// /api/judge レスポンスに含まれる next_question（nullなら質問なし=全制度確定）
{ "next_question": {
    "fact": "hitorioya_jiyuu",
    "askable_key": "hitorioya_jiyuu",  // フロントはこのキーに facts.askable[askable_key] = 回答値 で書き込む
    "text": "ひとり親となった理由を教えてください",
    "why": ["jidou_fuyou_teate", "jidou_ikusei_teate"],   // この質問で確定に近づく制度（必然性の可視化）
    "choices": [
      { "value": "rikon",  "label": "離婚" },
      { "value": "shibou", "label": "死別" },
      { "value": "mikon",  "label": "未婚" },
      { "value": "__free_text__", "label": "その他" },
      { "value": "declined", "label": "わからない / 答えたくない" }
    ],
    "allow_free_text": true,
    "child": null } }           // per-child質問の場合は対象の子ID（"c1"等）。フロントは
                                // child != null なら children[].askable[fact] に書き込む
```

| 設計要素 | 規則 |
|---|---|
| 質問の選定 | **決定的**: declined以外の未知factについて、「その事実を要求しているblocked制度数」最大のものを選ぶ。同点は対象制度の `potential_amount`（programs.yaml）合計が大きい順、さらに同点は **questions.yaml のファイル順**（=自然なインタビュー順を編集で制御できる）。per-childのfactは「未回答の子が残っている」場合のみ候補（全子declinedなら除外=再質問ループ防止） |
| 選択肢の生成 | **静的**: data/questions.yaml にfactごとの質問文・選択肢を定義。LLM生成しないので誤った選択肢が出ない |
| チャットUI内での表示 | 選択肢はチャット内に**チップとして埋め込み表示**。タップ→ facts に直接書いて /api/judge（LLM不使用、0円）。自由文入力の場合のみ /api/chat（Gemini）を使用 |
| 「わからない/答えたくない」 | factに **`"declined"`** を書く（nullのままにしない — ステートレス故にnullだと次の/api/judgeで同じ質問が最優先のまま再提示され**無限再質問**になる）。該当制度はblockedのまま、質問選定からは除外 |
| 「その他」（法定列挙外） | **値を書かず自由文入力へ誘導**（`__free_text__`）。Geminiが法定事由のいずれに該当するか分類し、どれにも該当しなければfactは未知のまま+「該当する事由が確認できませんでした」を表示。`sonota` のような**法定列挙にない値を有効値として書かない**（書くと `val(F,_)` の存在チェックを誤って通過し誤decidedになる） |
| 自由入力 | **POST /api/chat**（Gemini抽出）。「去年離婚して……」のような文から複数factを一度に抽出できるのが選択肢に対する付加価値 |
| 終了条件 | next_question = null または ユーザーの明示終了。**null には2状態がある**: (a) 全制度確定（blockedなし）、(b) 残る未知factがすべてdeclined（blockedカードが残存）。フロントは `results` 内の `status: "blocked"` の有無で判別する（専用フラグは不要 — blockedカードに「回答がなかったため確定できません（窓口で確認できます）」を表示すれば十分）。「ここまでで月◯円確定」を常時表示し、途中離脱でも価値が残る |

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
(4) 型は `boolean | enum | integer`（チップ）、`range_choice`（金額レンジ選択。値は `[lo, hi]`）、`integer_input`（数値入力欄+「わからない」。income_exact等の点値質問用）。

**正規化の責務分担**: v1ではfactgen.py が未知キーに `ValueError` を返し、app.py が 422 に変換する。
askable全キーの存在保証（Pydanticスキーマ強制）はv2で実装予定。
factgen（マッピング層）は欠落キーをnullと同一に扱う（この層に分岐は存在しない）。

### POST /api/proof（証明木取得）【実装済み】

```jsonc
// Request（status_term は不要 — サーバー側で再計算する）
{ "facts": {…}, "as_of": "2026-06-13", "municipality": "shibuya", "program": "jidou_fuyou_teate", "subject": "c1" }
// Response
{ "program": "jidou_fuyou_teate", "subject": "c1", "status": "decided(zenbu)", "proof": { ... } }
```

証明木はサーバー側で再計算する。クライアントがPrologテキストを送る経路は存在しない（セキュリティ規約）。

### ステートレス原則

- facts・対話履歴は全てクライアントが保持
- サーバーは何も保存しない（DB不要）
- リロードで全消去 → 「保存しません」が設計上の事実

### 対話履歴の制約

- クライアントが `history`（直近8往復・5KB上限）を保持して毎回送る
- サーバーはプロンプトに前置してから処理
- 上限超過分は古い側から切り捨て
- サーバーは毎回新規セッションのため、**直前に自分が何を質問したかを知らない**。履歴なしでは「いえ、ありません」等の省略応答が解釈不能になる

### GET /ops（「まわす」の見せ場）【実装予定】

- opsデータは **GCS公開バケット**に置き、フロントが直接フェッチ（Cache-Control: 300s）。ランタイム集計なし。コスト≒0円（GCS数KB）
- **書き込みジョブごとにファイルを分割**し、後勝ち上書きで相手のフィールドを消す競合を構造的に排除:
  - `ops/deploy.json` … デプロイCI（mainマージ）が書く: ルール更新履歴・golden合格率・デプロイ日時
  - `ops/verify.json` … nightly条文検証が書く: 最終検証日時・条文diff有無
  - フロントが2ファイルをフェッチして合成表示。これによりデプロイなしでも「最終検証: 昨日」が出せる
- **バケットにCORS設定が必須**（Cloud RunドメインからのフェッチはクロスオリジンHTTPのため）。
  `gcloud storage buckets update gs://<bucket> --cors-file=cors.json` をセットアップ手順に含める（origin = デプロイURL、method = GET）

## 推論エンジン層

### 基本構造（実装済み）

- `rules/engine.pl`: 3値ヘルパー（`yes/no/unknown/val/v_lt/v_geq/v_indet` + 型ガード）+ 証明木メタインタプリタ（prolog-reasonerから移植）。非module、`user` にロード
- **証明木は2段階再導出**: 通常照会でステータス確定 → ground状態項をメタインタプリタで再導出（cut=true扱いで健全、rule-schema.md で検証済み）。直接照会との一致をgoldenテストで恒常検証
- `rules/<program>.pl`: 1制度=1module（`:- module(prog_id, [kettei_status/3, required_fact/3]).`）。rule-schema.md v1 準拠
- 実行: engine.pl → facts.pl（生成）→ rules/*.pl をロードし、制度×子ごとに `once(Prog:kettei_status(P, C, S))` を**両引数束縛で**照会（未束縛照会はカットが他の子の解を刈る。rule-schema.md 呼び出し規約）。サブプロセス、タイムアウト15秒
- 解なし（once失敗）は `error` 扱い。catch-all節（全制度必須）と合わせた二重の防御で「結果からの無言の欠落」を排除
- ルールはイメージ焼き込み = ルール更新はデプロイ。二重ループ（法改正→再形式化→golden→再デプロイ）と一致し、`/ops` の更新履歴と連動

### ディレクトリ構成

```
rules/
├── engine.pl                        # 3値ヘルパー + 証明木メタインタプリタ
├── national/                        # 国制度（全国共通）
│   ├── jidou_teate.pl              # 実装済み
│   ├── jidou_fuyou_teate.pl        # 実装済み
│   ├── kouko_shugaku_shienkin.pl   # 実装済み
│   ├── tokubetsu_jidou_fuyou_teate.pl  # v2追加予定
│   ├── shogaiji_fukushi_teate.pl       # v2追加予定
│   ├── tokubetsu_shogaisha_teate.pl    # v2追加予定
│   ├── shussan_ikuji_ichijikin.pl      # v2追加予定
│   ├── shussan_kosodate_ouen.pl        # v2追加予定
│   ├── jukyo_kakuho_kyufukin.pl        # v2追加予定
│   ├── jiritsu_shien_iryo_seishin.pl   # v2追加予定
│   ├── jiritsu_shien_iryo_ikusei.pl    # v2追加予定
│   ├── nanbyo_iryo_josei.pl            # v2追加予定
│   ├── seikatsu_hogo.pl                # v2追加予定
│   ├── koto_shokugyo_kunren.pl         # v2追加予定
│   └── jiritsu_shien_kyoiku_kunren.pl  # v2追加予定
├── municipal/
│   ├── tokyo/                       # 都制度（23区共通）
│   │   ├── tokyo_018_support.pl    # 実装済み
│   │   ├── tokyo_jidou_ikusei_teate.pl  # 実装済み
│   │   ├── hitorioya_iryo_josei.pl      # v2追加予定
│   │   ├── tokyo_judo_shinshin_teate.pl # v2追加予定
│   │   ├── shinshin_shogaisha_iryo_josei.pl # v2追加予定
│   │   ├── jukensei_challenge.pl            # v2追加予定
│   │   ├── tokyo_akachan_first.pl           # v2追加予定
│   │   └── shiritsu_koko_jugyoryo_keigen.pl # v2追加予定
│   ├── shibuya/                     # 区独自制度
│   │   ├── shibuya_kodomo_iryouhi.pl   # 実装済み
│   │   ├── shibuya_birthday_support.pl # 実装済み
│   │   └── shibuya_shugaku_enjo.pl     # v2追加予定
│   ├── chiyoda/
│   │   └── chiyoda_kodomo_iryouhi.pl   # 実装済み
│   ... (23区分、子ども医療費助成は実装済み)
```

### engine.plの拡張（v2、実装予定）

v2で追加する述語（申請者自身の年齢チェック用）:

```prolog
% 申請者自身の年齢チェック（高齢者・障害者制度用）
claimant_age_check(P, MinAge) :- claimant(P), age(P, A), A >= MinAge.
```

### 制度間の排他・依存関係

Prologで自然に表現:

```prolog
% 生活保護受給中は他の多くの手当が停止
kettei_status(P, C, ineligible(seikatsu_hogo_jukyuu)) :-
    claimant(P), child(C), yes(seikatsu_hogo(P)), !.

% 児童養護施設入所中は児童手当の対象外
kettei_status(P, C, ineligible(shisetsu_nyusho)) :-
    claimant(P), child(C), yes(jido_yougo_shisetsu(C)), !.
```

## 対象制度カタログ

子育て限定から全カテゴリへ拡大。全制度がPrologを通る。

### 国制度（national）

| # | ID | 名称 | subject | complexity | 主な条件 |
|---|---|---|---|---|---|
| 1 | jidou_teate | 児童手当 | child | medium | 18歳年度末以下、2024-10所得制限撤廃 |
| 2 | jidou_fuyou_teate | 児童扶養手当 | child | complex | ひとり親、所得制限（逓減式） |
| 3 | kouko_shugaku_shienkin | 高等学校等就学支援金 | child | medium | 高校在学、2026-04所得制限撤廃 |
| 4 | tokubetsu_jidou_fuyou_teate | 特別児童扶養手当 | child | complex | 障害児（1級/2級）、所得制限 |
| 5 | shogaiji_fukushi_teate | 障害児福祉手当 | child | medium | 20歳未満重度障害、常時介護 |
| 6 | tokubetsu_shogaisha_teate | 特別障害者手当 | claimant | complex | 20歳以上重度障害、所得制限 |
| 7 | shussan_ikuji_ichijikin | 出産育児一時金 | claimant | simple | 健康保険加入、出産 |
| 8 | shussan_kosodate_ouen | 出産・子育て応援交付金 | claimant | simple | 妊娠届出＋出生、自治体経由 |
| 9 | jukyo_kakuho_kyufukin | 住居確保給付金 | claimant | complex | 離職・収入減、所得・資産制限 |
| 10 | jiritsu_shien_iryo_seishin | 自立支援医療（精神通院） | claimant | medium | 精神疾患、継続通院 |
| 11 | jiritsu_shien_iryo_ikusei | 自立支援医療（育成医療） | child | medium | 18歳未満、身体障害 |
| 12 | nanbyo_iryo_josei | 難病医療費助成 | claimant | complex | 指定難病認定 |
| 13 | seikatsu_hogo | 生活保護 | claimant | complex | 資産・能力活用後、最低生活費以下 |
| 14 | koto_shokugyo_kunren | 高等職業訓練促進給付金 | claimant | complex | ひとり親、資格取得訓練 |
| 15 | jiritsu_shien_kyoiku_kunren | 自立支援教育訓練給付金 | claimant | medium | ひとり親、指定講座受講 |

### 都制度（tokyo — 全23区共通）

| # | ID | 名称 | subject | complexity | 主な条件 |
|---|---|---|---|---|---|
| 16 | tokyo_018_support | 018サポート | child | simple | 18歳以下、都内在住 |
| 17 | tokyo_jidou_ikusei_teate | 児童育成手当 | child | medium | ひとり親、所得制限 |
| 18 | hitorioya_iryo_josei | ひとり親家庭等医療費助成 | claimant | medium | ひとり親、所得制限 |
| 19 | tokyo_judo_shinshin_teate | 東京都重度心身障害者手当 | claimant | complex | 重度障害、都認定 |
| 20 | shinshin_shogaisha_iryo_josei | 心身障害者医療費助成 | claimant | medium | 障害者手帳保持、所得制限 |
| 21 | jukensei_challenge | 受験生チャレンジ支援貸付 | child | medium | 中3・高3、所得制限 |
| 22 | tokyo_akachan_first | 赤ちゃんファースト | child | simple | 都内出生 |
| 23 | shiritsu_koko_jugyoryo_keigen | 私立高校授業料軽減助成金 | child | complex | 私立高校在学、2026所得制限撤廃 |

### 区制度（municipal — 区ごとに異なる）

| # | ID例 | 名称 | subject | complexity | 備考 |
|---|---|---|---|---|---|
| 24-46 | {ward}_kodomo_iryouhi | 子ども医療費助成 | child | simple | 23区×各1（対象年齢が区により異なる） |
| 47 | shibuya_birthday_support | バースデーサポート事業 | child | simple | 渋谷区独自 |
| 48+ | {ward}_shinshin_shogaisha_teate | 心身障害者福祉手当 | claimant | medium | 区独自の障害者手当（金額・条件が区により異なる） |
| - | {ward}_shugaku_enjo | 就学援助 | child | medium | 区ごとに基準・金額が異なる |
| - | {ward}_tenkyo_josei | 転居費用助成 | claimant | medium | 一部区のみ |

**実装状況**: Phase 1で7制度がgolden検証済み（国3+都2+渋谷区2）+ 23区子ども医療費助成。Phase 2で残り制度を追加予定。

### Prologルールの複雑度別テンプレート

#### Simple（5-15行）: 年齢 + 居住地チェック

```prolog
:- module(shussan_ikuji_ichijikin, [kettei_status/3, required_fact/3]).

kettei_status(P, self, error(structural_facts_missing)) :-
    claimant(P), \+ age(P, _), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing), Missing \= [], !.
kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), no(ninshin(P)), !.
kettei_status(P, self, decided(amount(500000))) :-
    claimant(P), yes(ninshin(P)), yes(kenkou_hoken(P)), !.
kettei_status(P, self, ineligible(no_health_insurance)) :-
    claimant(P), no(kenkou_hoken(P)), !.
kettei_status(_, _, error(no_rule_matched)).

required_fact(P, ninshin, "pregnancy status") :- claimant(P), unknown(ninshin(P)).
required_fact(P, kenkou_hoken, "health insurance") :- claimant(P), unknown(kenkou_hoken(P)).
```

#### Medium（15-40行）: 所得制限あり

```prolog
:- module(tokyo_jidou_ikusei_teate, [kettei_status/3, required_fact/3]).

ikusei_limit(N, L) :- integer(N), N >= 0, L is 3604000 + 380000 * N.

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C), \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(age_over)) :-
    claimant(P), child(C), age_nendo_matsu(C, A), A >= 18, !.
kettei_status(P, C, ineligible(not_single_parent)) :-
    claimant(P), child(C), no(hitorioya(P)), !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), child(C),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing), Missing \= [], !.
kettei_status(P, C, ineligible(income_over)) :-
    claimant(P), child(C), yes(hitorioya(P)),
    val(fuyou_ninzu(P), N), ikusei_limit(N, L),
    val(income(P), Inc), v_geq(Inc, L), !.
kettei_status(P, C, decided(amount(13500))) :-
    claimant(P), child(C), yes(hitorioya(P)), !.
kettei_status(_, _, error(no_rule_matched)).

required_fact(P, hitorioya, "single parent") :- claimant(P), unknown(hitorioya(P)).
required_fact(P, income, "income") :- claimant(P), unknown(income(P)).
required_fact(P, fuyou_ninzu, "dependents") :- claimant(P), unknown(fuyou_ninzu(P)).
```

#### Complex（40-100行）: 逓減計算、多条件

児童扶養手当（jidou_fuyou_teate.pl）が代表例。実装済み。

### 制度追加の手順（厳守）

1. `docs/statute_source.md` に出典を固定
2. `tests/cases/` にgoldenケースを作成（8件目安）
3. `rules/` にPrologルールを実装
4. `pytest` 緑を確認
5. `data/programs.yaml` の status を `supported` に昇格
6. commit

**品質ゲート**: golden未検証の制度を `supported` にしない。制度数を盛るために信頼を売らない。

## フロントエンド設計（チャットUI）【実装予定】

### 画面構成

```
┌─────────────────────────────────────────────┐
│  制度攻略エージェント              [区: 渋谷区 ▼] │
├─────────────────────────────────────────────┤
│                                             │
│  [agent] はじめまして！お住まいの区と、        │
│  ご家族の状況を教えてください。                │
│                                             │
│  [user] 渋谷区に住んでいて、3歳の子供が       │
│  います。去年離婚してひとり親です。            │
│                                             │
│  [agent] ありがとうございます。現時点で        │
│  以下の制度に該当する可能性があります：         │
│                                             │
│  ┌─ 判定結果カード ──────────────────┐       │
│  │ 月額 57,500円 + 一時金 10万円      │       │
│  │                                   │       │
│  │ ✅ 児童手当        月10,000円      │       │
│  │ ✅ 018サポート      月5,000円      │       │
│  │ ✅ 児童扶養手当    月42,500円      │       │
│  │ ✅ バースデーサポート 100,000円     │       │
│  │ ❓ 児童育成手当    あと1問で確定    │       │
│  │ ✅ 子ども医療費助成  自己負担なし   │       │
│  └───────────────────────────────────┘       │
│                                             │
│  あといくつか確認させてください。               │
│  税法上の扶養親族は何人ですか？                 │
│                                             │
│  [0人] [1人] [2人] [3人] [4人] [5人以上]      │
│                                             │
├─────────────────────────────────────────────┤
│ 法的助言ではありません。最終確認は窓口へ         │
├─────────────────────────────────────────────┤
│ [メッセージを入力...]            [送信]       │
└─────────────────────────────────────────────┘
```

### UIの設計原則

1. **チャットが主、カードが従**: 対話の流れの中に判定結果カードが挿入される
2. **選択肢チップ**: blocked制度の追加質問は選択肢チップとして提示（タップで即回答）
3. **カードはリアルタイム更新**: 新しい事実が追加されるたびに判定結果カードが更新される
4. **免責表示は常時固定**: 画面下部に常に表示
5. **区セレクタ**: ヘッダーに常設。変更時に全制度再判定

### 選択肢チップの処理

チャットUIでも選択肢チップは /api/judge 経由で処理可能（LLM不使用、0円）:

1. Geminiが「扶養親族は何人ですか？」と質問 + 選択肢チップを提示
2. ユーザーがチップをタップ → facts に直接書き込み → /api/judge
3. 判定結果を受けてカード更新 + 次の質問チップを表示

自由文入力の場合のみ /api/chat（Gemini）を使用。

### 技術構成

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
COPY rules/ rules/
COPY data/ data/
COPY web/ web/
COPY src/ src/
ENV PYTHONPATH=/app/src
EXPOSE 8080
CMD ["uvicorn", "seido.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

| 設定 | 値 |
|---|---|
| region | asia-northeast1 |
| min-instances | 0（**審査期間中のみ1**に上げる。約1,500円/月、クレジット内） |
| max-instances | 2（コスト上限を物理的に確保） |
| concurrency / timeout | 8 / 60s（judge毎にswiplサブプロセスを起動するため、高concurrencyは1vCPU上でCPU競合する） |
| 環境変数 | `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, モデルID（`MODEL_CHAT` / `MODEL_EXTRACT` / `MODEL_FORMALIZE` / `MODEL_EVAL`） |
| 認証 | `--allow-unauthenticated`（公開デモ） |
| CORS | **設定しない**（フロントは同一オリジン配信。docsの例の `allow_origins=["*"]` はコピーしない） |
| 監視 | Cloud Trace（OTel）+ Billing予算アラート。**ログにfactsを出力しない** |

## コスト防御・入力ガード（多層）

| 層 | 内容 |
|---|---|
| 課金 | Billing予算アラート（日次500円目安）+ 超過通知での手動停止（Pub/Sub自動停止はストレッチ） |
| スケール | `max-instances=2` で物理上限 |
| クォータ | Vertex AI側のプロジェクトクォータを絞る（RPM/日次） |
| レート制限 | slowapi（IPベース・moving window）【実装済み】: /api/chat 毎分5回、/api/judge 毎分**40回**（チップ1回答=judge1回のため。20回では正規操作・デモ中に429が出る）、/api/proof 毎分20回。RateLimitExceededハンドラ登録済み（429はJSONで返る）。key_funcは `X-Forwarded-For` **末尾**エントリ、ヘッダ無し時は `get_remote_address` にフォールバック（app.py `_client_ip`）。Cloud RunのフロントエンドはクライアントIPを末尾に**追記**するため、先頭を使うと偽ヘッダでバケットを回転させレート制限を回避できる（先頭案は却下）。ローカル/本番で単一コードパス、デプロイ時の差し替え不要。テストでは conftest.py で `limiter.enabled = False`。**インメモリ実装のためインスタンスごとに独立**（max=2なので実効上限は2倍。デモ規模では許容と明記） |
| 入力サイズ | `message` ≤ 500字 / facts JSON ≤ 10KB（リクエスト全体のJSON化サイズで検証、`MAX_FACTS_BYTES`）/ `history` ≤ 8往復・5KB をサーバー側で検証（413）。超過分の履歴は古い側から切り捨て。**注**: 生成されるPrologソースはJSON比で数倍に膨張しうるが、10KB制限下の実用データ量ではProlog側の肥大は問題にならない |
| 対話上限 | /api/chat はフロントで15ターン上限（UX用）。選択肢タップは /api/judge のみでLLM不使用のため制限不要。**ステートレス故にサーバーはターン数を強制できない**ため、コスト防御の実効線は上記レート制限+クォータであることを明記 |

## CI/CD（docs/dev-methodology.md の段階パイプラインを具体化）

| トリガ | 内容 | LLM |
|---|---|---|
| PR | pytest（goldenテスト: swipl決定的実行）+ lint | 不使用 |
| main merge | adk eval（Flash-Lite）→ Docker build → `gcloud run deploy` → `ops/deploy.json` をGCSへ | 少量 |
| nightly / 手動 | 条文ソース再取得 → 形式化エージェント再実行 → golden照合 → diffあればPR起票 + **`ops/verify.json` を更新** | 使用 |

## スコープ拡大戦略（網羅性こそが売りであることへの設計上の備え）

「10制度しか判定できない」で終わらないために、ルールベースを**スケールする構造**で作る。
v2.0で対象制度カタログ（上記）に具体的30+制度リストを規定。

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
| 1（Week 1-3） | コア7制度をgolden付きで検証済みに + 23区子ども医療費助成 | 深さの証明。判定品質の土台 |
| 2（Week 4、ストレッチ） | **国制度を中心に30+制度へ拡大**（v2.0で規定、architecture.md § 対象制度カタログ）。形式化エージェントの生産性（1制度あたりの追加時間の推移）を `/ops` に記録 | 広さの証明。「ルール追加の限界費用が下がる」というプロダクトの中心主張のデータ化 |
| 3（デモ） | **第2自治体の追加をパイプラインで実演**（municipal差分の形式化→golden→deploy） | 「まわす」の最強デモ。手作業のOpenFisca-Japanとの決定的な差別化 |

**品質ゲート（譲らない線）**: ユーザーに見せる判定は **golden検証済み制度のみ**。自動形式化しただけの制度は
`status: unsupported`（⬜カード）に留め、検証通過後に昇格させる。制度数を盛るために信頼を売らない。
網羅性の主張は「対応制度の**中で**は全解探索で取りこぼさない」+「対応制度を増やす限界費用が構造的に低い」の2段で語る。

## セキュリティ・プライバシー

### 不変の制約

- **ユーザー入力がPrologコードに到達する経路を作らない**: factgen.py が唯一のゲートウェイ。known/2 事実の生成はPython側のテンプレートのみ。値は型検証済みの数値/真偽/列挙に限る
- **ログにfacts/自由文を出力しない**: Cloud Loggingにはステータスコードとレイテンシのみ。プライバシー設計の根幹。コードレビューで `req.facts` や `facts_pl` のログ出力を検出した場合は即修正する（自動lint未導入、レビュー規約で担保）
- **「確実にもらえます」と断定しない**: Prolog判定＋条文根拠の範囲のみ
- **golden未検証の制度をsupportedにしない**: 制度数を盛るために信頼を売らない
- **goldenケースに実在人物の情報を入れない**: 全世帯架空
- **免責表示を常時固定**:「法的助言ではない」「最終判断は自治体窓口」

### Gemini固有のセキュリティ【/api/chat実装時に適用】

- **Structured Outputで事実抽出を制約**: 自由形式の出力を防止。Geminiが出力するのはJSONスキーマに沿った値のみ
- **抽出結果はPydanticスキーマで検証後にマージ**: 型・列挙値・レンジの妥当性
- **プロンプトインジェクション対策**: ユーザー入力はシステムプロンプトと分離（user role）
- **既知の値との矛盾は自動適用しない**: `proposed_corrections` でユーザー確認
- **confidence: low は自動適用しない**: 確認質問を生成

## 実装ロードマップ（ハッカソン締切: 2026-07-10）

### Phase 1: 基盤整備（~6/20）
- [ ] 未コミットのセキュリティ修正をコミット
- [ ] factgen.py にv2 askableキーを追加
- [ ] 申請者自身の `age(p1, Age)` 生成を追加
- [ ] チャットUI（HTML/CSS/JS）の基本実装
- [ ] /api/chat エンドポイント実装（Gemini連携）

### Phase 2: 制度拡大（~6/27）
- [ ] 国制度のPrologルール追加（simple/medium優先で10制度追加）
- [ ] 都制度のPrologルール追加（5制度追加）
- [ ] goldenケース作成・検証
- [ ] programs.yaml 更新

### Phase 3: 統合・品質（~7/4）
- [ ] 対話フロー全体のE2Eテスト
- [ ] 証明木の日本語説明（Gemini）
- [ ] 判定結果カードのUI洗練
- [ ] エッジケースのgolden追加

### Phase 4: デプロイ・提出（~7/10）
- [ ] Cloud Runデプロイ
- [ ] GitHub公開リポジトリ整備
- [ ] ProtoPediaページ作成
- [ ] 3分デモ動画撮影

## 未決事項

- プロダクト名（候補: モラエル / 制度ナビ / Todoke）
- MCPエンドポイント公開（案Gの+1日要素）: `/mcp` ルートに推論コアを露出。**Week 3の進捗を見てストレッチとして判断**
- 区独自制度の網羅度（23区×各制度のリサーチ工数）
- Geminiのモデルバージョン固定（Flash 2.0 vs 2.5）
