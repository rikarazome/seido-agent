"""Merge-policy unit tests for chat.py (no Gemini, no swipl).

Pins the extraction -> facts merge safety rules (architecture.md 対話
パイプライン): the extraction output comes from an LLM and must be treated
as untrusted -- nothing it says may overwrite a known answer, hallucinated
keys must not reach factgen (ValueError -> 500), and low-confidence
extractions must not silently drive money judgments.
"""
from seido.chat import _merge_facts


def base_facts():
    return {"claimant": {"birth_date": "1990-03-10"},
            "children": [{"id": "c1", "birth_date": "2021-01-01",
                          "askable": {}}],
            "askable": {"nenshu": [3_000_000, 3_000_000]}}


def ext(**kw):
    e = {"claimant_birth_date": None, "children": None, "municipality": None,
         "askable": {}, "confidence": "high", "clarification_needed": None}
    e.update(kw)
    return e


def test_null_only_existing_answers_never_overwritten():
    got = _merge_facts(base_facts(),
                       ext(askable={"nenshu": [9_000_000, 9_000_000]},
                           claimant_birth_date="1980-01-01"))
    assert got["askable"]["nenshu"] == [3_000_000, 3_000_000]
    assert got["claimant"]["birth_date"] == "1990-03-10"


def test_new_askable_values_fill_null_slots():
    got = _merge_facts(base_facts(), ext(askable={"hitorioya": True}))
    assert got["askable"]["hitorioya"] is True


def test_low_confidence_extraction_not_auto_applied():
    """architecture.md: confidence "low" の抽出は自動適用しない。An uncertain
    LLM guess must not silently become an input to a money judgment."""
    got = _merge_facts(base_facts(),
                       ext(askable={"hitorioya": True}, confidence="low"))
    assert "hitorioya" not in got["askable"]


def test_hallucinated_askable_key_dropped():
    """Keys outside ASKABLE_MAP would raise ValueError inside factgen during
    the judgment step -> the whole chat turn dies as a 500. Drop them at
    the merge boundary instead."""
    got = _merge_facts(base_facts(),
                       ext(askable={"maho_no_key": True, "hitorioya": True}))
    assert "maho_no_key" not in got["askable"]
    assert got["askable"]["hitorioya"] is True


def test_malformed_birth_dates_dropped_not_crashed():
    """Extraction dates are LLM output; '2021/01/01' etc. would raise
    ValueError in factgen -> 500. Skip them, keep the rest of the turn."""
    got = _merge_facts({"children": [], "askable": {}},
                       ext(claimant_birth_date="1990/03/10",
                           children=[{"birth_date": "2021/01/01"},
                                     {"birth_date": "2023-05-01"}]))
    assert "claimant" not in got or not got.get("claimant", {}).get("birth_date")
    assert [c["birth_date"] for c in got["children"]] == ["2023-05-01"]


def test_children_added_only_when_none_exist():
    got = _merge_facts(base_facts(),
                       ext(children=[{"birth_date": "2019-04-01"},
                                     {"birth_date": "2023-05-01"}]))
    assert len(got["children"]) == 1          # existing set wins (null-only)
    got2 = _merge_facts({"children": [], "askable": {}},
                        ext(children=[{"birth_date": "2019-04-01"}]))
    assert [c["id"] for c in got2["children"]] == ["c1"]


def test_claimant_birth_date_fills_empty_household():
    got = _merge_facts({"children": [], "askable": {}},
                       ext(claimant_birth_date="1958-05-01"))
    assert got["claimant"]["birth_date"] == "1958-05-01"
