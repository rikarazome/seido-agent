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


def test_api_chat_bad_as_of_is_422_not_500():
    """HTTPException(422) from as_of validation must not be swallowed by
    the generic Exception handler and re-raised as 500."""
    r = client.post("/api/chat", json={
        "message": "hi", "facts": FACTS, "as_of": "not-a-date"})
    assert r.status_code == 422


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
# fail safe: no program may silently vanish from the results
# ---------------------------------------------------------------------------

def test_partial_subject_results_become_error_not_fake_judgment(monkeypatch):
    """If the batch returns results for only SOME subjects of a program
    (one child's block lost), the program must surface as error -- partial
    data must never be aggregated as a complete judgment (FN guard)."""
    import seido.runner as runner_module
    from datetime import date
    monkeypatch.setattr(
        runner_module, "judge_batch",
        lambda facts_pl, queries, **k: [
            {"program": "jidou_teate", "subject": "c1",
             "status": "decided(amount(10000))", "proof": "none"}])
    result = runner_module.judge_request(
        {"children": [{"id": "c1", "birth_date": "2019-06-01"},
                      {"id": "c2", "birth_date": "2021-06-01"}],
         "askable": {}},
        date(2026, 6, 11), "shibuya")
    jt = next(r for r in result["results"] if r["program"] == "jidou_teate")
    assert jt["status"] == "error", (
        f"partial batch data (1 of 2 subjects) must not be aggregated "
        f"as a normal judgment, got status={jt['status']}")


def test_no_program_vanishes_when_batch_returns_nothing(monkeypatch):
    """If judge_batch yields no block for a program (malformed output,
    partial batch), the program must surface as a visible error card --
    never disappear from the response (FN guard)."""
    import seido.runner as runner_module
    from datetime import date
    monkeypatch.setattr(runner_module, "judge_batch", lambda *a, **k: [])
    result = runner_module.judge_request(
        {"children": [{"id": "c1", "birth_date": "2019-06-01"}],
         "askable": {}},
        date(2026, 6, 11), "shibuya")
    expected = {p["id"] for p in runner_module.programs()
                if runner_module._applicable(p, "shibuya")}
    got = {r["program"] for r in result["results"]}
    missing = sorted(expected - got)
    assert not missing, f"programs vanished silently: {missing[:5]}"
    assert any(r["status"] == "error" for r in result["results"])


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


def test_child_without_birth_date_is_422_not_500():
    """A child entry missing birth_date used to raise TypeError inside
    factgen (date.fromisoformat(None)), which escaped api_judge's
    `except ValueError` as a raw, non-JSON 500."""
    r = client.post("/api/judge", json={
        "facts": {"children": [{"id": "c1", "askable": {}}], "askable": {}},
        "municipality": "shibuya"})
    assert r.status_code == 422
    assert r.json()["detail"] == "invalid facts schema"


def test_duplicate_child_ids_rejected_not_double_counted():
    """Duplicate ids made judge_batch query the same subject twice and the
    aggregator sum both -> inflated amounts (observed live: jidou_teate
    60,000 yen for a 2-child household)."""
    r = client.post("/api/judge", json={
        "facts": {"children": [
            {"id": "c1", "birth_date": "2020-01-01", "askable": {}},
            {"id": "c1", "birth_date": "2022-01-01", "askable": {}}],
            "askable": {}},
        "municipality": "shibuya"})
    assert r.status_code == 422


def test_chat_rejects_invalid_facts_before_llm(monkeypatch):
    """/api/chat must 422 on invalid request facts BEFORE reaching the
    chat engine: correct status for the caller AND no Gemini spend on
    garbage (cost defense). chat_turn is patched to prove it is never
    reached."""
    def _must_not_run(**kw):
        raise AssertionError("chat_turn must not run for invalid facts")
    monkeypatch.setattr(chat_module, "chat_turn", _must_not_run)
    r = client.post("/api/chat", json={
        "message": "こんにちは",
        "facts": {"children": [{"id": "c1", "askable": {}}], "askable": {}},
        "history": [], "municipality": "shibuya"})
    assert r.status_code == 422
    assert r.json()["detail"] == "invalid facts schema"


def test_extraction_json_repair_recovers_truncated_output():
    """gemini-3.5-flash occasionally emits extraction JSON with the
    trailing close-braces missing (finish_reason=STOP, observed live
    2026-07-08 with the hitorioya scenario). The content is complete, so
    bracket-balancing must recover it instead of dropping the whole turn
    to the empty fallback (which silently discards correct extractions)."""
    # exact captured live output (closing "\n}" missing)
    truncated = (
        '{\n  "claimant_birth_date": "1990-03-10",\n  "children": [\n'
        '    {\n      "birth_date": "2021-01-01"\n    },\n'
        '    {\n      "birth_date": "2024-01-01"\n    }\n  ],\n'
        '  "municipality": null,\n  "askable": {\n'
        '    "hitorioya": true,\n    "hitorioya_jiyuu": "rikon",\n'
        '    "nenshu": [\n      2000000,\n      4000000\n    ]\n  },\n'
        '  "confidence": "high",\n  "clarification_needed": null')
    got = chat_module._parse_extraction_json(truncated)
    assert got["askable"]["hitorioya"] is True
    assert got["askable"]["hitorioya_jiyuu"] == "rikon"
    assert got["claimant_birth_date"] == "1990-03-10"

    # valid JSON passes through untouched
    ok = chat_module._parse_extraction_json('{"askable": {"ninshin": true}}')
    assert ok == {"askable": {"ninshin": True}}

    # truncation inside a string value: close the string too
    got = chat_module._parse_extraction_json('{"askable": {"rishoku_jiyuu": "kai')
    assert got["askable"]["rishoku_jiyuu"] == "kai"

    # irreparable garbage / empty / non-dict fall back safely
    assert chat_module._parse_extraction_json("not json at all") == \
        {"askable": {}, "confidence": "low"}
    assert chat_module._parse_extraction_json("") == \
        {"askable": {}, "confidence": "low"}
    assert chat_module._parse_extraction_json("[1, 2") == \
        {"askable": {}, "confidence": "low"}


def test_rate_limit_bucket_keyed_by_xff_last_entry():
    """Cloud Run's front end APPENDS the real client IP to X-Forwarded-For,
    so the bucket key must be the LAST entry. The first entry is client-
    supplied and spoofable -- keying on it would let an attacker rotate
    fake IPs to bypass the cost defense entirely."""
    limiter.enabled = True
    limiter.reset()
    payload = {"facts": FACTS, "as_of": "2026-06-11",
               "municipality": "nosuchward"}
    try:
        for _ in range(40):
            r = client.post("/api/judge", json=payload,
                            headers={"X-Forwarded-For": "9.9.9.9"})
            assert r.status_code == 400
        r = client.post("/api/judge", json=payload,
                        headers={"X-Forwarded-For": "9.9.9.9"})
        assert r.status_code == 429, "same client must be limited"
        # spoofed first entry, same real (last) IP -> still the same bucket
        r = client.post("/api/judge", json=payload,
                        headers={"X-Forwarded-For": "1.2.3.4, 9.9.9.9"})
        assert r.status_code == 429, "spoofed first XFF entry must not escape the bucket"
        # different real client -> separate bucket, not limited
        r = client.post("/api/judge", json=payload,
                        headers={"X-Forwarded-For": "8.8.8.8"})
        assert r.status_code == 400, "distinct clients must get distinct buckets"
        # no header at all (local dev) -> falls back to remote address, works
        r = client.post("/api/judge", json=payload)
        assert r.status_code == 400
    finally:
        limiter.enabled = False
        limiter.reset()
