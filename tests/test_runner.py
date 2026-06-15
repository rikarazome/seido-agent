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

    # unsupported programs surface honestly
    assert r["shibuya_shugaku_enjo"]["status"] == "unsupported"

    # headline: 25,000 + 10,000 monthly, 100,000 (birthday) + 100,000 (akachan) oneoff
    assert resp["headline"]["monthly_yen"] == 35000
    assert resp["headline"]["oneoff_yen"] == 200000

    # shussan_ikuji_ichijikin: blocked on ninshin + kenkou_hoken
    assert r["shussan_ikuji_ichijikin"]["status"] == "blocked"

    # hitorioya_iryo_josei: blocked (hitorioya unknown)
    assert r["hitorioya_iryo_josei"]["status"] == "blocked"

    # shinshin_shogaisha_iryo_josei: blocked (shogai_techo + income + fuyou_ninzu unknown)
    assert r["shinshin_shogaisha_iryo_josei"]["status"] == "blocked"

    # next question: fuyou_ninzu unlocks 5 programs (most blocked programs need it)
    q = resp["next_question"]
    assert q["fact"] == "fuyou_ninzu"
    assert "jidou_fuyou_teate" in q["why"]
    assert len(q["why"]) >= 4  # grows as income-limited programs are added
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
