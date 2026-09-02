"""Every instance behind Mindy's two review notes, with where each one lives.

Two corrections are baked in, because a plain grep gets both wrong.

"Custom Formulation" is not 27 page edits. The Capabilities column she sees at
the bottom of every page is a DEFAULT inside the Global Footer module, so it is
one edit that lands on every page at once. Counting it per page conflates one
fix with dozens, and hides that the prose mentions of "custom formulation" in
FAQ answers are a different thing she did not ask about.

manufactur* is not one bucket either. "Manufactured in Vermont, U.S.A." is
approved provenance and "contract manufacturing" is the industry's own noun --
a blanket swap to Providing would break both, so every hit is classified.
"""
import sys, json, re, csv, urllib.request, urllib.parse
sys.path.insert(0, "/tmp")
from hs import call, TOK

COPY_KEYS = {"html","value","text","heading","subheading","body_text","content",
             "label_text","button_text","preview_text","plain_text","header",
             "subheader","title","alt","link_text","description","answer",
             "question","linkLabel","headline"}

CF       = re.compile(r"custom[\s\-]{0,3}formulation", re.I)
MFG      = re.compile(r"manufactur(?:ing|er|ers|ed|e)", re.I)
PROV     = re.compile(r"manufactured\s+in\s+vermont", re.I)
CONTRACT = re.compile(r"contract\s+manufactur", re.I)
CLAIM    = re.compile(r"\b(we|our|us)\b[^.:;]{0,60}\bmanufactur", re.I)

def raw(path):
    u = "https://api.hubapi.com/cms/v3/source-code/published/content/" + urllib.parse.quote(path)
    r = urllib.request.Request(u, headers={"Authorization": "Bearer " + TOK})
    with urllib.request.urlopen(r) as f:
        return f.read().decode("utf8", "replace")

def flat(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()

def fields(node, path="", field=None):
    if isinstance(node, dict):
        nm = node.get("name")
        base = path + "/" + nm if isinstance(nm, str) and 0 < len(nm) < 60 else path
        for k, v in node.items():
            yield from fields(v, base, k)
    elif isinstance(node, list):
        for v in node:
            yield from fields(v, path, field)
    elif isinstance(node, str) and field in COPY_KEYS and node.strip():
        yield (path or "(page)", field, node)

def classify(s):
    if PROV.search(s):     return "KEEP  Vermont provenance"
    if CONTRACT.search(s): return "KEEP  industry term"
    if CLAIM.search(s):    return "CHANGE  first-person claim"
    return "REVIEW  neutral noun"

def hits(text, rx):
    f, out = flat(text), []
    for m in rx.finditer(f):
        a = f.rfind(".", 0, m.start()) + 1
        b = f.find(".", m.end())
        out.append(f[a:(len(f) if b < 0 else b + 1)].strip()[:280])
    return out

rows = []

# ---- global modules: one edit, every page ------------------------------------
for mod in ("Global Footer", "Global Header"):
    for leaf in ("fields.json", "module.html"):
        p = "Private Label/Modules/%s.module/%s" % (mod, leaf)
        try: s = raw(p)
        except Exception: continue
        for h in hits(s, CF):
            rows.append({"scope": "GLOBAL MODULE", "page": mod, "kind": "Custom Formulation",
                         "verdict": "REMOVE  one edit, all 127 pages", "module": p,
                         "field": "default", "text": h})
        for h in hits(s, MFG):
            rows.append({"scope": "GLOBAL MODULE", "page": mod, "kind": "manufactur*",
                         "verdict": classify(h), "module": p, "field": "default", "text": h})

# ---- page content ------------------------------------------------------------
pages, after = [], None
while True:
    q = {"limit": 100}
    if after: q["after"] = after
    r = call("GET", "/cms/v3/pages/site-pages", q=q)
    pages += [p for p in r.get("results", []) if "praxera" in (p.get("url") or "").lower()]
    after = (r.get("paging") or {}).get("next", {}).get("after")
    if not after: break

for p in sorted(pages, key=lambda x: x.get("slug") or ""):
    slug = p.get("slug") or "(home)"
    d = call("GET", "/cms/v3/pages/site-pages/%s/draft" % p["id"])
    seen = set()
    for where, field, text in fields(d):
        for rx, kind in ((CF, "Custom Formulation"), (MFG, "manufactur*")):
            if not rx.search(text): continue
            for h in hits(text, rx):
                k = (slug, where, field, h)
                if k in seen: continue
                seen.add(k)
                rows.append({
                    "scope": "PAGE COPY", "page": slug, "kind": kind,
                    "verdict": ("PROSE  not the footer link" if kind == "Custom Formulation"
                                else classify(h)),
                    "module": where, "field": field, "text": h})

cols = ["scope","page","kind","verdict","module","field","text"]
with open("deliverables/mindy_review_instances.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

from collections import Counter
print("pages scanned: %d      instances: %d" % (len(pages), len(rows)))
for kind in ("Custom Formulation", "manufactur*"):
    sub = [r for r in rows if r["kind"] == kind]
    print("\n=== %s — %d instances, %d locations ===" % (kind, len(sub), len({r['page'] for r in sub})))
    for v, n in Counter(r["verdict"] for r in sub).most_common():
        print("   %-34s %3d" % (v, n))
