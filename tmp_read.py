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
    raw = resp.read(50000)
    ct = resp.headers.get("Content-Type", "")
    charset = None
    if "charset=" in ct:
        charset = ct.split("charset=")[-1].strip().split(";")[0]
    if charset:
        try:
            data = raw.decode(charset)
        except:
            data = None
    else:
        data = None
    if data is None:
        try:
            data = raw.decode("utf-8")
        except:
            for enc in ("shift_jis", "euc-jp"):
                try:
                    data = raw.decode(enc)
                    break
                except:
                    continue
    if data is None:
        data = raw.decode("utf-8", "ignore")
    text = re.sub(r"<[^>]+>", " ", data)
    text = re.sub(r"\s+", " ", text)
    for kw in sys.argv[2:]:
        if kw in text:
            idx = text.find(kw)
            print(f'FOUND "{kw}": {text[max(0,idx-15):idx+30]}')
        else:
            print(f'NOT FOUND: "{kw}"')
except Exception as e:
    print(f"FETCH ERROR: {e}")
