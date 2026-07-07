"""/api/chat engine: Gemini fact extraction + Prolog judgment + Gemini response.

Pipeline:
  1. Gemini extracts structured facts from user utterance
  2. Merge extracted facts into existing facts (null-only overwrite)
  3. factgen + Prolog judgment (reuses judge_request)
  4. Gemini generates natural language response

Design rules (architecture.md):
  - Gemini does NOT judge. It only extracts facts and generates responses.
  - Prolog does NOT dialogue. It only judges.
  - All judgment results come from Prolog. Gemini explains them.
  - No facts or user text are logged (privacy).
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from .runner import judge_request, questions, municipalities

# ---------------------------------------------------------------------------
# Gemini client (lazy init — works without API key until actually called)
# ---------------------------------------------------------------------------
_client = None
JST = timezone(timedelta(hours=9))


def _get_client():
    global _client
    if _client is None:
        try:
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY not set. "
                    "Set it as an environment variable to enable /api/chat."
                )
            _client = genai.Client(api_key=api_key)
        except ImportError:
            raise RuntimeError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )
    return _client


MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

# ---------------------------------------------------------------------------
# Build askable schema from questions.yaml (done once at import)
# ---------------------------------------------------------------------------
_ASKABLE_LINES = []
for _q in questions():
    _key = _q.get("askable_key", _q["fact"])
    _t = _q["type"]
    if _t == "boolean":
        _vd = "true / false"
    elif _t == "enum":
        _vd = " / ".join(f'"{k}"({v})' for k, v in _q.get("choices", {}).items())
    elif _t == "range_choice":
        _vd = "[下限, 上限] (整数ペア)"
    elif _t in ("integer", "integer_input"):
        _vd = "整数"
    else:
        _vd = "文字列"
    _ASKABLE_LINES.append(f"  {_key}: {_vd}  → {_q['text']}")

_ASKABLE_BLOCK = "\n".join(_ASKABLE_LINES)

_WARD_NAMES = {}
try:
    for _wid, _wdata in municipalities().items():
        _WARD_NAMES[_wdata["name"]] = _wid
except Exception:
    pass
_WARD_LIST = ", ".join(f"{v}={k}" for k, v in _WARD_NAMES.items()) or "shibuya=渋谷区"

# ---------------------------------------------------------------------------
# Step 1: Extraction system prompt
# ---------------------------------------------------------------------------
EXTRACTION_SYSTEM_PROMPT = f"""\
あなたは日本の社会保障制度の相談窓口で、ユーザーの発話から世帯情報を抽出するエンジンです。

## あなたの役割
- ユーザーが自然言語で述べた情報を、後段のProlog判定エンジンが使えるJSON形式に変換する。
- あなたは判定しない。判定はPrologが行う。あなたは情報の抽出のみ行う。

## 抽出ルール
1. ユーザーが**明確に述べた事実のみ**抽出する。推測・補完しない。
2. 述べていない項目はaskableに含めない。
3. 曖昧な場合は抽出しない。確信度が低い場合はconfidence: "low"にする。
4. 年収の扱い:
   - 「年収500万」→ nenshu: [5000000, 5000000]
   - 「年収400〜600万」→ nenshu: [4000000, 6000000]
   - 「年収500万くらい」→ nenshu: [4000000, 6000000]（幅を持たせる）
5. 子どもの年齢から生年月日を推定する場合:
   - 「5歳の子ども」→ 今日の日付から逆算して birth_date を推定（例: 今日が2026-07-01なら "2021-01-01"）
   - 正確な日付不明は年の1月1日とする（安全側）
6. 区名の変換: {_WARD_LIST}
7. booleanは必ず true/false で出力（"はい"/"いいえ" ではない）

## askableキー一覧
{_ASKABLE_BLOCK}

## 出力JSON形式（厳守）
{{
  "claimant_birth_date": "YYYY-MM-DD" or null,
  "children": [{{"birth_date": "YYYY-MM-DD"}}, ...] or null,
  "municipality": "ward_id" or null,
  "askable": {{
    "key1": value1,
    "key2": value2
  }},
  "confidence": "high" / "medium" / "low",
  "clarification_needed": "確認事項（日本語）" or null
}}

askableには抽出できたキーのみ含める。抽出できなかったキーは含めない。
"""

# ---------------------------------------------------------------------------
# Step 4: Response system prompt
# ---------------------------------------------------------------------------
RESPONSE_SYSTEM_PROMPT = """\
あなたは日本の社会保障制度の相談エージェントです。
Prolog推論エンジンの判定結果をもとに、ユーザーにわかりやすく回答します。

## あなたの役割
- Prolog判定エンジンの結果を**そのまま**自然言語で伝える。
- あなた自身は制度の該当/非該当を判断しない。Prologの結果のみ伝える。
- 判定結果に含まれない制度について言及しない。

## 判定ステータスの意味（Prologが返す3状態）
- **decided**: 提供された情報で判定完了。受給見込みあり。金額も確定。
- **blocked**: 追加情報があれば判定できる。「まだわからない」状態。
- **ineligible**: 条件を満たさない。受給見込みなし。

## 回答ルール
1. **断定表現の禁止**（最重要ルール）:
   ❌「受給できます」「該当します」「もらえます」「対象です」
   ✅「受給できる可能性があります」「該当する見込みです」「対象となりそうです」
2. 初回応答では「法的助言ではなく、正確な判断は自治体窓口でご確認ください」と伝える。
3. decided制度がある場合: 制度名・金額・簡単な説明を伝える。
4. blocked制度がある場合: 「あと○件の制度は追加の情報で判定できます」と伝える。
5. next_questionがある場合: 自然な流れで次の質問をする。
6. 回答は簡潔に（3〜5文）。箇条書きで制度を列挙してよい。
7. センシティブな話題（ひとり親、障害、生活保護等）には配慮する。
8. 制度の説明は[JUDGMENT DATA]のdescriptionフィールドをそのまま使う。自分で説明を作らない。
9. 金額は[JUDGMENT DATA]のamountフィールドの値を使う。自分で計算しない。
"""


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------
def _merge_facts(existing: dict, extracted: dict) -> dict:
    """Merge extracted facts into existing, null-only overwrite policy."""
    merged = json.loads(json.dumps(existing))

    if extracted.get("claimant_birth_date"):
        merged.setdefault("claimant", {})
        if not merged["claimant"].get("birth_date"):
            merged["claimant"]["birth_date"] = extracted["claimant_birth_date"]

    if extracted.get("children") and not merged.get("children"):
        merged["children"] = [
            {"id": f"c{i+1}", "birth_date": c["birth_date"], "askable": {}}
            for i, c in enumerate(extracted["children"])
            if c.get("birth_date")
        ]

    ext_askable = extracted.get("askable") or {}
    merged.setdefault("askable", {})
    for key, val in ext_askable.items():
        if val is not None and merged["askable"].get(key) is None:
            merged["askable"][key] = val

    return merged


# ---------------------------------------------------------------------------
# Build judgment summary for Gemini (Step 4 input)
# ---------------------------------------------------------------------------
def _build_judgment_summary(judgment: dict) -> str:
    """Format Prolog judgment results for Gemini to interpret."""
    lines = []
    decided = [r for r in judgment["results"] if r.get("status") == "decided"]
    blocked = [r for r in judgment["results"] if r.get("status") == "blocked"]
    ineligible = [r for r in judgment["results"]
                  if r.get("status") == "ineligible"]

    headline = judgment.get("headline", {})
    parts = []
    if headline.get("monthly_yen"):
        parts.append(f"月額{headline['monthly_yen']:,}円")
    if headline.get("oneoff_yen"):
        parts.append(f"一時金{headline['oneoff_yen']:,}円")
    if headline.get("yearly_yen"):
        parts.append(f"年額{headline['yearly_yen']:,}円")
    if headline.get("in_kind_count"):
        parts.append(f"現物給付{headline['in_kind_count']}件")
    if parts:
        lines.append(f"## 受給見込み総額（下限）: {' + '.join(parts)}")
    lines.append("")

    if decided:
        lines.append(f"## 受給見込み（{len(decided)}件）")
        for r in decided:
            amt = _amount_text(r.get("amount"))
            desc = r.get("description", "")
            uf = r.get("used_facts", [])
            reason_parts = []
            for f in uf:
                if f["fact"] in ("age", "age_nendo_matsu"):
                    reason_parts.append(f"{f['subject']}の年齢{f['value']}歳")
                else:
                    reason_parts.append(f"{f['fact']}={f['value']}")
            reason = "、".join(reason_parts) if reason_parts else "基本条件を満たしている"
            lines.append(f"- {r['name']}（{amt}）: {desc} [根拠: {reason}]")
        lines.append("")

    if blocked:
        lines.append(f"## 追加情報で判定可能（{len(blocked)}件）")
        for r in blocked[:5]:
            missing = r.get("missing", [])
            lines.append(f"- {r['name']}: 不足情報={','.join(missing[:3])}")
        if len(blocked) > 5:
            lines.append(f"  ...他{len(blocked)-5}件")
        lines.append("")

    if ineligible:
        lines.append(f"## 非該当（{len(ineligible)}件） ※ユーザーには詳細不要、聞かれた場合のみ")
        for r in ineligible[:3]:
            lines.append(f"- {r['name']}: {r.get('reason', '')}")
        lines.append("")

    nq = judgment.get("next_question")
    if nq:
        lines.append("## 次に聞くべき質問")
        lines.append(f"質問文: {nq['text']}")
        lines.append(f"理由: この質問で{len(nq.get('why', []))}件の制度の判定が進む")
        if nq.get("choices"):
            choice_labels = [c["label"] for c in nq["choices"][:5]]
            lines.append(f"選択肢: {' / '.join(choice_labels)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main chat function
# ---------------------------------------------------------------------------
MAX_HISTORY_TURNS = 8
MAX_MESSAGE_CHARS = 500


def chat_turn(
    message: str,
    facts: dict,
    history: list[dict],
    municipality: str = "shibuya",
    as_of: Optional[date] = None,
) -> dict:
    if len(message) > MAX_MESSAGE_CHARS:
        message = message[:MAX_MESSAGE_CHARS]

    history = (history or [])[-MAX_HISTORY_TURNS:]
    if as_of is None:
        as_of = datetime.now(JST).date()

    client = _get_client()

    # --- Step 1: Extract facts ---
    extraction_input = (
        f"今日の日付: {as_of.isoformat()}\n"
        f"現在の既知事実:\n{json.dumps(facts, ensure_ascii=False, indent=2)}\n\n"
        f"ユーザーの発話:\n{message}\n\n"
        "上記の発話から新たに判明した事実をJSON形式で出力してください。"
    )

    history_for_extraction = [
        {"role": h["role"], "parts": [{"text": h["content"]}]}
        for h in history[-4:]
    ]
    history_for_extraction.append(
        {"role": "user", "parts": [{"text": extraction_input}]}
    )

    extraction_response = client.models.generate_content(
        model=MODEL,
        contents=history_for_extraction,
        config={
            "system_instruction": EXTRACTION_SYSTEM_PROMPT,
            "temperature": 0.1,
            "response_mime_type": "application/json",
            # thinking off: extraction is mechanical, and thought tokens
            # count toward output limits on 2.5+/3.x flash models
            "thinking_config": {"thinking_budget": 0},
        },
    )

    try:
        extracted = json.loads(extraction_response.text)
    except (json.JSONDecodeError, AttributeError):
        extracted = {"askable": {}, "confidence": "low"}

    # --- Step 2: Merge ---
    merged_facts = _merge_facts(facts, extracted)

    # --- Step 3: Prolog judgment ---
    judgment = judge_request(merged_facts, as_of, municipality)

    # --- Step 4: Generate response ---
    judgment_summary = _build_judgment_summary(judgment)

    history_for_response = [
        {"role": h["role"], "parts": [{"text": h["content"]}]}
        for h in history[-6:]
    ]
    history_for_response.append(
        {"role": "user", "parts": [{"text": message}]}
    )
    history_for_response.append(
        {"role": "user", "parts": [{"text":
            f"[JUDGMENT DATA — Prologエンジンの判定結果。この情報をもとに回答してください]\n\n"
            f"{judgment_summary}"
        }]}
    )

    response_result = client.models.generate_content(
        model=MODEL,
        contents=history_for_response,
        config={
            "system_instruction": RESPONSE_SYSTEM_PROMPT,
            "temperature": 0.7,
            "max_output_tokens": 600,
            # thinking off: without this, thought tokens eat the 600-token
            # budget and the visible reply gets truncated mid-sentence
            "thinking_config": {"thinking_budget": 0},
        },
    )

    response_text = (
        response_result.text
        or "申し訳ありません、応答を生成できませんでした。"
    )

    return {
        "response": response_text,
        "facts": merged_facts,
        "extracted": extracted,
        "judgment": {
            "headline": judgment["headline"],
            "results": judgment["results"],
        },
        "next_question": judgment.get("next_question"),
    }


def _amount_text(amount: Optional[dict]) -> str:
    if not amount:
        return "金額未定"
    if amount.get("type") == "in_kind":
        return "現物給付"
    yen = amount.get("yen")
    if yen is not None:
        unit = {"monthly": "月額", "yearly": "年額", "oneoff": "一時金"}
        return f"{unit.get(amount['type'], '')}{yen:,}円"
    lo, hi = amount.get("yen_min"), amount.get("yen_max")
    if lo is not None:
        unit = {"monthly": "月額", "yearly": "年額", "oneoff": "一時金"}
        return f"{unit.get(amount['type'], '')}{lo:,}〜{hi:,}円"
    return "金額未定"
