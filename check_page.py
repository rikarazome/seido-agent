import urllib.request, ssl, sys
ctx = ssl.create_default_context()
url = sys.argv[1]
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=15, context=ctx).read(50000).decode('utf-8', 'ignore')
# Extract lines with amounts
for line in data.split('\n'):
    s = line.strip()
    if any(k in s for k in ['月額', '円', '手当額', '支給額', '金額']):
        clean = s.replace('<', ' <').replace('>', '> ')
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', clean).strip()
        if text and len(text) < 200:
            print(text)
