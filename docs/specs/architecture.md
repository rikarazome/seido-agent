# アーキテクチャ設計書（v1）

2026-06-11 確定。プロダクト形態の決定（Webアプリ + 同一コンテナでのサービス統合）に基づく技術設計。

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
   │                    │   └─ /ops         … CIが生成した静的JSON       │
   │                    │                                              │
   │                    │  ADK Runner（ヒアリングエージェント）            │──▶ Vertex AI
   │                    │   └─ tools: run_judgment, extract_facts      │    (Gemini)
   │                    │                                              │
   │                    │  推論エンジン層（Python）                       │
   │                    │   ├─ facts JSON → .plファクト変換（決定的）     │
   │                    │   ├─ swipl サブプロセス実行                    │
   │                    │   └─ rules/*.pl + engine.pl（イメージに同梱）   │
                        └──────────────────────────────────────────────┘
        ビルド時（CI, GitHub Actions）:
        条文 → 形式化エージェント(Gemini) → rules/*.pl → goldenテスト → イメージ焼き込み → deploy
```

## LLM使用ポイント（コスト構造の根拠）

| 処理 | 実行タイミング | 担当 | コスト |
|---|---|---|---|
| 法令の形式化（条文→Prologルール） | **ビルド時のみ** | Gemini | ユーザー数と無関係に償却 |
| フォーム入力→全制度一次判定 | ランタイム | **Prologのみ** | **0円**（トークン不使用） |
| 自由文回答→事実抽出 | ランタイム | Gemini（Structured Output） | 小 |
| 次の質問の文面化 | ランタイム | blocked のmissing facts（Prolog）+ Gemini | 小 |
| 証明木の日本語説明 | ランタイム | Gemini | 小 |

試算: 約2〜3円/セッション（Flash）。一次判定だけで離脱するユーザーは **0円**。

## API設計

### POST /api/judge（一次判定、LLM不使用）

```jsonc
// Request: クライアントが保持する世帯事実の全量
{
  "facts": {
    "claimant": { "birth_date": "1988-04-01", "income": 4200000, "hitorioya": null },
    "children": [ { "birth_date": "2019-06-01" }, { "birth_date": "2023-02-15" } ],
    "fuyou_ninzu": 2
  }
}
// Response: 全制度の判定結果（4状態）
{
  "total_monthly_yen": 25000,          // decided合計（見出し用）
  "results": [
    { "program": "jidou_teate", "name": "児童手当",
      "status": "decided", "amount_monthly": 25000,
      "proof": { /* 証明木。条文参照ノード付き */ } },
    { "program": "jidou_fuyou_teate", "name": "児童扶養手当",
      "status": "blocked", "missing": ["hitorioya_jiyuu"],
      "missing_label": "あと1問で確定します" },
    { "program": "...", "status": "ineligible", "reason": "...", "statute_ref": "..." },
    { "program": "...", "status": "unsupported" }   // 未対応制度（正直に表示）
  ]
}
```

- `facts` → `.pl` ファクト変換は **Python側の決定的マッピング**（誕生日→年齢・年度末年齢の計算を含む）。LLMを通さない
- 全制度に対して `kettei_status/3` を全解探索。1リクエストで10制度ぶん返す

### POST /api/chat（対話1ターン、ステートレスラッパー）

```jsonc
// Request
{ "facts": { /* 現在の全量 */ }, "message": "離婚して子どもと二人暮らしです" }
// Response
{ "facts": { /* 更新後の全量。クライアントが次回これを送る */ },
  "reply": "ありがとうございます。では…",
  "next_question": "前年の所得（源泉徴収票の額）を教えてください",
  "judgment": { /* /api/judge と同形式の再判定結果 */ } }
```

- サーバー内部では **リクエストごとにADKセッションを生成**（`create_session(state=facts)`）→ 1ターン実行 → セッション破棄。ADKの `/run` REST APIは直接公開せず、このラッパーで包む
- これによりインスタンスが消えても会話は壊れない（サーバーは何も覚えていない）
- ヒアリングエージェントのツール: `extract_facts`（自由文→事実、Structured Output）、`run_judgment`（Prolog再判定）
- ガード: 1セッションの対話は最大10往復でフロント側が打ち切り

### GET /ops（「まわす」の見せ場）

ランタイム集計はしない。**CIが生成した静的JSON**（制度別golden合格率・最終検証日時・ルール更新履歴・直近の条文diff）をそのまま配信。コスト0円で常時公開できる。

## 推論エンジン層

- `engine.pl`: 証明木メタインタプリタ（prolog-reasonerの実装を移植）+ `kettei_status/3` の共通ドライバ
- `rules/<program>.pl`: 制度ごとのルール（docs/specs/rule-schema.md 準拠。ローマ字述語・`:- discontiguous`・理由付き除外）
- 実行: `swipl -q -g main rules/... facts.pl` をサブプロセスで起動、JSON出力を受ける。タイムアウト5秒
- ルールはコンテナイメージに焼き込む = **ルール更新はデプロイで行う**。これが二重ループ（法改正→再形式化→golden→再デプロイ）と一致し、`/ops` の更新履歴とも連動する

## フロントエンド画面フロー

```
[1] トップ: 30秒フォーム（家族構成・生年月・所得レンジ・住まい）
     │ POST /api/judge
[2] 結果一覧: 「💰 月25,000円相当 見つかりました」
     ├─ ✅ 該当カード: 金額 + 「なぜ？」→ 証明木を条文リンク付きで展開
     ├─ ❓ あとN問カード: タップで対話パネルへ（POST /api/chat ループ）
     ├─ ❌ 非該当カード: 理由 + 根拠条文
     └─ ⬜ 未対応カード: 対象外制度の正直な表示
[3] 常時表示: 「法的助言ではありません」「入力情報は保存されません」公式窓口リンク
```

- 素のHTML/CSS/JS、1ページ構成。facts はJSの変数（メモリ上）にのみ存在し、リロードで消える
- 証明木はネストされた折りたたみリストで表現（木構造ライブラリ不要）

## コンテナとデプロイ

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends swi-prolog \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt . && RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

| 設定 | 値 |
|---|---|
| region | asia-northeast1 |
| min-instances | 0（**審査期間中のみ1**に上げる。約1,500円/月、クレジット内） |
| max-instances | 2（コスト上限を物理的に確保） |
| concurrency / timeout | 20 / 60s |
| 環境変数 | `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` |
| 認証 | `--allow-unauthenticated`（公開デモ） |
| 監視 | Cloud Trace（OTel）+ Billing予算アラート |

## コスト防御（多層）

1. Billing予算アラート（日次500円目安）+ 超過通知での手動停止（Pub/Sub自動停止はストレッチ）
2. `max-instances=2` でスケール上限
3. Vertex AI側のプロジェクトクォータを絞る（RPM/日次）
4. アプリ層レート制限: IPあたり毎分N回（FastAPIミドルウェア。Cloud Armorは使わない＝固定費回避）
5. 対話は1セッション最大10往復

## CI/CD（docs/dev-methodology.md の段階パイプラインを具体化）

| トリガ | 内容 | LLM |
|---|---|---|
| PR | pytest（goldenテスト: swipl決定的実行）+ lint | 不使用 |
| main merge | adk eval（Flash-Lite）→ Docker build → `gcloud run deploy` → `/ops` JSON生成 | 少量 |
| nightly / 手動 | 条文ソース再取得 → 形式化エージェント再実行 → golden照合 → diffあればPR起票 | 使用 |

## セキュリティ・プライバシー

- 個人情報の保存なし（ログにfactsを出力しない。Cloud Loggingにはステータスコードとレイテンシのみ）
- プロンプトインジェクション面: 自由文入力はStructured Outputで事実抽出に限定し、抽出結果はスキーマ検証してからPrologへ。**ユーザー入力が直接Prologコードに混ざる経路を作らない**（ファクト生成はPython側のテンプレートのみ）
- 免責表示を常時固定（「法的助言ではない」「最終判断は自治体窓口」）

## 未決事項

- プロダクト名（候補: モラエル / うけとりナビ / Todoke / 証明つき給付金チェッカー）
- MCPエンドポイント公開（案Gの+1日要素）: `/mcp` ルートに推論コアを露出する。**Week 3の進捗を見てストレッチとして判断**
- 所得制限の公式数値検証（rule-schema.md 既知の課題。golden case作成と同時に実施）
