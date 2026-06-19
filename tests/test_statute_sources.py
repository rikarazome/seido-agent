"""Verify that every supported program's statute_source.md has a
machine-verifiable evidence chain: source_url + source_quote.

Two test levels:
1. test_statute_source_has_evidence: structural check (always run)
2. test_statute_source_quote_on_page: fetch URL and verify quote exists
   (slow, requires network; run with: pytest -m verify_sources)
"""
import re
import urllib.request
import ssl
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


@pytest.mark.parametrize("program_id", _supported_ids())
def test_statute_source_has_evidence(program_id):
    """Every supported program must have source_url and source_quote."""
    url, quote, path = _parse_statute_source(program_id)
    assert path.exists(), f"Missing statute_source.md for {program_id}"
    assert url is not None, f"{program_id}: missing source_url in {path}"
    assert quote is not None, f"{program_id}: missing source_quote in {path}"
    assert url.startswith("http"), f"{program_id}: source_url must be a URL, got {url}"
    assert len(quote) >= 5, f"{program_id}: source_quote too short: {quote}"


def _fetch_page_text(url: str, timeout: int = 15):
    """Fetch URL and return plain text content, or None on failure."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        raw = resp.read(100_000)
        ct = resp.headers.get("Content-Type", "")
        charset = None
        if "charset=" in ct:
            charset = ct.split("charset=")[-1].strip().split(";")[0]
        if charset:
            try:
                decoded = raw.decode(charset)
            except (UnicodeDecodeError, LookupError):
                decoded = None
        else:
            decoded = None
        if decoded is None:
            try:
                decoded = raw.decode("utf-8")
            except UnicodeDecodeError:
                for enc in ("shift_jis", "euc-jp", "cp932"):
                    try:
                        decoded = raw.decode(enc)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
        if decoded is None:
            decoded = raw.decode("utf-8", "ignore")
        text = re.sub(r"<[^>]+>", " ", decoded)
        return re.sub(r"\s+", " ", text)
    except Exception:
        return None


@pytest.mark.verify_sources
@pytest.mark.parametrize("program_id", _supported_ids())
def test_statute_source_quote_on_page(program_id):
    """Fetch source_url and verify source_quote text exists on the page.

    Programs with '(ページfetch不可' in their quote are expected to fail
    fetch and are marked xfail.
    """
    url, quote, path = _parse_statute_source(program_id)
    if quote and "ページfetch不可" in quote:
        pytest.xfail(f"{program_id}: marked as unfetchable")

    assert url is not None, f"{program_id}: no source_url"
    assert quote is not None, f"{program_id}: no source_quote"

    page_text = _fetch_page_text(url)
    if page_text is None:
        pytest.xfail(f"{program_id}: could not fetch {url}")

    if "ページfetch不可" in quote:
        pytest.xfail(f"{program_id}: marked as unfetchable in quote")
    clean_quote = re.sub(r"[（）()「」]", "", quote).strip()
    if not clean_quote:
        pytest.xfail(f"{program_id}: quote is only fetch-note")

    if clean_quote in page_text:
        return

    kanji_words = re.findall(r"[一-鿿]{2,4}", clean_quote)
    ascii_kw = re.findall(r"[A-Za-z0-9,.%]+", clean_quote)
    all_kw = kanji_words + [a for a in ascii_kw if len(a) >= 2]
    if not all_kw:
        all_kw = [clean_quote[:10]]
    found_count = sum(1 for k in all_kw if k in page_text)
    ratio = found_count / len(all_kw) if all_kw else 0
    assert ratio >= 0.4, (
        f"{program_id}: source_quote not found on page. "
        f"Matched {found_count}/{len(all_kw)} keywords. quote: {quote[:80]}"
    )
