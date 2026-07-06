"""Error-handling contract tests (production-fixes design v11).

Pins the production error behavior:
- PrologError messages carry no swipl stderr (stderr may echo generated
  facts -- privacy rule: no facts in messages or logs)
- /api/judge and /api/proof map PrologError to a generic 500
- /api/chat catches PrologError BEFORE RuntimeError (PrologError is a
  RuntimeError subclass; 503 is reserved for missing chat configuration)
- /healthz verifies swipl actually runs, 503 when it cannot
- rate limiting returns a JSON 429 through the registered handler
"""
import pytest
from fastapi.testclient import TestClient

import seido.app as app_module
import seido.chat as chat_module
from seido.app import app, limiter
from seido.prolog import PrologError, judge_batch

client = TestClient(app)

FACTS = {"children": [{"id": "c1", "birth_date": "2019-06-01"}],
         "askable": {}}


# ---------------------------------------------------------------------------
# prolog.py: no stderr in PrologError messages
# ---------------------------------------------------------------------------

def test_prolog_error_message_contains_no_stderr():
    """Broken facts make swipl halt at load (on_error halt); the raised
    PrologError must NOT echo stderr, which contains the facts text."""
    with pytest.raises(PrologError) as exc:
        judge_batch("known(broken",
                    [("jidou_teate", "rules/national/jidou_teate.pl", "c1")])
    msg = str(exc.value)
    assert "known(broken" not in msg, "stderr (echoing facts) leaked into message"
    assert "ERROR" not in msg, "raw swipl stderr leaked into message"


# ---------------------------------------------------------------------------
# /api/judge, /api/proof: PrologError -> generic 500
# ---------------------------------------------------------------------------

def _raise_prolog_error(*a, **k):
    raise PrologError("prolog execution failed")


def test_api_judge_maps_prolog_error_to_500(monkeypatch):
    monkeypatch.setattr(app_module, "judge_request", _raise_prolog_error)
    r = client.post("/api/judge", json={"facts": FACTS, "as_of": "2026-06-11"})
    assert r.status_code == 500
    assert r.json()["detail"] == "judgment failed"


def test_api_proof_maps_prolog_error_to_500(monkeypatch):
    monkeypatch.setattr(app_module, "judge", _raise_prolog_error)
    r = client.post("/api/proof", json={
        "facts": FACTS, "as_of": "2026-06-11",
        "program": "jidou_teate", "subject": "c1"})
    assert r.status_code == 500
    assert r.json()["detail"] == "judgment failed"


# ---------------------------------------------------------------------------
# /api/chat: except-clause ordering (PrologError before RuntimeError)
# ---------------------------------------------------------------------------

def test_api_chat_prolog_error_is_500_not_config_503(monkeypatch):
    """A Prolog failure inside chat must not masquerade as 'not configured'."""
    monkeypatch.setattr(chat_module, "chat_turn", _raise_prolog_error)
    r = client.post("/api/chat", json={"message": "hi", "facts": FACTS})
    assert r.status_code == 500
    assert r.json()["detail"] == "judgment failed"


def test_api_chat_missing_config_is_fixed_503(monkeypatch):
    """RuntimeError (no API key) -> 503 with a fixed message that does not
    expose the internal exception text."""
    def raise_runtime(*a, **k):
        raise RuntimeError("GEMINI_API_KEY not set. secret internals here")
    monkeypatch.setattr(chat_module, "chat_turn", raise_runtime)
    r = client.post("/api/chat", json={"message": "hi", "facts": FACTS})
    assert r.status_code == 503
    assert r.json()["detail"] == "chat is not configured"


# ---------------------------------------------------------------------------
# /healthz: verifies swipl
# ---------------------------------------------------------------------------

def test_healthz_ok_with_real_swipl():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_healthz_503_when_swipl_unavailable(monkeypatch):
    def broken_run(*a, **k):
        raise FileNotFoundError("swipl")
    monkeypatch.setattr(app_module.subprocess, "run", broken_run)
    r = client.get("/healthz")
    assert r.status_code == 503


# ---------------------------------------------------------------------------
# rate limiting: JSON 429 via registered handler
# ---------------------------------------------------------------------------

def test_rate_limit_returns_json_429():
    """41 fast requests (invalid municipality -> 400, no Prolog run) must
    produce a JSON 429 once the 40/minute judge limit is exceeded.
    limiter is re-enabled only inside this test."""
    limiter.enabled = True
    try:
        statuses = []
        for _ in range(41):
            r = client.post("/api/judge", json={
                "facts": FACTS, "as_of": "2026-06-11",
                "municipality": "nosuchward"})
            statuses.append(r.status_code)
        assert statuses[-1] == 429, f"expected 429 on request 41, got {statuses[-1]}"
        # the registered handler must produce JSON, not an unhandled 500
        last = client.post("/api/judge", json={
            "facts": FACTS, "as_of": "2026-06-11",
            "municipality": "nosuchward"})
        assert last.status_code == 429
        assert "error" in last.json()
    finally:
        limiter.enabled = False
