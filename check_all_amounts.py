import urllib.request, ssl, re, sys
ctx = ssl.create_default_context()
url = sys.argv[1]
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=15, context=ctx).read(100000).decode('utf-8', 'ignore')
text = re.sub(r'<[^>]+>', ' ', data)
text = re.sub(r'\s+', ' ', text)
for m in re.finditer(r'月額\s*[\d,]+円', text):
    start = max(0, m.start() - 100)
    print(text[start:m.end() + 30])
    print('---')
