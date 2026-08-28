#!/usr/bin/env python3
"""Swap icons on the Private Label pages, and change nothing else.

Two things this gets right that an earlier version did not.

It writes to the DRAFT. HubSpot keeps unpublished edits there and returns the base
record from /cms/v3/pages/site-pages/{id}; on this project the base sat five days
stale while the site rendered current content. Writing to the base would have put
new icons where nothing renders them and left the draft untouched.

And it keys the swap on the SLOT, not on the filename that is in it. One current
file, pl-icon-30d8dc8a51.svg, serves 42 different labels across the site -- mapping
filename to new icon would have stamped a single glyph across all 42.

usage: icon_swap.py --dry [slug ...]      show every change, write nothing
       icon_swap.py --apply <slug> [...]  write, verifying each page
"""
import copy, json, os, re, sys, time, urllib.request

TOK = os.environ["TOKEN"]
API = "https://api.hubapi.com"
H   = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
sys.path.insert(0, S + "iconplan")
from build import RULES, JUDGE, match          # one source of truth for the mapping

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

STAMPS = {"authorName", "updatedById", "updatedAt", "updated"}

def swap(page, urls, report):
    """Rewrite icon.src per slot. The key is the card's own eyebrow/title/stat."""
    def walk(o, pk=None):
        if isinstance(o, dict):
            if pk != "icon":
                ic = o.get("icon")
                # Match the Praxera folder too, not just the old /icons/ path.
                # One card had already been moved to phone-ink.png by hand, and a
                # detector keyed on "/icons/" could not see it -- so the page kept
                # a navy icon beside two green ones and nothing reported it.
                src = str(ic.get("src", "")) if isinstance(ic, dict) else ""
                if "/icons/" in src or "/Praxera/" in src:
                    key = ((o.get("number_or_eyebrow") or "").strip()
                           or re.sub(r"<[^>]+>", "", o.get("title") or "").strip()
                           or re.sub(r"<[^>]+>", "", o.get("stat_label") or "").strip())
                    icon, judged = match(key)
                    if icon and icon in urls:
                        report.append((key, ic["src"].rsplit("/", 1)[-1],
                                       urls[icon].rsplit("/", 1)[-1], judged))
                        ic["src"] = urls[icon]
            for k, v in o.items(): walk(v, k)
        elif isinstance(o, list):
            for v in o: walk(v, pk)
    walk(page); return page

def icon_urls():
    """Newest upload wins: an icon can sit under several names as it is re-cut."""
    url = f"{API}/files/v3/files/search?limit=100&path=/Praxera"; f = {}
    while url:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H)))
        for x in d.get("results", []): f[x["name"]] = x
        url = d.get("paging", {}).get("next", {}).get("link")
    bases = {re.sub(r"-\d+$", "", re.sub(r"-ink$", "", re.sub(r"-\d+$", "", n)))
             for n in f if re.match(r".*-ink(-\d+)?$", n)}
    best = {}
    for n, x in f.items():
        m = re.match(r"^(.+?)-green(?:-\d+)?$", n)
        if not m or m.group(1) not in bases: continue
        b = m.group(1); t = str(x.get("createdAt") or "")
        if b not in best or t > best[b][0]: best[b] = (t, x["url"])
    return {b: u for b, (t, u) in best.items()}

def run(slugs, apply_):
    idx = json.load(open(S + "../reference/page_index.json"))
    urls = icon_urls()
    print(f"{len(urls)} icons available in /Praxera\n")
    total = pages = judged = 0
    for p in idx["production"]:
        if slugs and p["slug"] not in slugs: continue
        live = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
        after = copy.deepcopy(live); rep = []
        swap(after, urls, rep)
        if not rep: continue
        bad = [d for d in differences(live, after) if not d[0].endswith("/icon/src")]
        if bad:
            print(f"  REFUSED on {p['slug']}: {len(bad)} non-icon change(s)")
            for k, a, b in bad[:5]: print(f"      {k}\n        {str(a)[:80]}\n        {str(b)[:80]}")
            sys.exit(1)
        n = len(differences(live, after)); total += n; pages += 1
        judged += sum(1 for r in rep if r[3])
        print(f"\n{p['slug']}  —  {n} icon(s)")
        for key, old, new, j in rep:
            print(f"     {'~' if j else ' '} {key[:34]:36} {old:26} -> {new}")
        if not apply_: continue
        fresh = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
        if fresh.get("updatedAt") != live.get("updatedAt"):
            print(f"  SKIPPED {p['slug']}: edited by someone else since this run started"); continue
        call("PATCH", f"/cms/v3/pages/site-pages/{p['id']}/draft", after)
        back = call("GET", f"/cms/v3/pages/site-pages/{p['id']}/draft")
        # HubSpot stamps its own audit fields on any write: the page's "last edited
        # by" becomes whoever owns the token. That is not a content change, and
        # treating it as one aborted a run whose page was in fact untouched.
        stray = [d for d in differences(live, back)
                 if not d[0].endswith("/icon/src")
                 and d[0].lstrip("/") not in STAMPS]
        if stray:
            print(f"  READBACK MISMATCH on {p['slug']} — restore from the snapshot and stop")
            for k, a, b in stray[:5]: print(f"      {k}")
            sys.exit(1)
        print(f"     verified: {n} changed, 0 other fields touched")
        time.sleep(0.3)
    print(f"\n{'WOULD CHANGE' if not apply_ else 'CHANGED'}: {total} icon(s) on {pages} page(s)"
          f"   ({judged} of them are judgement calls, marked ~)")

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    run(set(a), "--apply" in sys.argv)
