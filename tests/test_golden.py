"""Golden tests: deterministic, zero LLM calls (PR-stage CI gate).

Each case is the v1 facts JSON plus a fixed as_of date; expectation is the
exact writeq/1 rendering of kettei_status/3's third argument.
Never rewrite an expectation to make a rule pass -- fix the rule, or change
the case WITH the statute source in the same commit (see CLAUDE.md).
"""
from datetime import date
from pathlib import Path

import pytest
import yaml

from seido.factgen import facts_to_prolog
from seido.prolog import judge, query_value

GOLDEN = Path(__file__).resolve().parent / "golden"


def _collect():
    for prog_dir in sorted(p for p in GOLDEN.iterdir() if p.is_dir()):
        cases_file = prog_dir / "cases.yaml"
        if not cases_file.exists():
            continue
        cases = yaml.safe_load(cases_file.read_text(encoding="utf-8"))
        for case in cases:
            yield prog_dir.name, case


PARAMS = list(_collect())


@pytest.mark.parametrize(
    "program,case", PARAMS, ids=[c["name"] for _, c in PARAMS]
)
def test_golden(program, case):
    facts_pl = facts_to_prolog(case["facts"], date.fromisoformat(case["as_of"]))
    exp = case["expect"]
    rule_file = f"rules/national/{program}.pl"
    got = judge(facts_pl, program=program, rule_file=rule_file,
                subject=exp["subject"])
    assert got == f"{exp['status']}({exp['detail']})"
    if "amount" in exp:
        # household monthly amount (per_household programs, teate_amount/2)
        got_amount = query_value(facts_pl, program=program,
                                 rule_file=rule_file,
                                 goal="teate_amount(p1, A)")
        assert got_amount == str(exp["amount"])
