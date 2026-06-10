"""CI invariants (docs/dev-methodology.md): structural safety conditions."""
from pathlib import Path

import pytest

from seido.prolog import judge, load_all_modules

REPO = Path(__file__).resolve().parents[1]

SENTINEL_CAP = 999_999_999  # unbounded-range sentinel (rule-schema.md)


def _all_rule_files():
    return sorted(
        str(p.relative_to(REPO)).replace("\\", "/")
        for p in (REPO / "rules").rglob("*.pl")
        if p.name != "engine.pl"
    )


def test_all_modules_load_together():
    """Every program module must coexist in one swipl process (namespace
    isolation). CI loads ALL municipalities together even though runtime
    loads only one -- this is what catches missing municipal prefixes."""
    load_all_modules(_all_rule_files())


@pytest.mark.parametrize("program", ["jidou_teate", "jidou_fuyou_teate"])
def test_structural_guard_missing_ages(program):
    """Structural facts missing (mapping-layer bug) must surface as an
    error card, never as a wrong ineligible: bare NAF over structural
    facts in the ineligible clauses succeeds when the facts are ABSENT,
    which without a guard turns 'ages unknown' into 'child past FY-end
    age 18'. Hand-written facts bypass factgen's birth_date requirement
    to simulate exactly that bug."""
    facts = (
        ":- dynamic claimant/1, child/1, kango_by/2, seikei_futan/2, "
        "age/2, age_nendo_matsu/2.\n"
        "claimant(p1).\nchild(c1).\nkango_by(c1, p1).\nseikei_futan(p1, c1).\n"
    )
    got = judge(facts, program=program,
                rule_file=f"rules/national/{program}.pl", subject="c1")
    assert got == "error(structural_facts_missing)"


def test_no_limit_reaches_sentinel():
    """Income limits must stay far below the unbounded-range sentinel.
    Static check on rule sources: any literal >= the sentinel would break
    the range(Lo, 999999999) convention silently."""
    import re

    for f in _all_rule_files():
        text = (REPO / f).read_text(encoding="ascii")
        for num in re.findall(r"\b\d{7,}\b", text):
            assert int(num) < SENTINEL_CAP, f"{f}: literal {num} >= sentinel"
