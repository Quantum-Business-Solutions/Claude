#!/usr/bin/env python3
"""Put an icon on a card that has none, and change nothing else.

The swap tool only rewrites a src it can already see, so it cannot fill a slot
that was emptied -- which is the state the resources row was left in, five cards
with icons and one without. Filling that one is what closes the row.

usage: TOKEN=... icon_fill.py <slug> <card label> <icon file> [--apply]
"""
import copy, json, os, sys, time, urllib.request

TOK = os.environ["TOKEN"]; API = "https://api.hubapi.com"
H = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
S = os.path.dirname(os.path.abspath(__file__)) + "/"
STAMPS = {"authorName", "updatedById", "updatedAt", "updated"}

def call(m, p, b=None, tries=4):
    for i in range(tries):
        try:
            r = urllib.request.Request(API + p, method=m, headers=H,
                                       data=json.dumps(b).encode() if b else None)
            with urllib.request.urlopen(r) as f: raw = f.read()
            return json.loads(raw) if raw else {}
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))

def flatten(o, p="", out=None):
    if out is None: out = {}
    if isinstance(o, dict):
        for k, v in o.items(): flatten(v, p + "/" + str(k), out)
    elif isinstance(o, list):
        for i, v in enumerate(o): flatten(v, p + f"[{i}]", out)
    else: out[p] = o
    return out

def differences(a, b):
    A, B = flatten(a), flatten(b)
    return sorted((k, A.get(k, "\0"), B.get(k, "\0"))
                  for k in set(A) | set(B) if A.get(k, "\0") != B.get(k, "\0"))

SLUG, LABEL, FILE = sys.argv[1], sys.argv[2], sys.argv[3]
apply_ = "--apply" in sys.argv
# The library runs past one page, and the name filter is ignored by this API,
# so walk the cursor rather than trusting the first hundred.
def find(name):
    u = "/files/v3/files/search?limit=100&path=/Praxera"
    while u:
        d = call("GET", u)
        for f in d.get("results", []):
            if f["name"] == name: return f["url"]
        nxt = d.get("paging", {}).get("next", {}).get("link")
        u = nxt.replace("https://api.hubapi.com", "") if nxt else None
    raise SystemExit(f"  {name} is not in /Praxera")
url = find(FILE)
idx = json.load(open(S + "../reference/page_index.json"))
p = next(x for x in idx["production"] if x["slug"] == SLUG)
live = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
after = copy.deepcopy(live); hits = []

def walk(o):
    if isinstance(o, dict):
        arr = o.get("cards")
        if isinstance(arr, list):
            for c in arr:
                if not isinstance(c, dict): continue
                if (c.get("title") or c.get("number_or_eyebrow") or "").strip() == LABEL:
                    ic = c.setdefault("icon", {})
                    if ic.get("src"):
                        print(f"  {LABEL} already has {ic['src'].rsplit('/',1)[-1]} -- refusing to overwrite")
                        sys.exit(1)
                    ic["src"] = url; ic.setdefault("alt", ""); ic.setdefault("loading", "lazy")
                    hits.append(c)
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(after)
if len(hits) != 1:
    print(f"  matched {len(hits)} cards named {LABEL!r} -- expected exactly one"); sys.exit(1)
bad = [d for d in differences(live, after) if not d[0].endswith(("/icon/src", "/icon/alt", "/icon/loading"))]
if bad:
    print(f"  REFUSED: {len(bad)} non-icon change(s)")
    for k, a, b in bad[:5]: print("      ", k)
    sys.exit(1)
print(f"  {SLUG}  {LABEL}  (none)  ->  {FILE}")
if not apply_:
    print("\nWOULD FILL: 1 icon"); sys.exit(0)
fresh = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
if fresh.get("updatedAt") != live.get("updatedAt"):
    print("  SKIPPED: edited by someone else since this run started"); sys.exit(0)
call("PATCH", f"/cms/v3/pages/site-pages/{p['id']}/draft", after)
back = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
stray = [d for d in differences(live, back)
         if not d[0].endswith(("/icon/src", "/icon/alt", "/icon/loading"))
         and d[0].lstrip("/") not in STAMPS]
if stray:
    print("  READBACK MISMATCH — restore from the snapshot and stop")
    for k, a, b in stray[:5]: print("      ", k); sys.exit(1)
print("     verified: 1 filled, 0 other fields touched\nFILLED: 1 icon")
