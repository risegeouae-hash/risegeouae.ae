"""Build a <=510-file browsable preview of the site for an Artifact review link."""
import sys, re, pathlib, shutil, csv, json, os
SITE = pathlib.Path('/home/user/risegeouae-site')
P = pathlib.Path(sys.argv[1]); os.chdir(SITE)
if P.exists(): shutil.rmtree(P)
P.mkdir(parents=True)
allp = [str(p.relative_to(SITE)) for p in SITE.rglob('*.html') if '/_source/' not in str(p) and '/.git/' not in str(p)]
top = ['index.html', 'directory.html', 'categories.html', 'countries.html', 'brands.html', 'insights.html', 'guides.html', 'glossary.html', 'regulations.html', 'bim.html',
       'opportunities.html', 'research.html', 'jobs.html', 'about.html', 'editorial-policy.html', 'corrections.html', 'authors.html', 'advertise.html', 'contact.html', 'faq.html', 'submit.html', 'claim.html']
keep = set(top)
for d in ['section', 'category', 'brand', 'guides', 'bim', 'glossary', 'research', 'jobs']:
    keep |= {p for p in allp if p.startswith(d + '/')}
for p in allp:
    if p.startswith('country/') and 'content="noindex"' not in open(p).read(): keep.add(p)
keep.add('country/syria.html')
rows = list(csv.DictReader(open('data/companies.csv')))
comp = ['company/' + r['url'].rsplit('/', 1)[1] for r in rows]
pri = [c for c, r in zip(comp, rows) if r['website']] + [c for c, r in zip(comp, rows) if not r['website']]
budget = 507 - len(keep) - 3
keep |= set(pri[:budget])
note = 'preview-missing.html'
for p in keep:
    s = open(p).read(); depth = p.count('/')
    def fix(m):
        h = m.group(1)
        if h.startswith(('http', 'mailto:', '#', 'data:', '/')): return m.group(0)
        path, _, frag = h.partition('#'); path, _, q = path.partition('?')
        if not path.endswith('.html'): return m.group(0)
        t = (SITE / pathlib.Path(p).parent / path).resolve().relative_to(SITE).as_posix()
        t2 = 'home.html' if t == 'index.html' else t if t in keep else note
        return 'href="' + '../' * depth + t2 + ('?' + q if q else '') + ('#' + frag if frag else '') + '"'
    s = re.sub(r'href="([^"]*)"', fix, s)
    out = P / ('home.html' if p == 'index.html' else p); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(s)
shutil.copytree('assets', P / 'assets')
(P / note).write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page in full site</title><link rel="stylesheet" href="assets/site.css?v=2"></head><body><section class="hero page-hero"><div class="wrap"><h1 class="page-h1">This page is in the full site</h1><p class="lede">The review preview holds about 500 of the site\'s pages. This one (a company profile or an empty-country page) is built and will go live with the rest. <a style="color:inherit" href="home.html">Back to the home page</a> or <a style="color:inherit" href="directory.html">search the directory</a>.</p></div></section></body></html>')
files = sorted(str(f.relative_to(P)) for f in P.rglob('*') if f.is_file())
old = set(json.load(open(sys.argv[2]))) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else set()
gone = sorted(old - set(files))
core = [f for f in files if not f.startswith('company/')]; compf = [f for f in files if f.startswith('company/')]
b = core + compf
json.dump(files, open(sys.argv[2], 'w'))
json.dump({**{f: None for f in gone}, **{f: f for f in b[:250]}}, open(P.parent / 'pb1.json', 'w'))
json.dump({f: f for f in b[250:]}, open(P.parent / 'pb2.json', 'w'))
print('files', len(files), 'removed', len(gone), 'batch2', len(b[250:]))
