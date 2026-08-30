#!/usr/bin/env python3
"""Replace the [BRAND_TBD] placeholder in page titles, and change nothing else.

The title tag is the browser tab and the headline in a Google result, so this is
the most visible thing on the site -- and the cheapest to fix, because twenty
pages already read "Praxera Private Label" and settle the pattern.

One title needs more than a substitution. About reads
"About [BRAND_TBD] Laboratories", where "Laboratories" is left from DaVinci
Laboratories; substituting the token alone would invent "Praxera Laboratories",
a company that does not exist. Shawn's ruling: Praxera replaces DaVinci
Laboratories entire, so that title becomes "About Praxera".

Only htmlTitle and metaDescription may move. Anything else and the page is
refused, on the same terms as the icon tools.

usage: TOKEN=... title_fix.py            show every change, write nothing
       TOKEN=... title_fix.py --apply    write, verifying each page
"""
import copy, json, os, re, sys, time, urllib.request

TOK = os.environ["TOKEN"]
API = "https://api.hubapi.com"
H   = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
STAMPS  = {"authorName", "updatedById", "updatedAt", "updated"}
ALLOWED = ("/htmlTitle", "/metaDescription")

# titles that are not a straight token swap, and why
SPECIAL = {
    "pl-demo-about": ("About [BRAND_TBD] Laboratories | [BRAND_TBD] Private Label",
                      "About Praxera | Praxera Private Label"),
}

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
    return [d for d in diffs if d[0] not in ALLOWED and d[0].lstrip("/") not in STAMPS]

apply_ = "--apply" in sys.argv
idx = json.load(open(S + "../reference/page_index.json"))
changed = skipped = 0
for p in idx["production"]:
    live = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
    t, m = live.get("htmlTitle") or "", live.get("metaDescription") or ""
    if "[BRAND_TBD]" not in t and "[BRAND_TBD]" not in m: continue
    if p["slug"] in SPECIAL:
        want, new_t = SPECIAL[p["slug"]]
        if t != want:
            print(f"  SKIPPED {p['slug']}: title is not what the special case expects\n"
                  f"      expected {want!r}\n      found    {t!r}")
            skipped += 1; continue
    else:
        new_t = t.replace("[BRAND_TBD]", "Praxera")
    new_m = m.replace("[BRAND_TBD]", "Praxera")
    after = copy.deepcopy(live); after["htmlTitle"] = new_t; after["metaDescription"] = new_m
    bad = unexpected(differences(live, after))
    if bad:
        print(f"  REFUSED on {p['slug']}: {len(bad)} unexpected change(s)")
        for k, a, b in bad[:5]: print(f"      {k}")
        sys.exit(1)
    changed += 1
    tag = "  *" if p["slug"] in SPECIAL else "   "
    print(f"{tag} {p['slug']}")
    if t != new_t: print(f"       title  {t}\n           ->  {new_t}")
    if m != new_m: print(f"       meta   {m[:80]}\n           ->  {new_m[:80]}")
    if not apply_: continue
    fresh = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
    if fresh.get("updatedAt") != live.get("updatedAt"):
        print(f"       SKIPPED: edited by someone else since this run started")
        changed -= 1; skipped += 1; continue
    body = {"htmlTitle": new_t}
    if m != new_m: body["metaDescription"] = new_m
    call("PATCH", f"/cms/v3/pages/site-pages/{p['id']}/draft", body)
    back = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
    stray = unexpected(differences(live, back))
    if stray:
        print(f"       READBACK MISMATCH — restore from the snapshot and stop")
        for k, a, b in stray[:5]: print(f"      {k}")
        sys.exit(1)
    if back.get("slug") != live.get("slug"):
        print("       SLUG MOVED — this must never happen"); sys.exit(1)
    print(f"       verified: title updated, 0 other fields touched")
print(f"\n{'CHANGED' if apply_ else 'WOULD CHANGE'}: {changed} page(s)"
      + (f"   ({skipped} skipped)" if skipped else "")
      + "\n  * = the About title, which drops 'Laboratories' rather than inventing"
        " 'Praxera Laboratories'")
