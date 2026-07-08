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

from .factgen import ASKABLE_MAP
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
制度の該当判定は別のProlog推論エンジンが行い、その結果は画面上の「判定カード」に
常に表示されています。判定内容（制度名・金額）の表示はカードだけが行います。

## あなたの返信の役割（この3つだけ）
1. ユーザーの発話から何を理解したかを短く確認する。
   [TURN DATA]の「反映された情報」に基づくこと。反映されなかった内容を
   反映されたかのように言ってはいけない。
2. 判定カードの更新を件数の変化で案内する
   （例: 「受給見込みの制度がN件からM件に増えました。詳細は下のカードをご覧ください」）。
3. [TURN DATA]に次の質問があれば、自然な流れで尋ねる。

## 禁止事項（最重要）
- 制度名を書かない。制度を列挙しない。個別の金額を書かない。
- 該当/非該当をあなたが判断・示唆しない。
- [TURN DATA]にない数値を書かない。
- 断定表現の禁止:
  ❌「受給できます」「該当します」「もらえます」「対象です」
  ✅「受給できる可能性があります」「見込みです」

## その他のルール
- 初回応答（会話履歴が空のとき）は「法的助言ではなく、正確な判断は自治体窓口で
  ご確認ください」と一言添える。
- 反映された情報が「なし」の場合: 判定に使える情報を読み取れなかったことを正直に
  伝え、選択肢からの回答か別の言い方を促す。
- センシティブな話題（ひとり親、障害、生活保護など）には配慮ある言葉遣いをする。
- 全体で2〜4文、簡潔に。
"""


# ---------------------------------------------------------------------------
# Extraction JSON parsing (with truncation repair)
# ---------------------------------------------------------------------------
def _close_brackets(text: str) -> str:
    """Append the closing quotes/brackets a truncated JSON text is missing."""
    stack = []
    in_str = False
    esc = False
    for ch in text:
        if esc:
            esc = False
            continue
        if in_str:
            if ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]" and stack:
            stack.pop()
    suffix = '"' if in_str else ""
    suffix += "".join("}" if c == "{" else "]" for c in reversed(stack))
    return text + suffix


def _parse_extraction_json(text: str) -> dict:
    """Parse Step-1 output, repairing truncated JSON before giving up.

    gemini-3.5-flash occasionally emits the extraction JSON with the
    trailing close-braces missing (finish_reason=STOP even with
    response_mime_type json; observed live 2026-07-08). The content is
    complete, so bracket-balancing recovers the whole extraction instead
    of dropping the turn to the empty fallback.
    """
    for candidate in (text, _close_brackets(text or "")):
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return {"askable": {}, "confidence": "low"}


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------
def _valid_iso_date(s) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def _merge_facts(existing: dict, extracted: dict) -> dict:
    """Merge extracted facts into existing, null-only overwrite policy.

    The extraction is LLM output and treated as untrusted:
    - confidence "low" is not auto-applied (architecture.md; an uncertain
      guess must not silently drive a money judgment)
    - askable keys outside ASKABLE_MAP are dropped (they would raise
      ValueError inside factgen and kill the whole turn as a 500)
    - malformed birth dates are dropped for the same reason
    """
    merged = json.loads(json.dumps(existing))
    if extracted.get("confidence") == "low":
        return merged

    if _valid_iso_date(extracted.get("claimant_birth_date")):
        merged.setdefault("claimant", {})
        if not merged["claimant"].get("birth_date"):
            merged["claimant"]["birth_date"] = extracted["claimant_birth_date"]

    if extracted.get("children") and not merged.get("children"):
        valid = [c for c in extracted["children"]
                 if _valid_iso_date(c.get("birth_date"))]
        merged["children"] = [
            {"id": f"c{i+1}", "birth_date": c["birth_date"], "askable": {}}
            for i, c in enumerate(valid)
        ]

    ext_askable = extracted.get("askable") or {}
    merged.setdefault("askable", {})
    for key, val in ext_askable.items():
        if (key in ASKABLE_MAP and val is not None
                and merged["askable"].get(key) is None):
            merged["askable"][key] = val

    return merged


# ---------------------------------------------------------------------------
# Build turn summary for Gemini (Step 4 input)
# ---------------------------------------------------------------------------
def _applied_diff(existing: dict, merged: dict) -> list[str]:
    """Facts this turn actually added (i.e. survived the merge guards).

    The response confirms ONLY these back to the user: confirming a fact
    the merge dropped would tell the user it was applied when the
    judgment never saw it.
    """
    diff = []
    old_bd = (existing.get("claimant") or {}).get("birth_date")
    new_bd = (merged.get("claimant") or {}).get("birth_date")
    if new_bd and not old_bd:
        diff.append(f"あなたの生年月日 = {new_bd}")
    if merged.get("children") and not existing.get("children"):
        diff.append(f"お子さんの人数と生年月日（{len(merged['children'])}人）")
    old_ask = existing.get("askable") or {}
    for key, val in (merged.get("askable") or {}).items():
        if val is not None and old_ask.get(key) is None:
            diff.append(f"{key} = {val}")
    return diff


def _build_turn_summary(existing_facts: dict, merged_facts: dict,
                        prev_judgment: dict, judgment: dict) -> str:
    """Mechanical turn data for the response prompt.

    Deliberately contains NO program names and no per-program amounts:
    the judgment card is the only channel that displays judgments, so the
    reply cannot paraphrase (and thereby distort) them. The reply's job is
    understanding-confirmation + count delta + next question.
    """

    def counts(j):
        rs = j["results"]
        return (sum(1 for r in rs if r.get("status") == "decided"),
                sum(1 for r in rs if r.get("status") == "blocked"))

    lines = ["## 今回の発話から判定に反映された情報"]
    applied = _applied_diff(existing_facts, merged_facts)
    if applied:
        lines += [f"- {a}" for a in applied]
    else:
        lines.append("- なし（判定に反映できる新情報はありませんでした）")

    prev_d, _ = counts(prev_judgment)
    new_d, new_b = counts(judgment)
    prev_m = (prev_judgment.get("headline") or {}).get("monthly_yen") or 0
    new_m = (judgment.get("headline") or {}).get("monthly_yen") or 0
    lines.append("")
    lines.append("## 判定の変化（機械計算値。これ以外の数値を書かないこと）")
    lines.append(f"- 受給見込みの制度: {prev_d}件 → {new_d}件")
    lines.append(f"- 月額合計の下限: {prev_m:,}円 → {new_m:,}円")
    lines.append(f"- 追加情報があれば判定が進む制度: {new_b}件")

    nq = judgment.get("next_question")
    lines.append("")
    lines.append("## 次にユーザーに聞くべき質問")
    if nq:
        lines.append(f"- {nq['text']}"
                     f"（答えると{len(nq.get('why', []))}件の制度の判定が進みます）")
    else:
        lines.append("- なし（これ以上の質問はありません）")
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

    extracted = _parse_extraction_json(
        getattr(extraction_response, "text", None) or "")

    # --- Step 2: Merge ---
    merged_facts = _merge_facts(facts, extracted)

    # --- Step 3: Prolog judgment ---
    judgment = judge_request(merged_facts, as_of, municipality)
    # delta baseline = judgment for the facts the client sent, i.e. what the
    # card showed before this turn; skipped when the merge applied nothing
    if merged_facts != facts:
        prev_judgment = judge_request(facts, as_of, municipality)
    else:
        prev_judgment = judgment

    # --- Step 4: Generate response ---
    judgment_summary = _build_turn_summary(facts, merged_facts,
                                           prev_judgment, judgment)

    history_for_response = [
        {"role": h["role"], "parts": [{"text": h["content"]}]}
        for h in history[-6:]
    ]
    history_for_response.append(
        {"role": "user", "parts": [{"text": message}]}
    )
    history_for_response.append(
        {"role": "user", "parts": [{"text":
            f"[TURN DATA — 機械計算の判定変化データ。この情報のみに基づいて回答してください]\n\n"
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


