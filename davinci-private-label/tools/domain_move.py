#!/usr/bin/env python3
"""Move Private Label pages onto a different connected domain, changing nothing else.

The slug is deliberately untouched. Audit spreadsheets on this project point at
slugs, so en/pl-demo-aging stays en/pl-demo-aging and only the hostname in front
of it changes -- which is the whole reason this is safe to do now rather than
after launch, while all 65 pages are still unpublished drafts with no traffic,
no backlinks and no redirects to maintain.

Only /domain and the /url that HubSpot derives from it may move. Anything else
and the page is refused, on the same terms as the icon tools.

usage: TOKEN=... domain_move.py <domain> [slug ...]          show every change
       TOKEN=... domain_move.py <domain> [slug ...] --apply   write and verify
"""
import copy, json, os, sys, time, urllib.request

TOK = os.environ["TOKEN"]
API = "https://api.hubapi.com"
H   = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
STAMPS  = {"authorName", "updatedById", "updatedAt", "updated"}
ALLOWED = ("/domain", "/url", "/absoluteUrl", "/resolvedDomain")

def call(method, path, body=None, tries=4):
    for i in range(tries):
        try:
            r = urllib.request.Request(API + path, method=method, headers=H,
                                       data=json.dumps(body).encode() if body else None)
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

def unexpected(diffs):
    return [d for d in diffs
            if d[0] not in ALLOWED and d[0].lstrip("/") not in STAMPS]

DOMAIN = sys.argv[1]
slugs  = [a for a in sys.argv[2:] if not a.startswith("--")]
apply_ = "--apply" in sys.argv

live_domains = {d["domain"] for d in call("GET", "/cms/v3/domains?limit=100")["results"]}
if DOMAIN not in live_domains:
    print(f"{DOMAIN} is not connected to this portal. Connected: {sorted(live_domains)}")
    sys.exit(1)

idx = json.load(open(S + "../reference/page_index.json"))
moved = same = 0
for p in idx["production"]:
    if slugs and p["slug"] not in slugs: continue
    live = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
    if live.get("domain") == DOMAIN: same += 1; continue
    after = copy.deepcopy(live); after["domain"] = DOMAIN
    bad = unexpected(differences(live, after))
    if bad:
        print(f"  REFUSED on {p['slug']}: {len(bad)} unexpected change(s)")
        for k, a, b in bad[:5]: print(f"      {k}")
        sys.exit(1)
    moved += 1
    print(f"  {p['slug']:44} {live.get('domain')}  ->  {DOMAIN}")
    if not apply_: continue
    fresh = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
    if fresh.get("updatedAt") != live.get("updatedAt"):
        print(f"    SKIPPED {p['slug']}: edited by someone else since this run started")
        moved -= 1; continue
    call("PATCH", f"/cms/v3/pages/site-pages/{p['id']}/draft", {"domain": DOMAIN})
    back = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
    stray = unexpected(differences(live, back))
    if stray:
        print(f"    READBACK MISMATCH on {p['slug']} — restore from the snapshot and stop")
        for k, a, b in stray[:5]: print(f"      {k}\n         - {str(a)[:70]}\n         + {str(b)[:70]}")
        sys.exit(1)
    if back.get("slug") != live.get("slug"):
        print(f"    SLUG MOVED on {p['slug']} — this must never happen"); sys.exit(1)
    print(f"    verified: domain moved, slug unchanged, 0 other fields touched")
print(f"\n{'MOVED' if apply_ else 'WOULD MOVE'}: {moved} page(s)"
      + (f"   ({same} already on {DOMAIN})" if same else ""))
