"""Unit tests for the deterministic mapping layer (no swipl needed)."""
from datetime import date

import pytest

from seido.factgen import (
    ASKABLE_MAP, CHILD_ASKABLE_PREDS, facts_to_prolog, salary_to_shotoku,
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


# -- claimant age generation (v2) --

def test_structural_facts_declared_discontiguous():
    """Claimant + children interleave age/2 etc. clauses; without a
    discontiguous declaration swipl prints ~30 warning lines per request
    (log noise that buried a real error during container verification
    2026-07-08, and a hard failure if a future swipl escalates warnings)."""
    facts = {
        "claimant": {"birth_date": "1990-03-10"},
        "children": [{"id": "c1", "birth_date": "2021-01-01"},
                     {"id": "c2", "birth_date": "2024-01-01"}],
        "askable": {},
    }
    out = facts_to_prolog(facts, date(2026, 7, 8))
    assert ":- discontiguous" in out
    for pred in ("claimant/1", "child/1", "kango_by/2", "seikei_futan/2",
                 "age/2", "age_nendo_matsu/2", "birth_nendo/2"):
        assert pred in out.split(":- discontiguous", 1)[1].split(".", 1)[0], \
            f"{pred} missing from discontiguous declaration"


def test_claimant_birth_date_generates_age():
    facts = {
        "claimant": {"birth_date": "1988-04-01"},
        "children": [],
        "askable": {},
    }
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "age(p1, 38)." in out
    assert "age_nendo_matsu(p1, 38)." in out


def test_claimant_birth_date_age_boundary():
    """Birthday hasn't occurred yet in the reference date."""
    facts = {
        "claimant": {"birth_date": "1988-07-01"},
        "children": [],
        "askable": {},
    }
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "age(p1, 37)." in out


def test_claimant_no_birth_date_no_age():
    """Without claimant.birth_date, no age(p1, _) should be emitted."""
    facts = {"children": [], "askable": {}}
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "age(p1," not in out


def test_claimant_empty_object_no_age():
    facts = {"claimant": {}, "children": [], "askable": {}}
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "age(p1," not in out


# -- v2 askable keys --

V2_KEYS = [
    "shogai_techo", "shogai_teido", "kaigo_nintei", "ninshin",
    "shussan_yoteibi", "juutaku_type", "hikazei", "koyou_hoken",
    "rishoku", "rishoku_jiyuu", "seikatsu_hogo", "nanbyo_nintei",
    "jido_yougo_shisetsu",
]


@pytest.mark.parametrize("key", V2_KEYS)
def test_v2_askable_key_in_map(key):
    """All v2 keys from architecture.md must exist in ASKABLE_MAP."""
    assert key in ASKABLE_MAP


def test_v2_boolean_askable_generates_known():
    facts = {"children": [], "askable": {"ninshin": True}}
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "known(ninshin(p1), true)" in out


def test_v2_enum_askable_generates_known():
    facts = {"children": [], "askable": {"shogai_techo": "shintai_1"}}
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "known(shogai_techo(p1), shintai_1)" in out


def test_v2_per_child_askable():
    """jido_yougo_shisetsu is per_child: injected for every child."""
    facts = {
        "children": [
            {"id": "c1", "birth_date": "2020-01-01"},
            {"id": "c2", "birth_date": "2022-01-01"},
        ],
        "askable": {"jido_yougo_shisetsu": True},
    }
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "known(jido_yougo_shisetsu(c1), true)" in out
    assert "known(jido_yougo_shisetsu(c2), true)" in out


def test_v2_null_and_declined_emit_nothing():
    facts = {"children": [], "askable": {
        "seikatsu_hogo": None,
        "hikazei": "declined",
    }}
    out = facts_to_prolog(facts, date(2026, 6, 15))
    assert "seikatsu_hogo" not in out
    assert "hikazei" not in out


# -- data sync guard --

def test_child_askable_preds_matches_questions_yaml():
    """CHILD_ASKABLE_PREDS must stay in sync with questions.yaml scope:per_child."""
    from seido.runner import questions
    per_child = {q["fact"] for q in questions() if q.get("scope") == "per_child"}
    assert CHILD_ASKABLE_PREDS == per_child
