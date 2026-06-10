"""swipl subprocess runner for judgments (deterministic test harness core)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENGINE = (REPO / "rules" / "engine.pl").as_posix()


class PrologError(RuntimeError):
    pass


def judge(facts_pl: str, program: str, rule_file: str, subject: str,
          claimant: str = "p1", timeout: int = 15) -> str:
    """Run once(Program:kettei_status(Claimant, Subject, S)); return writeq(S).

    Per the calling convention (rule-schema.md) both arguments are bound.
    A no-solution outcome is reported as error(no_solution) -- the runner
    half of the fail-safe double guard.
    """
    rules = (REPO / rule_file).as_posix()
    with tempfile.TemporaryDirectory() as td:
        facts = Path(td) / "facts.pl"
        facts.write_text(facts_pl, encoding="ascii")
        driver = Path(td) / "driver.pl"
        driver.write_text(
            f":- consult('{ENGINE}').\n"
            f":- consult('{facts.as_posix()}').\n"
            f":- use_module('{rules}').\n"
            "main :-\n"
            f"    ( once({program}:kettei_status({claimant}, {subject}, S))\n"
            "    -> true ; S = error(no_solution) ),\n"
            "    writeq(S), nl, halt(0).\n",
            encoding="ascii",
        )
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


def load_all_modules(rule_files: list[str], timeout: int = 20) -> None:
    """CI invariant: every rule module loads together without clashes."""
    goals = "".join(
        f":- use_module('{(REPO / f).as_posix()}').\n" for f in rule_files
    )
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "load_all.pl"
        driver.write_text(
            f":- consult('{ENGINE}').\n{goals}"
            "main :- halt(0).\n",
            encoding="ascii",
        )
        proc = subprocess.run(
            ["swipl", "-q", "-g", "main", str(driver)],
            capture_output=True, text=True, timeout=timeout,
        )
    if proc.returncode != 0:
        raise PrologError(f"module load failed:\n{proc.stderr}")
