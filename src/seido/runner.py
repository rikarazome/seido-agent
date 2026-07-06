"""/api/judge runner: evaluate all programs, aggregate, pick next question.

Everything here is deterministic (no LLM): facts -> Prolog -> per-subject
statuses -> program cards -> headline -> next_question, per the rules in
docs/specs/architecture.md.
"""
from __future__ import annotations

import copy
import logging
import re
import time
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

from .factgen import CHILD_ASKABLE_PREDS, CLAIMANT, facts_to_prolog, salary_to_shotoku
from .prolog import PrologError, judge, judge_batch, query_proof, query_value

REPO = Path(__file__).resolve().parents[2]

log = logging.getLogger(__name__)

_STATUS_RE = re.compile(r"^(decided|blocked|ineligible|error)\((.*)\)$")
_DETAIL_RE = re.compile(r"^(\w+)\((\w+)\)$")
_KNOWN_RE = re.compile(r"known\((\w+)\((\w+)\),\s*([^)]+)\)")


@lru_cache(maxsize=1)
def programs() -> list[dict]:
    return yaml.safe_load(
        (REPO / "data" / "programs.yaml").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def questions() -> list[dict]:
    return yaml.safe_load(
        (REPO / "data" / "questions.yaml").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def municipalities() -> dict[str, dict]:
    rows = yaml.safe_load(
        (REPO / "data" / "municipalities.yaml").read_text(encoding="utf-8"))
    return {m["id"]: m for m in rows}


@lru_cache(maxsize=1)
def _fact_to_askable() -> dict[str, str]:
    """Derive fact->askable_key mapping from questions.yaml (non-identity only).

    questions.yaml is the single source of truth for askable_key overrides;
    this avoids a second hardcoded copy that can silently drift."""
    return {q["fact"]: q["askable_key"]
            for q in questions() if "askable_key" in q}


def rule_file(meta: dict) -> str:
    if meta["layer"] == "national":
        return f"rules/national/{meta['id']}.pl"
    return f"rules/municipal/{meta['municipality']}/{meta['id']}.pl"


def _applicable(meta: dict, municipality: str) -> bool:
    if meta["layer"] == "national":
        return True
    parents = municipalities()[municipality].get("parents") or []
    return meta["municipality"] in [municipality, *parents]


def _parse_status(raw: str) -> dict:
    m = _STATUS_RE.match(raw)
    if not m:
        return {"kind": "error", "reason": f"unparseable: {raw}"}
    kind, inner = m.group(1), m.group(2)
    if kind == "blocked":
        body = inner.strip()[1:-1]  # strip [ ]
        missing = [x.strip() for x in body.split(",")] if body else []
        return {"kind": kind, "missing": missing}
    if kind in ("ineligible", "error"):
        return {"kind": kind, "reason": inner.strip("'")}
    md = _DETAIL_RE.match(inner)  # decided
    if md and md.group(2).isdigit():
        return {"kind": kind, "detail": inner,
                "func": md.group(1), "yen": int(md.group(2))}
    return {"kind": kind, "detail": inner, "func": inner, "yen": None}


_AGE_RE = re.compile(r"node\((age_nendo_matsu|age)\((\w+),(\d+)\),true\)")

def _extract_used_facts(proof_str: str) -> list[dict]:
    """Extract facts actually used in proof tree."""
    results = []
    seen = set()
    for m in _KNOWN_RE.finditer(proof_str):
        pred, subj, val = m.group(1), m.group(2), m.group(3)
        key = f"known:{pred}"
        if key in seen:
            continue
        seen.add(key)
        results.append({"fact": pred, "subject": subj, "value": val.strip()})
    for m in _AGE_RE.finditer(proof_str):
        pred, subj, val = m.group(1), m.group(2), m.group(3)
        key = f"age:{pred}:{subj}"
        if key in seen:
            continue
        seen.add(key)
        results.append({"fact": pred, "subject": subj, "value": val})
    return results


def _household_amount(meta, facts, facts_pl, as_of):
    """per_household amount via teate_amount/2; two-point taper evaluation
    when income is only known as a range (architecture.md)."""
    rf = rule_file(meta)
    goal = f"teate_amount({CLAIMANT}, A)"
    try:
        got = query_value(facts_pl, meta["id"], rf, goal)
    except PrologError:
        return None
    if got.isdigit():
        return {"type": meta["amount_type"], "yen": int(got)}
    nenshu = (facts.get("askable") or {}).get("nenshu")
    if not isinstance(nenshu, list):
        return None
    amounts = []
    for endpoint in (salary_to_shotoku(nenshu[0]), salary_to_shotoku(nenshu[1])):
        f2 = copy.deepcopy(facts)
        f2.setdefault("askable", {})["shotoku_exact"] = endpoint
        a = query_value(facts_to_prolog(f2, as_of),
                        meta["id"], rf, goal)
        if not a.isdigit():
            return None
        amounts.append(int(a))
    return {"type": meta["amount_type"],
            "yen_min": min(amounts), "yen_max": max(amounts)}


def _aggregate(meta, subj_results, facts, facts_pl, as_of):
    card = {"program": meta["id"], "name": meta["name"],
            "description": meta.get("description") or "",
            "children": subj_results,
            "statute": meta.get("statute") or []}
    kinds = [s["kind"] for s in subj_results]
    decided_yen = sum(s["yen"] or 0 for s in subj_results
                      if s["kind"] == "decided")
    if "error" in kinds:
        card["status"] = "error"
    elif "blocked" in kinds:
        card["status"] = "blocked"
        missing = sorted({f for s in subj_results if s["kind"] == "blocked"
                          for f in s["missing"]})
        card["missing"] = missing
        if decided_yen:
            card["partial_amount"] = {"type": meta["amount_type"],
                                      "yen": decided_yen}
    elif "decided" in kinds:
        card["status"] = "decided"
        if meta["amount_type"] == "in_kind":
            card["amount"] = {"type": "in_kind"}
        elif meta["unit"] == "per_household" and any(
                s["yen"] is None for s in subj_results if s["kind"] == "decided"):
            kubuns = {s["detail"] for s in subj_results
                      if s["kind"] == "decided"}
            if len(kubuns) > 1:
                card["status"] = "error"
                card["reason"] = "inconsistent_household_kubun"
            else:
                card["amount"] = _household_amount(meta, facts, facts_pl,
                                                   as_of)
        else:
            card["amount"] = {"type": meta["amount_type"], "yen": decided_yen}
        first_decided = next(s for s in subj_results if s["kind"] == "decided")
        proof = first_decided.get("_proof", "")
        if proof and proof not in ("none", "no_proof"):
            card["used_facts"] = _extract_used_facts(proof)
        else:
            try:
                proof = query_proof(facts_pl, meta["id"], rule_file(meta),
                                    first_decided["subject"], first_decided["raw"])
                card["used_facts"] = _extract_used_facts(proof)
            except PrologError:
                card["used_facts"] = []
    else:
        card["status"] = "ineligible"
        card["reason"] = next(s["reason"] for s in subj_results
                              if s["kind"] == "ineligible")
    return card


def _headline(results):
    h = {"monthly_yen": 0, "oneoff_yen": 0, "yearly_yen": 0, "in_kind_count": 0}
    for r in results:
        amount = r.get("amount")
        if r["status"] != "decided" or not amount:
            continue
        if amount["type"] == "in_kind":
            h["in_kind_count"] += 1
            continue
        # lower bound for ranges -- never overstate (trust design)
        yen = amount.get("yen", amount.get("yen_min", 0))
        h[f"{amount['type']}_yen"] += yen
    return h


def _pending_children(fact, facts):
    """Children for which a per-child askable is still unanswered
    (None = pending; \"declined\" = asked and refused, not pending)."""
    out = []
    for i, ch in enumerate(facts.get("children") or [], start=1):
        cid = ch.get("id") or f"c{i}"
        if (ch.get("askable") or {}).get(fact) is None:
            out.append((cid, ch))
    return out


def _question_for(fact, why, facts):
    qmeta = next((q for q in questions() if q["fact"] == fact), None)
    if qmeta is None:
        return None
    q = {"fact": fact,
         "askable_key": qmeta.get("askable_key", fact),
         "text": qmeta["text"], "why": sorted(why),
         "allow_free_text": True, "choices": []}
    qtype = qmeta["type"]
    if qmeta.get("scope") == "per_child":
        pend = _pending_children(fact, facts)
        if not pend:
            return None
        cid, ch = pend[0]
        q["child"] = cid
        year = ch["birth_date"][:4]
        q["text"] = qmeta["text"].replace("{child}", f"{year}年生まれのお子さん")
    if qtype == "boolean":
        q["choices"] = [{"value": True, "label": "はい"},
                        {"value": False, "label": "いいえ"}]
    elif qtype == "enum":
        order = qmeta.get("primary", list(qmeta["choices"]))
        q["choices"] = [{"value": v, "label": qmeta["choices"][v]}
                        for v in order]
        q["choices"].append({"value": "__free_text__", "label": "その他"})
    elif qtype == "integer":
        q["choices"] = [{"value": v, "label": str(v)}
                        for v in qmeta["choices"]]
    elif qtype == "range_choice":
        q["choices"] = [dict(c) for c in qmeta["choices"]]
    elif qtype == "integer_input":
        q["input"] = "number"
    q["choices"].append({"value": "declined", "label": "わからない / 答えたくない"})
    return q


def _next_question(results, facts):
    askable = facts.get("askable") or {}
    candidates: dict[str, set] = {}
    for r in results:
        if r.get("status") != "blocked":
            continue
        for fact in r.get("missing", []):
            key = _fact_to_askable().get(fact, fact)
            if fact in CHILD_ASKABLE_PREDS:
                if not _pending_children(fact, facts):
                    continue  # every child answered or declined
            elif askable.get(key) == "declined":
                continue
            candidates.setdefault(fact, set()).add(r["program"])
    if not candidates:
        return None
    potential = {p["id"]: p.get("potential_amount") or 0 for p in programs()}
    order = {q["fact"]: i for i, q in enumerate(questions())}
    best = sorted(
        candidates.items(),
        key=lambda kv: (-len(kv[1]),
                        -sum(potential[p] for p in kv[1]),
                        order.get(kv[0], 999)),
    )
    for fact, why in best:
        q = _question_for(fact, why, facts)
        if q is not None:
            return q
    return None


def judge_request(facts: dict, as_of: date,
                  municipality: str = "shibuya") -> dict:
    if municipality not in municipalities():
        raise ValueError(f"unknown municipality: {municipality}")
    facts_pl = facts_to_prolog(facts, as_of)
    children = [c.get("id") or f"c{i}"
                for i, c in enumerate(facts.get("children") or [], start=1)]

    # Build query list and track non-queryable programs
    results = []
    batch_queries = []  # (program_id, rule_file, subject)
    batch_meta = []     # (meta, subject) parallel to batch_queries
    for meta in programs():
        if not _applicable(meta, municipality):
            continue
        if meta["status"] != "supported":
            results.append({"program": meta["id"], "name": meta["name"],
                            "status": "unsupported"})
            continue
        subjects = ["self"] if meta["subject"] == "claimant" else children
        if not subjects:
            results.append({"program": meta["id"], "name": meta["name"],
                            "status": "ineligible",
                            "reason": "no_eligible_subject"})
            continue
        for s in subjects:
            batch_queries.append((meta["id"], rule_file(meta), s))
            batch_meta.append((meta, s))

    # Single swipl process for all judgments + proof trees
    if batch_queries:
        t0 = time.monotonic()
        batch_results = judge_batch(facts_pl, batch_queries)
        log.info("prolog batch: size=%d duration_ms=%d",
                 len(batch_queries), int((time.monotonic() - t0) * 1000))
        br_lookup = {}
        for br in batch_results:
            br_lookup.setdefault(br["program"], []).append(br)
        expected_subjects = {}
        for m2, s in batch_meta:
            expected_subjects.setdefault(m2["id"], []).append(s)

        seen_programs = set()
        for meta, _s in batch_meta:
            if meta["id"] in seen_programs:
                continue
            seen_programs.add(meta["id"])
            raw_list = br_lookup.get(meta["id"], [])
            subj_results = []
            for br in raw_list:
                parsed = _parse_status(br["status"])
                parsed["subject"] = br["subject"]
                parsed["raw"] = br["status"]
                parsed["_proof"] = br.get("proof", "none")
                subj_results.append(parsed)
            expected = expected_subjects[meta["id"]]
            if len(subj_results) == len(expected):
                results.append(_aggregate(meta, subj_results, facts,
                                          facts_pl, as_of))
            else:
                # fail safe: missing or partial batch results must never be
                # aggregated as a complete judgment or vanish silently --
                # surface a visible error card instead (UI: 要窓口確認)
                log.error("batch results for program=%s: got %d of %d "
                          "subjects", meta["id"], len(subj_results),
                          len(expected))
                results.append({"program": meta["id"], "name": meta["name"],
                                "status": "error",
                                "reason": "no_batch_result"})

    return {"headline": _headline(results), "results": results,
            "next_question": _next_question(results, facts)}
