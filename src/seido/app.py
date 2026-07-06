"""FastAPI app: stateless judgment API + Gemini chat (docs/specs/architecture.md).

/api/judge: deterministic Prolog judgment (no LLM, 0 yen)
/api/chat:  Gemini fact extraction + Prolog judgment + Gemini response
No facts or user text are logged anywhere in this module.
"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import logging
import subprocess
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .factgen import facts_to_prolog
from .prolog import PrologError, judge, query_proof
from .runner import judge_request, municipalities, programs, rule_file

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))
MAX_FACTS_BYTES = 10_000

app = FastAPI(title="seido-agent", docs_url=None, redoc_url=None)

# IP-based rate limiting (in-memory; per-instance on Cloud Run, acceptable).
# NOTE for Cloud Run deploy: behind the proxy get_remote_address returns the
# proxy IP -- switch key_func to the first X-Forwarded-For entry then.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
    """Liveness: verify swipl actually starts (the app is useless without it).
    swipl startup is ~40ms, negligible for health-check traffic."""
    try:
        proc = subprocess.run(
            ["swipl", "-q", "-g", "halt", "-t", "halt"],
            capture_output=True, timeout=5)
        if proc.returncode != 0:
            raise RuntimeError
        return {"ok": True}
    except Exception:
        raise HTTPException(503, "swipl unavailable")


@app.get("/api/municipalities")
def api_municipalities():
    return {"municipalities": [{"id": m["id"], "name": m["name"]}
                               for m in municipalities().values()]}


@app.post("/api/judge")
@limiter.limit("40/minute")
def api_judge(request: Request, req: JudgeRequest):
    _guard_size(req)
    if req.municipality not in municipalities():
        raise HTTPException(400, "unknown municipality")
    t0 = time.monotonic()
    try:
        result = judge_request(req.facts, _parse_as_of(req.as_of),
                               municipality=req.municipality)
    except ValueError:
        raise HTTPException(422, "invalid facts schema")
    except PrologError:
        log.exception("judgment failed")
        raise HTTPException(500, "judgment failed")
    # privacy rule: log aggregates only, never facts
    kinds = [r["status"] for r in result["results"]]
    log.info("judge: municipality=%s programs=%d decided=%d blocked=%d "
             "ineligible=%d duration_ms=%d",
             req.municipality, len(kinds), kinds.count("decided"),
             kinds.count("blocked"), kinds.count("ineligible"),
             int((time.monotonic() - t0) * 1000))
    return result


@app.post("/api/proof")
@limiter.limit("20/minute")
def api_proof(request: Request, req: ProofRequest):
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
    try:
        status = judge(facts_pl, req.program, rf, req.subject)
        proof = query_proof(facts_pl, req.program, rf, req.subject, status)
    except PrologError:
        log.exception("proof failed")
        raise HTTPException(500, "judgment failed")
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
@limiter.limit("5/minute")
def api_chat(request: Request, req: ChatRequest):
    """One chat turn: Gemini extraction → Prolog judgment → Gemini response."""
    if len(req.message) > MAX_CHAT_MESSAGE:
        raise HTTPException(413, "message too long")
    if len(req.history) > MAX_CHAT_HISTORY * 2:
        req.history = req.history[-(MAX_CHAT_HISTORY * 2):]
    if req.municipality not in municipalities():
        raise HTTPException(400, "unknown municipality")
    _guard_size(req)
    t0 = time.monotonic()
    try:
        from .chat import chat_turn
        result = chat_turn(
            message=req.message,
            facts=req.facts,
            history=req.history,
            municipality=req.municipality,
            as_of=_parse_as_of(req.as_of),
        )
    except PrologError:              # RuntimeError subclass -- must come first
        log.exception("judgment failed in chat")
        raise HTTPException(500, "judgment failed")
    except RuntimeError:             # missing GEMINI_API_KEY / google-genai
        log.exception("chat not configured")
        raise HTTPException(503, "chat is not configured")
    except Exception:
        log.exception("chat_turn failed")
        raise HTTPException(500, "internal error in chat engine")
    # privacy rule: never log message content or extracted facts
    log.info("chat: municipality=%s duration_ms=%d",
             req.municipality, int((time.monotonic() - t0) * 1000))
    return result


# static frontend, same origin (no CORS needed) -- mounted last so the
# /api and /healthz routes above take precedence
_WEB = Path(__file__).resolve().parents[2] / "web"
app.mount("/", StaticFiles(directory=str(_WEB), html=True), name="static")
