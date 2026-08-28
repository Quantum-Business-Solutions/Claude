#!/usr/bin/env python3
"""What has actually changed in the Private Label pages, field by field.

Timestamps say a page moved; they do not say what moved, and on this project the
difference has mattered -- a six-second sweep across twelve pages by "HubSpot
System" looks identical to twelve people editing copy until you read the fields.

Compares the draft against a baseline: the page's own base record by default
(HubSpot leaves that behind at the last publish, which on this project is 25
August), or a snapshot directory with --since.

usage: TOKEN=... changelog.py [--since snapshots/pages/<stamp>] [--full]
"""
import json, os, re, sys, gzip, glob, html, collections, urllib.request

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))

def text(v):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(str(v)))).strip()

FIELDS = ("title","label","heading","name","headline","content","subhead","body",
          "number_or_eyebrow","eyebrow","stat_label","value","alt","question","answer")

def leaves(o, path=""):
    """Every piece of human-readable copy, keyed by where it sits."""
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and k in FIELDS and v.strip():
                out[f"{path}/{k}"] = v
            elif isinstance(v, (dict, list)):
                out.update(leaves(v, f"{path}/{k}"))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(leaves(v, f"{path}[{i}]"))
    return out

def compare(old, new):
    a, b = leaves(old.get("layoutSections")), leaves(new.get("layoutSections"))
    ch = []
    for k in sorted(set(a) | set(b)):
        x, y = text(a.get(k, "")), text(b.get(k, ""))
        if x != y: ch.append((k, x, y))
    for k in ("htmlTitle", "metaDescription", "slug", "name", "featuredImageAltText"):
        x, y = text(old.get(k) or ""), text(new.get(k) or "")
        if x != y: ch.append(("(page) " + k, x, y))
    return ch

def classify(x, y):
    """Name the edit, so a sweep of identical rewrites reads as one thing."""
    if x and not y: return "deleted"
    if y and not x: return "added"
    if x.replace("™","").replace("®","").strip() == y.strip(): return "symbol removed"
    if re.sub(r"\s+","",x.lower()) == re.sub(r"\s+","",y.lower()): return "whitespace/case"
    if "davinci" in x.lower() and "davinci" not in y.lower(): return "DaVinci removed"
    return "rewritten"

idx  = json.load(open(S + "../reference/page_index.json"))
snap = None
if "--since" in sys.argv:
    d = sys.argv[sys.argv.index("--since") + 1].rstrip("/")
    snap = {p: json.loads(gzip.open(f).read().decode())
            for f in glob.glob(f"{d}/*.json.gz") for p in [os.path.basename(f).split(".")[0]]}
    print(f"baseline: snapshot {d}\n")
else:
    print("baseline: each page's base record (last publish)\n")

kinds = collections.Counter(); pages = 0; total = 0; detail = []
for p in idx["production"]:
    new = get(f"/cms/v3/pages/site-pages/{p['id']}/draft")
    if snap is not None:
        if p["id"] not in snap: continue
        old = snap[p["id"]]; old = old.get("draft", old)
    else:
        old = get(f"/cms/v3/pages/site-pages/{p['id']}")
    ch = compare(old, new)
    if not ch: continue
    pages += 1; total += len(ch)
    who = f'{new.get("authorName") or "?"}  {new.get("updatedAt","")[:16].replace("T"," ")}'
    detail.append((p["slug"], who, ch))
    for _, x, y in ch: kinds[classify(x, y)] += 1

print(f"{pages} of {len(idx['production'])} pages differ  --  {total} field(s) changed")
print("  " + "   ".join(f"{v} {k}" for k, v in kinds.most_common()) + "\n")
cap = None if "--full" in sys.argv else 4
for slug, who, ch in sorted(detail, key=lambda x: -len(x[2])):
    print(f"\n{slug}   [{who}]   {len(ch)} field(s)")
    for k, x, y in ch[:cap]:
        print(f"    {classify(x,y):16} {k[-52:]}")
        print(f"        - {x[:132]}")
        print(f"        + {y[:132]}")
    if cap and len(ch) > cap: print(f"    ... {len(ch)-cap} more (--full)")
