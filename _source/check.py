import re, pathlib, collections, json, html
root = pathlib.Path('/home/user/risegeouae-site')
pages = [p for p in root.rglob('*.html') if '/_source/' not in str(p) and '/.git/' not in str(p)]
bad = collections.Counter(); ex = {}; ldbad = 0
for p in pages:
    s = p.read_text()
    for m in re.finditer(r'href="([^"#?]+)', s):
        h = html.unescape(m.group(1))
        if h.startswith(('http', 'mailto:', 'data:', '/')): continue
        if not (p.parent / h).resolve().exists(): bad[h] += 1; ex[h] = str(p)
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: json.loads(m.group(1))
        except Exception: ldbad += 1
print(len(pages), 'pages; broken links', sum(bad.values()), '; bad JSON-LD', ldbad)
for h, n in bad.most_common(10): print(n, h, ex[h])
