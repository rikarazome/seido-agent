# アーキテクチャ設計書（v1.1）

2026-06-11 確定、同日レビュー指摘14件を反映して改訂。プロダクト形態の決定（Webアプリ + 同一コンテナでのサービス統合）に基づく技術設計。

## 決定事項サマリ

| 項目 | 決定 | 理由 |
|---|---|---|
| 形態 | ログイン不要のモバイル対応Webアプリ | とどける力・デモ体験が最強。審査員もProtoPedia訪問者もURLタップで完結 |
| 入力方式 | 構造化フォーム → 一次判定 → 不足分のみ対話 | 純チャットより速く、トークン消費が1桁少ない。質問の必然性が見える |
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
| フォーム入力→全制度一次判定 | ランタイム | **Prologのみ** | —（**0円**、トークン不使用） |
| 自由文回答→事実抽出 / 質問文面化 / 証明木の日本語説明 | ランタイム | Gemini | Flash系 |
| adk eval（CI） | mainマージ時 | Gemini | Flash-Lite系 |

試算: 約2〜3円/セッション（Flash）。一次判定だけで離脱するユーザーは **0円**。

## facts JSONスキーマ（rule-schema.md v1 と1:1対応）

```jsonc
{
  "facts": {
    "claimant": { "birth_date": "1988-04-01" },
    "children": [ { "id": "c1", "birth_date": "2019-06-01" } ],
    "askable": {
      // 値の型: 数値（点値） | [lo, hi]（レンジ） | true/false | 列挙文字列 | null（未知）
      "nenshu": [3000000, 5000000],      // 年収（額面）。フォームはレンジ選択
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
- `nenshu` →給与所得控除等の決定的計算で**各制度の所得定義**に変換し `known(income(P), ...)` 等を生成。レンジは `range(Lo,Hi)` のまま伝播（区間評価はProlog側）
- `null` / 欠落キーは **known事実を生成しない**（= Prolog側で unknown）

## API設計

### POST /api/judge（一次判定、LLM不使用）

```jsonc
// Request: { "facts": {…上記…}, "as_of": "..." }
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
      "status": "decided",
      "amount": { "type": "monthly", "yen": 25000 },
      "proof": { /* 証明木 */ },
      "statute": [ { "ref": "児童手当法…", "url": "…" } ] },
    { "program": "jidou_fuyou_teate", "name": "児童扶養手当",
      "status": "blocked", "missing": ["hitorioya_jiyuu"],
      "missing_label": "あと1問で確定します" },
    { "program": "...", "status": "ineligible", "reason": "...", "statute": [ … ] },
    { "program": "...", "status": "unsupported" }   // data/programs.yaml の status から生成
  ]
}
```

- 見出しは「💰 月25,000円 ＋ 一時金10万円」のように**種別を分けて表示**。月額・一時金・年額・現物を雑に足さない
- 制度名・条文リンク・amount_type は `data/programs.yaml` から付与（ルールは判定と区分のみ返す）
- 全制度module（10個）に対して `Prog:kettei_status/3` を全解照会。1リクエストで全制度ぶん返す

### POST /api/chat（対話1ターン、ステートレスラッパー）

```jsonc
// Request
{ "facts": { /* 現在の全量 */ }, "message": "離婚して子どもと二人暮らしです" }
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

**ADKセッションの扱い**:
- `get_fast_api_app(session_service_uri=None)` → **InMemorySessionService を明示**（docsの例にあるsqlite URIは使わない。「DBなし」と矛盾しコンテナ内にファイルが残るため）
- リクエストごとに `create_session(state=facts)` → 1ターン実行 → **`delete_session`**（ウォームインスタンスのメモリ増加防止）。ADKの `/run` REST は直接公開しない
- インスタンスが消えても会話は壊れない（サーバーは何も覚えていない）

### GET /ops（「まわす」の見せ場）

- ops.json（制度別golden合格率・最終検証日時・ルール更新履歴・直近の条文diff）は **GCS公開バケット**に置き、フロントが直接フェッチ（Cache-Control: 300s）
- 書き込みは2経路: **mainマージ時のデプロイCI** と **nightlyの条文検証ワークフロー**。これによりデプロイなしでも「最終検証: 昨日」が出せる（デプロイ時焼き込み方式だとnightly結果が反映されない）
- ランタイム集計なし。コスト≒0円（GCS数KB）

## 推論エンジン層

- `rules/engine.pl`: 3値ヘルパー（`yes/no/unknown/val/v_lt/v_geq/v_indet`）+ 証明木メタインタプリタ（prolog-reasonerから移植）。非module、`user` にロード
- `rules/<program>.pl`: 1制度=1module（`:- module(prog_id, [kettei_status/3, required_fact/3]).`）。rule-schema.md v1 準拠
- 実行: engine.pl → facts.pl（生成）→ rules/*.pl をロードし、制度ごとに `Prog:kettei_status/3` を照会。サブプロセス、タイムアウト5秒
- **多ファイル+module構成はWeek 2統合テストの最初の項目**。不調時のフォールバック: 制度ごとに別swiplプロセス（起動50ms×10、+0.5秒で許容範囲）
- ルールはイメージ焼き込み = ルール更新はデプロイ。二重ループ（法改正→再形式化→golden→再デプロイ）と一致し、`/ops` の更新履歴と連動

## フロントエンド画面フロー

```
[1] トップ: 30秒フォーム（家族構成・生年月・年収レンジ・住まい）
     │ POST /api/judge
[2] 結果一覧: 「💰 月25,000円 + 一時金10万円 見つかりました」
     ├─ ✅ 該当カード: 金額（種別表示）+ 「なぜ？」→ 証明木を条文リンク付きで展開
     ├─ ❓ あとN問カード: タップで対話パネルへ（POST /api/chat ループ）
     ├─ ❌ 非該当カード: 理由 + 根拠条文
     └─ ⬜ 未対応カード: programs.yaml の unsupported 制度を正直に表示
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
| concurrency / timeout | 20 / 60s |
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
| 入力サイズ | `message` ≤ 500字 / facts JSON ≤ 10KB をサーバー側で検証（413） |
| 対話上限 | フロントは10往復で打ち切り（UX用）。**ステートレス故にサーバーはターン数を強制できない**ため、コスト防御の実効線は上記レート制限+クォータであることを明記 |

## CI/CD（docs/dev-methodology.md の段階パイプラインを具体化）

| トリガ | 内容 | LLM |
|---|---|---|
| PR | pytest（goldenテスト: swipl決定的実行）+ lint | 不使用 |
| main merge | adk eval（Flash-Lite）→ Docker build → `gcloud run deploy` → ops.json をGCSへ | 少量 |
| nightly / 手動 | 条文ソース再取得 → 形式化エージェント再実行 → golden照合 → diffあればPR起票 + **ops.json の検証日時を更新** | 使用 |

## セキュリティ・プライバシー

- 個人情報の保存なし（Cloud Loggingにはステータスコードとレイテンシのみ。factsと自由文は記録しない）
- プロンプトインジェクション面: 自由文入力はStructured Outputで事実抽出に限定し、Pydanticスキーマ検証後にマージ。**ユーザー入力が直接Prologコードに混ざる経路を作らない**（known/2 事実の生成はPython側のテンプレートのみ。値は型検証済みの数値/真偽/列挙に限る）
- 免責表示を常時固定（「法的助言ではない」「最終判断は自治体窓口」）

## 未決事項

- プロダクト名（候補: モラエル / うけとりナビ / Todoke / 証明つき給付金チェッカー）
- MCPエンドポイント公開（案Gの+1日要素）: `/mcp` ルートに推論コアを露出。**Week 3の進捗を見てストレッチとして判断**
- 所得制限の公式数値・年収→所得変換式の検証（golden case作成と同時、statute_source.mdに出典固定）
- module + 多ファイルロードの実機確認（Week 2統合テスト先頭。フォールバック: 制度別プロセス）
