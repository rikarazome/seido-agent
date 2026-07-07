"""Scenario tests for the /api/judge runner (deterministic, no LLM).

Covers the aggregation rules and question selection of
docs/specs/architecture.md against real swipl evaluation.
"""
from datetime import date

from seido.runner import judge_request

AS_OF = date(2026, 6, 11)


def base_household():
    return {
        "children": [
            {"id": "c1", "birth_date": "2019-06-01"},   # FY-end 7
            {"id": "c2", "birth_date": "2025-06-01"},   # age 1, born FY2025
        ],
        "askable": {
            "nenshu": None, "shotoku_exact": None, "hitorioya": None,
            "hitorioya_jiyuu": None, "seikei_douitsu_partner": None,
            "fuyou_ninzu": None, "kenkou_hoken": None,
        },
    }


def by_id(resp):
    return {r["program"]: r for r in resp["results"]}


def test_first_pass_shibuya_two_children():
    resp = judge_request(base_household(), AS_OF, municipality="shibuya")
    r = by_id(resp)

    # jidou_teate: c1 = 10,000 (rank 2? no -- eldest counted: c1 rank 1,
    # age 7 -> 10,000; c2 rank 2, age 1 < 3 -> 15,000), program sums 25,000
    assert r["jidou_teate"]["status"] == "decided"
    assert r["jidou_teate"]["amount"] == {"type": "monthly", "yen": 25000}

    # 018: both children eligible -> 10,000/month
    assert r["tokyo_018_support"]["amount"] == {"type": "monthly", "yen": 10000}

    # birthday support: c2 born FY2025 -> 100,000 one-off; c1 past window
    assert r["shibuya_birthday_support"]["status"] == "decided"
    assert r["shibuya_birthday_support"]["amount"] == {"type": "oneoff", "yen": 100000}

    # medical subsidy blocked on insurance question
    assert r["shibuya_kodomo_iryouhi"]["status"] == "blocked"
    assert r["shibuya_kodomo_iryouhi"]["missing"] == ["kenkou_hoken"]

    # single-parent programs blocked (hitorioya unknown)
    assert r["jidou_fuyou_teate"]["status"] == "blocked"
    assert r["tokyo_jidou_ikusei_teate"]["status"] == "blocked"

    # shugaku shienkin: no high-school-age child
    assert r["kouko_shugaku_shienkin"]["status"] == "ineligible"

    # shugaku_enjo now supported (hikazei-based), blocked on hikazei
    assert r["shibuya_shugaku_enjo"]["status"] == "blocked"

    # headline: jidou_teate(25k) + 018(10k) = 35k monthly
    # oneoff: birthday(100k) + akachan(100k) + hajimete(100k) + bukka(2x20k) = 340k
    assert resp["headline"]["monthly_yen"] == 35000
    assert resp["headline"]["oneoff_yen"] == 340000

    # shussan_ikuji_ichijikin: blocked on ninshin + kenkou_hoken
    assert r["shussan_ikuji_ichijikin"]["status"] == "blocked"

    # hitorioya_iryo_josei: blocked (hitorioya unknown)
    assert r["hitorioya_iryo_josei"]["status"] == "blocked"

    # shinshin_shogaisha_iryo_josei: blocked (shogai_techo + income + fuyou_ninzu unknown)
    assert r["shinshin_shogaisha_iryo_josei"]["status"] == "blocked"

    # next question: income unlocks the most blocked programs (including new adult programs)
    q = resp["next_question"]
    assert q is not None
    assert len(q["why"]) >= 4
    labels = [c["label"] for c in q["choices"]]
    assert labels[-1].startswith("わからない")          # auto-appended, last


def test_declined_fact_skipped_in_question_selection():
    facts = base_household()
    facts["askable"]["hitorioya"] = "declined"
    resp = judge_request(facts, AS_OF, municipality="shibuya")
    # single-parent programs stay blocked, but the question moves on
    assert by_id(resp)["jidou_fuyou_teate"]["status"] == "blocked"
    assert resp["next_question"]["fact"] != "hitorioya"


def test_childless_household_no_eligible_subject():
    facts = {"children": [], "askable": {}}
    resp = judge_request(facts, AS_OF, municipality="shibuya")
    r = by_id(resp)
    assert r["jidou_teate"]["status"] == "ineligible"
    assert r["jidou_teate"]["reason"] == "no_eligible_subject"
    assert resp["headline"]["monthly_yen"] == 0
    # shussan_ikuji_ichijikin is claimant-level, still blocked even without children
    assert r["shussan_ikuji_ichijikin"]["status"] == "blocked"
    assert resp["next_question"] is not None


def test_childless_claimant_with_birth_date():
    """Chat UI scenario: adult user with no children, claimant birth_date
    provided for age-based programs (disability, medical, etc.)."""
    facts = {
        "children": [],
        "claimant": {"birth_date": "1985-05-15"},
        "askable": {"nenshu": [2_000_000, 4_000_000]},
    }
    resp = judge_request(facts, AS_OF, municipality="shibuya")
    r = by_id(resp)
    # child programs ineligible (no children)
    assert r["jidou_teate"]["status"] == "ineligible"
    assert r["jidou_teate"]["reason"] == "no_eligible_subject"
    # claimant-level programs still reachable
    assert r["shussan_ikuji_ichijikin"]["status"] == "blocked"
    # disability programs blocked on shogai_techo
    assert r["tokubetsu_shogaisha_teate"]["status"] == "blocked"
    # next question should exist (claimant programs are blocked)
    assert resp["next_question"] is not None


def test_no_claimant_birth_date_blocks_age_programs_not_error():
    """The birth-date step is skippable (form skip button; chat users may
    never state it), so claimant-age rules returning error(structural_no_age)
    must surface as blocked on claimant_birth_date -- "give us the birth date
    and we can judge" -- not as an error card (fail safe: ask, don't alarm)."""
    resp = judge_request(base_household(), AS_OF, municipality="shibuya")
    r = by_id(resp)
    errors = [p for p, c in r.items() if c["status"] == "error"]
    assert errors == [], f"unexpected error cards: {errors}"
    assert r["silver_pass"]["status"] == "blocked"
    assert r["silver_pass"]["missing"] == ["claimant_birth_date"]
    # with the birth date provided, the same program decides normally
    facts = base_household()
    facts["claimant"] = {"birth_date": "1950-01-01"}   # age 76
    r2 = by_id(judge_request(facts, AS_OF, municipality="shibuya"))
    assert r2["silver_pass"]["status"] == "decided"


def test_household_amount_absent_rule_is_quiet(caplog):
    """boshi_jiritsu_kyouiku etc. decide qualitatively (no fixed yen) and
    define no teate_amount/2. The amount must come back None WITHOUT a
    swipl process error: the old path raised Unknown procedure inside
    swipl (rc=1) and logged 3 ERRORs per request, burying real failures
    (found during container verification 2026-07-08)."""
    facts = {"claimant": {"birth_date": "1990-03-10"},
             "children": [{"id": "c1", "birth_date": "2021-01-01"},
                          {"id": "c2", "birth_date": "2024-01-01"}],
             "askable": {"nenshu": [2_000_000, 4_000_000], "hitorioya": True,
                         "hitorioya_jiyuu": "rikon"}}
    with caplog.at_level("ERROR", logger="seido.prolog"):
        resp = judge_request(facts, date(2026, 7, 8), municipality="shibuya")
    r = by_id(resp)
    # behavior unchanged: decided, amount honestly absent
    assert r["boshi_jiritsu_kyouiku"]["status"] == "decided"
    assert r["boshi_jiritsu_kyouiku"].get("amount") is None
    # fixed-amount programs unaffected
    assert r["jidou_teate"]["amount"] == {"type": "monthly", "yen": 25000}
    # and the log is clean -- no swipl failures, no warning spam
    prolog_errors = [rec for rec in caplog.records
                     if rec.name == "seido.prolog"]
    assert prolog_errors == [], \
        f"swipl errors leaked: {[rec.getMessage()[:80] for rec in prolog_errors]}"


def test_chat_flow_childless_progressive_answers():
    """Simulates the chat UI chip-tap flow for a childless user,
    progressively answering questions until all programs settle."""
    facts = {
        "children": [],
        "claimant": {"birth_date": "1990-03-01"},
        "askable": {"nenshu": [2_000_000, 4_000_000]},
    }
    answers = {
        "ninshin": False, "kenkou_hoken": True, "hitorioya": False,
        "fuyou_ninzu": 0, "shogai_techo": "declined",
        "seikatsu_hogo": False, "nanbyo_nintei": False,
        "hikazei": False, "koyou_hoken": "declined",
        "rishoku": "declined", "shotoku_exact": "declined",
        "seikei_douitsu_partner": "declined",
        "hitorioya_jiyuu": "declined",
        "hoken_shubetsu": "shakai_hoken", "byouki_kyugyou": False,
        "kaigo_family": False, "daigaku_zaigaku": False,
        "kaigo_nintei": False, "haiguusha": False,
        "jutaku_loan": False, "iryouhi_10man": False,
        "seimei_hoken": False, "jishin_hoken": False,
    }
    for _ in range(40):
        resp = judge_request(facts, AS_OF, municipality="shibuya")
        q = resp["next_question"]
        if q is None:
            break
        key = q["askable_key"]
        if key in answers:
            facts["askable"][key] = answers[key]
        else:
            facts["askable"][key] = "declined"
    assert resp["next_question"] is None
    r = by_id(resp)
    # child programs ineligible (no children)
    assert r["jidou_teate"]["status"] == "ineligible"
    # programs with all-declined facts stay blocked (design: L436 of architecture.md)
    # but no more questions are asked — verify no infinite loop
    still_blocked = [p for p in r.values() if p["status"] == "blocked"]
    for b in still_blocked:
        # every missing fact must be declined (otherwise question selection is broken)
        for m in b.get("missing", []):
            assert facts["askable"].get(m) == "declined", (
                f"{b['program']} blocked on {m} which is not declined")


def test_other_ward_gets_national_and_tokyo_programs_only():
    """Any of the 23 wards immediately gets national + tokyo-layer
    programs; other wards' municipal programs must not leak in."""
    resp = judge_request(base_household(), AS_OF, municipality="setagaya")
    ids = set(by_id(resp))
    assert "jidou_teate" in ids
    assert "tokyo_018_support" in ids
    assert "tokyo_jidou_ikusei_teate" in ids
    assert not any(p.startswith("shibuya_") for p in ids)


def test_unknown_municipality_rejected():
    import pytest
    with pytest.raises(ValueError):
        judge_request(base_household(), AS_OF, municipality="osaka")


def test_per_household_amount_not_summed_over_children():
    facts = {
        "children": [
            {"id": "c1", "birth_date": "2019-06-01"},
            {"id": "c2", "birth_date": "2023-08-01"},
        ],
        "askable": {
            "nenshu": 1_000_000, "shotoku_exact": None, "hitorioya": True,
            "hitorioya_jiyuu": "rikon", "seikei_douitsu_partner": False,
            "fuyou_ninzu": 2, "kenkou_hoken": True,
        },
    }
    resp = judge_request(facts, AS_OF, municipality="shibuya")
    jft = by_id(resp)["jidou_fuyou_teate"]
    assert jft["status"] == "decided"
    # household amount 48,050 + 11,350, NOT doubled per child
    assert jft["amount"] == {"type": "monthly", "yen": 59400}


def test_ichibu_range_amount_two_point_eval():
    facts = {
        "children": [{"id": "c1", "birth_date": "2019-06-01"}],
        "askable": {
            # nenshu 2-3M -> shotoku range(1,320,000, 2,020,000): fully inside
            # the partial-payment band for 0 dependents (690,000..2,080,000)
            "nenshu": [2_000_000, 3_000_000], "shotoku_exact": None,
            "hitorioya": True, "hitorioya_jiyuu": "rikon",
            "seikei_douitsu_partner": False, "fuyou_ninzu": 0,
            "kenkou_hoken": True,
        },
    }
    resp = judge_request(facts, AS_OF, municipality="shibuya")
    jft = by_id(resp)["jidou_fuyou_teate"]
    assert jft["status"] == "decided"
    # taper evaluated at both endpoints (decreasing in income)
    assert jft["amount"] == {"type": "monthly",
                             "yen_min": 12920, "yen_max": 31410}
