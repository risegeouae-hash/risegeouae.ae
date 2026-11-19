"""GeoAtlas MEA static site generator.
Reads companies.csv and writes the full website into ../site/. Run: python3 build.py
"""
import csv, json, re, html, shutil, datetime, pathlib
from collections import Counter, defaultdict

BASE_URL = "https://risegeouae.ae"          # live domain, no trailing slash
SITE = "GeoAtlas MEA"
TAGLINE = "The geospatial industry directory for the Middle East and Africa"
SUBMIT_EMAIL = "info@risegeouae.ae"         # placeholder inbox for listings
SUBMIT_ENDPOINT = ""                        # e.g. a Formspree URL to receive submissions directly
TODAY = datetime.date.today().isoformat()

here = pathlib.Path(__file__).parent
out = here.parent  # builds into the repo root
pass
(out / "assets").mkdir(parents=True, exist_ok=True)

e = lambda s: html.escape(str(s or ""), quote=True)
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")).strip("-")

GCC = ["United Arab Emirates","Saudi Arabia","Qatar","Bahrain","Kuwait","Oman"]
MENA = ["Egypt","Jordan","Morocco","Lebanon","Iraq","Algeria","Tunisia","Libya","Turkey","Yemen","Syria","Palestine","Iran"]
def region(c): return "Regional & multinational" if c=="Regional (MEA)" else "GCC" if c in GCC else "Wider MENA" if c in MENA else "Sub-Saharan Africa"
REGIONS = ["GCC","Wider MENA","Sub-Saharan Africa","Regional & multinational"]
COORDS = {"Dubai":(25.20,55.27),"Abu Dhabi":(24.45,54.38),"Riyadh":(24.71,46.68),"Jeddah":(21.49,39.19),"Tabuk":(28.38,36.57),"Doha":(25.29,51.53),"Manama":(26.23,50.59),"Kuwait City":(29.38,47.99),"Muscat":(23.59,58.41),"Cairo":(30.04,31.24),"Amman":(31.95,35.93),"Rabat":(34.02,-6.84),"Ben Guerir":(32.24,-7.95),"Abuja":(9.08,7.40),"Nairobi":(-1.29,36.82),"Kigali":(-1.95,30.06),"Dakar":(14.72,-17.47),"Bamako":(12.64,-8.00),"Johannesburg":(-26.20,28.05),"Pretoria":(-25.75,28.19),"Cape Town":(-33.92,18.42),"Durban":(-29.86,31.02),"Addis Ababa":(9.03,38.74)}
CAT_BLURB = {
 "Survey Company":"Land, engineering, cadastral, topographic and building survey firms, including accredited real-estate surveyors.",
 "GIS & Consulting":"GIS consultancies, system integrators and spatial data specialists building maps, platforms and digital twins.",
 "Hardware Supplier":"Distributors and manufacturers of GNSS receivers, total stations, laser scanners and mobile mapping systems.",
 "Software Vendor":"GIS, photogrammetry, CAD and location-intelligence software companies and platforms.",
 "Drone & UAV Services":"Drone survey operators, aerial mapping firms and UAV platform suppliers.",
 "Satellite & Earth Observation":"Satellite operators, imagery providers and Earth observation analytics companies.",
 "Hydrographic & Marine":"Hydrographic survey firms and marine positioning and sonar equipment makers.",
 "Government & Agency":"National mapping agencies, space agencies, cadastre authorities and survey regulators.",
 "Association & Education":"Professional bodies, institutes and societies for surveyors and GIS professionals."}
NOUN={"Survey Company":("survey company","survey companies"),"GIS & Consulting":("GIS consultancy","GIS consultancies"),"Hardware Supplier":("hardware supplier","hardware suppliers"),"Software Vendor":("software vendor","software vendors"),"Drone & UAV Services":("drone and UAV operator","drone and UAV operators"),"Satellite & Earth Observation":("satellite and Earth observation company","satellite and Earth observation companies"),"Hydrographic & Marine":("hydrographic and marine firm","hydrographic and marine firms"),"Government & Agency":("government agency","government agencies"),"Association & Education":("professional body","professional bodies")}
def noun(k,n=1): return NOUN.get(k,(k.lower(),k.lower()))[0 if n==1 else 1]
def art(w): return ("an " if w[0].lower() in "aeiou" else "a ")+w
def andjoin(xs): xs=list(xs); return xs[0] if len(xs)==1 else ", ".join(xs[:-1])+" and "+xs[-1]
def fmtc(lat, lon): return f"{abs(lat):.2f}° {'N' if lat>=0 else 'S'}, {abs(lon):.2f}° {'E' if lon>=0 else 'W'}"

rows = list(csv.DictReader(open(here/"companies.csv", encoding="utf-8")))
seen=set()
for r in rows:
    s = slug(r["name"]); 
    while s in seen: s += "-2"
    seen.add(s); r["slug"]=s
    r["region"]=region(r["country"])
    r["svc"]=[x.strip() for x in r["services"].split(";") if x.strip()]
    r["checked"]= "check" not in r["source"].lower()
    r["cslug"]=slug(r["country"]); r["kslug"]=slug(r["category"])
rows.sort(key=lambda r:(REGIONS.index(r["region"]), not r["checked"], r["country"], r["name"].lower()))
by_country=defaultdict(list); by_cat=defaultdict(list)
for r in rows: by_country[r["country"]].append(r); by_cat[r["category"]].append(r)
real_countries=[c for c in by_country if c!="Regional (MEA)"]
N=len(rows)

def url(path): return BASE_URL + "/" + path.lstrip("/")
def rel(depth, path): return ("../"*depth) + path

ICON='<svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" stroke-width="1.5" opacity=".5"/><path d="M2 16h28M16 2v28" stroke="currentColor" stroke-width="1" opacity=".35"/><path d="M16 6l3.5 10L16 26l-3.5-10z" fill="#E5B23A"/></svg>'
FAVICON = "data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230F2A25'/%3E%3Cpath d='M16 5l4 11-4 11-4-11z' fill='%23E5B23A'/%3E%3C/svg%3E"

def page(path, title, desc, body, depth, jsonld=(), current="", og_type="website", noindex=False):
    canon = url(path) if path!="index.html" else BASE_URL + "/"
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in jsonld)
    nav = [("index.html","Home"),("directory.html","Directory"),("countries.html","Countries"),("categories.html","Categories"),("faq.html","FAQ"),("about.html","About")]
    navh = "".join(f'<li><a class="l" href="{rel(depth,p)}"{" aria-current=page" if p==current else ""}>{l}</a></li>' for p,l in nav)
    footer_c = "".join(f'<li><a href="{rel(depth,"country/"+slug(c)+".html")}">{e(c)}</a></li>' for c in sorted(real_countries, key=lambda c:-len(by_country[c]))[:6])
    footer_k = "".join(f'<li><a href="{rel(depth,"category/"+slug(k)+".html")}">{e(k)}</a></li>' for k in sorted(by_cat, key=lambda k:-len(by_cat[k]))[:6])
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
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="icon" href="{FAVICON}">
<link rel="alternate" type="application/json" href="{rel(depth,"data/companies.json")}" title="Directory dataset (JSON)">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{rel(depth,"assets/site.css")}">
{ld}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<nav class="nav" aria-label="Main"><div class="wrap">
<a class="brand" href="{rel(depth,"index.html")}">{ICON}<span>{SITE}<br><small>MIDDLE EAST &amp; AFRICA</small></span></a>
<ul>{navh}<li><a class="l cta" href="{rel(depth,"submit.html")}">List your company</a></li></ul>
</div></nav>
<main id="main">
{body}
</main>
<footer class="site"><div class="wrap">
<div><a class="brand" href="{rel(depth,"index.html")}">{ICON}<span>{SITE}</span></a><p>{TAGLINE}. {N} listings across {len(real_countries)} countries, compiled from public registries, partner directories and company submissions.</p><p class="mono" style="font-size:12px">Updated {TODAY} · <a href="{rel(depth,"data/companies.csv")}">Download data (CSV)</a></p></div>
<div><h4>Countries</h4><ul>{footer_c}<li><a href="{rel(depth,"countries.html")}">All countries</a></li></ul></div>
<div><h4>Categories</h4><ul>{footer_k}<li><a href="{rel(depth,"categories.html")}">All categories</a></li></ul></div>
<div><h4>Directory</h4><ul><li><a href="{rel(depth,"directory.html")}">Search the directory</a></li><li><a href="{rel(depth,"submit.html")}">List your company</a></li><li><a href="{rel(depth,"faq.html")}">FAQ</a></li><li><a href="{rel(depth,"about.html")}">About &amp; methodology</a></li></ul></div>
</div></footer>
<script src="{rel(depth,"assets/site.js")}" defer></script>
</body>
</html>
'''
    p = out / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(doc, encoding="utf-8")
    if not noindex: SITEMAP.append((canon, path))
SITEMAP=[]

def crumbs(depth, items):
    lis = "".join(f'<li><a href="{rel(depth,p)}">{e(n)}</a></li>' if p else f'<li aria-current="page">{e(n)}</li>' for n,p in items)
    ld = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,**({"item":url(p) if p!="index.html" else BASE_URL+"/"} if p else {})} for i,(n,p) in enumerate(items)]}
    return f'<ol class="crumbs">{lis}</ol>', ld

def host(w): return re.sub(r"^https?://(www\.)?","",w).split("/")[0] if w else ""
def card(r, depth):
    c = COORDS.get(r["city"])
    loc = ", ".join(x for x in [r["city"], r["country"] if r["country"]!="Regional (MEA)" else "Multinational"] if x)
    tags = "".join(f'<span class="tag">{e(s)}</span>' for s in r["svc"][:5])
    return f'''<article class="card" data-c="{e(r["country"])}" data-r="{e(r["region"])}" data-k="{e(r["category"])}" data-s="{e("|".join(r["svc"]))}" data-h="{e(" ".join([r["name"],r["category"],r["country"],r["city"],r["services"],r["description"]]).lower())}">
<div class="top"><h3><a href="{rel(depth,"company/"+r["slug"]+".html")}">{e(r["name"])}</a></h3><span class="cat">{e(r["category"])}</span></div>
<div class="loc"><span>{e(loc)}</span>{f"<span>{fmtc(*c)}</span>" if c else ""}</div>
{f'<p class="desc">{e(r["description"])}</p>' if r["description"] else ""}
{f'<div class="tags">{tags}</div>' if tags else ""}
<div class="foot"><span class="host">{e(host(r["website"])) or "No website listed"}</span><span class="src{"" if r["checked"] else " check"}" title="Source: {e(r["source"])}"><i></i>{"Sourced" if r["checked"] else "Check"}</span></div>
</article>'''

def itemlist(name, items):
    return {"@context":"https://schema.org","@type":"ItemList","name":name,"numberOfItems":len(items),
            "itemListElement":[{"@type":"ListItem","position":i+1,"url":url("company/"+r["slug"]+".html"),"name":r["name"]} for i,r in enumerate(items)]}

ORG = {"@context":"https://schema.org","@type":"Organization","@id":BASE_URL+"/#org","name":SITE,"url":BASE_URL+"/","description":TAGLINE,"areaServed":["Middle East","Africa"]}
WEBSITE = {"@context":"https://schema.org","@type":"WebSite","@id":BASE_URL+"/#site","name":SITE,"url":BASE_URL+"/","publisher":{"@id":BASE_URL+"/#org"},
           "potentialAction":{"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":BASE_URL+"/directory.html?q={search_term_string}"},"query-input":"required name=search_term_string"}}

def map_svg(depth):
    # equirectangular graticule: lon -20..62, lat -38..40
    W,H=560,520; x=lambda lon:(lon+20)/88*W; y=lambda lat:(40-lat)/78*H
    g="".join(f'<line class="grat" x1="{x(lo):.1f}" y1="0" x2="{x(lo):.1f}" y2="{H}"/><text class="lbl" x="{x(lo)+3:.1f}" y="{H-6}">{abs(lo)}°{"E" if lo>=0 else "W"}</text>' for lo in range(-10,61,10))
    g+="".join(f'<line class="grat" x1="0" y1="{y(la):.1f}" x2="{W}" y2="{y(la):.1f}"/><text class="lbl" x="4" y="{y(la)-4:.1f}">{abs(la)}°{"N" if la>=0 else "S"}{" EQ" if la==0 else ""}</text>' for la in range(-30,41,10))
    cnt=Counter(r["city"] for r in rows if r["city"] in COORDS)
    pts=""
    for city,n in sorted(cnt.items(), key=lambda t:-t[1]):
        la,lo=COORDS[city]; cx,cy=x(lo),y(la); rad=4+min(n,30)**0.6*2.2
        ctry=next(r["country"] for r in rows if r["city"]==city)
        OFF={"Dubai":(0,rad+16,"middle"),"Riyadh":(-rad-6,4,"end"),"Jeddah":(-rad-6,4,"end")}
        dx,dy,anc=OFF.get(city,(rad+4,4,"start"))
        lab = f'<text class="cname" x="{cx+dx:.1f}" y="{cy+dy:.1f}" text-anchor="{anc}">{e(city)} {n}</text>' if city in ("Dubai","Riyadh","Jeddah","Cairo","Rabat","Abuja","Nairobi","Johannesburg","Cape Town","Dakar","Addis Ababa") else ""
        pts+=f'<a href="{rel(depth,"country/"+slug(ctry)+".html")}" aria-label="{e(city)}: {n} listings"><circle class="halo" cx="{cx:.1f}" cy="{cy:.1f}" r="{rad*2:.1f}"/><circle class="city" cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}"/>{lab}</a>'
    return f'<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-label="Plot of listed companies by city across the Middle East and Africa">{g}{pts}</svg><div class="map-cap">Listings by city · equirectangular, 10° graticule</div>'

def tiles_countries(depth):
    h=""
    for reg in REGIONS:
        cs=[c for c in sorted(by_country, key=lambda c:(-len(by_country[c]),c)) if region(c)==reg]
        if not cs: continue
        h+=f'<div class="region-h">{reg}</div><div class="tiles">'+"".join(f'<a class="tile" href="{rel(depth,"country/"+slug(c)+".html")}"><span>{e(c if c!="Regional (MEA)" else "Multinational suppliers")}</span><em>{len(by_country[c])}</em></a>' for c in cs)+'</div>'
    return h
def tiles_cats(depth):
    return '<div class="tiles">'+"".join(f'<a class="tile" href="{rel(depth,"category/"+slug(k)+".html")}"><span>{e(k)}<small>{e(CAT_BLURB.get(k,"")[:70])}…</small></span><em>{len(v)}</em></a>' for k,v in sorted(by_cat.items(), key=lambda t:-len(t[1])))+'</div>'

# FAQ (AEO): direct, quotable answers
nsurvey=len(by_cat["Survey Company"]); ndld=sum(1 for r in rows if "Dubai Land" in r["source"])
FAQ=[
 ("What is GeoAtlas MEA?", f"GeoAtlas MEA is a free directory of the geospatial industry in the Middle East and Africa. It lists {N} survey companies, GIS consultancies, equipment and software suppliers, drone and satellite operators, mapping agencies and professional bodies across {len(real_countries)} countries, searchable by country, category and service."),
 ("How do I find an accredited land surveyor in Dubai?", f"Dubai Land Department (DLD) publishes the list of survey companies accredited for real-estate and land surveys in Dubai. All {ndld} DLD-accredited firms are listed in GeoAtlas MEA under United Arab Emirates, with the phone numbers DLD publishes. Always confirm current accreditation on dubailand.gov.ae before appointing a surveyor."),
 ("Who regulates surveying and mapping in Saudi Arabia?", "The General Authority for Survey and Geospatial Information (GEOSA), formerly GASGI, is Saudi Arabia's national survey and mapping authority. It maintains the national geodetic network and licenses surveying and geospatial activity in the Kingdom."),
 ("What is the difference between a survey company and a GIS company?", "A survey company measures the real world in the field: boundaries, levels, buildings, utilities and the seabed, using GNSS, total stations, laser scanners and drones. A GIS company manages and analyses that spatial data, building maps, databases, dashboards and digital twins. Many firms in the region do both."),
 ("Where can I buy GNSS receivers, total stations and laser scanners in the Middle East?", "Major manufacturers such as Trimble, Leica Geosystems, Topcon, CHC Navigation, Stonex, RIEGL and FARO sell through regional offices and authorised dealers. See the Hardware Supplier category for distributors by country."),
 ("Which organisations run Earth observation satellites in the region?", "Government operators include the Mohammed Bin Rashid Space Centre (UAE), the Egyptian Space Agency, NASRDA (Nigeria) and SANSA (South Africa). Commercial operators and imagery providers include Space42, Neo Space Group, SARsatX, Space Imaging Middle East and Amaya Space."),
 ("How do I list my company in the directory?", f"Listing is free. Fill in the form on the List your company page with your company name, country, category, services and website. Each submission is checked against the company website before it is published."),
 ("What do the Sourced and Check labels mean?", "Sourced means the entry was taken from a published list such as a government accreditation register or an official partner directory. Check means the entry comes from general public information and its details have not yet been confirmed against the company's own website."),
 ("Can I download the directory data?", "Yes. The full dataset is available as CSV and JSON from the links in the site footer, so researchers and AI tools can cite it. Please credit GeoAtlas MEA when you reuse it."),
]
FAQ_LD={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ]}

# ---------- HOME
toolbar_js_hint=""
featured=[r for r in rows if r["checked"] and r["website"]][:6]
home=f'''<section class="hero"><div class="wrap">
<div><p class="eyebrow">{TAGLINE}</p>
<h1>Every surveyor, GIS firm and supplier, on one map sheet.</h1>
<p class="lede">Find survey companies, GIS consultancies, GNSS and scanner suppliers, drone and satellite operators, mapping agencies and professional bodies from the Gulf to the Cape.</p>
<form class="hero-search" action="directory.html" method="get" role="search"><input name="q" id="home-q" type="search" placeholder="Try “LiDAR”, “bathymetry” or “Riyadh”" aria-label="Search the directory"><button class="btn primary" type="submit">Search</button></form>
<div class="stats"><div><b>{N}</b>listings</div><div><b>{len(real_countries)}</b>countries</div><div><b>{nsurvey}</b>survey companies</div><div><b>{len(by_cat)}</b>categories</div></div></div>
<div>{map_svg(0)}</div>
</div></section>
<section class="s"><div class="wrap"><h2>Browse by country</h2><p class="sub">Start with the GCC, where the directory is most complete, then the wider MENA region and Sub-Saharan Africa.</p>{tiles_countries(0)}</div></section>
<section class="s alt"><div class="wrap"><h2>Browse by category</h2><p class="sub">Nine categories cover the whole geospatial value chain, from field survey to satellite imagery.</p>{tiles_cats(0)}</div></section>
<section class="s"><div class="wrap"><h2>Recently sourced listings</h2><p class="sub">Entries confirmed from official registers and partner directories.</p><div class="grid">{"".join(card(r,0) for r in featured)}</div><p style="margin-top:20px"><a class="btn solid" href="directory.html">Search all {N} listings</a></p></div></section>
<section class="s alt"><div class="wrap" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;align-items:start">
<div><h2>Is your company missing?</h2><p class="sub">Listing is free for any company, agency or association working in geospatial in the Middle East or Africa. We check every submission before publishing.</p><a class="btn primary" href="submit.html">List your company</a></div>
<div>{"".join(f'<details class="q"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in FAQ[:4])}<p><a href="faq.html">More questions</a></p></div>
</div></section>'''
page("index.html", f"{SITE} | Geospatial, Survey & GIS Companies Directory – Middle East & Africa",
     f"Free directory of {N} geospatial companies across {len(real_countries)} Middle East and African countries: land survey firms, GIS consultancies, GNSS and scanner suppliers, drone and satellite operators.",
     home, 0, [ORG, WEBSITE, itemlist("Featured geospatial companies", featured)], "index.html")

# ---------- DIRECTORY
def toolbar(depth, preset_country="", preset_cat=""):
    svc=Counter(s for r in rows for s in r["svc"])
    opts=lambda items: "".join(f'<option value="{e(k)}">{e(k)} ({n})</option>' for k,n in items)
    return f'''<div class="toolbar" id="filters"><div class="wrap">
<div class="row"><div class="search"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input id="q" type="search" placeholder="Search names, services, cities…" aria-label="Search the directory"></div>
<select id="f-region" aria-label="Region"><option value="">All regions</option>{opts([(g,sum(1 for r in rows if r["region"]==g)) for g in REGIONS])}</select>
<select id="f-country" aria-label="Country"><option value="">All countries</option>{opts(sorted(Counter(r["country"] for r in rows).items()))}</select>
<select id="f-service" aria-label="Service"><option value="">All services</option>{opts(sorted([(k,n) for k,n in svc.items() if n>1], key=lambda t:(-t[1],t[0])))}</select></div>
<div class="row" style="justify-content:space-between"><div class="chips" role="group" aria-label="Category"><button class="chip" type="button" data-k="" aria-pressed="true">All</button>{"".join(f'<button class="chip" type="button" data-k="{e(k)}" aria-pressed="false">{e(k)}<span class="n">{len(v)}</span></button>' for k,v in sorted(by_cat.items()))}</div><span class="meta" id="count" aria-live="polite">{N} of {N} shown</span></div>
</div></div>'''
dbody=f'''<section class="hero page-hero"><div class="wrap">{crumbs(0,[("Home","index.html"),("Directory","")])[0]}<h1 class="page-h1">Geospatial directory</h1><p class="lede">All {N} listings. Search by name, service or city, then narrow by region, country, service and category.</p></div></section>
{toolbar(0)}<div class="wrap listing"><div class="grid" id="list">{"".join(card(r,0) for r in rows)}<div class="empty" id="empty" hidden>Nothing matches those filters. Clear a filter, or <a href="submit.html">add the company you were looking for</a>.</div></div></div>'''
page("directory.html", f"Search {N} Geospatial, Survey & GIS Companies | {SITE}",
     f"Search and filter {N} survey companies, GIS firms, suppliers and agencies across the Middle East and Africa by country, category and service.",
     dbody, 0, [crumbs(0,[("Home","index.html"),("Directory","")])[1], itemlist("Geospatial companies in the Middle East and Africa", rows)], "directory.html")

# ---------- COMPANY PAGES
TYPE={"Government & Agency":"GovernmentOrganization","Association & Education":"Organization"}
for r in rows:
    d=1; cname=r["country"] if r["country"]!="Regional (MEA)" else "Multinational suppliers"
    cr, crld = crumbs(d,[("Home","index.html"),(cname,"country/"+r["cslug"]+".html"),(r["name"],"")])
    c=COORDS.get(r["city"])
    ld={"@context":"https://schema.org","@type":TYPE.get(r["category"],"LocalBusiness" if r["city"] and r["country"]!="Regional (MEA)" else "Organization"),
        "@id":url("company/"+r["slug"]+".html")+"#org","name":r["name"],"description":r["description"],
        "url":r["website"] or None,"telephone":r["phone"] or None,
        "address":{"@type":"PostalAddress","addressLocality":r["city"] or None,"addressCountry":r["country"]} if r["country"]!="Regional (MEA)" else None,
        "areaServed":r["country"] if r["country"]!="Regional (MEA)" else ["Middle East","Africa"],
        "knowsAbout":r["svc"],"sameAs":[r["website"]] if r["website"] else None}
    if c: ld["geo"]={"@type":"GeoCoordinates","latitude":c[0],"longitude":c[1]}
    ld={k:v for k,v in ld.items() if v not in (None,"",[])}
    if isinstance(ld.get("address"),dict): ld["address"]={k:v for k,v in ld["address"].items() if v}
    related=[x for x in by_country[r["country"]] if x is not r and x["category"]==r["category"]][:3] or [x for x in by_cat[r["category"]] if x is not r][:3]
    summary=f'{r["name"]} is {art(noun(r["category"]))} {"based in "+(r["city"]+", " if r["city"] else "")+r["country"] if r["country"]!="Regional (MEA)" else "serving the Middle East and Africa"}.'
    if r["svc"]: summary+=f' Listed services: {andjoin(r["svc"])}.'
    facts=[("Category",f'<a href="{rel(d,"category/"+r["kslug"]+".html")}">{e(r["category"])}</a>'),
           ("Country",f'<a href="{rel(d,"country/"+r["cslug"]+".html")}">{e(cname)}</a>'),
           ("City",e(r["city"]) or "–"),
           ("Coordinates",f'<span class="mono">{fmtc(*c)}</span> <span class="note">(city)</span>' if c else "–"),
           ("Website",f'<a href="{e(r["website"])}" rel="noopener nofollow" target="_blank">{e(host(r["website"]))} ↗</a>' if r["website"] else "Not listed"),
           ("Phone",f'<span class="mono">{e(r["phone"])}</span>' if r["phone"] else "Not listed"),
           ("Source",f'<span class="src{"" if r["checked"] else " check"}"><i></i>{e(r["source"])}</span>')]
    body=f'''<section class="hero page-hero"><div class="wrap">{cr}<p class="eyebrow" style="margin-top:18px">{e(r["category"])}</p><h1 class="page-h1">{e(r["name"])}</h1><p class="lede">{e(r["description"])}</p></div></section>
<div class="wrap detail"><div class="prose"><p class="answer">{e(summary)}</p>
<h2>Services</h2><div class="tags">{"".join(f'<a class="tag" href="{rel(d,"directory.html")}?s={e(s)}">{e(s)}</a>' for s in r["svc"]) or "<span class=note>No services listed yet.</span>"}</div>
{f'<h2>Similar companies</h2><div class="grid" style="grid-template-columns:1fr">{"".join(card(x,d) for x in related)}</div>' if related else ""}
<p class="note" style="margin-top:28px">Is this your company? <a href="{rel(d,"submit.html")}">Update or claim this listing</a>. Details come from public sources; confirm them with the company before relying on them.</p></div>
<aside><div class="panel"><dl class="facts">{"".join(f"<dt>{k}</dt><dd>{v}</dd>" for k,v in facts)}</dl>{f'<p style="margin:18px 0 0"><a class="btn solid" href="{e(r["website"])}" rel="noopener nofollow" target="_blank">Visit website</a></p>' if r["website"] else ""}</div></aside></div>'''
    loc_t = f'{r["city"]+", " if r["city"] else ""}{cname}'
    page(f'company/{r["slug"]}.html', f'{r["name"]} – {r["category"]} in {loc_t} | {SITE}',
         (r["description"] or summary)[:155], body, d, [ld, crld], og_type="profile")

# ---------- COUNTRY PAGES
country_list=[]
for ctry, items in by_country.items():
    d=1; cname=ctry if ctry!="Regional (MEA)" else "Multinational suppliers"
    cr, crld = crumbs(d,[("Home","index.html"),("Countries","countries.html"),(cname,"")])
    kc=Counter(r["category"] for r in items)
    breakdown=andjoin(f'{n} {noun(k,n)}' for k,n in kc.most_common())
    answer = (f'GeoAtlas MEA lists {len(items)} geospatial organisations in {ctry}: {breakdown}.' if ctry!="Regional (MEA)" else
              f'These {len(items)} manufacturers and platforms sell across the Middle East and Africa through regional offices and dealers: {breakdown}.')
    cities=Counter(r["city"] for r in items if r["city"])
    if cities: answer+=f' Most are based in {andjoin(c for c,_ in cities.most_common(3))}.'
    faq=[(f"How many survey companies are there in {cname}?", f'The directory currently lists {kc.get("Survey Company",0)} survey companies in {cname}, out of {len(items)} geospatial organisations in total. The list grows as companies are added and submitted.')] if ctry!="Regional (MEA)" else []
    gov=[r for r in items if r["category"]=="Government & Agency"]
    if gov and ctry!="Regional (MEA)": faq.append((f"Which government agencies handle mapping and geospatial data in {ctry}?", "Listed agencies: "+"; ".join(r["name"]+(" – "+r["description"].rstrip(".") if r["description"] else "") for r in gov)+"."))
    fld={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]} if faq else None
    chips="".join(f'<a class="chip" href="{rel(d,"category/"+slug(k)+".html")}">{e(k)}<span class="n">{n}</span></a>' for k,n in kc.most_common())
    body=f'''<section class="hero page-hero"><div class="wrap">{cr}<p class="eyebrow" style="margin-top:18px">{e(region(ctry))}</p><h1 class="page-h1">Geospatial &amp; survey companies in {e(cname)}</h1><p class="lede">{e(answer)}</p></div></section>
<div class="wrap listing"><div class="chips" style="margin-bottom:18px">{chips}</div><div class="grid">{"".join(card(r,d) for r in items)}</div>
{"".join(f'<details class="q" open><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in faq)}
<p class="note" style="margin-top:24px">Know a firm in {e(cname)} that is missing? <a href="{rel(d,"submit.html")}">Add it to the directory</a>.</p></div>'''
    ttl = f"{len(items)} Geospatial, Survey & GIS Companies in {cname} | {SITE}" if ctry!="Regional (MEA)" else f"Multinational Geospatial Suppliers in the Middle East & Africa | {SITE}"
    page(f"country/{slug(ctry)}.html", ttl, answer[:155], body, d, [x for x in [itemlist(f"Geospatial companies in {cname}", items), crld, fld] if x])
cr, crld = crumbs(0,[("Home","index.html"),("Countries","")])
page("countries.html", f"Geospatial Companies by Country – Middle East & Africa | {SITE}", f"Browse survey, GIS and geospatial companies in {len(real_countries)} countries across the GCC, wider MENA and Sub-Saharan Africa.",
     f'<section class="hero page-hero"><div class="wrap">{cr}<h1 class="page-h1">Browse by country</h1><p class="lede">{len(real_countries)} countries so far, grouped by region.</p></div></section><div class="wrap listing">{tiles_countries(0)}</div>', 0, [crld], "countries.html")

# ---------- CATEGORY PAGES
for k, items in by_cat.items():
    d=1; cr, crld = crumbs(d,[("Home","index.html"),("Categories","categories.html"),(k,"")])
    cc=Counter(r["country"] for r in items)
    answer=f'{CAT_BLURB.get(k,"")} GeoAtlas MEA lists {len(items)} in this category across {len([c for c in cc if c!="Regional (MEA)"])} countries, led by {andjoin([c for c,_ in cc.most_common(4) if c!="Regional (MEA)"][:3] or ["multinational suppliers"])}.'
    chips="".join(f'<a class="chip" href="{rel(d,"country/"+slug(c)+".html")}">{e(c if c!="Regional (MEA)" else "Multinational")}<span class="n">{n}</span></a>' for c,n in cc.most_common())
    body=f'''<section class="hero page-hero"><div class="wrap">{cr}<p class="eyebrow" style="margin-top:18px">Category</p><h1 class="page-h1">{e(k)} directory: Middle East &amp; Africa</h1><p class="lede">{e(answer)}</p></div></section>
<div class="wrap listing"><div class="chips" style="margin-bottom:18px">{chips}</div><div class="grid">{"".join(card(r,d) for r in items)}</div></div>'''
    page(f"category/{slug(k)}.html", f"{k} – {len(items)} Listings in the Middle East & Africa | {SITE}", answer[:155], body, d, [itemlist(f"{k} in the Middle East and Africa", items), crld])
cr, crld = crumbs(0,[("Home","index.html"),("Categories","")])
page("categories.html", f"Geospatial Industry Categories | {SITE}", "Browse geospatial companies by category: survey firms, GIS consultancies, hardware suppliers, software vendors, drone operators, satellite and EO, hydrographic, agencies and associations.",
     f'<section class="hero page-hero"><div class="wrap">{cr}<h1 class="page-h1">Browse by category</h1><p class="lede">The whole geospatial value chain, from field survey to satellite imagery.</p></div></section><div class="wrap listing">{tiles_cats(0)}</div>', 0, [crld], "categories.html")

# ---------- FAQ
cr, crld = crumbs(0,[("Home","index.html"),("FAQ","")])
page("faq.html", f"FAQ: Finding Survey, GIS & Geospatial Companies in the Middle East & Africa | {SITE}", "Answers on finding accredited surveyors in Dubai, survey regulation in Saudi Arabia, GIS vs survey companies, equipment suppliers and listing your company.",
     f'<section class="hero page-hero"><div class="wrap">{cr}<h1 class="page-h1">Frequently asked questions</h1><p class="lede">Straight answers about the directory and about finding geospatial services in the region.</p></div></section><div class="wrap listing prose">{"".join(f"<details class=q open><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q,a in FAQ)}</div>',
     0, [FAQ_LD, crld], "faq.html")

# ---------- ABOUT
cr, crld = crumbs(0,[("Home","index.html"),("About","")])
srcs=Counter(s.strip() for r in rows for s in r["source"].split(";"))
page("about.html", f"About & Methodology | {SITE}", f"How {SITE} collects, labels and updates geospatial company listings for the Middle East and Africa.",
f'''<section class="hero page-hero"><div class="wrap">{cr}<h1 class="page-h1">About {SITE}</h1><p class="lede">{TAGLINE}, built to put every firm, supplier and survey company in the region in one place.</p></div></section>
<div class="wrap listing prose">
<p class="answer">{SITE} is an open directory of the geospatial industry across the GCC, the wider Middle East and North Africa, and Sub-Saharan Africa. It is free to search and free to be listed in.</p>
<h2>What we include</h2><p>Any organisation whose main work is geospatial: land and engineering survey, GIS, photogrammetry, remote sensing, hydrography, drone mapping, satellite imagery, survey equipment and software, plus the agencies and professional bodies that regulate and represent the profession.</p>
<h2>Where the data comes from</h2><p>Listings are compiled from public registers and directories, then supplemented by company submissions. Only business contact details that the organisation itself or a public authority has published are shown.</p>
<ul>{"".join(f"<li>{e(s)} <span class=meta>({n})</span></li>" for s,n in srcs.most_common())}</ul>
<h2>Sourced and Check labels</h2><p><span class="src"><i></i>Sourced</span> entries come from a published register or partner directory. <span class="src check"><i></i>Check</span> entries come from general public information and have not yet been confirmed against the company's own website.</p>
<h2>Corrections and removals</h2><p>To correct, update or remove a listing, use the <a href="submit.html">listing form</a> or email <span class="mono">{SUBMIT_EMAIL}</span>.</p>
<h2>Reuse the data</h2><p>The dataset is available as <a href="data/companies.csv">CSV</a> and <a href="data/companies.json">JSON</a>. Please credit {SITE} with a link to {BASE_URL}.</p>
</div>''', 0, [ORG, crld], "about.html")

# ---------- SUBMIT
cats_opts="".join(f'<option>{e(k)}</option>' for k in sorted(by_cat))
cr, crld = crumbs(0,[("Home","index.html"),("List your company","")])
page("submit.html", f"List Your Geospatial Company for Free | {SITE}", "Add your survey, GIS, drone, satellite or geospatial equipment company to the Middle East and Africa directory. Free listing, checked before publishing.",
f'''<section class="hero page-hero"><div class="wrap">{cr}<h1 class="page-h1">List your company</h1><p class="lede">Free for any company, agency or association working in geospatial in the Middle East or Africa. We check every submission against your website before it goes live.</p></div></section>
<div class="wrap detail"><form class="sub panel" id="sub" novalidate data-endpoint="{e(SUBMIT_ENDPOINT)}" data-email="{e(SUBMIT_EMAIL)}">
<label>Company name *<input id="f-name" required autocomplete="organization"></label>
<label>Category<select id="f-cat">{cats_opts}</select></label>
<label>Country *<input id="f-country" required list="countrylist"></label>
<label>City<input id="f-city"></label>
<label class="full">Services (comma separated)<input id="f-services" placeholder="Topographic survey, Drone mapping, GIS"></label>
<label>Website<input id="f-web" type="url" placeholder="https://"></label>
<label>Business phone<input id="f-phone" type="tel"></label>
<label class="full">Business email<input id="f-email" type="email"></label>
<label class="full">Short description (max 300 characters)<textarea id="f-desc" maxlength="300"></textarea></label>
<div class="row" style="grid-column:1/-1"><button class="btn solid" type="submit">Send listing</button><span class="note" id="f-status" role="status"></span></div>
<div class="out" id="out" hidden><pre id="out-text"></pre><div class="row"><button class="btn solid" type="button" id="copy">Copy listing</button><span class="note">Paste it into an email to <span class="mono">{SUBMIT_EMAIL}</span>.</span></div></div>
</form>
<aside class="prose"><h2 style="margin-top:0">What happens next</h2><p>We check the details against your website and publish the listing, usually within a few working days.</p><p>Only add business contact details you are happy to make public. To change or remove an existing listing, send the same form with the company name and what should change.</p><p class="note">Listings go to <span class="mono">{SUBMIT_EMAIL}</span>.</p></aside>
<datalist id="countrylist">{"".join(f"<option value='{e(c)}'>" for c in sorted(set(GCC+MENA+real_countries)))}</datalist></div>''', 0, [crld], "submit.html")

# ---------- 404
page("404.html", f"Page not found | {SITE}", "This page does not exist.", f'<section class="hero page-hero"><div class="wrap"><h1 class="page-h1">Off the map</h1><p class="lede">This page does not exist. Try the <a style="color:inherit" href="/directory.html">directory search</a> or go back to the <a style="color:inherit" href="/">home page</a>.</p></div></section>', 0, noindex=True)

# ---------- assets, data, SEO files
shutil.copy(here/"site.css", out/"assets/site.css"); shutil.copy(here/"site.js", out/"assets/site.js")
(out/"data").mkdir(exist_ok=True)
shutil.copy(here/"companies.csv", out/"data/companies.csv")
pub=[{k:r[k] for k in ("name","category","country","city","services","website","phone","description","source")}|{"url":url("company/"+r["slug"]+".html")} for r in rows]
(out/"data/companies.json").write_text(json.dumps(pub, ensure_ascii=False, indent=1), encoding="utf-8")
(out/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{'1.0' if p=='index.html' else '0.8' if '/' not in p else '0.6'}</priority></url>\n" for u,p in SITEMAP)+"</urlset>\n", encoding="utf-8")
(out/"robots.txt").write_text(f"# {SITE}: search engines and AI assistants are welcome to index and cite this directory.\nUser-agent: *\nAllow: /\n\n"+"".join(f"User-agent: {b}\nAllow: /\n\n" for b in ["Googlebot","Bingbot","GPTBot","OAI-SearchBot","ChatGPT-User","ClaudeBot","Claude-SearchBot","PerplexityBot","Google-Extended","Applebot-Extended"])+f"Sitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
llms=f"# {SITE}\n\n> {TAGLINE}. {N} survey companies, GIS consultancies, equipment and software suppliers, drone and satellite operators, mapping agencies and professional bodies across {len(real_countries)} countries. Free to search; data downloadable as CSV and JSON.\n\n"
llms+=f"## Key pages\n- [Directory search]({url('directory.html')}): all listings with filters\n- [FAQ]({url('faq.html')}): finding surveyors and geospatial services in the region\n- [About & methodology]({url('about.html')}): sources and labels\n- [Dataset (JSON)]({url('data/companies.json')})\n- [Dataset (CSV)]({url('data/companies.csv')})\n\n## Countries\n"
llms+="".join(f"- [{c if c!='Regional (MEA)' else 'Multinational suppliers'}]({url('country/'+slug(c)+'.html')}): {len(v)} listings\n" for c,v in sorted(by_country.items(), key=lambda t:-len(t[1])))
llms+="\n## Categories\n"+"".join(f"- [{k}]({url('category/'+slug(k)+'.html')}): {CAT_BLURB.get(k,'')}\n" for k in sorted(by_cat))
(out/"llms.txt").write_text(llms, encoding="utf-8")
full=llms+"\n## All listings\n"+"".join(f"- [{r['name']}]({url('company/'+r['slug']+'.html')}) | {r['category']} | {r['city']+', ' if r['city'] else ''}{r['country']} | {r['services'].replace(';',',')} | {r['website'] or 'no website listed'}\n" for r in rows)
(out/"llms-full.txt").write_text(full, encoding="utf-8")
(out/"CNAME").write_text(BASE_URL.split("//")[1]+"\n")
(out/".nojekyll").write_text("")
print(f"Built {len(SITEMAP)} indexable pages, {N} listings, into {out}")
