#!/usr/bin/env python3
"""Inventory the HubSpot assets serving Private Label, for the Praxera migration.

The 63 website pages are the visible part. Behind them sit forms that collect,
workflows that enrol, and emails that get sent -- and the rebrand is not finished
until those carry the new name too.

The check worth running is not "what is named Private Label" but "what does the
new site actually depend on". Those are different sets: the new pages already use
a Praxera-named consultation form that no live workflow listens to, so the
nurture the old site fed is not fed by the new one.

usage: TOKEN=... asset_inventory.py > inventory.json
"""
import json, os, re, sys, time, collections, urllib.request
import concurrent.futures as cf

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"
PL    = re.compile(r"private[\s_-]?label|praxera", re.I)
STALE = re.compile(r"\bOLD\b|DO NOT USE|deprecated|unused|\btest\b|copy of", re.I)

def get(u, tr=4):
    if u.startswith("/"): u = "https://api.hubapi.com" + u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(
            u, headers={"Authorization": "Bearer " + T}), timeout=40))
        except Exception:
            if i == tr - 1: raise
            time.sleep(1.5 * (i + 1))

def page(u, cap=40):
    out, n = [], 0
    while u and n < cap:
        d = get(u); out += d.get("results", []); n += 1
        nx = d.get("paging", {}).get("next", {})
        u = nx.get("link") or (u.split("?")[0] + "?limit=100&after=" + nx["after"]
                               if nx.get("after") else None)
    return out

GUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

forms  = {f["id"]: f.get("name", "") for f in page("/marketing/v3/forms?limit=100")}
flows  = page("/automation/v4/flows?limit=100")
emails = page("/marketing/v3/emails?limit=100")
lps    = page("/cms/v3/pages/landing-pages?limit=100")

# which forms the new site actually embeds
idx = json.load(open(S + "../reference/page_index.json"))
def scan(p):
    s = json.dumps(get(f"/cms/v3/pages/site-pages/{p['id']}/draft"))
    return p["slug"], {g for g in GUID.findall(s) if g in forms}
with cf.ThreadPoolExecutor(5) as ex: pages = list(ex.map(scan, idx["production"]))
used = collections.defaultdict(set)
for slug, gs in pages:
    for g in gs: used[g].add(slug)

# which workflows reference which form -- the dependency that decides migration order
def body(f):
    try: return f, json.dumps(get(f"/automation/v4/flows/{f['id']}"))
    except Exception: return f, ""
with cf.ThreadPoolExecutor(8) as ex: bodies = list(ex.map(body, flows))
listens = collections.defaultdict(list)
for f, s in bodies:
    for g in {x for x in GUID.findall(s) if x in forms}:
        listens[g].append({"name": f.get("name", ""), "live": bool(f.get("isEnabled"))})

out = {
 "forms_on_new_site": [
    {"id": g, "name": forms[g], "pages": sorted(used[g]),
     "workflows": listens.get(g, []),
     "live_workflows": sum(1 for w in listens.get(g, []) if w["live"])}
    for g in sorted(used, key=lambda x: -len(used[x]))],
 "workflows": [{"name": f.get("name", ""), "id": f.get("id"), "live": bool(f.get("isEnabled"))}
    for f in flows if PL.search(f.get("name", ""))],
 "emails": [{"name": e.get("name", ""), "state": e.get("state", ""),
             "updated": (e.get("updatedAt") or "")[:10]}
    for e in emails if PL.search(e.get("name", ""))],
 "landing_pages": [{"name": p.get("name", ""), "state": p.get("currentState", ""),
                    "slug": p.get("slug", ""), "stale": bool(STALE.search(p.get("name", "")))}
    for p in lps if PL.search(p.get("name", ""))],
 "other_forms": [{"id": g, "name": n, "stale": bool(STALE.search(n))}
    for g, n in forms.items() if PL.search(n) and g not in used],
}
json.dump(out, sys.stdout, indent=1)
