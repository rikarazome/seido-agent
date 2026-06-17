import urllib.request, ssl, sys, re
ctx = ssl.create_default_context()
url = sys.argv[1]
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=15, context=ctx).read(80000).decode('utf-8', 'ignore')
text = re.sub(r'<[^>]+>', ' ', data)
text = re.sub(r'\s+', ' ', text)
# Find "手当額" or "月額" context
for keyword in ['手当額', '月額', '支給額']:
    idx = text.find(keyword)
    if idx >= 0:
        print(f'=== {keyword} at pos {idx} ===')
        print(text[max(0,idx-50):idx+200])
        print()
