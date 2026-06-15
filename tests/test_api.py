"""API smoke tests (no LLM, no network)."""
from fastapi.testclient import TestClient

from seido.app import app

client = TestClient(app)

FACTS = {
    "children": [{"id": "c1", "birth_date": "2019-06-01"}],
    "askable": {"nenshu": None, "shotoku_exact": None, "hitorioya": None,
                "hitorioya_jiyuu": None, "seikei_douitsu_partner": None,
                "fuyou_ninzu": None, "kenkou_hoken": None},
}


def test_judge_endpoint():
    r = client.post("/api/judge", json={"facts": FACTS, "as_of": "2026-06-11"})
    assert r.status_code == 200
    body = r.json()
    assert body["headline"]["monthly_yen"] >= 15000  # jidou_teate + 018
    assert body["next_question"] is not None


def test_judge_rejects_oversized_payload():
    big = dict(FACTS)
    big["askable"] = dict(FACTS["askable"], hitorioya_jiyuu=None)
    r = client.post("/api/judge",
                    json={"facts": big, "as_of": "2026-06-11",
                          "municipality": "x" * 20_000})
    assert r.status_code == 413


def test_proof_endpoint_recomputes_status():
    r = client.post("/api/proof", json={
        "facts": FACTS, "as_of": "2026-06-11",
        "program": "jidou_teate", "subject": "c1"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"].startswith("decided(")
    assert body["proof"].startswith("node(")


def test_proof_rejects_unknown_program():
    r = client.post("/api/proof", json={
        "facts": FACTS, "as_of": "2026-06-11",
        "program": "evil_program", "subject": "c1"})
    assert r.status_code == 404


def test_municipalities_endpoint():
    r = client.get("/api/municipalities")
    assert r.status_code == 200
    munis = r.json()["municipalities"]
    assert len(munis) == 23
    assert {"id": "shibuya", "name": "東京都渋谷区"} in munis


def test_judge_rejects_unknown_municipality():
    r = client.post("/api/judge", json={
        "facts": FACTS, "as_of": "2026-06-11", "municipality": "osaka"})
    assert r.status_code == 400


def test_judge_works_for_every_registered_ward():
    munis = client.get("/api/municipalities").json()["municipalities"]
    for m in munis:
        r = client.post("/api/judge", json={
            "facts": FACTS, "as_of": "2026-06-11", "municipality": m["id"]})
        assert r.status_code == 200, m["id"]
        ids = {x["program"] for x in r.json()["results"]}
        assert "jidou_teate" in ids and "tokyo_018_support" in ids, m["id"]


def test_proof_rejects_bad_subject():
    for bad in ["c1_inject)", "SELF", "1c", "c", "c1 c2"]:
        r = client.post("/api/proof", json={
            "facts": FACTS, "as_of": "2026-06-11",
            "program": "jidou_teate", "subject": bad})
        assert r.status_code == 422, f"should reject subject={bad!r}"


def test_as_of_range_validation():
    r = client.post("/api/judge", json={
        "facts": FACTS, "as_of": "9999-12-31", "municipality": "shibuya"})
    assert r.status_code == 422


def test_too_many_children_rejected():
    big_facts = {
        "children": [{"birth_date": "2020-01-01"} for _ in range(25)],
        "askable": {},
    }
    r = client.post("/api/judge", json={
        "facts": big_facts, "as_of": "2026-06-11", "municipality": "shibuya"})
    assert r.status_code == 422


def test_child_id_injection_blocked_via_api():
    evil_facts = {
        "children": [{"id": "c1). halt(1). x(", "birth_date": "2020-01-01"}],
        "askable": {},
    }
    r = client.post("/api/judge", json={
        "facts": evil_facts, "as_of": "2026-06-11", "municipality": "shibuya"})
    assert r.status_code == 422


def test_static_frontend_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "もらい忘れチェッカー" in r.text


def test_interview_flow_end_to_end():
    """The full chip-tap loop the frontend drives: each answer updates
    facts client-side and re-judges; amounts grow; proof retrievable."""
    facts = {
        "children": [{"id": "c1", "birth_date": "2019-06-01", "askable": {}},
                     {"id": "c2", "birth_date": "2025-06-01", "askable": {}}],
        "askable": {"nenshu": [2_000_000, 4_000_000], "shotoku_exact": None,
                    "hitorioya": None, "hitorioya_jiyuu": None,
                    "seikei_douitsu_partner": None, "fuyou_ninzu": None,
                    "kenkou_hoken": None},
    }

    def judge():
        r = client.post("/api/judge",
                        json={"facts": facts, "as_of": "2026-06-11"})
        assert r.status_code == 200
        return r.json()

    resp = judge()
    assert resp["headline"]["monthly_yen"] == 35000   # jidou_teate + 018
    assert resp["headline"]["oneoff_yen"] == 200000   # birthday + akachan (c2 FY2025)
    assert resp["next_question"]["fact"] == "hitorioya"

    # answer chips in the order the engine asks
    household_answers = {"hitorioya": True, "hitorioya_jiyuu": "rikon",
                         "seikei_douitsu_partner": False, "fuyou_ninzu": 2,
                         "kenkou_hoken": True, "shotoku_exact": 1_400_000,
                         "ninshin": False}
    per_child_answers = {"koukou_zaigaku": False, "gakkou_kubun": None}
    for _ in range(15):                                # frontend turn cap
        q = resp["next_question"]
        if q is None:
            break
        key = q["askable_key"]
        child = q.get("child")
        if child:
            assert key in per_child_answers, f"unexpected per-child question: {key}"
            ch = next(c for c in facts["children"] if c["id"] == child)
            ch["askable"][key] = per_child_answers[key]
        else:
            assert key in household_answers, f"unexpected question: {key}"
            facts["askable"][key] = household_answers[key]
        resp = judge()
    assert resp["next_question"] is None

    by = {r["program"]: r for r in resp["results"]}
    jft = by["jidou_fuyou_teate"]
    assert jft["status"] == "decided"                 # shotoku 1.4M < 1.45M zenbu limit
    assert jft["amount"]["yen"] == 59400              # zenbu + 1 addition
    assert by["tokyo_jidou_ikusei_teate"]["status"] == "decided"
    assert by["shibuya_kodomo_iryouhi"]["status"] == "decided"
    # headline now includes 13,500 x2 (ikusei) + 59,400 + 35,000
    assert resp["headline"]["monthly_yen"] == 35000 + 27000 + 59400

    # proof retrievable for a decided program (what the なぜ? button does)
    r = client.post("/api/proof", json={
        "facts": facts, "as_of": "2026-06-11",
        "program": "jidou_fuyou_teate", "subject": "c1"})
    assert r.status_code == 200
    assert r.json()["proof"].startswith("node(")
