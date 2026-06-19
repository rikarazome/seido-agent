"""Verify that every supported program's statute_source.md has a
machine-verifiable evidence chain: source_url + source_quote.

This test does NOT fetch URLs (that's for periodic CI).
It checks that the required fields exist and are non-empty.
"""
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]


def _supported_ids():
    progs = yaml.safe_load((REPO / "data" / "programs.yaml").read_text(encoding="utf-8"))
    return [p["id"] for p in progs if p.get("status") == "supported"]


def _parse_statute_source(program_id: str):
    """Extract source_url and source_quote from statute_source.md."""
    path = REPO / "tests" / "golden" / program_id / "statute_source.md"
    if not path.exists():
        return None, None, path
    text = path.read_text(encoding="utf-8")
    url_match = re.search(r"source_url:\s*(\S+)", text)
    quote_match = re.search(r'source_quote:\s*"([^"]+)"', text)
    url = url_match.group(1) if url_match else None
    quote = quote_match.group(1) if quote_match else None
    return url, quote, path


@pytest.fixture(scope="module")
def supported_programs():
    return _supported_ids()


@pytest.mark.parametrize("program_id", _supported_ids())
def test_statute_source_has_evidence(program_id):
    """Every supported program must have source_url and source_quote."""
    url, quote, path = _parse_statute_source(program_id)
    assert path.exists(), f"Missing statute_source.md for {program_id}"
    assert url is not None, f"{program_id}: missing source_url in {path}"
    assert quote is not None, f"{program_id}: missing source_quote in {path}"
    assert url.startswith("http"), f"{program_id}: source_url must be a URL, got {url}"
    assert len(quote) >= 5, f"{program_id}: source_quote too short: {quote}"
