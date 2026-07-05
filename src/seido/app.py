"""FastAPI app: stateless judgment API + Gemini chat (docs/specs/architecture.md).

/api/judge: deterministic Prolog judgment (no LLM, 0 yen)
/api/chat:  Gemini fact extraction + Prolog judgment + Gemini response
No facts or user text are logged anywhere in this module.
"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .factgen import facts_to_prolog
from .prolog import judge, query_proof
from .runner import judge_request, municipalities, programs, rule_file

log = logging.getLogger(__name__)

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
        d = date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(422, "as_of must be YYYY-MM-DD")
    if not (date(2020, 1, 1) <= d <= date(2100, 12, 31)):
        raise HTTPException(422, "as_of out of supported range")
    return d


def _guard_size(req: BaseModel) -> None:
    if len(req.model_dump_json()) > MAX_FACTS_BYTES:
        raise HTTPException(413, "facts payload too large")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/municipalities")
def api_municipalities():
    return {"municipalities": [{"id": m["id"], "name": m["name"]}
                               for m in municipalities().values()]}


@app.post("/api/judge")
def api_judge(req: JudgeRequest):
    _guard_size(req)
    if req.municipality not in municipalities():
        raise HTTPException(400, "unknown municipality")
    try:
        return judge_request(req.facts, _parse_as_of(req.as_of),
                             municipality=req.municipality)
    except ValueError:
        raise HTTPException(422, "invalid facts schema")


@app.post("/api/proof")
def api_proof(req: ProofRequest):
    """Proof tree for one (program, subject). The status term is recomputed
    server-side -- the client never supplies Prolog text (security rule)."""
    _guard_size(req)
    meta = next((p for p in programs() if p["id"] == req.program), None)
    if meta is None or meta.get("status") != "supported":
        raise HTTPException(404, "unknown or unsupported program")
    if req.subject != "self" and not (
        req.subject.startswith("c") and req.subject[1:].isdigit()
    ):
        raise HTTPException(422, "subject must be 'self' or 'c<N>'")
    try:
        facts_pl = facts_to_prolog(req.facts, _parse_as_of(req.as_of))
    except (ValueError, KeyError):
        raise HTTPException(422, "invalid facts schema")
    rf = rule_file(meta)
    status = judge(facts_pl, req.program, rf, req.subject)
    proof = query_proof(facts_pl, req.program, rf, req.subject, status)
    return {"program": req.program, "subject": req.subject,
            "status": status, "proof": proof}


class ChatRequest(BaseModel):
    message: str
    facts: dict
    history: list = []
    municipality: str = "shibuya"
    as_of: Optional[str] = None


MAX_CHAT_MESSAGE = 500
MAX_CHAT_HISTORY = 8


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    """One chat turn: Gemini extraction → Prolog judgment → Gemini response."""
    if len(req.message) > MAX_CHAT_MESSAGE:
        raise HTTPException(413, "message too long")
    if len(req.history) > MAX_CHAT_HISTORY * 2:
        req.history = req.history[-(MAX_CHAT_HISTORY * 2):]
    if req.municipality not in municipalities():
        raise HTTPException(400, "unknown municipality")
    _guard_size(req)
    try:
        from .chat import chat_turn
        return chat_turn(
            message=req.message,
            facts=req.facts,
            history=req.history,
            municipality=req.municipality,
            as_of=_parse_as_of(req.as_of),
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception:
        log.exception("chat_turn failed")
        raise HTTPException(500, "internal error in chat engine")


# static frontend, same origin (no CORS needed) -- mounted last so the
# /api and /healthz routes above take precedence
_WEB = Path(__file__).resolve().parents[2] / "web"
app.mount("/", StaticFiles(directory=str(_WEB), html=True), name="static")
