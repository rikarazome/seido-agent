import urllib.request, ssl, sys, re
ctx = ssl.create_default_context()
url = sys.argv[1]
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=15, context=ctx).read(100000).decode('utf-8', 'ignore')
text = re.sub(r'<[^>]+>', ' ', data)
text = re.sub(r'\s+', ' ', text)
idx = text.find('3級')
if idx >= 0:
    print(text[idx:idx+300])
