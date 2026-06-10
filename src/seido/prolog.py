"""swipl subprocess runner for judgments (deterministic test harness core)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENGINE = (REPO / "rules" / "engine.pl").as_posix()

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
        raise PrologError(f"swipl failed (rc={proc.returncode}):\n{proc.stderr}")
    if not expect_output:
        return ""
    out = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    if not out:
        raise PrologError(f"no output from swipl:\n{proc.stderr}")
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
        raise PrologError(f"swipl failed (rc={proc.returncode}):\n{proc.stderr}")
    out = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    if not out:
        raise PrologError(f"no output from swipl:\n{proc.stderr}")
    return out[-1].strip()


def judge(facts_pl: str, program: str, rule_file: str, subject: str,
          claimant: str = "p1", timeout: int = 15) -> str:
    """Run once(Program:kettei_status(Claimant, Subject, S)); return writeq(S).

    Per the calling convention (rule-schema.md) both arguments are bound.
    A no-solution outcome is reported as error(no_solution) -- the runner
    half of the fail-safe double guard.
    """
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
                 status_term: str, claimant: str = "p1",
                 timeout: int = 15) -> bool:
    """Stage-2 re-derivation check: the GROUND status from the plain query
    must be re-derivable by the proof-tree meta-interpreter (and a different
    status must not be). Run on every golden case as a CI invariant."""
    body = (
        "main :-\n"
        f"    ( once(prove({program},\n"
        f"                 kettei_status({claimant}, {subject}, {status_term}),\n"
        "                 _))\n"
        "    -> writeq(agree) ; writeq(disagree) ),\n"
        "    nl, halt(0).\n"
    )
    return _query_driver(facts_pl, rule_file, body, timeout) == "agree"


def load_all_modules(rule_files: list[str], timeout: int = 20) -> None:
    """CI invariant: every rule module loads together without clashes."""
    goals = "".join(
        f":- use_module('{(REPO / f).as_posix()}', []).\n" for f in rule_files
    )
    _run_driver(
        f":- consult('{ENGINE}').\n{goals}main :- halt(0).\n",
        timeout, expect_output=False,
    )
