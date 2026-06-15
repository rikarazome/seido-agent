"""Unit tests for the deterministic mapping layer (no swipl needed)."""
from datetime import date

import pytest

from seido.factgen import (
    CHILD_ASKABLE_PREDS, facts_to_prolog, salary_to_shotoku,
)

# 2020-onward salary deduction brackets (kyuuyo shotoku koujo)
CASES = [
    (1_000_000, 450_000),     # deduction floor 550,000
    (1_625_000, 1_075_000),   # boundary of floor bracket
    (1_700_000, 1_120_000),   # 40% - 100,000
    (3_000_000, 2_020_000),   # 30% + 80,000
    (5_000_000, 3_560_000),   # 20% + 440,000
    (6_500_000, 4_760_000),   # 20% + 440,000 (<= 6.6M)
    (8_000_000, 6_100_000),   # 10% + 1,100,000
    (20_000_000, 18_050_000), # cap 1,950,000
]


@pytest.mark.parametrize("nenshu,shotoku", CASES)
def test_salary_to_shotoku(nenshu, shotoku):
    assert salary_to_shotoku(nenshu) == shotoku


def test_nenshu_point_converted():
    facts = {"children": [], "askable": {"nenshu": 3_000_000}}
    out = facts_to_prolog(facts, date(2026, 6, 11))
    assert "known(income(p1), 2020000)" in out


def test_nenshu_range_converts_endpoints():
    facts = {"children": [], "askable": {"nenshu": [1_000_000, 3_000_000]}}
    out = facts_to_prolog(facts, date(2026, 6, 11))
    assert "known(income(p1), range(450000,2020000))" in out


def test_shotoku_exact_bypasses_conversion():
    facts = {"children": [],
             "askable": {"nenshu": [1_000_000, 3_000_000],
                         "shotoku_exact": 1_500_000}}
    out = facts_to_prolog(facts, date(2026, 6, 11))
    assert "known(income(p1), 1500000)" in out
    assert "range" not in out


# -- injection defence --

@pytest.mark.parametrize("bad_id", [
    "c1). :- halt(1). child(c2",
    "../etc/passwd",
    "C1",          # uppercase
    "1abc",        # digit start
    "c1 c2",       # space
    "a(b)",        # parens
])
def test_malicious_child_id_rejected(bad_id):
    facts = {"children": [{"id": bad_id, "birth_date": "2020-01-01"}],
             "askable": {}}
    with pytest.raises(ValueError, match="invalid identifier"):
        facts_to_prolog(facts, date(2026, 6, 11))


def test_valid_child_ids_accepted():
    for cid in ["c1", "child_a", "abc123"]:
        facts = {"children": [{"id": cid, "birth_date": "2020-01-01"}],
                 "askable": {}}
        out = facts_to_prolog(facts, date(2026, 6, 11))
        assert f"child({cid})." in out


def test_empty_child_id_gets_auto_generated():
    facts = {"children": [{"id": "", "birth_date": "2020-01-01"}],
             "askable": {}}
    out = facts_to_prolog(facts, date(2026, 6, 11))
    assert "child(c1)." in out


# -- data sync guard --

def test_child_askable_preds_matches_questions_yaml():
    """CHILD_ASKABLE_PREDS must stay in sync with questions.yaml scope:per_child."""
    from seido.runner import questions
    per_child = {q["fact"] for q in questions() if q.get("scope") == "per_child"}
    assert CHILD_ASKABLE_PREDS == per_child
