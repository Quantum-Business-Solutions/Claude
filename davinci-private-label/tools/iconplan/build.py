#!/usr/bin/env python3
"""Build the Praxera icon plan: one outcome for every icon slot on the site.

Reads the live pages and the live /Praxera file library, decides what happens to
each slot, and renders the plan. Kept in the repo rather than a scratch directory
because the scratch directory has been cleared mid-build three times.

usage: TOKEN=... build.py            rebuild everything
       TOKEN=... build.py --render   re-render from the cached scan
"""
import json, os, re, sys, base64, html, collections, urllib.request

TOK = os.environ["TOKEN"]
H   = {"Authorization": "Bearer " + TOK}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
IDX = S + "../../reference/page_index.json"

def get(u):
    if u.startswith("/"): u = "https://api.hubapi.com" + u
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H)))

def fetch(u):
    return urllib.request.urlopen(
        urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=25).read()

# ---------------------------------------------------------------- scan
def scan_slots():
    """Every icon slot, with the key the page uses to label it."""
    idx = json.load(open(IDX)); rows = []
    def sniff(o, slug, pk=None):
        if isinstance(o, dict):
            if pk != "icon":
                src = None; ic = o.get("icon")
                if isinstance(ic, dict) and "/icons/" in str(ic.get("src", "")): src = ic["src"]
                elif isinstance(o.get("src"), str) and "/icons/" in o["src"]: src = o["src"]
                if src:
                    t = next((o[k] for k in ("title","label","heading","name","headline")
                              if isinstance(o.get(k), str) and o[k].strip()), "")
                    rows.append({"slug": slug, "icon": src.rsplit("/",1)[-1],
                        "title": re.sub(r"<[^>]+>", "", t).strip(),
                        "eyebrow": (o.get("number_or_eyebrow") or o.get("eyebrow") or "").strip(),
                        "stat": re.sub(r"<[^>]+>", "", o.get("stat_label") or "").strip()})
            for k, v in o.items(): sniff(v, slug, k)
        elif isinstance(o, list):
            for v in o: sniff(v, slug, pk)
    for p in idx["production"]:
        sniff(get(f"/cms/v3/pages/site-pages/{p['id']}"), p["slug"])
    return rows

def scan_icons(rows):
    """The new icons, and the ones currently on the pages, as data URIs.

    An icon can sit in the library under several names as it is re-cut
    (prenatal-care-green, prenatal-care-green-1, fitness-green-64) with the stale
    twin still present, so always take the most recent upload. Learn the real icon
    names from the "-ink" files first: splitting "design-your-brand-green" by its
    suffix alone yields "design-your" + "brand-green" and loses the icon."""
    url = "https://api.hubapi.com/files/v3/files/search?limit=100&path=/Praxera"; f = {}
    while url:
        d = get(url)
        for x in d.get("results", []): f[x["name"]] = x
        url = d.get("paging", {}).get("next", {}).get("link")
    bases = {re.sub(r"-\d+$", "", re.sub(r"-ink$", "", re.sub(r"-\d+$", "", n)))
             for n in f if re.match(r".*-ink(-\d+)?$", n)}
    best = {}
    for n, x in f.items():
        m = re.match(r"^(.+?)-green(?:-\d+)?$", n)
        if not m or m.group(1) not in bases: continue
        b = m.group(1); t = str(x.get("createdAt") or "")
        if b not in best or t > best[b][0]: best[b] = (t, x)
    new = {b: "data:image/png;base64," + base64.b64encode(fetch(x["url"])).decode()
           for b, (t, x) in best.items()}
    cur = {}
    for r in rows:
        if r["icon"] in cur: continue
        try:
            cur[r["icon"]] = "data:image/svg+xml;base64," + base64.b64encode(fetch(
                "https://info.davincilabs.com/hubfs/private-label/icons/" + r["icon"])).decode()
        except Exception: pass
    return new, cur, sorted(bases)

# ---------------------------------------------------------------- the rules
# key on the page -> new icon. First match wins, so anchored tags sit above the
# looser phrase rules.
RULES = [
 (r"schedule a consultation|book a consultation","calendar"),
 (r"^email$|email marketing","mail"), (r"^phone$","phone"),
 (r"mailing address|^address$","map-pin"), (r"social media marketing|^social","social"),
 (r"guide|library|^resource|read the guide|content marketing","file-text"),
 (r"^pediatric$","baby"), (r"^liver$|^detox$","liver"), (r"^lung$","lung"),
 (r"^senior$","senior"), (r"^mobility$","mobility"), (r"^stress$","stress"),
 # Sarah asked for consolidation rather than one icon per tag: marine, mushroom
 # and premium omega "all would fit into one category".
 (r"^bone$","bone-health"), (r"^nootropic$|^memory$","cognitive"),
 (r"^gut$|^high-cfu$|^strains$|^enzymes$","probiotics"),
 (r"^beauty$|^collagen$|^hair$","beauty-mood"),
 (r"^fat absorption$|^appetite$|^glp-1 support$","weight-management"),
 (r"^comprehensive$|^formula$","foundation"),
 (r"^testosterone$|^hgh support$","mens-health"),
 (r"^fertility$|^cycle support$","hormonal-balance"),
 (r"^botanical$|^mushroom$|^greens$|^greens\+probiotic$","botanical"),
 (r"^cardio$|^cardio energy$|^blood pressure$|^cholesterol$","cardiovascular"),
 (r"^cellular$|^cellular energy$|^mitochondrial$|^ubiquinol$|^longevity$","cellular"),
 (r"^immune$","immune"), (r"^omegas$|^premium omega$|^marine$","omega"),
 (r"^protein$|^vegan protein$","protein"),
 (r"^b-complex$|^vitamin c$|^vitamin d$|^minerals$|^folate$|^methylation$","vitamin-mineral"),
 (r"^foundation$|^daily$|^multi$|^multivitamin$","foundation"),
 (r"^hormonal$","hormonal-balance"), (r"^liposomal$","liposomal"),
 (r"^energy$|^vitality$","energy"), (r"^prenatal$","prenatal-care"),
 (r"^muscle$","muscle"), (r"^endurance$","endurance"), (r"^strength$","strength"),
 (r"^body comp$","body-composition"), (r"^brain$|^cognitive$","cognitive"),
 (r"^men's$|^prostate$","mens-health"), (r"^women's$","womens-health"),
 (r"^probiotic$|^digestive$","probiotics"), (r"^metabolic$","weight-management"),
 (r"^relaxation$|^sleep$","sleep"), (r"^skin & beauty$","beauty-mood"),
 (r"^bone & immune$","bone-health"), (r"^fitness$|^recovery$","fitness"),
 (r"u\.?s\.? manufactur|fda[- ]registered|fda & compliance","us-manufacturing"),
 (r"doctor[- ]formulated|clinical credibility|scientific rigor","doctor-formulated"),
 (r"white[- ]glove|partnership, not transaction","white-glove-support"),
 (r"^antioxidant$","antioxidant"),
 (r"pricing & margins|^pricing$","pricing"),
 (r"^discovery|kickoff|audience & positioning|brand discovery","discovery-strategy"),
 (r"product selection|formula selection|template selection","product-selection-design"),
 (r"label approval|label design|truth in labeling|branding & labels","label-approval"),
 (r"^brand & design$|design your|design iteration","design-your-brand"),
 (r"^production$|^manufacturing$|cgmp|compliance & qa","production"),
 (r"shipping|fulfillment|^distribution$|^launch$","shipping-launch"),
 (r"start selling|marketing & sales","start-selling"),
 (r"build your product line","build-your-product-line"),
]
# rules that put a tag on the nearest available icon rather than a real match
JUDGE = {"^foundation$|^daily$|^multi$|^multivitamin$","^energy$|^vitality$",
 "^men's$|^prostate$","^probiotic$|^digestive$","^metabolic$","^relaxation$|^sleep$",
 "^fitness$|^recovery$","^gut$|^high-cfu$|^strains$|^enzymes$",
 "^comprehensive$|^formula$","^fat absorption$|^appetite$|^glp-1 support$"}

def match(k):
    for p, i in RULES:
        if k and re.search(p, k, re.I): return i, (p in JUDGE)
    return None, False

def disposition(r):
    """One outcome per slot, following the decisions taken on the 25 August call."""
    k = r["eyebrow"] or r["title"] or r["stat"]
    ic, j = match(k)
    if re.search(r"shopify|amazon|ebay|woo|bigcommerce", k or "", re.I): return "LOGO", None, False
    if r["stat"]:   return "STRIP", None, False   # Tammy: "I personally agree"
    if ic:          return "SWAP", ic, j
    if r["eyebrow"]:return "ART", None, False     # a category tag with no icon
    return "STRIP", None, False                   # a benefit claim loses its icon

# ---------------------------------------------------------------- render
def render(rows, NEW, CUR):
    def img(s, c="ic"): return f'<img class="{c}" src="{s}" alt="">' if s else '<span class="q">?</span>'
    def e(s): return html.escape(s or "")
    P = collections.defaultdict(lambda: {"n":0,"cur":collections.Counter(),"pg":set(),"kind":"","j":False})
    strip = collections.defaultdict(lambda: {"n":0,"cur":collections.Counter()})
    logo  = collections.defaultdict(lambda: {"n":0,"cur":collections.Counter()})
    art   = collections.defaultdict(lambda: {"n":0,"cur":collections.Counter()})
    d = collections.Counter()
    for r in rows:
        out, ic, j = disposition(r); d[out] += 1
        k = r["eyebrow"] or r["title"] or r["stat"] or "(no label)"
        kind = "category tag" if r["eyebrow"] else ("stat band" if r["stat"] else "concept")
        if out == "SWAP":
            p = P[(k, ic)]; p["n"]+=1; p["cur"][r["icon"]]+=1; p["pg"].add(r["slug"])
            p["kind"]=kind; p["j"]=j
        else:
            (strip if out=="STRIP" else logo if out=="LOGO" else art)[k]["n"] += 1
            (strip if out=="STRIP" else logo if out=="LOGO" else art)[k]["cur"][r["icon"]] += 1
    mrows = ""
    for (k, ic), p in sorted(P.items(), key=lambda x: (-x[1]["n"], x[0][0].lower())):
        cur = "".join(img(CUR.get(c)) for c, _ in p["cur"].most_common(4))
        warn = f'<span class="warn">{len(p["cur"])} different icons today</span>' if len(p["cur"])>1 else ""
        jm = '<span class="jm">judgement call</span>' if p["j"] else ""
        mrows += (f'<tr><td class="key"><b>{e(k)}</b><span class="tag">{p["kind"]}</span>{jm}{warn}</td>'
                  f'<td class="cell">{cur}</td><td class="arrow">&rarr;</td>'
                  f'<td class="cell">{img(NEW.get(ic),"ic nu")}</td><td class="nm">{e(ic)}</td>'
                  f'<td class="num">{p["n"]}</td><td class="num">{len(p["pg"])}</td></tr>')
    def chips(dd, limit=None):
        it = sorted(dd.items(), key=lambda x: -x[1]["n"])
        if limit: it = it[:limit]
        return "".join(f'<div class="uitem">'
            f'{"".join(img(CUR.get(c)) for c,_ in v["cur"].most_common(1))}'
            f'<span class="ul">{e(k)}</span><span class="un">{v["n"]}</span></div>' for k, v in it)
    steps = {k: v for k, v in art.items() if re.match(r"^(STEP|WEEK)", k)}
    rest  = {k: v for k, v in art.items() if k not in steps}
    open(S+"plan.html","w").write(open(S+"template.html").read().format(
        swap=d["SWAP"], strip=d["STRIP"], logo=d["LOGO"], art=d["ART"],
        nicons=len({i for (_, i) in P}), mrows=mrows, nostrip=350-d["STRIP"],
        stripchips=chips(strip, 44), nstrip=len(strip), logochips=chips(logo),
        artchips=chips(rest), nart=sum(v["n"] for v in rest.values()),
        nstep=sum(v["n"] for v in steps.values()), nstepvar=len(steps)))
    print(f"SWAP {d['SWAP']}  STRIP {d['STRIP']}  LOGO {d['LOGO']}  ART {d['ART']}"
          f"   ({len({i for (_,i) in P})} icons across {len(P)} rules)")

if __name__ == "__main__":
    if "--render" in sys.argv:
        c = json.load(open(S+"cache.json"))
    else:
        rows = scan_slots()
        new, cur, roster = scan_icons(rows)
        c = {"rows": rows, "new": new, "cur": cur, "roster": roster}
        json.dump(c, open(S+"cache.json","w"))
        print(f"scanned {len(rows)} slots, {len(new)} icons, {len(cur)} current files")
    render(c["rows"], c["new"], c["cur"])
