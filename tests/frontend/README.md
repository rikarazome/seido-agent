# フロントエンド回帰ハーネス（node製・pytest対象外）

`web/index.html` の `<script>` を DOM スタブ + fetch モックで駆動する回帰テスト。
ブラウザ不要・LLM 不使用（fixtureは実 judge_request 出力から生成）。

## 実行手順

```bash
cd tests/frontend
python extract_js.py        # index.html から page_script.js を抽出（毎回）
node --check page_script.js # 構文チェック
node chat_flow_test.js      # チャット統合: オンボーディング + 成功/XSS/429/通信断/区切替/競合/503
node proof_render_test.js   # esc()/証明木レンダリングのエスケープ検査
node render_all_proofs.js   # 実APIから採取した25制度分の証明木を全レンダリング
```

すべて exit code 0 / `ALL PASS` が green の条件。

## fixture の再生成

- `chat_fixtures.json`: `python gen_chat_fixture.py`（swipl 必須、Gemini 不要）。
  判定部は実 judge_request 出力、応答文はダミー（XSS ペイロード含む）。
- `proof.json` / `proofs_all.json`: 実サーバの /api/proof から採取したもの。
  ルール変更で証明木の形が変わったら採り直す。

## 注意

- `page_script.js` は生成物（gitignore 済み）。コミットしない。
- ハーネスの DOM スタブは最小実装。新しい DOM API を index.html で使ったら
  スタブにも足すこと（無いと TypeError で落ちて気づける）。
