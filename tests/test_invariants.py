"""CI invariants (docs/dev-methodology.md): structural safety conditions."""
from pathlib import Path

from seido.prolog import load_all_modules

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


def test_no_limit_reaches_sentinel():
    """Income limits must stay far below the unbounded-range sentinel.
    Static check on rule sources: any literal >= the sentinel would break
    the range(Lo, 999999999) convention silently."""
    import re

    for f in _all_rule_files():
        text = (REPO / f).read_text(encoding="ascii")
        for num in re.findall(r"\b\d{7,}\b", text):
            assert int(num) < SENTINEL_CAP, f"{f}: literal {num} >= sentinel"
