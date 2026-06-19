import urllib.request, ssl, re, sys
ctx = ssl.create_default_context()
url = sys.argv[1]
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=15, context=ctx).read(100000).decode('utf-8', 'ignore')
text = re.sub(r'<[^>]+>', ' ', data)
text = re.sub(r'\s+', ' ', text)
keywords = sys.argv[2:]
for kw in keywords:
    idx = text.find(kw)
    if idx >= 0:
        print(f'=== {kw} ===')
        print(text[max(0, idx - 50):idx + 200])
        print()
