"""GeoAtlas MEA static site generator (v2: 4 sections, 146 directory categories, content hubs).
Reads data/*.csv and content/*.md and writes the full website into the repo root. Run: python3 build.py
"""
import csv, json, re, html, shutil, datetime, pathlib
from collections import Counter, defaultdict
import markdown

BASE_URL = "https://risegeouae.ae"
SITE = "GeoAtlas MEA"
TAGLINE = "The geospatial industry directory for the Middle East and Africa"
EMAIL = "info@risegeouae.ae"
SUBMIT_ENDPOINT = ""
TODAY = datetime.date.today().isoformat()
TODAY_H = datetime.date.today().strftime("%-d %b %Y")
OWNER = "Rise Geo Control Systems Trading LLC"; OWN_BRAND = "GEOTEXON"
DISCLOSURE = ("GeoAtlas MEA is published by Rise Geo Control Systems Trading LLC, a survey equipment supplier, rental and training company in Dubai, United Arab Emirates, and the UAE partner of the GEOTEXON brand. Rise Geo and GEOTEXON appear first in the lists they belong to.")

here = pathlib.Path(__file__).parent
out = here.parent
D = here / "data"
e = lambda s: html.escape(str(s or ""), quote=True)
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")).strip("-")
def url(path): return BASE_URL + "/" + path.lstrip("/") if path != "index.html" else BASE_URL + "/"
def rel(depth, path): return ("../" * depth) + path
def andjoin(xs):
    xs = list(xs)
    return "" if not xs else xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
def host(w): return re.sub(r"^https?://(www\.)?", "", w).split("/")[0] if w else ""
rd = lambda f: list(csv.DictReader(open(D / f, encoding="utf-8")))

# ------------------------------------------------------------------ data
COUNTRIES = rd("countries.csv")
REGION_OF = {c["country"]: c["region"] for c in COUNTRIES}
REGIONS = []
for c in COUNTRIES:
    if c["region"] not in REGIONS: REGIONS.append(c["region"])

DCATS = rd("directory-categories.csv")
SECTIONS = [("A. Services", "Services", "services", "Survey, mapping, drone, GIS and BIM service providers."),
            ("B. Products & Equipment", "Products & Equipment", "products-equipment", "Manufacturers, distributors, dealers, rental and repair for every type of survey equipment."),
            ("C. Software & Data", "Software & Data", "software-data", "Geospatial software vendors, resellers, implementation partners and data providers."),
            ("D. Institutions & Community", "Institutions & Community", "institutions-community", "Agencies, registries, universities, training, professional bodies, events and NGOs.")]
SEC = {s[0]: s for s in SECTIONS}
CAT = {}
for c in DCATS:
    c["slug"] = slug(c["category"]); c["sec"] = SEC[c["section"]]; c["items"] = []
    CAT[c["category"]] = c

ROLE_RANK = ["Manufacturer (OEM)", "Regional office of a manufacturer", "Authorised distributor", "Dealer / reseller", "Supplier / trader",
             "Rental provider", "Service, calibration & repair centre", "Systems integrator", "Software developer / vendor", "Consultant",
             "Service provider / contractor", "Training provider"]
dmap = {(r["name"], r["country"]): r for r in rd("companies-directory-categories.csv")}
rows = rd("companies-master.csv")
seen = set()
for r in rows:
    s = slug(r["name"])
    while s in seen: s += "-2"
    seen.add(s); r["slug"] = s
    m = dmap[(r["name"], r["country"])]
    r["cats"] = [x.strip() for x in m["all_categories"].split(";") if x.strip() in CAT]
    r["primary"] = m["primary_category"] if m["primary_category"] in CAT else (r["cats"][0] if r["cats"] else "")
    if r["primary"] and r["primary"] not in r["cats"]: r["cats"].insert(0, r["primary"])
    r["bts"] = [x.strip() for x in r["business_types"].split(";") if x.strip()]
    r["rank"] = min([ROLE_RANK.index(b) for b in r["bts"] if b in ROLE_RANK] or [99])
    r["svc"] = [x.strip() for x in r["subcategories"].split(";") if x.strip()]
    r["brandlist"] = [x.strip() for x in r["brands"].split(";") if x.strip()]
    r["checked"] = r["verified"] == "yes" if r.get("verified") else "check" not in (r["source"] + " " + r["description"]).lower()
    r["region"] = REGION_OF.get(r["country"], "Regional (MEA)")
    r["cslug"] = slug(r["country"])
    r["secs"] = sorted({CAT[c]["sec"][2] for c in r["cats"]})
    for c in r["cats"]: CAT[c]["items"].append(r)
order = lambda r: (r["name"] != OWNER, r["rank"], not r["checked"], r["country"], r["name"].lower())
rows.sort(key=order)
for c in CAT.values(): c["items"].sort(key=order)
BYNAME = {r["name"]: r for r in rows}
by_country = defaultdict(list)
for r in rows: by_country[r["country"]].append(r)
real_countries = [c for c in by_country if c != "Regional (MEA)"]
N = len(rows)
LIVE = [c for c in DCATS if c["items"]]

BRANDS = rd("brands.csv")
for b in BRANDS: b["slug"] = slug(b["brand"]); b["dealers"] = []
BR = {b["brand"]: b for b in BRANDS}
for l in rd("brand-dealers.csv"):
    if l["brand"] in BR: BR[l["brand"]]["dealers"].append(l)
DEALER_RANK = lambda l: (l["company"] != OWNER, 0 if "Regional office" in l["business_type"] else 1 if "Authorised" in l["business_type"] else 2 if "Dealer" in l["business_type"] else 3, l["country"], l["company"])
for b in BRANDS: b["dealers"].sort(key=DEALER_RANK)
BRANDS.sort(key=lambda b: (b["brand"] != OWN_BRAND, b["brand"] == "Top Tech", -len(b["dealers"]), b["brand"]))
company_brands = defaultdict(set)
for b in BRANDS:
    for l in b["dealers"]: company_brands[l["company"]].add(b["brand"])

# ------------------------------------------------------------------ chrome
ICON = '<svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" stroke-width="1.5" opacity=".5"/><path d="M2 16h28M16 2v28" stroke="currentColor" stroke-width="1" opacity=".35"/><path d="M16 6l3.5 10L16 26l-3.5-10z" fill="#E5B23A"/></svg>'
FAVICON = "data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230F2A25'/%3E%3Cpath d='M16 5l4 11-4 11-4-11z' fill='%23E5B23A'/%3E%3C/svg%3E"
MENU = [
 ("Directory", "directory.html", [(s[1], f"section/{s[2]}.html") for s in SECTIONS] + [("Countries", "countries.html"), ("Brands", "brands.html")]),
 ("Insights", "insights.html", [("News & analysis", "insights.html"), ("Research snapshot", "research/state-of-mea-geospatial-2026.html")]),
 ("Guides", "guides.html", [("How to hire a land surveyor", "guides/how-to-hire-a-land-surveyor.html"), ("Total station vs GNSS", "guides/total-station-vs-gnss.html"), ("Glossary", "glossary.html")]),
 ("Regulations", "regulations.html", [("Country rules & licensing", "regulations.html"), ("BIM Hub", "bim.html"), ("BIM mandates tracker", "bim/mandates.html"), ("ISO 19650 explained", "bim/iso-19650-explained.html")]),
 ("Jobs", "jobs.html", [("All jobs", "jobs.html"), ("Land surveyor jobs", "jobs/land-surveyor-jobs.html"), ("GIS jobs", "jobs/gis-jobs.html"), ("BIM jobs", "jobs/bim-jobs.html"), ("Drone pilot jobs", "jobs/drone-pilot-jobs.html"), ("Internships & graduates", "jobs/internships.html"), ("Post a job, free", "jobs/post-a-job.html")]),
 ("Opportunities", "opportunities.html", [("Events", "opportunities.html#events"), ("Training & courses", "opportunities.html#training"), ("Universities", "category/universities-surveying-gis-and-geomatics.html"), ("Jobs & internships", "jobs.html"), ("Post a tender", "opportunities.html#post")]),
 ("Research", "research.html", [("State of MEA geospatial 2026", "research/state-of-mea-geospatial-2026.html"), ("Data downloads", "research.html#data"), ("Methodology", "about.html#method")]),
]
SITEMAP = []
def page(path, title, desc, body, depth, jsonld=(), current="", og_type="website", noindex=False):
    canon = url(path)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in jsonld if x)
    navh = ""
    for name, p, subs in MENU:
        cur = ' aria-current="page"' if current == name else ""
        sub = "".join(f'<li><a href="{rel(depth, sp)}">{e(sn)}</a></li>' for sn, sp in subs)
        navh += f'<li class="dd"><a class="l" href="{rel(depth, p)}"{cur}>{name}</a><ul class="menu">{sub}</ul></li>'
    fcols = [
        ("Directory", [(s[1], f"section/{s[2]}.html") for s in SECTIONS] + [("Countries", "countries.html"), ("Brands", "brands.html")]),
        ("Learn", [("Guides", "guides.html"), ("Regulations", "regulations.html"), ("BIM Hub", "bim.html"), ("Research", "research.html"), ("Glossary", "glossary.html")]),
        ("Community", [("Jobs & internships", "jobs.html"), ("Post a job", "jobs/post-a-job.html"), ("List your company", "submit.html"), ("Claim your profile", "claim.html"), ("Write or review for us", "authors.html"), ("Opportunities", "opportunities.html")]),
        ("Trust", [("About & methodology", "about.html"), ("Editorial policy", "editorial-policy.html"), ("Corrections", "corrections.html"), ("Advertise & disclosure", "advertise.html"), ("Contact", "contact.html"), ("FAQ", "faq.html")]),
    ]
    foot = "".join(f'<div><h4>{h}</h4><ul>{"".join(f"<li><a href={chr(34)}{rel(depth, p)}{chr(34)}>{e(n)}</a></li>" for n, p in items)}</ul></div>' for h, items in fcols)
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="{"noindex" if noindex else "index,follow,max-image-preview:large,max-snippet:-1"}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="theme-color" content="#0F2A25">
<link rel="icon" href="{FAVICON}">
<link rel="alternate" type="application/json" href="{rel(depth, "data/companies.json")}" title="Directory dataset (JSON)">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{rel(depth, "assets/site.css")}?v=2">
{ld}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<nav class="nav" aria-label="Main"><div class="wrap">
<a class="brand" href="{rel(depth, "index.html")}">{ICON}<span>{SITE}<br><small>MIDDLE EAST &amp; AFRICA</small></span></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="mainmenu">Menu</button>
<ul id="mainmenu">{navh}<li><a class="l cta" href="{rel(depth, "submit.html")}">List your company</a></li></ul>
</div></nav>
<main id="main">
{body}
</main>
<footer class="site"><div class="wrap">
<div class="about"><a class="brand" href="{rel(depth, "index.html")}">{ICON}<span>{SITE}</span></a><p>{TAGLINE}. {N} listings in {len(real_countries)} countries and {len(LIVE)} active categories, compiled from public registers, partner directories and company submissions.</p><p class="mono" style="font-size:12px">Updated {TODAY} · <a href="{rel(depth, "data/companies.csv")}">Download data (CSV)</a></p></div>
{foot}
</div></footer>
<script src="{rel(depth, "assets/site.js")}?v=2" defer></script>
</body>
</html>
'''
    p = out / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(doc, encoding="utf-8")
    if not noindex: SITEMAP.append((canon, path))

def crumbs(depth, items):
    lis = "".join(f'<li><a href="{rel(depth, p)}">{e(n)}</a></li>' if p else f'<li aria-current="page">{e(n)}</li>' for n, p in items)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, **({"item": url(p)} if p else {})} for i, (n, p) in enumerate(items)]}
    return f'<ol class="crumbs">{lis}</ol>', ld

def hero(depth, items, h1, lede, eyebrow=""):
    cr, ld = crumbs(depth, items)
    return f'<section class="hero page-hero"><div class="wrap">{cr}{f"<p class=eyebrow style=margin-top:18px>{e(eyebrow)}</p>" if eyebrow else ""}<h1 class="page-h1">{h1}</h1>{f"<p class=lede>{lede}</p>" if lede else ""}</div></section>', ld

def badge(r):
    b = r["bts"][0] if r["bts"] else ""
    if r["rank"] <= 1: return '<span class="role mfr">Manufacturer</span>' if r["rank"] == 0 else '<span class="role mfr">Regional office</span>'
    if r["rank"] == 2: return '<span class="role dist">Authorised distributor</span>'
    if r["rank"] in (3, 4): return '<span class="role deal">Dealer / supplier</span>'
    return ""

def card(r, depth):
    loc = ", ".join(x for x in [r["city"], r["country"] if r["country"] != "Regional (MEA)" else "Region-wide"] if x)
    tags = "".join(f'<span class="tag">{e(s)}</span>' for s in r["svc"][:4])
    brands = sorted(set(r["brandlist"]) | company_brands.get(r["name"], set()))
    return f'''<article class="card" data-c="{e(r["country"])}" data-r="{e(r["region"])}" data-sec="{" ".join(r["secs"])}" data-k="{e("|".join(r["cats"]))}" data-h="{e(" ".join([r["name"], r["country"], r["city"], r["subcategories"], r["description"], " ".join(r["cats"]), " ".join(brands)]).lower())}">
<div class="top"><h3><a href="{rel(depth, "company/" + r["slug"] + ".html")}">{e(r["name"])}</a></h3>{badge(r)}</div>
<div class="loc"><span>{e(loc)}</span><span class="cat">{e(r["primary"])}</span></div>
{f'<p class="desc">{e(r["description"])}</p>' if r["description"] else ""}
{f'<p class="brands"><b>Brands:</b> {e(", ".join(brands))}</p>' if brands else ""}
{f'<div class="tags">{tags}</div>' if tags else ""}
<div class="foot"><span class="host">{e(host(r["website"])) or "No website listed"}</span><span class="src{"" if r["checked"] else " check"}" title="Source: {e(r["source"])}"><i></i>{"Verified" if r["checked"] else "Unverified"}</span></div>
</article>'''

def grid(items, depth): return '<div class="grid">' + "".join(card(r, depth) for r in items) + "</div>"
def itemlist(name, items):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "numberOfItems": len(items),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": url("company/" + r["slug"] + ".html"), "name": r["name"]} for i, r in enumerate(items[:100])]}
def faqld(faq): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in faq]} if faq else None
def faqhtml(faq, title="Questions"): return f'<h2>{title}</h2>' + "".join(f'<details class="q" open><summary>{e(q)}</summary><p>{a}</p></details>' for q, a in faq) if faq else ""
ORG = {"@context": "https://schema.org", "@type": "Organization", "@id": BASE_URL + "/#org", "name": SITE, "url": BASE_URL + "/", "description": TAGLINE, "areaServed": ["Middle East", "Africa"], "email": EMAIL, "parentOrganization": {"@type": "Organization", "name": OWNER, "url": "https://rise-geo.com", "brand": {"@type": "Brand", "name": OWN_BRAND, "url": "https://geotexon.com"}}}
WEBSITE = {"@context": "https://schema.org", "@type": "WebSite", "@id": BASE_URL + "/#site", "name": SITE, "url": BASE_URL + "/", "publisher": {"@id": BASE_URL + "/#org"},
           "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": BASE_URL + "/directory.html?q={search_term_string}"}, "query-input": "required name=search_term_string"}}
def catlink(depth, name, n=True):
    c = CAT[name]
    return f'<a class="chip" href="{rel(depth, "category/" + c["slug"] + ".html")}">{e(name)}{('<span class="n">%d</span>' % len(c['items'])) if n else ""}</a>'

# ------------------------------------------------------------------ articles
ART = {  # slug -> config
 "how-to-hire-a-land-surveyor": dict(path="guides/how-to-hire-a-land-surveyor.html", hub=("Guides", "guides.html"), kind="How-to guide", author_role="Land surveying",
     cats=["Land Surveyors", "Cadastral & Boundary Surveyors", "Topographic Surveyors", "Real Estate & Building Surveyors", "Construction Setting-Out & As-Built Surveyors"], find="Land Surveyors", howto=True),
 "total-station-vs-gnss": dict(path="guides/total-station-vs-gnss.html", hub=("Guides", "guides.html"), kind="Comparison", author_role="Survey equipment", disclose=True,
     cats=["GNSS Receiver Dealers & Suppliers", "Total Station Dealers & Suppliers", "GNSS Receiver Manufacturers", "Total Station Manufacturers", "Land Surveying Equipment Rental"], find="Total Station Dealers & Suppliers"),
 "iso-19650-explained": dict(path="bim/iso-19650-explained.html", hub=("BIM Hub", "bim.html"), kind="BIM Hub explainer", author_role="BIM management",
     cats=["BIM Consultants", "BIM Modelling & Coordination Services", "Scan-to-BIM Services", "BIM Software Vendors"], find="BIM Consultants"),
 "rtk-ppk-cors": dict(path="glossary/rtk-ppk-cors.html", hub=("Glossary", "glossary.html"), kind="Glossary", author_role="Geodesy",
     cats=["GNSS Receiver Dealers & Suppliers", "Geodetic & GNSS Survey Services"], find="GNSS Receiver Dealers & Suppliers", glossary=True),
}
PLACE = {"BIMMANDATES": "bim/mandates.html", "REGHUB": "regulations.html", "GLOSSRTK": "glossary/rtk-ppk-cors.html"}
for k, a in ART.items():
    md = (here / "content" / (k + ".md")).read_text(encoding="utf-8")
    a["title"] = md.split("\n", 1)[0].lstrip("# ").strip()
    body = md.split("\n", 1)[1]
    qa = re.search(r"^> \*\*Quick answer:\*\*\s*(.+)$", body, re.M)
    a["answer"] = qa.group(1).strip(); body = body.replace(qa.group(0), "")
    faq = []
    if "#### FAQ" in body:
        pre, post = body.split("#### FAQ", 1)
        nxt = re.split(r"\n(?=\*[A-Z]|#### )", post, maxsplit=1)
        for m in re.finditer(r"\*\*(.+?\?)\*\*\s*(.+)", nxt[0]): faq.append((m.group(1), m.group(2).strip()))
        body = pre + ("\n" + nxt[1] if len(nxt) > 1 else "")
    a["faq"] = faq
    a["md"] = body.replace("#### ", "## ")
    a["depth"] = a["path"].count("/")
ARTSLUG = {a["title"]: k for k, a in ART.items()}

def md_html(text, depth):
    h = markdown.markdown(text, extensions=["tables"])
    for key, p in PLACE.items(): h = h.replace(f'href="{key}"', f'href="{rel(depth, p)}"')
    # link category and firm names inside "Browse"/"Find providers"/"include" paragraphs
    def linkpara(m):
        p = m.group(0)
        if not re.search(r"Browse|Find providers|include|includes|Regional distributors|Manufacturers with", p): return p
        for name in sorted(CAT, key=len, reverse=True):
            if CAT[name]["items"] and name in p and f">{name}<" not in p:
                p = re.sub(r"(?<![\w>])" + re.escape(name) + r"(?![\w<])", f'<a href="{rel(depth, "category/" + CAT[name]["slug"] + ".html")}">{e(name)}</a>', p, count=1)
        for name in sorted(BYNAME, key=len, reverse=True):
            short = re.sub(r"\s*\(.*?\)$", "", name)
            for cand in (name, short):
                if len(cand) > 4 and cand in p and f">{cand}" not in p:
                    p = re.sub(r"(?<![\w>/\"])" + re.escape(cand) + r"(?![\w<])", f'<a href="{rel(depth, "company/" + BYNAME[name]["slug"] + ".html")}">{e(cand)}</a>', p, count=1); break
        return p
    h = re.sub(r"<p>.*?</p>", linkpara, h, flags=re.S)
    return h.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")

def learn_strip(depth, catnames=(), country=None):
    picks = [k for k, a in ART.items() if set(a["cats"]) & set(catnames)] if catnames else ["how-to-hire-a-land-surveyor", "total-station-vs-gnss", "iso-19650-explained"]
    if not picks: return ""
    return '<aside class="learn"><h2>Learn</h2><div class="learn-grid">' + "".join(
        f'<a href="{rel(depth, ART[k]["path"])}"><small>{e(ART[k]["kind"])}</small><b>{e(ART[k]["title"])}</b><span>{e(ART[k]["answer"][:120])}…</span></a>' for k in picks[:4]) + "</div></aside>"

# ------------------------------------------------------------------ map
COORDS = {"Dubai": (25.20, 55.27), "Abu Dhabi": (24.45, 54.38), "Sharjah": (25.35, 55.42), "Riyadh": (24.71, 46.68), "Jeddah": (21.49, 39.19), "Dammam": (26.43, 50.10), "Doha": (25.29, 51.53), "Manama": (26.23, 50.59), "Kuwait City": (29.38, 47.99), "Muscat": (23.59, 58.41), "Cairo": (30.04, 31.24), "Amman": (31.95, 35.93), "Beirut": (33.89, 35.50), "Rabat": (34.02, -6.84), "Casablanca": (33.57, -7.59), "Tunis": (36.81, 10.18), "Algiers": (36.75, 3.06), "Tripoli": (32.89, 13.19), "Khartoum": (15.50, 32.56), "Abuja": (9.08, 7.40), "Lagos": (6.52, 3.38), "Accra": (5.60, -0.19), "Nairobi": (-1.29, 36.82), "Kampala": (0.35, 32.58), "Kigali": (-1.95, 30.06), "Dar es Salaam": (-6.79, 39.21), "Addis Ababa": (9.03, 38.74), "Dakar": (14.72, -17.47), "Abidjan": (5.36, -4.01), "Conakry": (9.64, -13.58), "Cotonou": (6.37, 2.39), "Bamako": (12.64, -8.00), "Johannesburg": (-26.20, 28.05), "Pretoria": (-25.75, 28.19), "Cape Town": (-33.92, 18.42), "Durban": (-29.86, 31.02), "Lusaka": (-15.39, 28.32), "Harare": (-17.83, 31.05), "Gaborone": (-24.65, 25.91), "Maputo": (-25.97, 32.57), "Luanda": (-8.84, 13.23), "Antananarivo": (-18.88, 47.51), "Freetown": (8.48, -13.23), "Lilongwe": (-13.96, 33.79), "Nicosia": (35.17, 33.36), "Istanbul": (41.01, 28.98), "Ankara": (39.93, 32.86), "Tehran": (35.69, 51.39), "Baghdad": (33.31, 44.36)}
def map_svg(depth):
    W, H = 560, 560; x = lambda lon: (lon + 20) / 88 * W; y = lambda lat: (42 - lat) / 80 * H
    g = "".join(f'<line class="grat" x1="{x(lo):.1f}" y1="0" x2="{x(lo):.1f}" y2="{H}"/><text class="lbl" x="{x(lo)+3:.1f}" y="{H-6}">{abs(lo)}°{"E" if lo >= 0 else "W"}</text>' for lo in range(-10, 61, 10))
    g += "".join(f'<line class="grat" x1="0" y1="{y(la):.1f}" x2="{W}" y2="{y(la):.1f}"/><text class="lbl" x="4" y="{y(la)-4:.1f}">{abs(la)}°{"N" if la >= 0 else "S"}{" EQ" if la == 0 else ""}</text>' for la in range(-30, 41, 10))
    cnt = Counter(r["city"] for r in rows if r["city"] in COORDS); pts = ""; placed = []
    for city, n in sorted(cnt.items(), key=lambda t: -t[1]):
        la, lo = COORDS[city]; cx, cy = x(lo), y(la); rad = 3.5 + min(n, 40) ** 0.6 * 2
        ctry = next(r["country"] for r in rows if r["city"] == city)
        ok = n >= 4 and all(abs(cx - px) > 70 or abs(cy - py) > 22 for px, py in placed)
        if ok: placed.append((cx, cy))
        lab = f'<text class="cname" x="{cx+rad+4:.1f}" y="{cy+4:.1f}">{e(city)} {n}</text>' if ok else ""
        pts += f'<a href="{rel(depth, "country/" + slug(ctry) + ".html")}" aria-label="{e(city)}: {n} listings"><circle class="halo" cx="{cx:.1f}" cy="{cy:.1f}" r="{rad*2:.1f}"/><circle class="city" cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}"/>{lab}</a>'
    return f'<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-label="Plot of listed organisations by city across the Middle East and Africa">{g}{pts}</svg><div class="map-cap">Listings by city · equirectangular, 10° graticule</div>'

# ------------------------------------------------------------------ section pages and category pages
def sec_cats(s): return [c for c in DCATS if c["section"] == s[0]]
def sec_count(s): return len({r["name"] for c in sec_cats(s) for r in c["items"]})
def sec_body(s, depth):
    cats = sec_cats(s)
    if s[2] in ("products-equipment", "software-data"):
        lines = []
        for c in cats:
            ln = c["product_or_software_line"] or c["category"]
            if ln not in lines: lines.append(ln)
        h = ""
        for ln in lines:
            group = [c for c in cats if (c["product_or_software_line"] or c["category"]) == ln]
            live = [c for c in group if c["items"]]
            if not live: continue
            lname = ln if ln != "Data" else "Geospatial data providers"
            h += f'<div class="line"><h3>{e(lname)}</h3><div class="chips">' + "".join(catlink(depth, c["category"]) for c in live) + '</div></div>'
        return h
    return '<div class="tiles">' + "".join(f'<a class="tile" href="{rel(depth, "category/" + c["slug"] + ".html")}"><span>{e(c["category"])}</span><em>{len(c["items"])}</em></a>' for c in cats if c["items"]) + "</div>"

for s in SECTIONS:
    d = 1; cats = sec_cats(s); live = [c for c in cats if c["items"]]
    h, ld = hero(d, [("Home", "index.html"), ("Directory", "directory.html"), (s[1], "")], e(s[1]), f'{e(s[3])} {sec_count(s)} organisations in {len(live)} categories.', "Directory section")
    note = f'<p class="note">{len(cats) - len(live)} more categories in this section are open for listings and will appear once a company is added. <a href="{rel(d, "submit.html")}">List your company</a>.</p>' if len(cats) > len(live) else ""
    disc = ""
    page(f"section/{s[2]}.html", f"{s[1]} Directory – Middle East & Africa | {SITE}", f"{s[3]} {sec_count(s)} organisations across the Middle East and Africa.",
         h + f'<div class="wrap listing">{sec_body(s, d)}{note}{disc}</div>', d, [ld], "Directory")

for c in LIVE:
    d = 1; items = c["items"]; s = c["sec"]
    cc = Counter(r["country"] for r in items)
    top = [x for x, _ in cc.most_common(5) if x != "Regional (MEA)"][:3]
    role_note = " Manufacturers and regional offices are listed first, then authorised distributors, then dealers and suppliers." if s[2] in ("products-equipment", "software-data") else ""
    answer = f'{SITE} lists {len(items)} {c["category"]} across {len([x for x in cc if x != "Regional (MEA)"])} countries in the Middle East and Africa' + (f', led by {andjoin(top)}.' if top else ".") + role_note
    h, ld = hero(d, [("Home", "index.html"), (s[1], f"section/{s[2]}.html"), (c["category"], "")], e(c["category"]) + " in the Middle East &amp; Africa", e(answer), c["code"] + " · " + s[1])
    tabs = ""
    if c["product_or_software_line"] and c["product_or_software_line"] != "Data":
        sib = [x for x in DCATS if x["product_or_software_line"] == c["product_or_software_line"]]
        tabs = '<nav class="tabs" aria-label="Roles">' + "".join(
            (f'<a href="{rel(d, "category/" + x["slug"] + ".html")}"{" aria-current=page" if x is c else ""}>{e(x["role"])} <span>{len(x["items"])}</span></a>' if x["items"] else f'<span class="off">{e(x["role"])} <span>0</span></span>') for x in sib) + "</nav>"
    brandsec = ""
    if s[2] == "products-equipment":
        bs = sorted({b for r in items for b in (set(r["brandlist"]) | company_brands.get(r["name"], set())) if b in BR})
        if bs: brandsec = '<div class="chips" style="margin:8px 0 18px"><span class="meta" style="margin-right:6px">Brands in this list:</span>' + "".join(f'<a class="chip" href="{rel(d, "brand/" + BR[b]["slug"] + ".html")}">{e(b)}</a>' for b in bs) + "</div>"
    chips = '<div class="chips" style="margin-bottom:18px">' + "".join(f'<a class="chip" href="{rel(d, "country/" + slug(x) + ".html")}">{e(x if x != "Regional (MEA)" else "Region-wide")}<span class="n">{n}</span></a>' for x, n in cc.most_common()) + "</div>"
    faq = [(f"How many {c['category']} are listed in the Middle East and Africa?", f"{len(items)} are listed today, in {andjoin([x for x,_ in cc.most_common() if x!='Regional (MEA)'][:6]) or 'region-wide entries'}{' and more' if len(cc)>6 else ''}. The list grows as companies are added; any firm can list itself for free.")]
    if "UAE" not in c["category"] and cc.get("United Arab Emirates"): faq.append((f"Which {c['category']} are in the UAE?", andjoin([r["name"] for r in items if r["country"] == "United Arab Emirates"][:8]) + (" and others." if cc["United Arab Emirates"] > 8 else ".")))
    disc = ""
    body = h + f'<div class="wrap listing">{tabs}{brandsec}{chips}{grid(items, d)}{learn_strip(d, [c["category"]])}<div class="prose">{faqhtml(faq)}</div>{disc}<p class="note" style="margin-top:24px">Missing a company? <a href="{rel(d, "submit.html")}">Add it for free</a> or <a href="{rel(d, "claim.html")}">claim an existing profile</a>.</p></div>'
    page(f"category/{c['slug']}.html", f"{c['category']} – {len(items)} in the Middle East & Africa | {SITE}", answer[:158], body, d,
         [itemlist(f"{c['category']} in the Middle East and Africa", items), ld, faqld(faq)], "Directory")

# old category URLs from v1 -> new pages (for .htaccess)
OLDCAT = {"survey-company": "category/land-surveyors.html", "gis-and-consulting": "category/gis-consultants.html", "hardware-supplier": "section/products-equipment.html",
          "software-vendor": "section/software-data.html", "drone-and-uav-services": "category/drone-survey-and-mapping-companies.html", "satellite-and-earth-observation": "category/satellite-imagery-providers.html",
          "hydrographic-and-marine": "category/hydrographic-and-bathymetric-surveys.html", "government-and-agency": "category/national-mapping-and-survey-agencies.html", "association-and-education": "section/institutions-community.html"}

# ------------------------------------------------------------------ directory + categories index
def toolbar():
    opts = lambda items: "".join(f'<option value="{e(k)}">{e(k)} ({n})</option>' for k, n in items)
    return f'''<div class="toolbar" id="filters"><div class="wrap">
<div class="row"><div class="search"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input id="q" type="search" placeholder="Search names, brands, services, cities…" aria-label="Search the directory"></div>
<select id="f-region" aria-label="Region"><option value="">All regions</option>{opts([(g, sum(1 for r in rows if r["region"] == g)) for g in REGIONS if any(r["region"] == g for r in rows)])}</select>
<select id="f-country" aria-label="Country"><option value="">All countries</option>{opts(sorted(Counter(r["country"] for r in rows).items()))}</select>
<select id="f-cat" aria-label="Category"><option value="">All categories</option>{opts([(c["category"], len(c["items"])) for c in LIVE])}</select></div>
<div class="row" style="justify-content:space-between"><div class="chips" role="group" aria-label="Section"><button class="chip" type="button" data-sec="" aria-pressed="true">All</button>{"".join(f'<button class="chip" type="button" data-sec="{s[2]}" aria-pressed="false">{e(s[1])}<span class="n">{sec_count(s)}</span></button>' for s in SECTIONS)}</div><span class="meta" id="count" aria-live="polite"></span></div>
</div></div>'''
h, ld = hero(0, [("Home", "index.html"), ("Directory", "")], "Geospatial directory", f"All {N} listings. Search by name, brand, service or city, then narrow by section, category, region and country.")
secs = '<div class="secs">' + "".join(f'<a class="sec" href="section/{s[2]}.html"><small>{s[0][:2]}</small><b>{e(s[1])}</b><span>{e(s[3])}</span><em>{sec_count(s)} listings · {len([c for c in sec_cats(s) if c["items"]])} categories</em></a>' for s in SECTIONS) + "</div>"
page("directory.html", f"Search {N} Survey, GIS, BIM & Geospatial Companies | {SITE}", f"Search and filter {N} survey firms, GIS consultancies, equipment dealers, software vendors, agencies and universities across the Middle East and Africa.",
     h + f'<div class="wrap" style="padding-top:24px">{secs}</div>' + toolbar() + f'<div class="wrap listing"><div class="grid" id="list">{"".join(card(r, 0) for r in rows)}</div><div class="empty" id="empty" hidden>Nothing matches those filters. Clear a filter, or <a href="submit.html">add the company you were looking for</a>.</div></div>',
     0, [ld, itemlist("Geospatial organisations in the Middle East and Africa", rows)], "Directory")
h, ld = hero(0, [("Home", "index.html"), ("Directory", "directory.html"), ("All categories", "")], "All categories", f"{len(DCATS)} categories in four sections; {len(LIVE)} have listings today.")
page("categories.html", f"All {len(DCATS)} Geospatial Directory Categories | {SITE}", "Every category in the Middle East and Africa geospatial directory: services, products and equipment, software and data, institutions and community.",
     h + '<div class="wrap listing">' + "".join(f'<h2><a href="section/{s[2]}.html">{e(s[1])}</a></h2>{sec_body(s, 0)}' for s in SECTIONS) + "</div>", 0, [ld], "Directory")

# ------------------------------------------------------------------ company pages
TYPE = lambda r: "GovernmentOrganization" if any(c in r["cats"] for c in ("National Mapping & Survey Agencies", "Land Registries & Cadastre Authorities", "Municipal GIS Departments", "Space Agencies", "Geological Surveys", "Statistics & Census Bureaus")) \
    else "CollegeOrUniversity" if any(c in r["cats"] for c in ("Universities (Surveying, GIS & Geomatics)",)) else "EducationalOrganization" if "Technical Colleges & Vocational Institutes" in r["cats"] \
    else "LocalBusiness" if r["city"] and r["country"] != "Regional (MEA)" else "Organization"
for r in rows:
    d = 1; cname = r["country"] if r["country"] != "Regional (MEA)" else "Region-wide"
    brands = sorted(set(r["brandlist"]) | company_brands.get(r["name"], set()))
    ld = {"@context": "https://schema.org", "@type": TYPE(r), "@id": url("company/" + r["slug"] + ".html") + "#org", "name": r["name"], "description": r["description"],
          "url": r["website"] or None, "telephone": r["phone"] or None,
          "address": {"@type": "PostalAddress", **({"addressLocality": r["city"]} if r["city"] else {}), "addressCountry": r["country"]} if r["country"] != "Regional (MEA)" else None,
          "areaServed": r["country"] if r["country"] != "Regional (MEA)" else ["Middle East", "Africa"], "knowsAbout": r["svc"] or None,
          "brand": [{"@type": "Brand", "name": b} for b in brands] or None, "sameAs": [r["website"]] if r["website"] else None}
    if r["city"] in COORDS: ld["geo"] = {"@type": "GeoCoordinates", "latitude": COORDS[r["city"]][0], "longitude": COORDS[r["city"]][1]}
    ld = {k: v for k, v in ld.items() if v not in (None, "", [])}
    role = andjoin([b.lower() for b in r["bts"]][:3]) or "organisation"
    summary = f'{r["name"]} is listed in {SITE} as {"an" if role[0] in "aeiou" else "a"} {role} ' + (f'based in {r["city"] + ", " if r["city"] else ""}{r["country"]}' if r["country"] != "Regional (MEA)" else "serving the Middle East and Africa") + f'. It appears in {len(r["cats"])} directory {"category" if len(r["cats"]) == 1 else "categories"}' + (f', led by {r["primary"]}' if r["primary"] else "") + "."
    if brands: summary += f" Brands: {andjoin(brands)}."
    related = [x for x in CAT[r["primary"]]["items"] if x is not r and x["country"] == r["country"]][:3] if r["primary"] else []
    if not related and r["primary"]: related = [x for x in CAT[r["primary"]]["items"] if x is not r][:3]
    facts = [("Main category", f'<a href="{rel(d, "category/" + CAT[r["primary"]]["slug"] + ".html")}">{e(r["primary"])}</a>' if r["primary"] else "–"),
             ("Business type", e("; ".join(r["bts"])) or "–"),
             ("Country", f'<a href="{rel(d, "country/" + r["cslug"] + ".html")}">{e(cname)}</a>'), ("City", e(r["city"]) or "–"),
             ("Brands", ", ".join(f'<a href="{rel(d, "brand/" + BR[b]["slug"] + ".html")}">{e(b)}</a>' if b in BR else e(b) for b in brands) or "–"),
             ("Website", f'<a href="{e(r["website"])}" rel="noopener nofollow" target="_blank">{e(host(r["website"]))} ↗</a>' if r["website"] else "Not listed"),
             ("Phone", f'<span class="mono">{e(r["phone"])}</span>' if r["phone"] else "Not listed"),
             ("Status", f'<span class="src{"" if r["checked"] else " check"}"><i></i>{"Verified" if r["checked"] else "Unverified, details to confirm"}</span>'),
             ("Source", e(r["source"]))]
    h, cld = hero(d, [("Home", "index.html"), (cname, "country/" + r["cslug"] + ".html"), (r["name"], "")], e(r["name"]), e(r["description"]), r["primary"])
    body = h + f'''<div class="wrap detail"><div class="prose"><p class="answer">{e(summary)}</p>
<h2>Directory categories</h2><div class="chips">{"".join(catlink(d, c) for c in r["cats"])}</div>
{f'<h2>Services</h2><div class="tags">{"".join(f"<span class=tag>{e(s)}</span>" for s in r["svc"])}</div>' if r["svc"] else ""}
{f'<h2>Similar organisations</h2><div class="grid" style="grid-template-columns:1fr">{"".join(card(x, d) for x in related)}</div>' if related else ""}
<div class="claim"><b>Is this your organisation?</b> Claim this free profile to correct details, add services, brands and projects, and get a “Listed on {SITE}” badge for your website. <a class="btn solid" href="{rel(d, "claim.html")}?n={e(r["name"])}">Claim this profile</a></div>
<p class="note">Details come from public sources (see Source). Confirm them with the organisation before relying on them. <a href="{rel(d, "corrections.html")}">Report an error</a>.</p></div>
<aside><div class="panel"><dl class="facts">{"".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts)}</dl>{f'<p style="margin:18px 0 0"><a class="btn solid" href="{e(r["website"])}" rel="noopener nofollow" target="_blank">Visit website</a></p>' if r["website"] else ""}</div></aside></div>'''
    page(f'company/{r["slug"]}.html', f'{r["name"]} – {r["primary"] or "Geospatial"} in {r["city"] + ", " if r["city"] else ""}{cname} | {SITE}', (r["description"] or summary)[:158], body, d, [ld, cld], "Directory", og_type="profile")

# ------------------------------------------------------------------ country pages (all 70)
REGLINK = {"National Mapping & Survey Agencies", "Land Registries & Cadastre Authorities", "Professional Bodies & Licensing Councils", "Municipal GIS Departments"}
def country_tiles(depth, with_empty=True):
    hh = ""
    for reg in REGIONS:
        cs = [c["country"] for c in COUNTRIES if c["region"] == reg]
        cs.sort(key=lambda c: (-len(by_country.get(c, [])), c))
        if reg == "Regional (MEA)": continue
        hh += f'<div class="region-h">{e(reg)}</div><div class="tiles">' + "".join(f'<a class="tile{"" if by_country.get(c) else " empty-t"}" href="{rel(depth, "country/" + slug(c) + ".html")}"><span>{e(c)}</span><em>{len(by_country.get(c, [])) or "+"}</em></a>' for c in cs if with_empty or by_country.get(c)) + "</div>"
    if by_country.get("Regional (MEA)"):
        hh += f'<div class="region-h">Region-wide</div><div class="tiles"><a class="tile" href="{rel(depth, "country/regional-mea.html")}"><span>Manufacturers, software &amp; satellites serving all of MEA</span><em>{len(by_country["Regional (MEA)"])}</em></a></div>'
    return hh
for cinfo in COUNTRIES:
    ctry = cinfo["country"]; items = by_country.get(ctry, []); d = 1
    cname = ctry if ctry != "Regional (MEA)" else "Region-wide (all MEA)"
    kc = Counter(r["primary"] for r in items)
    if items:
        answer = (f'{SITE} lists {len(items)} geospatial organisations in {ctry}: ' if ctry != "Regional (MEA)" else f'{len(items)} manufacturers, software vendors and satellite operators serve the whole Middle East and Africa region: ') + andjoin(f"{n} {k.lower()}" for k, n in kc.most_common(4)) + (" and more." if len(kc) > 4 else ".")
        cities = Counter(r["city"] for r in items if r["city"])
        if cities and ctry != "Regional (MEA)": answer += f' Most are based in {andjoin(c for c, _ in cities.most_common(3))}.'
    else:
        answer = f"No organisations in {ctry} are listed yet. {SITE} covers all 70 Middle East and African countries; be the first listed in {ctry}, free."
    h, ld = hero(d, [("Home", "index.html"), ("Countries", "countries.html"), (cname, "")], ("Geospatial, survey &amp; GIS companies in " + e(cname)) if ctry != "Regional (MEA)" else "Region-wide suppliers", e(answer), cinfo["region"])
    secblocks = ""
    for s in SECTIONS:
        its = [r for r in items if s[2] in r["secs"]]
        if its:
            ccats = Counter(c for r in its for c in r["cats"] if CAT[c]["sec"] is s)
            secblocks += f'<h2 id="{s[2]}">{e(s[1])} <span class="meta">{len(its)}</span></h2><div class="chips" style="margin-bottom:14px">' + "".join(f'<a class="chip" href="{rel(d, "category/" + CAT[k]["slug"] + ".html")}">{e(k)}<span class="n">{n}</span></a>' for k, n in ccats.most_common(12)) + "</div>" + grid(sorted(its, key=order), d)
    reg = [r for r in items if set(r["cats"]) & REGLINK]
    faq = []
    if items and ctry != "Regional (MEA)":
        nsurv = len([r for r in items if "Land Surveyors" in r["cats"] or "Topographic Surveyors" in r["cats"]])
        faq.append((f"How many survey companies are listed in {ctry}?", f"{nsurv} land or topographic survey firms are listed in {ctry}, out of {len(items)} geospatial organisations in total."))
        if reg: faq.append((f"Which authorities regulate surveying and mapping in {ctry}?", "Listed authorities and bodies: " + "; ".join(r["name"] for r in reg[:6]) + ". Confirm licensing rules with the authority before appointing a surveyor."))
        eq = [r for r in items if "products-equipment" in r["secs"]]
        if eq: faq.append((f"Where can I buy survey equipment in {ctry}?", "Listed manufacturers, distributors and dealers include " + andjoin([r["name"] for r in eq[:6]]) + "."))
    empty_cta = "" if items else f'<div class="claim"><b>Be the first listed in {e(ctry)}.</b> Survey firms, GIS consultancies, equipment dealers, agencies and universities in {e(ctry)} can add a free listing in two minutes. <a class="btn solid" href="{rel(d, "submit.html")}">List your organisation</a></div>'
    body = h + f'<div class="wrap listing">{empty_cta}{secblocks}{learn_strip(d)}<div class="prose">{faqhtml(faq)}</div><p class="note" style="margin-top:24px">Know an organisation in {e(cname)} that is missing? <a href="{rel(d, "submit.html")}">Add it to the directory</a>.</p></div>'
    ttl = f"{len(items)} Survey, GIS & Geospatial Companies in {ctry} | {SITE}" if items and ctry != "Regional (MEA)" else f"Survey & GIS Companies in {ctry} – List Yours Free | {SITE}" if ctry != "Regional (MEA)" else f"Region-wide Geospatial Manufacturers & Vendors in MEA | {SITE}"
    page(f"country/{slug(ctry)}.html", ttl, answer[:158], body, d, [itemlist(f"Geospatial organisations in {cname}", items) if items else None, ld, faqld(faq)], "Directory", noindex=not items)
h, ld = hero(0, [("Home", "index.html"), ("Countries", "")], "Browse by country", f"All 70 Middle East and African countries. {len(real_countries)} have listings today; the rest are open for the first listing.")
page("countries.html", f"Geospatial Companies by Country – 70 Middle East & African Countries | {SITE}", f"Survey, GIS, BIM and geospatial organisations in {len(real_countries)} countries across the GCC, Levant, North, West, Central, East and Southern Africa.",
     h + f'<div class="wrap listing">{country_tiles(0)}</div>', 0, [ld], "Directory")

# ------------------------------------------------------------------ brands
BRAND_SITE = {"GEOTEXON": "https://geotexon.com", "Top Tech": "https://www.toptechgnss.com/"}
OWN_NOTE = {"Top Tech": '<p>Brand website: <a href="https://www.toptechgnss.com/" rel="noopener" target="_blank">toptechgnss.com</a>. Company: Shanghai Hexin Survey Instrument Co., Ltd, Shanghai, China (<a href="https://www.hexinsurvey.com" rel="noopener" target="_blank">hexinsurvey.com</a>). Model list to be added.</p>', "GEOTEXON": '<p>Official site: <a href="https://geotexon.com" rel="noopener" target="_blank">geotexon.com</a>. In the UAE, GEOTEXON is supplied by <a href="../company/rise-geo-control-systems-trading-llc.html">Rise Geo Control Systems Trading LLC</a>. Models marked “in development” are not yet released.</p>'}
for b in BRANDS:
    d = 1; dl = b["dealers"]; byc = defaultdict(list)
    for l in dl: byc[l["country"]].append(l)
    lines = [x.strip() for x in b["product_lines"].split(";") if x.strip()]
    answer = f'{b["brand"]} is {"a " + b["origin_country"] + " " if b["origin_country"] not in ("", "not verified") else "a "}brand{" of " + b["parent_group"] if b["parent_group"] not in ("", "not verified", b["brand"]) else ""} for {andjoin([x.lower() for x in lines][:4])}. ' + (f'{SITE} lists {len(dl)} regional offices, distributors and dealers for {b["brand"]} in {len(byc)} {"country" if len(byc)==1 else "countries"} of the Middle East and Africa.' if dl else f'No {b["brand"]} dealer is listed yet; regional dealers can add themselves for free.')
    h, ld = hero(d, [("Home", "index.html"), ("Brands", "brands.html"), (b["brand"], "")], e(b["brand"]) + ": where to buy in the Middle East &amp; Africa", e(answer), "Brand")
    def dl_row(l):
        r = BYNAME.get(l["company"])
        nm = f'<a href="{rel(d, "company/" + r["slug"] + ".html")}">{e(l["company"])}</a>' if r else e(l["company"])
        return f'<tr><td>{nm}</td><td>{e(l["business_type"])}</td><td>{e(r["city"]) if r else ""}</td></tr>'
    tables = "".join(f'<h3>{e(c if c != "Regional (MEA)" else "Region-wide")}</h3><div class="tbl"><table><thead><tr><th>Company</th><th>Role</th><th>City</th></tr></thead><tbody>{"".join(dl_row(l) for l in ls)}</tbody></table></div>' for c, ls in sorted(byc.items(), key=lambda t: (t[0] != "United Arab Emirates", t[0])))
    facts = [("Parent group", e(b["parent_group"])), ("Origin", e(b["origin_country"])), ("Product lines", e(b["product_lines"])), ("MEA partners listed", str(len(dl)))]
    bld = {"@context": "https://schema.org", "@type": "Brand", "name": b["brand"], "description": answer, "url": url(f"brand/{b['slug']}.html"), **({"sameAs": [BRAND_SITE[b["brand"]]]} if b["brand"] in BRAND_SITE else {})}
    body = h + f'<div class="wrap detail"><div class="prose"><p class="answer">{e(answer)}</p><h2>Where to buy {e(b["brand"])}</h2><p class="note">Ordered by role: regional offices first, then authorised distributors, then dealers. Roles marked “role not stated on page” come from the manufacturer\'s contact page, which does not label roles; confirm with the manufacturer.</p>{tables or "<p>No partners listed yet.</p>"}{OWN_NOTE.get(b["brand"], "")}</div><aside><div class="panel"><dl class="facts">{"".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts)}</dl><p style="margin:18px 0 0"><a class="btn solid" href="{rel(d, "submit.html")}">Are you a {e(b["brand"])} dealer? List free</a></p></div></aside></div>'
    page(f"brand/{b['slug']}.html", f"{b['brand']} Dealers & Distributors in the Middle East & Africa | {SITE}", answer[:158], body, d, [bld, ld], "Directory")
h, ld = hero(0, [("Home", "index.html"), ("Brands", "")], "Brands and where to buy them", f"{len(BRANDS)} equipment, software and imagery brands, each with its regional offices, distributors and dealers in the Middle East and Africa.")
btiles = '<div class="tiles">' + "".join(f'<a class="tile" href="brand/{b["slug"]}.html"><span>{e(b["brand"])}<small>{e(b["product_lines"][:70])}</small></span><em>{len(b["dealers"])}</em></a>' for b in BRANDS) + "</div>"
page("brands.html", f"Survey Equipment & Geospatial Software Brands – Where to Buy in MEA | {SITE}", "Find regional offices, authorised distributors and dealers for Leica, Trimble, Topcon, Esri, DJI and more across the Middle East and Africa.",
     h + f'<div class="wrap listing">{btiles}</div>', 0, [ld], "Directory")

# ------------------------------------------------------------------ articles
def byline(a): return f'<p class="byline">By <a href="{rel(a["depth"], "authors.html")}">{SITE} editorial team</a> ({e(a["author_role"])}) · Technical review: pending, see <a href="{rel(a["depth"], "editorial-policy.html")}">editorial policy</a> · Published {TODAY_H} · Last reviewed {TODAY_H}</p>'
def find_box(a, depth):
    c = CAT.get(a["find"]); its = c["items"][:6] if c else []
    if not its: return ""
    return f'<aside class="find"><h2>Find providers</h2><div class="grid">{"".join(card(r, depth) for r in its)}</div><p><a class="btn solid" href="{rel(depth, "category/" + c["slug"] + ".html")}">See all {len(c["items"])} {e(c["category"])}</a></p></aside>'
for k, a in ART.items():
    d = a["depth"]
    hub = a["hub"]
    items = [("Home", "index.html"), hub, (a["title"], "")]
    if hub[0] == "BIM Hub": items.insert(1, ("Regulations", "regulations.html"))
    h, ld = hero(d, items, e(a["title"]), "", a["kind"])
    bodyh = md_html(a["md"], d)
    faq = [(q, ans) for q, ans in a["faq"]]
    related = "".join(f'<li><a href="{rel(d, b["path"])}">{e(b["title"])}</a></li>' for kk, b in ART.items() if kk != k)
    catlinks = "".join(catlink(d, c) for c in a["cats"] if c in CAT and CAT[c]["items"])
    disc = ""
    art_ld = {"@context": "https://schema.org", "@type": "Article" if not a.get("glossary") else "Article", "headline": a["title"], "description": a["answer"], "datePublished": TODAY, "dateModified": TODAY,
              "author": {"@type": "Organization", "name": f"{SITE} editorial team", "url": url("authors.html")}, "publisher": {"@id": BASE_URL + "/#org"},
              "mainEntityOfPage": url(a["path"]), "about": [{"@type": "Thing", "name": c} for c in a["cats"]], "isAccessibleForFree": True, "inLanguage": "en"}
    extra = []
    if a.get("howto"):
        steps = re.findall(r"^\d\. \*\*(.+?):\*\*\s*(.+)$", a["md"], re.M)
        if steps: extra.append({"@context": "https://schema.org", "@type": "HowTo", "name": "What to include in a land survey brief", "step": [{"@type": "HowToStep", "position": i + 1, "name": n, "text": t} for i, (n, t) in enumerate(steps)]})
    if a.get("glossary"):
        terms = re.findall(r"^\*\*(RTK|PPK|CORS)[^*]*\*\*\s*(.+)$", a["md"], re.M)
        extra.append({"@context": "https://schema.org", "@type": "DefinedTermSet", "name": f"{SITE} Glossary", "url": url("glossary.html"),
                      "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t, "description": dsc[:300], "url": url(a["path"])} for t, dsc in terms]})
    body = h + f'''<div class="wrap article"><article class="prose">{byline(a)}<div class="answer-box"><b>Quick answer</b><p>{e(a["answer"])}</p></div>{bodyh}{find_box(a, d)}{faqhtml(faq, "FAQ")}
<h2>Related reading</h2><ul>{related}</ul>{disc}
<p class="note">Spotted an error? <a href="{rel(d, "corrections.html")}">Report it</a>. Update log: first published {TODAY_H}.</p></article>
<aside class="side"><div class="panel"><h3 style="margin-top:0">Directory categories</h3><div class="chips">{catlinks}</div><p class="note" style="margin-top:14px">Every guide links to live listings so you can act on it.</p></div></aside></div>'''
    page(a["path"], f"{a['title']} | {SITE}", a["answer"][:158], body, d, [art_ld, ld, faqld(faq)] + extra, hub[0] if hub[0] in ("Guides",) else "Regulations" if hub[0] == "BIM Hub" else "Guides", og_type="article")

def art_cards(depth, keys):
    return '<div class="learn-grid">' + "".join(f'<a href="{rel(depth, ART[k]["path"])}"><small>{e(ART[k]["kind"])}</small><b>{e(ART[k]["title"])}</b><span>{e(ART[k]["answer"][:140])}…</span></a>' for k in keys) + "</div>"
COMING = [("Cost guide", "Land survey cost in Dubai and the UAE"), ("BIM Hub", "Dubai Municipality BIM circulars explained"), ("Ranking", "Top survey companies in Dubai, with methodology"),
          ("Case study", "Drone topographic survey for a master-planned community"), ("Country rules", "Drone permits in Saudi Arabia"), ("Buying guide", "GNSS receivers for land surveying")]
def coming(): return '<ul class="coming">' + "".join(f"<li><small>{e(t)}</small>{e(n)}</li>" for t, n in COMING) + "</ul>"
SERIES = [("Weekly", "MEA Geospatial Jobs Weekly", "Every new survey, GIS, BIM and drone vacancy posted that week, by country."),
          ("Monthly", "Internship Watch", "Open internships and graduate programmes, with closing dates."),
          ("Monthly", "Who's Hiring in the Gulf", "The firms in the directory that are recruiting this month, and for what."),
          ("Quarterly", "Geospatial Salary Snapshot", "Salary ranges reported by employers and job posts, by role and country, with sources."),
          ("Each term", "Graduate Programme Calendar", "Application windows for graduate schemes at agencies, consultancies and vendors."),
          ("Monthly", "Career Spotlight", "A short interview with a surveyor, GIS lead or BIM manager about how they got the job.")]
def series_html(): return '<div class="topics">' + "".join(f'<div class="topic"><h3>{e(t)}</h3><p><b class="mono" style="font-size:12px">{e(f)}</b> · {e(d)}</p></div>' for f, t, d in SERIES) + "</div>"

# ------------------------------------------------------------------ hubs
def hubpage(path, name, h1, lede, inner, desc, ldx=(), trail=None):
    h, ld = hero(0, trail or [("Home", "index.html"), (name, "")], h1, lede, "Content hub")
    page(path, f"{h1} | {SITE}", desc, h + f'<div class="wrap listing hub">{inner}</div>', 0, [ld, *ldx], name)

hubpage("guides.html", "Guides", "Guides", "How-to guides, buying guides, cost guides, comparisons and the glossary, each tied to live listings.",
        f'<h2>How-to and comparison guides</h2>{art_cards(0, ["how-to-hire-a-land-surveyor", "total-station-vs-gnss"])}<h2>Glossary</h2>{art_cards(0, ["rtk-ppk-cors"])}<h2>Coming next</h2>{coming()}',
        "Practical guides to hiring surveyors, buying survey equipment and understanding GNSS, BIM and GIS in the Middle East and Africa.")
gl_terms = [("RTK", "Real-time kinematic GNSS: live corrections for centimetre positioning."), ("PPK", "Post-processed kinematic: corrections applied after the survey."), ("CORS", "Continuously operating reference stations that supply corrections.")]
hubpage("glossary.html", "Guides", "Geospatial glossary", "Plain-English definitions of survey, GIS, BIM and remote sensing terms.",
        '<div class="tbl"><table><thead><tr><th>Term</th><th>Meaning</th></tr></thead><tbody>' + "".join(f'<tr><td><a href="glossary/rtk-ppk-cors.html"><b>{t}</b></a></td><td>{e(dsc)}</td></tr>' for t, dsc in gl_terms) + '</tbody></table></div><p class="note">More terms (LOD, ISO 19650, PPP, datum, ground control point) are being added three a week.</p>',
        "Definitions of RTK, PPK, CORS and other survey, GIS and BIM terms.",
        [{"@context": "https://schema.org", "@type": "DefinedTermSet", "name": f"{SITE} Glossary", "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t, "description": dsc, "url": url("glossary/rtk-ppk-cors.html")} for t, dsc in gl_terms]}])

# Insights
hubpage("insights.html", "Insights", "Insights", "News briefs, analysis, case studies and interviews from the Middle East and Africa geospatial industry.",
        f'<h2>Latest</h2>{art_cards(0, ["iso-19650-explained", "how-to-hire-a-land-surveyor"])}<div class="learn-grid" style="margin-top:14px"><a href="research/state-of-mea-geospatial-2026.html"><small>Research</small><b>State of MEA geospatial 2026: the directory in numbers</b><span>Listings by country, section and category, with the open dataset.</span></a></div><h2>Coming in the first weeks</h2>{coming()}<h2>Regular series</h2>{series_html()}<div class="claim" style="margin-top:28px"><b>Have news, a project or a case study?</b> Send it to <a href="mailto:{EMAIL}">{EMAIL}</a>. We credit and link every contributor, and label anything sponsored.</div>',
        "News, analysis, case studies and interviews on surveying, GIS, drones, BIM and Earth observation in the Middle East and Africa.")

# Regulations hub: data-driven country table
regrows = ""
for cinfo in COUNTRIES:
    c = cinfo["country"]
    if c == "Regional (MEA)": continue
    its = by_country.get(c, [])
    def pick(cat): return [r for r in its if cat in r["cats"]]
    nm = pick("National Mapping & Survey Agencies"); lr = pick("Land Registries & Cadastre Authorities"); pb = pick("Professional Bodies & Licensing Councils")
    if not (nm or lr or pb): continue
    lk = lambda xs: "<br>".join(f'<a href="company/{r["slug"]}.html">{e(r["name"])}</a>' for r in xs[:2]) or "–"
    regrows += f'<tr><td><a href="country/{slug(c)}.html">{e(c)}</a></td><td>{lk(nm)}</td><td>{lk(lr)}</td><td>{lk(pb)}</td></tr>'
LIC = [("United Arab Emirates", "Surveying offices register with the land or municipal authority of each emirate. In Dubai, real estate surveyors who prepare unit and plot surveys for title registration work with the Dubai Land Department."),
       ("Saudi Arabia", "Engineering and survey offices are licensed through the professional and municipal systems; the General Authority for Survey and Geospatial Information (GEOSA) is the national survey authority."),
       ("Nigeria", "Surveyors must be registered with the Surveyors Council of Nigeria (SURCON)."),
       ("Kenya", "Cadastral surveys must be signed by a surveyor licensed under the Survey Act."),
       ("South Africa", "Land surveyors register with the South African Geomatics Council (SAGC).")]
hubpage("regulations.html", "Regulations", "Regulations, licensing and standards", "Who licenses surveyors, who runs the cadastre and which BIM rules apply, country by country.",
        f'''<div class="learn-grid"><a href="bim.html"><small>BIM Hub</small><b>BIM Hub: ISO 19650, mandates and delivery</b><span>Standards, roles, CDEs, LOD, 4D/5D and government BIM requirements in MEA.</span></a><a href="bim/mandates.html"><small>Tracker</small><b>BIM mandates tracker</b><span>Dubai, Abu Dhabi and Saudi Arabia: what is confirmed and what is still being verified.</span></a><a href="bim/iso-19650-explained.html"><small>Explainer</small><b>ISO 19650 explained</b><span>The six parts, the roles and the information requirements.</span></a></div>
<h2>Survey licensing in the largest markets</h2><div class="tbl"><table><thead><tr><th>Country</th><th>Who can sign a survey</th></tr></thead><tbody>{"".join(f"<tr><td><a href='country/{slug(c)}.html'>{e(c)}</a></td><td>{e(t)}</td></tr>" for c, t in LIC)}</tbody></table></div>
<p class="note">Summarised from the authorities' public information. Always confirm the current rule with the authority. Full country pages (licensing, cadastre, drone permits and data rules) are being written one a week.</p>
<h2>Authorities listed in the directory</h2><div class="tbl"><table><thead><tr><th>Country</th><th>National mapping &amp; survey</th><th>Land registry &amp; cadastre</th><th>Professional &amp; licensing body</th></tr></thead><tbody>{regrows}</tbody></table></div>''',
        "Survey licensing bodies, cadastre authorities, national mapping agencies and BIM mandates across the Middle East and Africa.")

# BIM hub
bimcats = [c for c in ["BIM Consultants", "BIM Modelling & Coordination Services", "Scan-to-BIM Services", "Digital Twin & Smart City Solutions", "BIM Software Vendors", "BIM Software Distributors & Resellers", "BIM Software Implementation Partners"] if CAT[c]["items"]]
BIMFAQ = [("What is BIM?", "Building information modelling (BIM) is the process of creating and managing a shared digital model of an asset, its geometry plus data, through design, construction and operation, so every party works from the same coordinated information."),
          ("What is the difference between LOD and level of information need?", "LOD (level of development, LOD 100 to 500 in the BIMForum specification) describes how developed and reliable a model element is. ISO 19650 replaces loose LOD labels with the level of information need, which sets the geometry, data and documentation each deliverable must contain."),
          ("What is a common data environment (CDE)?", "A CDE is the single agreed place where project information is stored, shared and approved. ISO 19650 defines four states: work in progress, shared, published and archived."),
          ("Is BIM mandatory in Dubai?", "Dubai Municipality has required BIM on larger and specialist buildings since 2013, with thresholds updated since. Confirm the current circular and thresholds with Dubai Municipality; our mandates tracker shows what is verified.")]
TOPICS = [("ISO 19650 information management", "The international standard for managing information over an asset's life: OIR, AIR, PIR and EIR requirements, the BIM execution plan (BEP), MIDP and TIDP, and the CDE workflow.", "bim/iso-19650-explained.html"),
          ("BIM execution plan (BEP)", "The delivery team's response to the client's exchange information requirements: roles, software, naming, LOD or level of information need, coordination and clash detection rules.", None),
          ("Level of development (LOD)", "LOD 100 (concept) to LOD 500 (field-verified as-built) describes how far a model element can be relied on. Pair it with the level of information need for data and documents.", None),
          ("Common data environment (CDE)", "One source of truth for drawings, models and documents, with status codes and revisions so everyone knows what can be used for construction.", None),
          ("4D and 5D BIM", "Linking the model to the programme (4D) and to quantities and cost (5D) to simulate sequencing and control budgets.", None),
          ("BIM for facility management (6D/7D)", "Handing over asset data (COBie or client templates) so operators can run and maintain the building from the model.", None),
          ("Scan-to-BIM", "Using terrestrial or mobile laser scanning to capture existing conditions and model them, usually to LOD 300 or higher, for renovation, MEP coordination and as-built records.", None),
          ("BIM and GIS integration", "Combining building models with GIS for campuses, utilities, roads and city digital twins, where survey control and coordinate systems must match.", None)]
hubpage("bim.html", "Regulations", "BIM Hub: ISO 19650, mandates and delivery in the Middle East &amp; Africa", "Professional guidance for clients, consultants, contractors and surveyors delivering BIM in the region, linked to the firms that do it.",
        f'''<div class="answer-box"><b>Quick answer</b><p>BIM in the Middle East is delivered to ISO 19650: the client sets information requirements, the delivery team answers with a BIM execution plan, and all information flows through a common data environment. Dubai Municipality has required BIM on larger buildings since 2013, and Saudi Arabia's major projects increasingly ask for it.</p></div>
<h2>Core topics</h2><div class="topics">{"".join(f'<div class="topic"><h3>{f"<a href={chr(34)}{p}{chr(34)}>{e(t)}</a>" if p else e(t)}</h3><p>{e(dsc)}</p></div>' for t, dsc, p in TOPICS)}</div>
<h2>Government BIM requirements</h2><p>Mandates change and are often published as circulars that are hard to find. Our <a href="bim/mandates.html">BIM mandates tracker</a> lists each requirement with its status: confirmed, or still being verified against the official copy.</p>
<h2>Read</h2>{art_cards(0, ["iso-19650-explained"])}
<h2>Find BIM providers</h2><div class="chips">{"".join(catlink(0, c) for c in bimcats)}</div>
<div class="prose">{faqhtml(BIMFAQ, "BIM questions")}</div>''',
        "ISO 19650, BEP, LOD, CDE, 4D/5D, FM, scan-to-BIM and government BIM mandates in the Middle East and Africa, with BIM consultants and software partners.", [faqld(BIMFAQ)], [("Home", "index.html"), ("Regulations", "regulations.html"), ("BIM Hub", "")])

# BIM mandates tracker
MAND = [("United Arab Emirates – Dubai", "Circular widely reported as No. 196 (2013)", "BIM for architectural and MEP work on buildings over 40 floors or over 300,000 sq ft, specialist buildings such as hospitals and universities, and projects by foreign engineering offices.", "Reported by secondary sources; official copy being obtained"),
        ("United Arab Emirates – Dubai", "Circular widely reported as No. 207 (2015)", "Thresholds lowered to buildings over 20 floors or over 200,000 sq ft, plus hospitals, universities, government projects and projects by foreign offices.", "Reported by secondary sources; official copy being obtained"),
        ("United Arab Emirates – Dubai", "Updated requirements effective 1 January 2024", "Architectural BIM above 20 floors and structural BIM above 40 floors; larger complexes and specialised buildings; all government projects; aligned with the Dubai Building Code.", "Circular number not verified"),
        ("United Arab Emirates – Abu Dhabi", "No mandate confirmed", "A BIM mandate was reported as under consideration in 2019.", "Not confirmed"),
        ("Saudi Arabia", "Major projects from January 2024 (reported)", "BIM management reported as required for major projects; the issuing authority and document were not identified.", "Not verified")]
h, ld = hero(1, [("Home", "index.html"), ("Regulations", "regulations.html"), ("BIM Hub", "bim.html"), ("BIM mandates tracker", "")], "BIM mandates tracker: Middle East", "Every government BIM requirement we know of, with an honest status. Nothing here is legal advice; confirm with the authority.", "BIM Hub")
page("bim/mandates.html", f"BIM Mandates in Dubai, Abu Dhabi and Saudi Arabia (Tracker) | {SITE}", "Dubai Municipality BIM circulars, Abu Dhabi and Saudi BIM requirements, each with a verification status.",
     h + '<div class="wrap listing prose"><div class="tbl"><table><thead><tr><th>Jurisdiction</th><th>Requirement</th><th>Scope</th><th>Status</th></tr></thead><tbody>' + "".join(f'<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td><td><span class="status">{e(s)}</span></td></tr>' for a, b, c, s in MAND) +
     f'</tbody></table></div><p class="note">Last reviewed {TODAY_H}. If you hold an official copy of a circular, <a href="../corrections.html">send it to us</a> and we will verify the entry and credit you.</p><p><a href="iso-19650-explained.html">ISO 19650 explained</a> · <a href="../bim.html">Back to the BIM Hub</a></p></div>', 1, [ld], "Regulations")

# Opportunities
ev = CAT["Conferences & Exhibitions"]["items"]; tr = CAT["Training Centres"]["items"]; un = CAT["Universities (Surveying, GIS & Geomatics)"]["items"]
hubpage("opportunities.html", "Opportunities", "Opportunities: events, training, jobs and tenders", "Conferences, courses, universities and a free board for geospatial jobs and tenders in the Middle East and Africa.",
        f'<h2 id="events">Events and conferences</h2>{grid(ev, 0)}<h2 id="training">Training and courses</h2>{grid(tr[:9], 0)}<p><a class="btn solid" href="{"category/" + CAT["Training Centres"]["slug"] + ".html"}">All {len(tr)} training providers</a> <a class="btn ghost" href="category/{CAT["Universities (Surveying, GIS & Geomatics)"]["slug"]}.html">{len(un)} universities</a></p>'
        f'<h2 id="jobs">Jobs and internships</h2><p>Vacancies, internships and graduate programmes have their own section: <a href="jobs.html">Jobs</a>. Employers can <a href="jobs/post-a-job.html">post a job free</a>.</p><h2 id="post">Post a tender</h2><div class="claim"><b>Tendering survey, GIS or BIM work?</b> Send the tender to <a href="mailto:{EMAIL}?subject=Job%20or%20tender%20post">{EMAIL}</a>. Tenders are published free while the board launches, with a link back to your listing.</div>',
        "Geospatial conferences, survey and GIS training, universities, jobs and tenders in the Middle East and Africa.")

# Research
seccounts = [(s[1], sec_count(s)) for s in SECTIONS]
topcats = sorted(LIVE, key=lambda c: -len(c["items"]))[:15]
topc = Counter(r["country"] for r in rows if r["country"] != "Regional (MEA)").most_common(15)
def bars(pairs, link=None):
    mx = max(n for _, n in pairs) or 1
    return '<div class="bars">' + "".join(f'<div class="bar"><span class="bl">{f"<a href={chr(34)}{link(k)}{chr(34)}>{e(k)}</a>" if link else e(k)}</span><span class="bt"><i style="width:{n/mx*100:.1f}%"></i></span><span class="bn">{n}</span></div>' for k, n in pairs) + "</div>"
rep_ld = {"@context": "https://schema.org", "@type": "Dataset", "name": f"{SITE} directory dataset", "description": f"{N} geospatial organisations in the Middle East and Africa with categories, country, city, website and source.", "url": url("research.html"),
          "creator": {"@id": BASE_URL + "/#org"}, "dateModified": TODAY, "license": "https://creativecommons.org/licenses/by/4.0/", "spatialCoverage": "Middle East and Africa",
          "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": url("data/companies.csv")}, {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": url("data/companies.json")}]}
snap = f'''<p class="answer">{SITE} lists {N} geospatial organisations in {len(real_countries)} of the 70 Middle East and African countries. The United Arab Emirates has the most listings ({len(by_country["United Arab Emirates"])}), followed by {andjoin(f"{c} ({n})" for c, n in topc[1:4])}. Land surveyors ({len(CAT["Land Surveyors"]["items"])}) and GIS consultants ({len(CAT["GIS Consultants"]["items"])}) are the largest categories.</p>
<p class="note">Source: {SITE} directory, {TODAY_H}. Counts include each organisation once per section or category it appears in.</p>
<h2>Listings by section</h2>{bars(seccounts)}<h2>Largest categories</h2>{bars([(c["category"], len(c["items"])) for c in topcats])}<h2>Countries with the most listings</h2>{bars(topc)}
<h2>Coverage gaps</h2><p>{70 - len(real_countries)} countries have no listing yet, including {andjoin([c["country"] for c in COUNTRIES if c["country"] != "Regional (MEA)" and not by_country.get(c["country"])][:8])}. Categories such as monitoring, geophysical survey, utility detection and equipment rental are thin. If you work in one, <a href="../submit.html">list your organisation</a>.</p>'''
h, ld = hero(1, [("Home", "index.html"), ("Research", "research.html"), ("State of MEA geospatial 2026", "")], "State of MEA geospatial 2026: the directory in numbers", "Original data on where the region's survey, GIS, BIM and geospatial organisations are, and what they do.", "Market report")
rep_art = {"@context": "https://schema.org", "@type": "Report", "name": "State of MEA geospatial 2026", "datePublished": TODAY, "author": {"@id": BASE_URL + "/#org"}, "publisher": {"@id": BASE_URL + "/#org"}, "about": "Geospatial industry in the Middle East and Africa"}
page("research/state-of-mea-geospatial-2026.html", f"State of MEA Geospatial 2026: {N} Organisations in Numbers | {SITE}", f"{N} geospatial organisations across {len(real_countries)} Middle East and African countries, by section, category and country.",
     h + f'<div class="wrap listing prose">{snap.replace("../submit.html", "../submit.html")}</div>', 1, [rep_art, rep_ld, ld], "Research", og_type="article")
hubpage("research.html", "Research", "Research and data", "Market reports, rankings and the open directory dataset, free to cite.",
        f'<div class="learn-grid"><a href="research/state-of-mea-geospatial-2026.html"><small>Market report</small><b>State of MEA geospatial 2026</b><span>{N} organisations by section, category and country.</span></a></div>'
        f'<h2 id="data">Data downloads</h2><p>The full directory is open under CC BY 4.0: please credit {SITE} with a link to {BASE_URL}.</p><ul><li><a href="data/companies.csv">companies.csv</a> ({N} rows)</li><li><a href="data/companies.json">companies.json</a></li><li><a href="data/brands.json">brands.json</a> (brands and where to buy)</li><li><a href="data/categories.json">categories.json</a> (the {len(DCATS)} categories)</li></ul>'
        f'<h2>Rankings</h2><p>Top-N lists by country and category are published with their methodology (data sources, inclusion criteria and scoring) on the <a href="about.html#method">methodology page</a>. The first, Top survey companies in Dubai, is coming soon.</p>',
        f"Original research and the open dataset of {N} geospatial organisations in the Middle East and Africa.", [rep_ld])

# ------------------------------------------------------------------ jobs and internships
JOBS = [j for j in rd("jobs.csv") if j.get("title")]  # real postings only; empty until employers post
ROLES = [
 dict(slug="land-surveyor-jobs", name="Land Surveyor & Survey Engineer Jobs", short="Land surveyor",
      answer="Land surveyor and survey engineer jobs in the Middle East and Africa usually ask for a diploma or degree in surveying or geomatics, field experience with GNSS and total stations, CAD skills, and for signing cadastral work, registration with the national surveying authority or council.",
      does="Set out buildings and roads, run topographic, cadastral and as-built surveys, process field data into CAD drawings and survey plans, and check work against the project's coordinate system and tolerances.",
      skills=["Degree or diploma in surveying, geomatics or civil engineering", "GNSS (RTK) and total station field work", "AutoCAD Civil 3D or similar survey CAD", "Local coordinate systems and datums", "For cadastral work: registration with the national survey authority or council (for example SURCON in Nigeria or SAGC in South Africa)"],
      employers=["Land Surveyors", "Topographic Surveyors", "Construction Setting-Out & As-Built Surveyors", "Cadastral & Boundary Surveyors"], guide="how-to-hire-a-land-surveyor"),
 dict(slug="gis-jobs", name="GIS Analyst & GIS Developer Jobs", short="GIS",
      answer="GIS jobs in the region range from GIS technician and analyst roles in municipalities, utilities and consultancies to GIS developer roles building web maps and enterprise systems. Employers look for ArcGIS or QGIS skills, spatial databases and, increasingly, Python and web development.",
      does="Capture and edit spatial data, build maps and dashboards, run spatial analysis, manage enterprise geodatabases, and develop web and mobile GIS applications.",
      skills=["ArcGIS Pro or QGIS", "Spatial databases (PostGIS, SQL Server, Oracle Spatial)", "Python for automation and analysis", "Web mapping (ArcGIS Enterprise, JavaScript map libraries)", "A degree in GIS, geography, geomatics or computer science"],
      employers=["GIS Consultants", "Custom GIS App Developers", "GIS Software Implementation Partners", "Municipal GIS Departments", "National Mapping & Survey Agencies"]),
 dict(slug="bim-jobs", name="BIM Modeller, Coordinator & Manager Jobs", short="BIM",
      answer="BIM jobs in the Gulf follow a ladder from BIM modeller to BIM coordinator to BIM manager. Employers ask for Revit and Navisworks skills, clash detection and coordination experience, and for senior roles a working knowledge of ISO 19650, BIM execution plans and common data environments.",
      does="Model buildings and infrastructure, coordinate disciplines and resolve clashes, manage the common data environment, write and enforce BIM execution plans, and prepare models for authority submission and handover.",
      skills=["Autodesk Revit, Navisworks and AutoCAD", "Clash detection and MEP coordination", "ISO 19650, BEP, EIR and CDE workflows (coordinator and manager roles)", "Tekla, Archicad or civil BIM tools for specialist roles", "A degree or diploma in architecture, engineering or construction"],
      employers=["BIM Consultants", "BIM Modelling & Coordination Services", "Scan-to-BIM Services", "Digital Twin & Smart City Solutions"], guide="iso-19650-explained"),
 dict(slug="drone-pilot-jobs", name="Drone Pilot & Photogrammetry Jobs", short="Drone",
      answer="Drone survey jobs combine flying and data processing: a remote pilot licence from the national civil aviation authority, mapping-grade flight planning, ground control with GNSS, and processing in photogrammetry or LiDAR software into orthophotos, surface models and point clouds.",
      does="Plan and fly mapping and inspection missions, set ground control points, process imagery into orthophotos, DSMs and point clouds, and deliver volumes, contours and inspection reports.",
      skills=["A remote pilot licence or permit from the national civil aviation authority", "Flight planning for mapping and inspection", "Photogrammetry software such as Pix4D or Agisoft Metashape", "GNSS ground control (RTK/PPK)", "Point cloud and GIS basics"],
      employers=["Drone Survey & Mapping Companies", "Drone Inspection Services", "LiDAR Survey Companies", "Aerial Survey & Photogrammetry Companies"]),
 dict(slug="hydrographic-surveyor-jobs", name="Hydrographic Surveyor Jobs", short="Hydrographic",
      answer="Hydrographic surveyors map the seabed, ports and waterways with single- and multibeam echo sounders and marine positioning. Many employers prefer qualifications from programmes recognised by the international FIG/IHO/ICA standards board (Category A or B), plus offshore safety certificates for vessel work.",
      does="Run bathymetric, dredging and offshore site surveys, operate echo sounders and positioning systems, process and clean sonar data, and produce charts and volume reports.",
      skills=["Multibeam and single-beam echo sounder operation", "Marine GNSS and motion sensors", "Processing software for hydrographic data", "Category A or B hydrographic training (preferred)", "Offshore safety and sea survival certificates for vessel work"],
      employers=["Hydrographic & Bathymetric Surveys", "Hydrographic & Marine Equipment Manufacturers"]),
 dict(slug="remote-sensing-jobs", name="Remote Sensing & Earth Observation Jobs", short="Remote sensing",
      answer="Remote sensing jobs in the region sit with space agencies, Earth observation companies and GIS consultancies. They ask for satellite image processing, classification and change detection, often with Python, cloud platforms and increasingly machine learning for feature extraction.",
      does="Process optical and SAR satellite imagery, classify land cover, detect change, monitor crops, environment and infrastructure, and turn imagery into maps and indicators.",
      skills=["Optical and SAR image processing", "Classification and change detection", "Python with geospatial libraries", "Cloud EO platforms", "A degree in remote sensing, geomatics, geography or physics"],
      employers=["Satellite Image Analysis & Remote Sensing Services", "Satellite Imagery Providers", "Space Agencies", "Location Intelligence & GeoAI Companies"]),
 dict(slug="survey-equipment-sales-jobs", name="Survey Equipment Sales & Technical Support Jobs", short="Equipment sales",
      answer="Survey equipment distributors and dealers hire sales engineers, product specialists and service technicians. These roles need hands-on knowledge of GNSS, total stations, scanners or drones, the ability to train customers, and for service roles, calibration and repair skills.",
      does="Demonstrate and sell instruments and software, train customers, provide technical support, and calibrate and repair equipment.",
      skills=["Field experience with GNSS, total stations, scanners or drones", "Customer training and demonstrations", "Calibration and repair (service roles)", "Knowledge of survey and CAD software", "Sales or account management experience"],
      employers=["Land Surveying Equipment Distributors", "Land Surveying Equipment Dealers & Suppliers", "Land Surveying Equipment Manufacturers", "Land Surveying Equipment Repair & Calibration"], guide="total-station-vs-gnss"),
 dict(slug="internships", name="Geospatial Internships & Graduate Programmes", short="Internships",
      answer="Survey, GIS and BIM internships in the Middle East and Africa are usually offered by consultancies, mapping agencies, municipalities and equipment dealers, often tied to university placement schemes. Apply early in the academic year with a CV, a short portfolio of maps or models, and your university's placement letter.",
      does="Support field surveys, data capture and digitising, map production, BIM modelling and equipment demonstrations under supervision, usually for two to six months.",
      skills=["Enrolment in, or recent graduation from, surveying, GIS, geomatics, architecture or engineering", "A portfolio: maps, models or a small project", "Basic ArcGIS/QGIS, AutoCAD or Revit", "A placement letter from your university, where required"],
      employers=["Universities (Surveying, GIS & Geomatics)", "National Mapping & Survey Agencies", "GIS Consultants", "Land Surveyors", "BIM Consultants"]),
]
def job_card(j, depth):
    return f'''<article class="card job"><div class="top"><h3><a href="{rel(depth, "jobs/" + slug(j["job_id"] + "-" + j["title"]) + ".html")}">{e(j["title"])}</a></h3><span class="role deal">{e(j["employment_type"])}</span></div>
<div class="loc"><span>{e(j["employer"])} · {e(", ".join(x for x in [j["city"], j["country"]] if x))}</span></div><p class="desc">{e(j["description"][:180])}</p>
<div class="foot"><span class="host">Posted {e(j["date_posted"])}</span><span class="host">Closes {e(j["valid_through"] or "open")}</span></div></article>'''
def jobs_for(role): return [j for j in JOBS if j["role"] == role or (role == "internships" and j["employment_type"].upper() == "INTERN")]
EMPTY_JOBS = lambda depth: f'<div class="claim"><b>No vacancies posted here yet.</b> Employers post free, and every vacancy appears in the weekly jobs roundup. <a class="btn solid" href="{rel(depth, "jobs/post-a-job.html")}">Post a job</a></div>'
for j in JOBS:
    d = 1; p = "jobs/" + slug(j["job_id"] + "-" + j["title"]) + ".html"
    jl = {"@context": "https://schema.org", "@type": "JobPosting", "title": j["title"], "description": j["description"], "datePosted": j["date_posted"], "validThrough": j["valid_through"] or None,
          "employmentType": j["employment_type"], "hiringOrganization": {"@type": "Organization", "name": j["employer"], **({"sameAs": url("company/" + BYNAME[j["employer"]]["slug"] + ".html")} if j["employer"] in BYNAME else {})},
          "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress", "addressLocality": j["city"], "addressCountry": j["country"]}}, "directApply": False}
    jl = {k: v for k, v in jl.items() if v}
    h, ld = hero(d, [("Home", "index.html"), ("Jobs", "jobs.html"), (j["title"], "")], e(j["title"]), e(f'{j["employer"]} · {j["city"]}, {j["country"]}'), j["employment_type"])
    page(p, f'{j["title"]} – {j["employer"]}, {j["city"]} | {SITE} Jobs', j["description"][:158], h + f'<div class="wrap listing prose"><p>{e(j["description"])}</p><p><b>Salary:</b> {e(j["salary"] or "Not stated")} · <b>Closes:</b> {e(j["valid_through"] or "Open")}</p><p><a class="btn solid" href="{e(j["apply_url"])}" rel="noopener nofollow" target="_blank">Apply on the employer\'s site</a></p><p class="note">Source: {e(j["source"])}. {SITE} does not process applications.</p></div>', d, [jl, ld], "Jobs")
for ro in ROLES:
    d = 1; cats = [c for c in ro["employers"] if c in CAT and CAT[c]["items"]]
    emp = []
    for c in cats:
        for r in CAT[c]["items"]:
            if r not in emp and r["website"]: emp.append(r)
    faq = [(f"What qualifications do {ro['short'].lower()} jobs need?", "; ".join(ro["skills"][:3]) + "."),
           (f"Who hires for {ro['short'].lower()} roles in the Middle East and Africa?", f"The directory lists {sum(len(CAT[c]['items']) for c in cats)} organisations in the categories that hire for these roles, including " + andjoin([r["name"] for r in emp[:5]]) + "." if emp else "Consultancies, agencies and suppliers listed in the directory."),
           ("How do I get new vacancies?", f"New vacancies appear on this page and in MEA Geospatial Jobs Weekly. Employers can post free on the Post a job page.")]
    roles_nav = '<nav class="tabs" aria-label="Job types">' + "".join(f'<a href="{rel(d, "jobs/" + x["slug"] + ".html")}"{" aria-current=page" if x is ro else ""}>{e(x["short"])}</a>' for x in ROLES) + "</nav>"
    jobs = jobs_for(ro["slug"])
    learn = ""
    if ro.get("guide"): learn = f'<h2>Read</h2>{art_cards(d, [ro["guide"]])}'
    train = [c for c in ["Universities (Surveying, GIS & Geomatics)", "Training Centres", "Technical Colleges & Vocational Institutes", "Vendor Academies & Certification"] if CAT[c]["items"]]
    h, ld = hero(d, [("Home", "index.html"), ("Jobs", "jobs.html"), (ro["name"], "")], e(ro["name"]) + " in the Middle East &amp; Africa", "", "Jobs")
    body = h + f'''<div class="wrap listing">{roles_nav}<div class="answer-box"><b>Quick answer</b><p>{e(ro["answer"])}</p></div>
<h2>Vacancies</h2>{('<div class="grid">' + "".join(job_card(j, d) for j in jobs) + "</div>") if jobs else EMPTY_JOBS(d)}
<div class="prose"><h2>What the job involves</h2><p>{e(ro["does"])}</p><h2>Skills and qualifications employers ask for</h2><ul>{"".join(f"<li>{e(s)}</li>" for s in ro["skills"])}</ul></div>
<h2>Who hires</h2><div class="chips" style="margin-bottom:14px">{"".join(catlink(d, c) for c in cats)}</div>{grid(emp[:6], d)}
<h2>Train for it</h2><div class="chips">{"".join(catlink(d, c) for c in train)}</div>{learn}
<div class="prose">{faqhtml(faq)}</div>
<div class="claim"><b>Get new {e(ro["short"].lower())} vacancies every week.</b> Ask to join MEA Geospatial Jobs Weekly at <a href="mailto:{EMAIL}?subject=Jobs%20Weekly">{EMAIL}</a>.</div></div>'''
    page(f"jobs/{ro['slug']}.html", f"{ro['name']} – Middle East & Africa | {SITE}", ro["answer"][:158], body, d, [ld, faqld(faq)], "Jobs")
# post a job
h, ld = hero(1, [("Home", "index.html"), ("Jobs", "jobs.html"), ("Post a job", "")], "Post a job or internship, free", "Reach surveyors, GIS analysts, BIM professionals and graduates across the Middle East and Africa. We check every post with the employer before publishing.")
jobform = f'''<form class="sub panel" id="sub" novalidate data-endpoint="{e(SUBMIT_ENDPOINT)}" data-email="{e(EMAIL)}" data-mode="job">
<label class="full">Job title *<input id="f-name" required placeholder="e.g. Land Surveyor, GIS Analyst, BIM Coordinator, GIS Intern"></label>
<label>Employer *<input id="f-employer" required autocomplete="organization"></label>
<label>Job type<select id="f-type"><option>Full-time</option><option>Part-time</option><option>Contract</option><option>Internship</option><option>Graduate programme</option></select></label>
<label>Country *<input id="f-country" required list="countrylist"></label>
<label>City<input id="f-city"></label>
<label>Role area<select id="f-role">{"".join(f"<option>{e(x['short'])}</option>" for x in ROLES)}</select></label>
<label>Closing date<input id="f-closes" type="date"></label>
<label class="full">How to apply (link or email) *<input id="f-apply" required placeholder="https:// or careers@yourcompany.com"></label>
<label class="full">Salary range (optional)<input id="f-salary"></label>
<label class="full">Description (duties, requirements)<textarea id="f-desc" maxlength="2000"></textarea></label>
<label class="full">Your work email (so we can confirm the post)<input id="f-email" type="email"></label>
<div class="row" style="grid-column:1/-1"><button class="btn solid" type="submit">Send job post</button><span class="note" id="f-status" role="status"></span></div>
<div class="out" id="out" hidden><pre id="out-text"></pre><div class="row"><button class="btn solid" type="button" id="copy">Copy</button><a class="btn ghost" id="mail" href="mailto:{EMAIL}">Open email</a></div></div>
</form><datalist id="countrylist">{"".join(f"<option value='{e(c['country'])}'>" for c in COUNTRIES)}</datalist>'''
example = '''<div class="example"><span class="ex-tag">Example layout, not a real vacancy</span><h3>GIS Analyst</h3><p class="meta">Example Engineering Consultancy · Dubai, United Arab Emirates · Full-time</p><p>Maintain the enterprise geodatabase, build ArcGIS dashboards for utility clients and support field data capture. Requires a degree in GIS or geomatics and two years of ArcGIS Pro experience.</p><p class="meta">Closes in 30 days · Apply on the employer's site</p></div>'''
page("jobs/post-a-job.html", f"Post a Survey, GIS or BIM Job for Free | {SITE}", "Post survey, GIS, BIM, drone and hydrographic jobs and internships free to reach professionals across the Middle East and Africa.",
     h + f'<div class="wrap detail">{jobform}<aside class="prose"><h2 style="margin-top:0">How posting works</h2><ol><li>Send the form, from your company email if you can.</li><li>We confirm the vacancy with you and publish it on the jobs pages, with Google-ready job markup so it can appear in Google job search.</li><li>It goes out in MEA Geospatial Jobs Weekly and is removed after the closing date.</li></ol><h2>How a post will look</h2>{example}</aside></div>', 1, [ld], "Jobs")
# jobs hub
h, ld = hero(0, [("Home", "index.html"), ("Jobs", "")], "Geospatial jobs and internships in the Middle East &amp; Africa", "Survey, GIS, BIM, drone, hydrographic and remote sensing vacancies, internships and graduate programmes, with the employers and training behind them.", "Jobs")
hub_jobs = ('<div class="grid">' + "".join(job_card(j, 0) for j in sorted(JOBS, key=lambda j: j["date_posted"], reverse=True)[:12]) + "</div>") if JOBS else EMPTY_JOBS(0)
JOBFAQ = [("Where can I find survey and GIS jobs in the Middle East?", f"This page lists survey, GIS, BIM, drone and hydrographic vacancies posted by employers across the Middle East and Africa, and MEA Geospatial Jobs Weekly sends new ones every week. The directory also lists {N} organisations you can approach directly."),
          ("How do I find a GIS or surveying internship?", "Apply to consultancies, mapping agencies and municipalities early in the academic year with a CV, a small portfolio and your university's placement letter. Internship Watch lists open internships every month."),
          ("Is posting a job free?", "Yes. Employers post jobs and internships free while the board launches. Every post is checked with the employer before it is published.")]
page("jobs.html", f"Survey, GIS & BIM Jobs and Internships – Middle East & Africa | {SITE}", "Land surveyor, GIS analyst, BIM, drone pilot and hydrographic jobs, internships and graduate programmes across the Middle East and Africa. Employers post free.",
     h + f'''<div class="wrap listing hub"><p><a class="btn primary" href="jobs/post-a-job.html">Post a job or internship</a> <a class="btn ghost" href="jobs/internships.html">Internships &amp; graduate programmes</a></p>
<h2>Latest vacancies</h2>{hub_jobs}
<h2>Browse by job type</h2><div class="learn-grid">{"".join(f'<a href="jobs/{x["slug"]}.html"><small>Jobs</small><b>{e(x["name"])}</b><span>{e(x["answer"][:120])}…</span></a>' for x in ROLES)}</div>
<h2>Regular series</h2><p class="sub">Recurring roundups that bring new vacancies and career advice to readers on a fixed schedule.</p>{series_html()}
<h2>Start your career</h2><div class="chips">{"".join(catlink(0, c) for c in ["Universities (Surveying, GIS & Geomatics)", "Training Centres", "Professional Bodies & Licensing Councils", "Recruitment & Staffing Agencies"] if CAT[c]["items"])}</div>
<div class="prose">{faqhtml(JOBFAQ)}</div></div>''', 0, [ld, faqld(JOBFAQ)], "Jobs")

# ------------------------------------------------------------------ trust & community pages
def simple(path, name, h1, lede, inner, desc, ldx=(), current=""):
    h, ld = hero(0, [("Home", "index.html"), (name, "")], h1, lede)
    page(path, f"{name} | {SITE}", desc, h + f'<div class="wrap listing prose">{inner}</div>', 0, [ld, *ldx], current)
srcs = Counter()
for r in rows:
    for s in r["source"].split(";"):
        s = s.strip()
        srcs[host(s) if s.startswith("http") else s] += 1
simple("about.html", "About", f"About {SITE}", f"{TAGLINE}, built to put every firm, supplier, agency and university in the region in one place.",
       f'''<p class="answer">{SITE} is an open directory of the geospatial industry across the GCC, the wider Middle East and all of Africa. It is free to search, free to be listed in, and its data is free to reuse.</p>
<h2>What we include</h2><p>Organisations whose main work is geospatial: land, engineering and hydrographic survey; drone, aerial and laser scanning; GIS, remote sensing and location intelligence; BIM and digital twins; survey equipment and software; and the agencies, universities, training centres, professional bodies and events around them. The directory has {len(DCATS)} categories in four sections. An organisation can appear in many categories.</p>
<h2 id="method">Methodology</h2><p>Listings are compiled from public registers, manufacturer partner and dealer pages, business directories and company submissions. Only business contact details published by the organisation or a public authority are shown. Equipment and software lists are ordered by role: manufacturers and regional offices first, then authorised distributors, then dealers and suppliers. Rankings, when published, will state their data sources, inclusion criteria and scoring.</p>
<p><span class="src"><i></i>Verified</span> entries were confirmed on a named source page or on the organisation’s live official website. <span class="src check"><i></i>Unverified</span> entries were found in a public source but their details are still to be confirmed; they are listed after verified entries.</p>
<h2>Main sources</h2><ul>{"".join(f"<li>{e(s)} <span class=meta>({n})</span></li>" for s, n in srcs.most_common(20))}</ul>
<h2 id="publisher">Publisher</h2><p>{e(DISCLOSURE)} See the <a href="company/rise-geo-control-systems-trading-llc.html">Rise Geo profile</a> and the <a href="brand/geotexon.html">GEOTEXON brand page</a>.</p>
<h2>Reuse the data</h2><p>See <a href="research.html#data">data downloads</a>. Please credit {SITE} with a link.</p>''', f"How {SITE} collects, labels, orders and updates geospatial listings for the Middle East and Africa.", [ORG])
simple("editorial-policy.html", "Editorial policy", "Editorial policy", "How we choose topics, check facts, label sponsored content and keep the directory independent.",
       f'''<h2>Independence</h2><p>Listings are free and are never paid for placement or ranking. See <a href="about.html#publisher">who publishes this site</a>. Sponsored content, if any, is labelled “Sponsored” at the top of the page. Rankings and “best of” lists, when published, will not rank the publisher’s own company or brand.</p>
<h2>How articles are made</h2><p>Each article targets a real question from buyers, surveyors or students, opens with a direct answer, cites primary sources (authority pages, standards, manufacturer specifications) and links to live listings. Drafts may be prepared with AI assistance; a named editor checks every number and rule before publication.</p>
<h2>Technical review</h2><p>Guides, cost, buying and regulation pages are reviewed by a practising specialist. Pages whose review is still pending say so in the byline. We are recruiting reviewers: see <a href="authors.html">authors and reviewers</a>.</p>
<h2>Unverified facts</h2><p>When a fact comes only from secondary sources, such as a circular number we have not seen in an official copy, we say so on the page and keep checking.</p>
<h2>Freshness</h2><p>Regulation and cost pages are re-reviewed at least every 90 days and carry a “Last reviewed” date and an update log.</p>
<p><a href="corrections.html">Corrections policy</a> · <a href="advertise.html">Advertising and disclosure</a></p>''', "Editorial standards, fact checking, AI use, sponsorship labelling and independence at GeoAtlas MEA.")
simple("corrections.html", "Corrections", "Corrections and error reports", "Found something wrong in a listing or article? We fix it and log it.",
       f'''<p class="answer">To report an error, email <a href="mailto:{EMAIL}?subject=Correction">{EMAIL}</a> with the page link, what is wrong and a source if you have one. Listing owners can also <a href="claim.html">claim their profile</a> to correct it directly.</p>
<h2>What happens next</h2><p>We check the report against the source, correct the page and add a dated line to the page's update log. Significant corrections are recorded below.</p>
<h2>Corrections log</h2><div class="tbl"><table><thead><tr><th>Date</th><th>Page</th><th>Correction</th></tr></thead><tbody><tr><td>{TODAY_H}</td><td>Whole site</td><td>Rebuilt with {len(DCATS)} categories and {N} listings; duplicate listings merged.</td></tr></tbody></table></div>''', "How to report errors in GeoAtlas MEA listings and articles, and the public corrections log.")
simple("authors.html", "Authors", "Authors and technical reviewers", "Who writes and checks the content, and how to join them.",
       f'''<h2>{SITE} editorial team</h2><p>Articles are researched and written by the {SITE} editorial team, which compiles the directory dataset and checks every listing source. Each article shows its review status in the byline.</p>
<h2>Become a technical reviewer or contributor</h2><p>We are recruiting practising land surveyors, hydrographers, BIM managers, GIS leads and remote sensing specialists from the region. Reviewers get a credited byline with their profile, credentials and a link to their firm's listing.</p>
<div class="claim"><b>Interested?</b> Email <a href="mailto:{EMAIL}?subject=Technical%20reviewer">{EMAIL}</a> with your role, licences or certifications, and the topics you know best.</div>''', "Authors and technical reviewers at GeoAtlas MEA, and how surveyors, BIM and GIS specialists can contribute.")
simple("advertise.html", "Advertise", "Advertise and sponsorship", "Reach survey, GIS, BIM and geospatial buyers across the Middle East and Africa, with clear labels.",
       f'''<h2>Options</h2><ul><li><b>Sponsored articles and case studies</b>, always labelled “Sponsored” with the sponsor named.</li><li><b>Event and course promotion</b> in Opportunities.</li><li><b>Newsletter sponsorship</b> of the weekly MEA geospatial roundup.</li></ul>
<h2>What we never sell</h2><p>Listing order, rankings and “where to buy” order are never for sale. Manufacturers and regional offices always come first, then authorised distributors, then dealers, by the same rule for everyone.</p>
<p>Contact <a href="mailto:{EMAIL}?subject=Advertising">{EMAIL}</a>.</p>''', "Advertising and sponsorship options at GeoAtlas MEA, and our disclosure rules.")
simple("contact.html", "Contact", "Contact", "Listings, corrections, partnerships, contributions and advertising.",
       f'<p class="answer">Email <a href="mailto:{EMAIL}">{EMAIL}</a>. To add a listing use <a href="submit.html">List your company</a>; to update one use <a href="claim.html">Claim your profile</a>.</p>', "Contact GeoAtlas MEA.", [ORG])

FAQ = [("What is GeoAtlas MEA?", f"{SITE} is a free directory of the geospatial industry in the Middle East and Africa. It lists {N} survey firms, GIS consultancies, BIM firms, equipment manufacturers and dealers, software vendors, agencies, universities and professional bodies in {len(real_countries)} countries, in {len(DCATS)} categories across four sections."),
       ("How do I find an accredited land surveyor in Dubai?", "Dubai Land Department (DLD) publishes the survey companies accredited for real-estate and land surveys in Dubai, and those firms are listed here under Real Estate & Building Surveyors in the UAE. Confirm current accreditation on dubailand.gov.ae before appointing a surveyor."),
       ("Who regulates surveying and mapping in Saudi Arabia?", "The General Authority for Survey and Geospatial Information (GEOSA) is Saudi Arabia's national survey and mapping authority. It maintains the national geodetic network and regulates surveying and geospatial activity in the Kingdom."),
       ("Where can I buy GNSS receivers, total stations and laser scanners in the Middle East and Africa?", "Each brand page lists its regional offices, authorised distributors and dealers by country; for example Leica Geosystems, Trimble, Topcon and Esri. Start at the Brands page or Products & Equipment."),
       ("Why do manufacturers appear first in equipment lists?", "Equipment and software lists follow one rule for everyone: manufacturers and regional offices first, then authorised distributors, then dealers, suppliers, rental and repair. Placement is never sold."),
       ("How do I list or claim my company?", "Listing is free. Use List your company for a new listing or Claim your profile to update an existing one. We check every submission before publishing."),
       ("What do the Sourced and Check labels mean?", "Sourced means the entry was taken from a published register or official partner list. Check means the entry comes from general public information and has not yet been confirmed with the organisation."),
       ("Can I download the directory data?", "Yes. The dataset is open as CSV and JSON on the Research page under CC BY 4.0. Please credit GeoAtlas MEA with a link.")]
simple("faq.html", "FAQ", "Frequently asked questions", "Straight answers about the directory and about finding geospatial services in the region.",
       "".join(f"<details class=q open><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in FAQ), "Answers on finding surveyors, equipment dealers, BIM providers and regulators in the Middle East and Africa, and on listing your company.", [faqld(FAQ)])

catopts = "".join(f'<optgroup label="{e(s[1])}">' + "".join(f'<option>{e(c["category"])}</option>' for c in sec_cats(s)) + "</optgroup>" for s in SECTIONS)
ctryopts = "".join(f"<option value='{e(c['country'])}'>" for c in COUNTRIES)
def form(mode):
    claim = mode == "claim"
    return f'''<form class="sub panel" id="sub" novalidate data-endpoint="{e(SUBMIT_ENDPOINT)}" data-email="{e(EMAIL)}" data-mode="{mode}">
<label class="full">{"Organisation name as listed" if claim else "Organisation name"} *<input id="f-name" required autocomplete="organization"></label>
{"<label>Your name *<input id=f-person required autocomplete=name></label><label>Your role<input id=f-role placeholder='Owner, manager, marketing'></label>" if claim else ""}
<label>Main category<select id="f-cat">{catopts}</select></label>
<label>More categories<input id="f-cats" placeholder="e.g. GNSS Receiver Dealers & Suppliers, Topographic Surveyors"></label>
<label>Country *<input id="f-country" required list="countrylist"></label>
<label>City<input id="f-city"></label>
<label class="full">Brands you make, distribute or sell (if any)<input id="f-brands" placeholder="e.g. Leica Geosystems, Trimble, DJI Enterprise"></label>
<label class="full">Role for those brands<select id="f-role2"><option value="">Not applicable</option><option>Manufacturer / regional office</option><option>Authorised distributor</option><option>Dealer / reseller</option><option>Rental</option><option>Repair & calibration</option></select></label>
<label class="full">Services (comma separated)<input id="f-services" placeholder="Topographic survey, Drone mapping, Scan-to-BIM"></label>
<label>Website<input id="f-web" type="url" placeholder="https://"></label>
<label>Business phone<input id="f-phone" type="tel"></label>
<label class="full">{"Work email (on your company domain, so we can verify you)" if claim else "Business email"}<input id="f-email" type="email"></label>
<label class="full">{"What should change?" if claim else "Short description (max 300 characters)"}<textarea id="f-desc" maxlength="{600 if claim else 300}"></textarea></label>
<div class="row" style="grid-column:1/-1"><button class="btn solid" type="submit">{"Send claim" if claim else "Send listing"}</button><span class="note" id="f-status" role="status"></span></div>
<div class="out" id="out" hidden><pre id="out-text"></pre><div class="row"><button class="btn solid" type="button" id="copy">Copy</button><a class="btn ghost" id="mail" href="mailto:{EMAIL}">Open email</a></div></div>
</form><datalist id="countrylist">{ctryopts}</datalist>'''
h, ld = hero(0, [("Home", "index.html"), ("List your company", "")], "List your organisation for free", "For any survey firm, GIS or BIM company, equipment manufacturer or dealer, software vendor, agency, university, training centre or association in the Middle East or Africa. We check every submission before it goes live.")
page("submit.html", f"List Your Geospatial Company for Free | {SITE}", "Add your survey, GIS, BIM, drone, equipment or software company to the Middle East and Africa directory. Free, in as many categories as fit.",
     h + f'<div class="wrap detail">{form("submit")}<aside class="prose"><h2 style="margin-top:0">What happens next</h2><p>We check the details against your website and publish the listing, usually within a few working days.</p><p>You can appear in several categories, and dealers appear on each brand’s “where to buy” page.</p><p>Already listed? <a href="claim.html">Claim your profile</a> instead.</p></aside></div>', 0, [ld], "")
h, ld = hero(0, [("Home", "index.html"), ("Claim your profile", "")], "Claim your free profile", "Take control of your listing: correct details, add categories, brands, services and projects, and get the “Listed on GeoAtlas MEA” badge.")
BADGE = f'<a href="{BASE_URL}/" title="Listed on {SITE}" style="display:inline-block;padding:6px 10px;border-radius:6px;background:#0F2A25;color:#E7EFEA;font:600 13px system-ui;text-decoration:none">Listed on {SITE}</a>'
page("claim.html", f"Claim Your Company Profile | {SITE}", "Claim and update your organisation's free profile in the Middle East and Africa geospatial directory, and get a Listed badge.",
     h + f'<div class="wrap detail">{form("claim")}<aside class="prose"><h2 style="margin-top:0">How claiming works</h2><ol><li>Send the form from an email on your company’s domain.</li><li>We confirm you work there and apply your changes.</li><li>Your profile shows “Claimed”, and you can update it any time.</li></ol><h2>Your badge</h2><p>Add this to your website so clients can find you here:</p><pre class="code">{e(BADGE.replace(BASE_URL + "/", BASE_URL + "/company/your-listing.html"))}</pre><div style="margin-top:8px">{BADGE}</div></aside></div>', 0, [ld], "")

page("404.html", f"Page not found | {SITE}", "This page does not exist.", f'<section class="hero page-hero"><div class="wrap"><h1 class="page-h1">Off the map</h1><p class="lede">This page does not exist. Try the <a style="color:inherit" href="/directory.html">directory search</a> or go back to the <a style="color:inherit" href="/">home page</a>.</p></div></section>', 0, noindex=True)

# ------------------------------------------------------------------ home
sec_tiles = '<div class="secs">' + "".join(f'<a class="sec" href="section/{s[2]}.html"><small>{s[0][:2]}</small><b>{e(s[1])}</b><span>{e(s[3])}</span><em>{sec_count(s)} listings · {len([c for c in sec_cats(s) if c["items"]])} categories</em></a>' for s in SECTIONS) + "</div>"
popular = sorted(LIVE, key=lambda c: -len(c["items"]))[:14]
topbrands = [b for b in BRANDS if b["dealers"]][:12]
home = f'''<section class="hero"><div class="wrap">
<div><p class="eyebrow">{TAGLINE}</p>
<h1>Every surveyor, GIS firm, BIM consultant and equipment dealer, on one map sheet.</h1>
<p class="lede">Find land surveyors, drone and LiDAR operators, GIS and BIM consultants, GNSS and total station dealers, software partners, mapping agencies and universities from the Gulf to the Cape.</p>
<form class="hero-search" action="directory.html" method="get" role="search"><input name="q" type="search" placeholder="Try “Leica”, “bathymetry”, “BIM” or “Nairobi”" aria-label="Search the directory"><button class="btn primary" type="submit">Search</button></form>
<div class="stats"><div><b>{N}</b>listings</div><div><b>{len(real_countries)}</b>countries</div><div><b>{len(LIVE)}</b>categories</div><div><b>{len(BRANDS)}</b>brands</div></div></div>
<div>{map_svg(0)}</div>
</div></section>
<section class="s"><div class="wrap"><h2>Survey equipment, rental and training in Dubai</h2><p class="sub">{e(OWNER)} supplies total stations, GNSS receivers and survey equipment, with rental, training and survey services, and is the UAE partner of GEOTEXON instruments.</p><div class="grid">{card(BYNAME[OWNER], 0)}<a class="card" href="brand/geotexon.html" style="text-decoration:none"><h3>GEOTEXON</h3><p style="color:var(--ink,inherit)">{e(BR[OWN_BRAND]["product_lines"])}</p><p class="meta">Brand · United Kingdom · supplied in the UAE by Rise Geo</p></a></div></div></section>
<section class="s"><div class="wrap"><h2>Browse the directory</h2><p class="sub">Four sections, named the way buyers search. Every organisation can appear in several categories.</p>{sec_tiles}
<h3 style="margin-top:28px">Popular categories</h3><div class="chips">{"".join(catlink(0, c["category"]) for c in popular)}</div></div></section>
<section class="s alt"><div class="wrap"><h2>Brands and where to buy them</h2><p class="sub">Regional offices first, then authorised distributors, then dealers.</p><div class="chips">{"".join(f'<a class="chip" href="brand/{b["slug"]}.html">{e(b["brand"])}<span class="n">{len(b["dealers"])}</span></a>' for b in topbrands)}<a class="chip" href="brands.html">All {len(BRANDS)} brands</a></div></div></section>
<section class="s"><div class="wrap"><h2>Guides and BIM Hub</h2><p class="sub">Answers first, sources cited, and linked to the firms that do the work.</p>{art_cards(0, list(ART))}<p style="margin-top:18px"><a class="btn ghost" href="bim.html">Open the BIM Hub</a> <a class="btn ghost" href="regulations.html">Regulations by country</a> <a class="btn ghost" href="research/state-of-mea-geospatial-2026.html">State of MEA geospatial 2026</a></p></div></section>
<section class="s alt"><div class="wrap"><h2>Browse by country</h2><p class="sub">All 70 countries of the Middle East and Africa.</p>{country_tiles(0, with_empty=False)}<p style="margin-top:16px"><a href="countries.html">See all 70 countries</a></p></div></section>
<section class="s"><div class="wrap" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;align-items:start">
<div><h2>Grow with the community</h2><p class="sub">List your organisation free, claim your profile, review for us, or post a job or tender.</p><p><a class="btn primary" href="submit.html">List your company</a> <a class="btn ghost" href="claim.html">Claim your profile</a></p></div>
<div>{"".join(f'<details class="q"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in FAQ[:4])}<p><a href="faq.html">More questions</a></p></div>
</div></section>'''
page("index.html", f"{SITE} | Survey, GIS, BIM & Geospatial Companies Directory – Middle East & Africa",
     f"Free directory of {N} geospatial organisations in {len(real_countries)} Middle East and African countries: land surveyors, GIS and BIM consultants, survey equipment dealers, software, agencies and universities.",
     home, 0, [ORG, WEBSITE, faqld(FAQ[:4])])

# ------------------------------------------------------------------ assets, data, SEO files
(out / "assets").mkdir(exist_ok=True)
shutil.copy(here / "site.css", out / "assets/site.css"); shutil.copy(here / "site.js", out / "assets/site.js")
(out / "data").mkdir(exist_ok=True)
pubcols = ["name", "primary_category", "categories", "business_types", "brands", "country", "city", "website", "phone", "description", "source", "url"]
pub = [{"name": r["name"], "primary_category": r["primary"], "categories": "; ".join(r["cats"]), "business_types": r["business_types"], "brands": "; ".join(sorted(set(r["brandlist"]) | company_brands.get(r["name"], set()))),
        "country": r["country"], "city": r["city"], "website": r["website"], "phone": r["phone"], "description": r["description"], "source": r["source"], "url": url("company/" + r["slug"] + ".html")} for r in rows]
with open(out / "data/companies.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=pubcols); w.writeheader(); w.writerows(pub)
(out / "data/companies.json").write_text(json.dumps(pub, ensure_ascii=False, indent=1), encoding="utf-8")
(out / "data/brands.json").write_text(json.dumps([{k: b[k] for k in ("brand", "parent_group", "origin_country", "product_lines")} | {"where_to_buy": b["dealers"], "url": url(f"brand/{b['slug']}.html")} for b in BRANDS], ensure_ascii=False, indent=1), encoding="utf-8")
(out / "data/categories.json").write_text(json.dumps([{k: c[k] for k in ("code", "section", "category", "product_or_software_line", "role")} | {"listings": len(c["items"]), "url": url(f"category/{c['slug']}.html") if c["items"] else None} for c in DCATS], ensure_ascii=False, indent=1), encoding="utf-8")
for old in ("category",):
    for f in (out / old).glob("*.html"):
        if f.stem in OLDCAT: f.unlink()
(out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{'1.0' if p == 'index.html' else '0.8' if '/' not in p or p.startswith(('section/', 'guides/', 'bim/', 'jobs/')) else '0.6'}</priority></url>\n" for u, p in SITEMAP) + "</urlset>\n", encoding="utf-8")
(out / "robots.txt").write_text(f"# {SITE}: search engines and AI assistants are welcome to index and cite this directory.\nUser-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended"]) + f"Sitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
llms = f"# {SITE}\n\n> {TAGLINE}. {N} survey firms, GIS and BIM consultancies, equipment manufacturers and dealers, software vendors, agencies, universities and professional bodies across {len(real_countries)} countries, in {len(DCATS)} categories and four sections. Free to search; data downloadable as CSV and JSON (CC BY 4.0).\n\n"
llms += f"## Key pages\n- [Directory search]({url('directory.html')})\n- [Brands and where to buy]({url('brands.html')})\n- [Countries]({url('countries.html')})\n- [FAQ]({url('faq.html')})\n- [About & methodology]({url('about.html')})\n\n## Guides\n" + "".join(f"- [{a['title']}]({url(a['path'])}): {a['answer']}\n" for a in ART.values())
llms += f"\n## Regulations\n- [Regulations, licensing and standards]({url('regulations.html')}): survey licensing bodies and authorities by country\n- [BIM Hub]({url('bim.html')}): ISO 19650, BEP, LOD, CDE, 4D/5D, FM, scan-to-BIM\n- [BIM mandates tracker]({url('bim/mandates.html')}): Dubai, Abu Dhabi and Saudi BIM requirements with verification status\n"
llms += f"\n## Jobs\n- [Geospatial jobs and internships]({url('jobs.html')}): survey, GIS, BIM, drone and hydrographic vacancies; employers post free\n" + "".join(f"- [{x['name']}]({url('jobs/' + x['slug'] + '.html')}): {x['answer']}\n" for x in ROLES)
llms += f"\n## Research\n- [State of MEA geospatial 2026]({url('research/state-of-mea-geospatial-2026.html')}): the directory in numbers\n- [Dataset (CSV)]({url('data/companies.csv')}) · [JSON]({url('data/companies.json')}) · [Brands JSON]({url('data/brands.json')})\n"
llms += "\n## Sections\n" + "".join(f"- [{s[1]}]({url('section/' + s[2] + '.html')}): {s[3]}\n" for s in SECTIONS)
llms += "\n## Categories\n" + "".join(f"- [{c['category']}]({url('category/' + c['slug'] + '.html')}): {len(c['items'])} listings\n" for c in LIVE)
llms += "\n## Countries\n" + "".join(f"- [{c}]({url('country/' + slug(c) + '.html')}): {len(v)} listings\n" for c, v in sorted(by_country.items(), key=lambda t: -len(t[1])))
(out / "llms.txt").write_text(llms, encoding="utf-8")
full = llms + "\n## Brands\n" + "".join(f"- [{b['brand']}]({url('brand/' + b['slug'] + '.html')}): {b['product_lines']} | {len(b['dealers'])} MEA partners\n" for b in BRANDS)
full += "\n## All listings\n" + "".join(f"- [{r['name']}]({url('company/' + r['slug'] + '.html')}) | {r['primary']} | {r['city'] + ', ' if r['city'] else ''}{r['country']} | {r['website'] or 'no website listed'}\n" for r in rows)
(out / "llms-full.txt").write_text(full, encoding="utf-8")
# redirects for removed v1 URLs
oldslugs = [s.strip() for s in (D / "old_company_slugs.txt").read_text().split() if s.strip()]
newslugs = {r["slug"] for r in rows}
REDIR = {f"/category/{k}.html": "/" + v for k, v in OLDCAT.items()}
REDIR.update({f"/company/{s}.html": "/directory.html" for s in oldslugs if s not in newslugs})
REDIR["/company/rise-geo.html"] = "/company/rise-geo-control-systems-trading-llc.html" if "rise-geo-control-systems-trading-llc" in newslugs else "/directory.html"
(here / "redirects.txt").write_text("".join(f"Redirect 301 {a} {b}\n" for a, b in sorted(REDIR.items())))
(out / "CNAME").write_text(BASE_URL.split("//")[1] + "\n"); (out / ".nojekyll").write_text("")
print(f"Built {len(SITEMAP)} indexable pages, {N} listings, {len(LIVE)} live categories, {len(BRANDS)} brands, {len(REDIR)} redirects")
