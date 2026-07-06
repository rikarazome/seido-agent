"""swipl subprocess runner for judgments (deterministic test harness core)."""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from .factgen import CLAIMANT as _DEFAULT_CLAIMANT, _validate_atom

REPO = Path(__file__).resolve().parents[2]
ENGINE = (REPO / "rules" / "engine.pl").as_posix()

log = logging.getLogger(__name__)

# stderr may echo consulted file content (generated facts: birth dates,
# income) on pathological failures. Log a 300-char head only -- enough for
# file:line + error kind -- and never put stderr in exception messages.
_STDERR_CAP = 300

# Halt on load-time errors: without this, a syntax error in generated facts
# only prints to stderr and swipl continues with a PARTIAL fact set, so a
# judgment over broken facts would be reported as a legitimate result.
# Wrapped in catch/3 for SWI versions without the on_error flag.
_ON_ERROR = ":- catch(set_prolog_flag(on_error, halt), _, true).\n"


class PrologError(RuntimeError):
    pass


def _run_driver(driver_text: str, timeout: int, expect_output: bool) -> str:
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "driver.pl"
        driver.write_text(_ON_ERROR + driver_text, encoding="ascii")
        proc = subprocess.run(
            ["swipl", "-q", "-g", "main", str(driver)],
            capture_output=True, text=True, timeout=timeout,
        )
    if proc.returncode != 0:
        log.error("swipl failed rc=%d: %s",
                  proc.returncode, proc.stderr[:_STDERR_CAP])
        raise PrologError("prolog execution failed")
    if not expect_output:
        return ""
    out = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    if not out:
        log.error("no output from swipl: %s", proc.stderr[:_STDERR_CAP])
        raise PrologError("prolog produced no output")
    return out[-1].strip()


def _query_driver(facts_pl: str, rule_file: str, body: str, timeout: int) -> str:
    rules = (REPO / rule_file).as_posix()
    with tempfile.TemporaryDirectory() as td:
        facts = Path(td) / "facts.pl"
        facts.write_text(facts_pl, encoding="ascii")
        driver_text = (
            f":- consult('{ENGINE}').\n"
            f":- consult('{facts.as_posix()}').\n"
            # empty import list: queries are module-qualified, and importing
            # exports would clash across programs (kettei_status/3 et al.)
            f":- use_module('{rules}', []).\n"
            f"{body}"
        )
        # facts file must outlive the subprocess: run inside this context
        driver = Path(td) / "driver.pl"
        driver.write_text(_ON_ERROR + driver_text, encoding="ascii")
        proc = subprocess.run(
            ["swipl", "-q", "-g", "main", str(driver)],
            capture_output=True, text=True, timeout=timeout,
        )
    if proc.returncode != 0:
        log.error("swipl failed rc=%d: %s",
                  proc.returncode, proc.stderr[:_STDERR_CAP])
        raise PrologError("prolog execution failed")
    out = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    if not out:
        log.error("no output from swipl: %s", proc.stderr[:_STDERR_CAP])
        raise PrologError("prolog produced no output")
    return out[-1].strip()


def judge(facts_pl: str, program: str, rule_file: str, subject: str,
          claimant: str = _DEFAULT_CLAIMANT, timeout: int = 15) -> str:
    """Run once(Program:kettei_status(Claimant, Subject, S)); return writeq(S).

    Per the calling convention (rule-schema.md) both arguments are bound.
    A no-solution outcome is reported as error(no_solution) -- the runner
    half of the fail-safe double guard.
    """
    _validate_atom(program)
    _validate_atom(subject)
    _validate_atom(claimant)
    body = (
        "main :-\n"
        f"    ( once({program}:kettei_status({claimant}, {subject}, S))\n"
        "    -> true ; S = error(no_solution) ),\n"
        "    writeq(S), nl, halt(0).\n"
    )
    return _query_driver(facts_pl, rule_file, body, timeout)


def query_value(facts_pl: str, program: str, rule_file: str, goal: str,
                var: str = "A", timeout: int = 15) -> str:
    """Run once(Program:Goal) and return writeq of Var (e.g. teate_amount(p1, A))."""
    body = (
        "main :-\n"
        f"    ( once({program}:{goal})\n"
        f"    -> true ; {var} = no_solution ),\n"
        f"    writeq({var}), nl, halt(0).\n"
    )
    return _query_driver(facts_pl, rule_file, body, timeout)


def proof_agrees(facts_pl: str, program: str, rule_file: str, subject: str,
                 status_term: str, claimant: str = _DEFAULT_CLAIMANT,
                 timeout: int = 15) -> bool:
    """Stage-2 re-derivation check: the GROUND status from the plain query
    must be re-derivable by the proof-tree meta-interpreter (and a different
    status must not be). Run on every golden case as a CI invariant."""
    _validate_atom(program)
    _validate_atom(subject)
    _validate_atom(claimant)
    body = (
        "main :-\n"
        f"    ( once(prove({program},\n"
        f"                 kettei_status({claimant}, {subject}, {status_term}),\n"
        "                 _))\n"
        "    -> writeq(agree) ; writeq(disagree) ),\n"
        "    nl, halt(0).\n"
    )
    return _query_driver(facts_pl, rule_file, body, timeout) == "agree"


def query_proof(facts_pl: str, program: str, rule_file: str, subject: str,
                status_term: str, claimant: str = _DEFAULT_CLAIMANT,
                timeout: int = 15) -> str:
    """Stage-2 re-derivation returning the proof tree term (writeq).

    status_term must come from a server-side judge() call, never from the
    client (no user input may reach Prolog source -- security rule)."""
    _validate_atom(program)
    _validate_atom(subject)
    _validate_atom(claimant)
    body = (
        "main :-\n"
        f"    ( once(prove({program},\n"
        f"                 kettei_status({claimant}, {subject}, {status_term}),\n"
        "                 Proof))\n"
        "    -> writeq(Proof) ; writeq(disagree) ),\n"
        "    nl, halt(0).\n"
    )
    return _query_driver(facts_pl, rule_file, body, timeout)


def judge_batch(facts_pl: str,
                queries: list[tuple[str, str, str]],
                claimant: str = _DEFAULT_CLAIMANT,
                timeout: int = 60) -> list[dict]:
    """Judge multiple (program_id, rule_file, subject) in one swipl process.

    Returns list of {"program": id, "subject": s, "status": term,
                     "proof": proof_term_or_none} in the same order as queries.
    """
    if not queries:
        return []
    for pid, _rf, subj in queries:
        _validate_atom(pid)
        _validate_atom(subj)
    _validate_atom(claimant)

    rule_files_set = sorted({rf for _, rf, _ in queries})
    loads = "".join(
        f":- use_module('{(REPO / rf).as_posix()}', []).\n"
        for rf in rule_files_set
    )

    judge_clauses = []
    for pid, _rf, subj in queries:
        judge_clauses.append(
            f"    judge_one({pid}, {subj})"
        )

    body = (
        "judge_one(Mod, Subj) :-\n"
        f"    ( once(Mod:kettei_status({claimant}, Subj, S))\n"
        "    -> true ; S = error(no_solution) ),\n"
        "    write('<<SEP>>'), write(Mod), write('|'), write(Subj), nl,\n"
        "    writeq(S), nl,\n"
        "    ( S = decided(_)\n"
        f"    -> ( once(prove(Mod, kettei_status({claimant}, Subj, S), Proof))\n"
        "       -> writeq(Proof) ; write(no_proof) )\n"
        "    ;  write(none) ), nl.\n"
        "\n"
        "main :-\n"
        + ",\n".join(judge_clauses)
        + ",\n    halt(0).\n"
    )

    with tempfile.TemporaryDirectory() as td:
        facts_f = Path(td) / "facts.pl"
        facts_f.write_text(facts_pl, encoding="ascii")
        driver_text = (
            f":- consult('{ENGINE}').\n"
            f":- consult('{facts_f.as_posix()}').\n"
            + loads
            + body
        )
        driver = Path(td) / "driver.pl"
        driver.write_text(_ON_ERROR + driver_text, encoding="ascii")
        proc = subprocess.run(
            ["swipl", "-q", "-g", "main", str(driver)],
            capture_output=True, text=True, timeout=timeout,
        )
    if proc.returncode != 0:
        log.error("swipl batch failed rc=%d: %s",
                  proc.returncode, proc.stderr[:_STDERR_CAP])
        raise PrologError("prolog execution failed")

    results = []
    blocks = proc.stdout.split("<<SEP>>")
    for block in blocks[1:]:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        header = lines[0].strip()
        parts = header.split("|", 1)
        pid, subj = parts[0].strip(), parts[1].strip()
        status = lines[1].strip()
        proof = lines[2].strip() if len(lines) > 2 else "none"
        results.append({
            "program": pid, "subject": subj,
            "status": status, "proof": proof,
        })
    return results


def load_all_modules(rule_files: list[str], timeout: int = 20) -> None:
    """CI invariant: every rule module loads together without clashes."""
    goals = "".join(
        f":- use_module('{(REPO / f).as_posix()}', []).\n" for f in rule_files
    )
    _run_driver(
        f":- consult('{ENGINE}').\n{goals}main :- halt(0).\n",
        timeout, expect_output=False,
    )
