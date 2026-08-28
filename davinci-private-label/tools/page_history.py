#!/usr/bin/env python3
"""Every field that changed on a page, revision by revision, with who and when.

HubSpot's revision history in the UI lists versions and lets you restore one,
but it will not tell you what actually differs between two of them. The API
returns the whole page object at each revision, so the diff can be done here:
walk consecutive revisions and report each changed field by name.

usage: TOKEN=... page_history.py <slug> [--limit N] [--all-fields]
"""
import json, os, re, sys, html, urllib.request

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"
SLUG  = sys.argv[1]
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 25
ALL   = "--all-fields" in sys.argv

# HubSpot rewrites these on every save; listing them would bury the real edits.
NOISE = re.compile(r"/(updated|updatedAt|updatedById|authorName|authorAt|authorUserId"
                   r"|revisionId|currentState|publishDate|createdAt|deletedAt"
                   r"|.*(Id|_id))$")

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))

def walk(o, p=""):
    d = {}
    if isinstance(o, dict):
        for k, v in o.items(): d.update(walk(v, f"{p}/{k}"))
    elif isinstance(o, list):
        for i, v in enumerate(o): d.update(walk(v, f"{p}[{i}]"))
    else: d[p] = o
    return d

def show(v):
    s = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(str(v)))).strip()
    return s or "(empty)"

def label(k):
    """Name the field the way a person would look for it.

    Keep the indices. Collapsing "rows[6]/0/rows[0]/0" to nothing made every
    row on the page report as the same field, so twenty distinct edits printed
    as one line twenty times."""
    k = k.replace("/layoutSections/", "").replace("/params/", ".")
    k = re.sub(r"/rows\[(\d+)\]/0", r">r\1", k)
    return k.strip("/")

idx  = json.load(open(S + "../reference/page_index.json"))
page = next(p for b, v in idx.items() if isinstance(v, list)
            for p in v if p["slug"] == SLUG)
revs = get(f"/cms/v3/pages/site-pages/{page['id']}/revisions?limit={LIMIT}")["results"]
revs.sort(key=lambda r: r["updated"])

print(f"{SLUG}   id {page['id']}   {len(revs)} revision(s), oldest first\n")
prev = None
for r in revs:
    when = str(r["updated"])[:19].replace("T", " ")
    who  = (r.get("user") or {}).get("fullName") or (r.get("user") or {}).get("email") or "?"
    if prev is None:
        print(f"{when}  {who:18} (earliest revision held)")
        prev = walk(r["object"]); continue
    cur  = walk(r["object"])
    keys = sorted(k for k in set(prev) | set(cur) if prev.get(k) != cur.get(k))
    real = [k for k in keys if ALL or not NOISE.search(k)]
    print(f"\n{when}  {who:18} {len(real)} field(s) changed"
          + (f"   [{len(keys)-len(real)} housekeeping hidden]" if len(keys) - len(real) else ""))
    for k in real:
        a, b = show(prev.get(k, "")), show(cur.get(k, ""))
        kind = ("icon" if k.endswith("/icon/src") else
                "added" if k not in prev else "removed" if k not in cur else "edit")
        if kind == "icon": a, b = a.rsplit("/", 1)[-1], b.rsplit("/", 1)[-1]
        print(f"    [{kind}] {label(k)}")
        print(f"        - {a[:118]}")
        print(f"        + {b[:118]}")
    prev = cur
