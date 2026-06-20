"""Fetch a URL and save the plain-text content as a dated snapshot.

Usage: python scripts/save_page_snapshot.py <program_id> <url>

Saves to: tests/golden/<program_id>/page_snapshot_YYYY-MM-DD.txt
The snapshot contains the full plain-text extraction of the page,
serving as reproducible evidence that the quoted text existed on
the page at the time of verification.
"""
import urllib.request, ssl, re, sys, os
from datetime import date

if len(sys.argv) < 3:
    print("Usage: python scripts/save_page_snapshot.py <program_id> <url>")
    sys.exit(1)

program_id = sys.argv[1]
url = sys.argv[2]

ctx = ssl.create_default_context()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ja,en;q=0.9",
}
req = urllib.request.Request(url, headers=headers)

try:
    resp = urllib.request.urlopen(req, timeout=20, context=ctx)
    raw = resp.read(100_000)
    ct = resp.headers.get("Content-Type", "")

    charset = None
    if "charset=" in ct:
        charset = ct.split("charset=")[-1].strip().split(";")[0]
    if charset:
        try:
            data = raw.decode(charset)
        except (UnicodeDecodeError, LookupError):
            data = None
    else:
        data = None
    if data is None:
        try:
            data = raw.decode("utf-8")
        except UnicodeDecodeError:
            for enc in ("shift_jis", "euc-jp", "cp932"):
                try:
                    data = raw.decode(enc)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
    if data is None:
        data = raw.decode("utf-8", "ignore")

    text = re.sub(r"<[^>]+>", " ", data)
    text = re.sub(r"\s+", " ", text).strip()

    out_dir = os.path.join("tests", "golden", program_id)
    os.makedirs(out_dir, exist_ok=True)
    filename = f"page_snapshot_{date.today().isoformat()}.txt"
    out_path = os.path.join(out_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"Fetched: {date.today().isoformat()}\n")
        f.write(f"Content-Type: {ct}\n")
        f.write(f"Text length: {len(text)}\n")
        f.write("---\n")
        f.write(text)

    print(f"Saved: {out_path} ({len(text)} chars)")

except Exception as e:
    print(f"FETCH ERROR: {e}")
    sys.exit(1)
