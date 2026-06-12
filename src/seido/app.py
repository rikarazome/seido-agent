"""FastAPI app: stateless judgment API (docs/specs/architecture.md).

LLM-free endpoints only; /api/chat (Gemini free-text extraction) is added
with the ADK integration. No facts are logged anywhere in this module.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .factgen import facts_to_prolog
from .prolog import judge, query_proof
from .runner import judge_request, programs, rule_file

JST = timezone(timedelta(hours=9))
MAX_FACTS_BYTES = 10_000

app = FastAPI(title="seido-agent", docs_url=None, redoc_url=None)


class JudgeRequest(BaseModel):
    facts: dict
    as_of: Optional[str] = None
    municipality: str = "shibuya"


class ProofRequest(BaseModel):
    facts: dict
    as_of: Optional[str] = None
    municipality: str = "shibuya"
    program: str
    subject: str


def _parse_as_of(raw: "Optional[str]") -> date:
    if raw is None:
        return datetime.now(JST).date()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(422, "as_of must be YYYY-MM-DD")


def _guard_size(req: BaseModel) -> None:
    if len(req.model_dump_json()) > MAX_FACTS_BYTES:
        raise HTTPException(413, "facts payload too large")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/api/judge")
def api_judge(req: JudgeRequest):
    _guard_size(req)
    try:
        return judge_request(req.facts, _parse_as_of(req.as_of),
                             municipality=req.municipality)
    except ValueError as e:  # schema violations from factgen
        raise HTTPException(422, str(e))


@app.post("/api/proof")
def api_proof(req: ProofRequest):
    """Proof tree for one (program, subject). The status term is recomputed
    server-side -- the client never supplies Prolog text (security rule)."""
    _guard_size(req)
    meta = next((p for p in programs() if p["id"] == req.program), None)
    if meta is None or meta.get("status") != "supported":
        raise HTTPException(404, "unknown or unsupported program")
    if req.subject != "self" and not req.subject.startswith("c"):
        raise HTTPException(422, "bad subject")
    try:
        facts_pl = facts_to_prolog(req.facts, _parse_as_of(req.as_of))
    except (ValueError, KeyError) as e:
        raise HTTPException(422, str(e))
    rf = rule_file(meta)
    status = judge(facts_pl, req.program, rf, req.subject)
    proof = query_proof(facts_pl, req.program, rf, req.subject, status)
    return {"program": req.program, "subject": req.subject,
            "status": status, "proof": proof}


# static frontend, same origin (no CORS needed) -- mounted last so the
# /api and /healthz routes above take precedence
_WEB = Path(__file__).resolve().parents[2] / "web"
app.mount("/", StaticFiles(directory=str(_WEB), html=True), name="static")
