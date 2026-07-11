# -*- coding: utf-8 -*-
"""_build_turn_summary contract: the response-prompt input must carry the
count delta but NEVER program names / per-program amounts -- the judgment
card is the only channel that displays judgments (architecture.md).
Deterministic: judge_request runs real Prolog, no Gemini.
"""
from datetime import date

from seido.chat import RESPONSE_SYSTEM_PROMPT, _applied_diff, _build_turn_summary
from seido.runner import judge_request

AS_OF = date(2026, 7, 8)

BASE_FACTS = {
    "children": [{"id": "c1", "birth_date": "2021-01-01", "askable": {}},
                 {"id": "c2", "birth_date": "2024-01-01", "askable": {}}],
    "askable": {"nenshu": [4000000, 6000000]},
}


def _with_hitorioya(facts):
    merged = {"children": [dict(c) for c in facts["children"]],
              "askable": dict(facts["askable"])}
    merged["askable"]["hitorioya"] = True
    merged["askable"]["hitorioya_jiyuu"] = "rikon"
    return merged


def test_turn_summary_has_delta_but_no_program_names():
    prev = judge_request(BASE_FACTS, AS_OF, "shibuya")
    merged = _with_hitorioya(BASE_FACTS)
    new = judge_request(merged, AS_OF, "shibuya")
    summary = _build_turn_summary(BASE_FACTS, merged, prev, new)

    prev_d = sum(1 for r in prev["results"] if r["status"] == "decided")
    new_d = sum(1 for r in new["results"] if r["status"] == "decided")
    assert new_d > prev_d, "hitorioya must unlock additional programs"
    assert f"{prev_d}件 → {new_d}件" in summary

    # NO decided program name may leak into the prompt input
    for r in new["results"]:
        if r["status"] == "decided":
            assert r["name"] not in summary, (
                f"program name leaked into turn summary: {r['name']}")

    # the applied facts are confirmed, the pre-existing ones are not
    assert "hitorioya = True" in summary
    assert "nenshu" not in summary

    # next question is carried for the reply to ask
    nq = new.get("next_question")
    if nq:
        assert nq["text"] in summary


def test_turn_summary_nothing_applied():
    prev = judge_request(BASE_FACTS, AS_OF, "shibuya")
    summary = _build_turn_summary(BASE_FACTS, BASE_FACTS, prev, prev)
    assert "なし（判定に反映できる新情報はありませんでした）" in summary
    d = sum(1 for r in prev["results"] if r["status"] == "decided")
    assert f"{d}件 → {d}件" in summary


def test_applied_diff_reports_only_survivors():
    existing = {"askable": {"nenshu": [0, 2000000]}}
    merged = {"askable": {"nenshu": [0, 2000000], "hitorioya": True}}
    diff = _applied_diff(existing, merged)
    assert diff == ["hitorioya = True"]

    # children only count as applied when they were absent before
    existing2 = {"children": [{"id": "c1", "birth_date": "2020-01-01",
                               "askable": {}}], "askable": {}}
    assert _applied_diff(existing2, existing2) == []


def test_response_prompt_forbids_program_names_and_assertions():
    assert "制度名を書かない" in RESPONSE_SYSTEM_PROMPT
    assert "断定表現の禁止" in RESPONSE_SYSTEM_PROMPT
    assert "受給できます" in RESPONSE_SYSTEM_PROMPT   # listed as forbidden example


def test_response_prompt_allows_terminology_but_not_program_details():
    # role 4: generic terminology questions get answered...
    assert "言葉の意味や質問の意図を尋ねている場合" in RESPONSE_SYSTEM_PROMPT
    assert "一般的な説明であり、正確な定義はお住まいの自治体窓口" \
        in RESPONSE_SYSTEM_PROMPT
    # ...but program-specific explanations stay firewalled to the card/statute
    assert "あなたの知識から説明しない" in RESPONSE_SYSTEM_PROMPT
