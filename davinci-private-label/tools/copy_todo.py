#!/usr/bin/env python3
"""What copy is still outstanding on the Private Label pages.

Two rewrites are in flight and neither is finished: DaVinci -> Praxera, and a
sweep replacing the manufacturing claim ("manufacturers" -> "providers",
"we make them" -> "they are made"). This finds what each has not reached yet,
so the remainder can be worked rather than rediscovered.

Reads the draft. The base record lags behind whatever the team last saved.

usage: TOKEN=... copy_todo.py [--full]
"""
import json, os, re, sys, html, collections, urllib.request

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))

# What to look for, and why it is on the list.
#
# "manufactur*" is split in two on purpose. Barb's sweep is only after the claim
# that Praxera does the manufacturing -- "50 years of supplement manufacturing",
# "we make them", "trusted supplement manufacturers". It is not after the word
# itself: "line up a vitamin manufacturer" is about the reader's supplier, and
# the blog titles carry it as a search term. Counting both together gives 241
# and hides the roughly forty that are actually the sweep's remainder.
CLAIM = (r"(we|our|us|praxera|foodscience)\b[^.]{0,60}\bmanufactur"
         r"|\bmanufactur\w*\b[^.]{0,40}\b(we|our|us)\b"
         r"|\b(supplement|vitamin|contract) manufactur(er|ing)s?\b"
         r"|\bmanufactured in (our|the) \w+")
CHECKS = [
 ("DaVinci",        r"da\s?vinci",            "must not appear -- brand is Praxera"),
 ("Prexera",        r"prexera",               "misspelling of Praxera"),
 ("mfg claim",      CLAIM,                    "Barb's sweep: -> provide / providers"),
 ("we make/produce",r"\bwe (make|produce|manufacture)\b", "Barb's sweep: -> they are made"),
 ("mfg (neutral)",  r"manufactur\w*",         "the word elsewhere -- probably leave"),
 ("Vermont",        r"\bvermont\b",           "ties the brand to the FoodScience plant"),
 ("FoodScience",    r"foodscience",           "legal entity -- decide per instance"),
 ("Custom Formulation", r"custom formulation","client asked about this wording"),
 ("trademark",      r"[™®]",                  "™ being removed elsewhere -- inconsistent"),
]
SKIP_NEUTRAL = {"mfg (neutral)"}

FIELDS = ("title","label","heading","name","headline","content","subhead","body",
          "number_or_eyebrow","eyebrow","stat_label","value","alt","question","answer")

def leaves(o, path=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and k in FIELDS and v.strip(): out[f"{path}/{k}"] = v
            elif isinstance(v, (dict, list)): out.update(leaves(v, f"{path}/{k}"))
    elif isinstance(o, list):
        for i, v in enumerate(o): out.update(leaves(v, f"{path}[{i}]"))
    return out

def sentences(v):
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(v))).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]

idx = json.load(open(S + "../reference/page_index.json"))
hits = collections.defaultdict(list)
# Shawn: "we are only looking at website pages and the copy in them right now
# under private label". The production bucket also carries two blog posts.
pages = [p for p in idx["production"] if not re.match(r"(-temporary-slug-)?blog/", p["slug"])]
print(f"{len(pages)} website pages ({len(idx['production'])-len(pages)} blog posts excluded)\n")
for p in pages:
    d = get(f"/cms/v3/pages/site-pages/{p['id']}/draft")
    seen = set()
    fields = dict(leaves(d.get("layoutSections")))
    for k in ("htmlTitle", "metaDescription", "featuredImageAltText"):
        if d.get(k): fields["(page) " + k] = d[k]
    for where, v in fields.items():
        for s in sentences(v):
            claimed = re.search(CLAIM, s, re.I)
            for name, pat, _ in CHECKS:
                if name in SKIP_NEUTRAL and claimed: continue
                if re.search(pat, s, re.I) and (name, s) not in seen:
                    seen.add((name, s))
                    hits[name].append((p["slug"], where.split("/")[-1], s))

print(f"{'check':20} {'hits':>5}  {'pages':>5}  why")
for name, pat, why in CHECKS:
    h = hits[name]
    print(f"{name:20} {len(h):>5}  {len({x[0] for x in h}):>5}  {why}")

cap = None if "--full" in sys.argv else 6
for name, pat, why in CHECKS:
    h = hits[name]
    if not h: continue
    print(f"\n=== {name} -- {len(h)} on {len({x[0] for x in h})} page(s) ===")
    for slug, field, s in sorted(h)[:cap]:
        print(f"  {slug:30} {field[:18]:18} {s[:104]}")
    if cap and len(h) > cap: print(f"  ... {len(h)-cap} more (--full)")
