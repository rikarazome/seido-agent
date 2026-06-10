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
