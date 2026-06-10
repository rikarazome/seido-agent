# 開発手法: 二重ループのDevOps設計

調査（2026-06-10、仕様駆動開発＋評価駆動/ハーネス）に基づく本プロジェクトの開発手法。
ハッカソンでは「エージェント開発のループの質」自体が審査対象（つくる・まわす・とどける）。

## 中核コンセプト: 二重ループ

このプロジェクトはDevOpsループが**2つ**あり、外側のループがそのまま製品価値になる。

```
[内側] ソフトウェア開発ループ（普通のDevOps）
  spec → test → implement → eval → CI → Cloud Run deploy → trace → 改善

[外側] ルールベース運用ループ（この製品固有のDevOps）
  条文取得 → LLM形式化 → 検証(golden cases) → ルールベースdeploy
  → 法改正検知 → diff → 再検証 → 再deploy
```

**審査での主張**: 「制度ルールをコードとして扱い、CI/CDで品質保証する。法改正対応=回帰テスト。これがRules as CodeのDevOps」。普通のチームは内側しか語れない。うちは外側が本体。

---

## 1. 仕様管理（軽量・Spec Kit不採用）

調査結論: GitHub Spec Kitはソロ＋マルチモジュール構成でオーバーヘッド過剰（「マークダウンの海」という実務評、ThoughtWorks RadarもAssess止まり）。AWS Kiroはロックイン。

採用: **CLAUDE.md（インデックス型）+ 最小限の仕様md**

```
seido-agent/
├── CLAUDE.md            # 規約・参照インデックス（短く保つ）
├── docs/
│   ├── specs/
│   │   ├── architecture.md      # エージェント構成・データフロー
│   │   ├── rule-schema.md       # Prologルールの述語設計（最重要仕様）
│   │   └── api.md               # エンドポイント仕様
│   ├── roadmap.md
│   └── ...
```

運用ルール:
- 仕様を書くのは**4時間超のタスクのみ**。それ未満はIssue/コミットメッセージで足りる
- 最重要仕様は `rule-schema.md`（述語の語彙・世帯モデル・証明木形式）。ここが全エージェントの契約になる
- 仕様と実装の乖離はテストで機械検出する（下記）。手動レビューに頼らない

## 2. 評価駆動開発（eval-first）

原則: **「eval = dataset + grader + harness。graderとharnessはコードより先に作る」**（RedHat 2026）

### 本プロジェクトの強み: graderが決定的に書ける

普通のLLMアプリはLLM-as-judge頼みになるが（長さ/形式/位置バイアス等の落とし穴多数）、うちは中核がPrologなので**決定的検証**ができる:

| 対象 | 評価方法 | LLM-judge要否 |
|---|---|---|
| 形式化エージェント | golden cases: 世帯プロファイル→該当/非該当の期待値をSWI-Prologで実行し完全一致 | 不要（決定的） |
| 推論エンジン | 制度ごとの単体テスト（境界値: 所得制限ちょうど等） | 不要 |
| 証明木 | 期待される根拠述語の集合と一致 | 不要 |
| ヒアリングエージェント | tool_trajectory + 「未束縛変数に対応する質問をしたか」 | ADK AgentEvaluator |
| 回答文生成 | rubricベース（誇張禁止・免責表示等） | 最小限のLLM-judge |

### ゴールデンケースの設計（Week 1で先に作る）

```
tests/golden/
├── jidou_teate/           # 制度ごとにディレクトリ
│   ├── cases.yaml         # 世帯プロファイル → 期待判定・期待根拠
│   └── statute_source.md  # 形式化の元になった条文（出典固定）
└── ...
```

- **cases.yaml の形式は v1 facts JSON と同形に固定**（書式が割れると~80ケースの手戻りになるため、ケース作成前に確定。docs/specs/architecture.md のfactsスキーマ参照）:

```yaml
- name: tashi_3rd_child_30000
  as_of: "2026-06-11"            # 必須固定（JST基準日。省略不可）
  facts: { claimant: {...}, children: [...], askable: {...} }  # /api/judge入力と同形
  expect:
    subject: c3                  # 子ID または self（claimant制度）
    status: decided              # decided | blocked | ineligible | error
    detail: amount(30000)        # kubun / 金額 / missingリスト / 理由
    proof_includes: [child_rank] # 証明木に含まれるべき述語（任意）
```

- 制度1つにつき該当3例・非該当3例・境界2例を目安（計~80ケース/10制度）。**境界には
  レンジ跨ぎ（v_indet → income_exact）と網羅漏れ検出（expect: error）を含める**こと
- 全goldenケースで**直接照会とメタ解釈再導出の結果一致**も検証（証明木2段階方式の回帰検知。rule-schema.md）
- **OpenFisca-Japanの実装を期待値の参照に使う**（児童手当等の既実装制度。ライセンス確認のこと）
- 形式化エージェントの回帰テスト: 同じ条文を再形式化→golden cases全パスを確認

## 3. テスト戦略（TDD + 失敗モード対策）

- Anthropic推奨どおりTDD（テスト先行→失敗確認→実装）。CLAUDE.mdに明記:
  - **既存テストを書き換えて通すことを禁止**（Claudeの既知の失敗モード）
  - テスト変更には理由の明記を要求
- 層: ①Prolog単体（決定的） ②形式化回帰（golden cases） ③エージェント統合（`adk eval`） ④E2E（デプロイ後スモーク）

## 4. CI/CD（GitHub Actions、最小構成）

調査結論: 「PRごとのevalは安い・速い・統計的有意のうち2つしか選べない」→ 段階分け。

```yaml
PR時（数分・無料/激安）:
  - pytest（Prolog単体 + golden cases）← LLM呼び出しゼロで決定的
  - 不変条件チェック: 全制度の限度額 < 番兵上限999999999（上限なしレンジ規約の安全条件）、
    全自治体ルールの同時ロード（module名衝突の検出）、直接照会×メタ解釈の一致
  - lint / typecheck
  - 形式化の回帰はキャッシュ済みルールで検証（LLM再生成しない）

mainマージ時:
  - adk eval（評価セット、Gemini Flash-Liteで実行）
  - gcloud run deploy --source .（カスタムDockerfile必須 — adk deploy cloud_runの自動生成イメージにはswi-prologが入らないため使えない。docs/specs/architecture.md参照）
  - デプロイ後スモークテスト

夜間（または手動）:
  - 形式化エージェントのフル再実行（条文→ルール再生成→golden全パス）
  - = 「法改正が来ても回る」ことの定常的証明
```

PRに評価結果を自動コメント（スコアのbefore/after）→ コミット履歴自体が審査資料になる。

## 5. オブザーバビリティ

- ADK 1.17+の `--otel_to_cloud` でCloud Traceにネイティブエクスポート（OTel GenAI semantic conventions準拠）
- マルチエージェントのトポロジービューで「ヒアリング→推論→形式化」のフローを可視化 → そのままアーキテクチャ説明のデモ素材になる
- カスタム属性: 推論時間、未束縛変数数、形式化の検証パス率

## 6. ツール選定（過剰回避）

| 採用 | 理由 |
|---|---|
| ADK AgentEvaluator + pytest | 公式・無料・Gemini統合 |
| GitHub Actions | 無料枠で足りる |
| `gcloud run deploy`（カスタムDockerfile） | swipl同梱が必要なためadk deployは不可。Terraformは過剰 |
| Cloud Trace (`--otel_to_cloud`) | ADK統合済み・無料枠内 |

| 不採用 | 理由 |
|---|---|
| GitHub Spec Kit / Kiro | ソロ5週間にオーバーヘッド過剰 |
| LangSmith | LangChain不使用 |
| Braintrust / promptfoo | 最終週に余裕があれば検討。必須でない |
| 評価データ100例超 | 20評価セット+80 goldenで十分 |

想定コスト: Gemini API $20-50（形式化・eval含む）+ Cloud Run $0-10（scale-to-zero、審査期間中のみmin=1）≒ **月$20-60**、クレジット$300内（詳細試算は docs/specs/architecture.md）

## 7. 審査へのアピール（とどける）

- README に評価セクション（ケース数・パス率・CIバッジ）
- PRごとの評価スコア推移 = 「評価駆動で開発した」一次証拠
- デモで見せる「まわす」: 条文を1行改正 → 夜間ジョブ相当を手動実行 → ルールdiff + 判定変化 + 全goldenパス、を数分で
- docs/EVALUATION.md に評価戦略を明文化（審査員向け）

## 週次への反映

- **Week 1 に追加**: golden cases設計（2-3制度ぶん）、pytest+CI骨格、CLAUDE.md作成 ← grader/harness先行の原則
- Week 2以降は roadmap.md のまま。各機能は「evalセット追加 → 実装 → パス」の順で進める
