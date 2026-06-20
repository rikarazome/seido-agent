# seido-agent 開発規約（インデックス型 — 短く保つ）

制度判定エージェント。DevOps×AI Agent Hackathon 2026（締切 7/10 23:59、ProtoPedia+GitHub+デプロイURL）。

## 仕様の正典（実装と食い違ったら仕様を直すか実装を直す。黙って乖離させない）

| ファイル | 内容 |
|---|---|
| docs/specs/rule-schema.md | **Prologルールの契約**（3値事実・module・呼び出し規約・catch-all・検証済みパターン表） |
| docs/specs/architecture.md | API・集約規則・一問一答エンジン・コスト防御・デプロイ |
| docs/dev-methodology.md | 二重ループ・eval-first・CI段階・golden書式 |
| docs/roadmap.md | 週次計画 |
| docs/target-programs.md | v1初期スコープ（参考。現在は248制度supported） |

## コマンド

- テスト: `python -m pytest -q`（swipl必須・決定的・LLMゼロ。**全コミットの前提条件**）
- ルールの意味論スパイク: prolog-reasoner MCP（`execute_prolog`）で検証 → golden化 → rules/へ

## 開発ループ（厳守）

1. **制度の追加・検証手順（1コミット1制度を厳守）**:
   1. 公式ページをPlaywright/fetchで読む（推測・テンプレート禁止）
   2. `python scripts/save_page_snapshot.py <program_id> <url>` でページ生テキストを保存（再現可能な証拠）
   3. statute_source.mdに条文テキストを引用して金額・条件・対象を記録
   4. cases.yamlのgolden期待値を**条文から**導出する（ルール出力からではない）
   5. ルールの全条件（年齢/所得/等級）を条文と1つずつ照合
   6. pytest GREEN → commit（コミットメッセージに「何を読んで何を確認したか」）
   - **絶対禁止**: バッチ生成、スクリプト一括、推測値、ルール出力をgoldenにコピー
   - 1セッションで大量にやろうとしない。焦りが品質を殺す
2. **既存テストを書き換えて通すことを禁止**。期待値の変更は条文出典の変更とセットでのみ可（コミットメッセージに理由必須）
3. ルールの意味論に触る変更は prolog-reasoner で先に検証し、rule-schema.md の検証済みパターン表を更新
4. プレースホルダ数値は `PLACEHOLDER - VERIFY` 併記必須。公式数値確定時は cases / rules / factgen を**同一コミット**で更新
5. コミットは main 直・小刻み（ソロ）。pytest 緑が条件。リスキーな実験はブランチへ

## Prolog規約（rule-schema.md の要約）

- 1制度=1module、id=module名=ファイル名。municipal制度は自治体プレフィックス必須（`shibuya_*`）
- 可問事実への素の `\+` 禁止（`no/1` を使う）。catch-all `kettei_status(_,_,error(no_rule_matched))` 必須
- 限度額・パラメータは式形式（表形式は定義域に穴 → N=3解なし事故の実例あり）
- 照会は両引数束縛 + `once/1`（未束縛照会はカットが他の解を刈る）
- 述語ローマ字・コメントASCII（一時ファイルのエンコーディング問題）

## してはいけないこと

- goldenケースに実在人物の情報を入れない（全世帯架空）
- 「確実に貰えます」「安全です」と言い切る文言をUI・プロンプト・docsに書かない（断定はProlog判定+条文根拠の範囲のみ。Fail Safe: 不明は不明と言う）
- golden未検証の制度を programs.yaml で supported にしない（制度数を盛るために信頼を売らない）
- ログに facts / 自由文入力を出力しない（プライバシー設計の根幹）
