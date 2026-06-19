import urllib.request, ssl, re, sys
ctx = ssl.create_default_context()
url = sys.argv[1]
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ja,en;q=0.9",
}
req = urllib.request.Request(url, headers=headers)
try:
    resp = urllib.request.urlopen(req, timeout=20, context=ctx)
    raw = resp.read(80000)
    try:
        data = raw.decode("utf-8")
    except:
        for enc in ("shift_jis", "euc-jp"):
            try:
                data = raw.decode(enc)
                break
            except:
                continue
        else:
            data = raw.decode("utf-8", "ignore")
    text = re.sub(r"<[^>]+>", " ", data)
    text = re.sub(r"\s+", " ", text)
    # Print relevant sections
    for kw in sys.argv[2:]:
        idx = text.find(kw)
        if idx >= 0:
            print(f'=== {kw} ===')
            print(text[max(0, idx - 30):idx + 200])
            print()
    if len(sys.argv) == 2:
        print(text[:500])
except Exception as e:
    print(f"FETCH ERROR: {e}")
