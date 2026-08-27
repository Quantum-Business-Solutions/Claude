#!/usr/bin/env python3
"""Capture every Private Label page so an icon swap can be undone.

Captures the DRAFT buffer, not the base record. The two diverge: HubSpot keeps
unpublished edits in the draft, and /cms/v3/pages/site-pages/{id} returns the base,
which on this project was five days stale while the site rendered current content.
Restoring from the base would silently roll the client's copy edits back.

Both are captured anyway -- the base is what a publish would promote -- but the
draft is what a restore writes.

usage: snapshot.py                  capture into snapshots/<timestamp>/
       snapshot.py --verify DIR     re-read the portal and diff against a capture
       snapshot.py --restore DIR [slug ...]   put the draft content back
"""
import gzip, json, os, re, sys, time, urllib.request

TOK = os.environ["TOKEN"]
API = "https://api.hubapi.com"
H   = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
ROOT= S + "../snapshots/pages/"

def call(method, path, body=None, tries=4):
    for i in range(tries):
        try:
            r = urllib.request.Request(API + path, method=method, headers=H,
                                       data=json.dumps(body).encode() if body else None)
            with urllib.request.urlopen(r) as f:
                raw = f.read()
            return json.loads(raw) if raw else {}
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))

ICON = re.compile(r"/private-label/icons/|/Praxera/")
def fingerprint(page):
    """Enough to tell whether a restore actually put things back."""
    blob = json.dumps(page)
    return {"bytes": len(blob),
            "icons": len(ICON.findall(blob)),
            "updatedAt": page.get("updatedAt"),
            "slug": page.get("slug")}

def pages():
    idx = json.load(open(S + "../reference/page_index.json"))
    return [(p["id"], p["slug"]) for p in idx["production"]]

def capture():
    stamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    out = ROOT + stamp + "/"
    os.makedirs(out, exist_ok=True)
    man = {"taken": stamp, "pages": {}}
    for pid, slug in pages():
        rec = {}
        for kind, path in (("draft", f"/cms/v3/pages/site-pages/{pid}/draft"),
                           ("base",  f"/cms/v3/pages/site-pages/{pid}")):
            try: rec[kind] = call("GET", path)
            except Exception as e: rec[kind] = {"__error": str(e)}
        gzip.open(f"{out}{pid}.json.gz", "wt").write(json.dumps(rec))
        d = rec.get("draft") or {}
        man["pages"][pid] = {"slug": slug, "draft": fingerprint(d) if "__error" not in d else None,
                             "base": fingerprint(rec["base"]) if "__error" not in rec.get("base",{}) else None}
        print(f"  {slug:44} draft {man['pages'][pid]['draft']['icons'] if man['pages'][pid]['draft'] else '?':>4} icons")
    json.dump(man, open(out + "manifest.json", "w"), indent=1)
    bad = [p for p, v in man["pages"].items() if not v["draft"]]
    total = sum(v["draft"]["icons"] for v in man["pages"].values() if v["draft"])
    print(f"\ncaptured {len(man['pages'])} pages -> {out}")
    print(f"  icon references captured : {total}")
    print(f"  pages that failed to read: {len(bad)}  {bad if bad else ''}")
    if bad: sys.exit(1)

def verify(d):
    man = json.load(open(f"{ROOT}{d}/manifest.json"))
    drift = 0
    for pid, v in man["pages"].items():
        live = fingerprint(call("GET", f"/cms/v3/pages/site-pages/{pid}/draft"))
        if v["draft"] and live["updatedAt"] != v["draft"]["updatedAt"]:
            drift += 1
            print(f"  CHANGED SINCE CAPTURE  {v['slug']:40} "
                  f"{v['draft']['updatedAt'][:19]} -> {str(live['updatedAt'])[:19]}")
    print(f"\n{len(man['pages'])} pages checked, {drift} changed since the capture")

def restore(d, only):
    man = json.load(open(f"{ROOT}{d}/manifest.json"))
    n = 0
    for pid, v in man["pages"].items():
        if only and v["slug"] not in only: continue
        rec = json.loads(gzip.open(f"{ROOT}{d}/{pid}.json.gz", "rt").read())
        draft = rec.get("draft")
        if not draft or "__error" in draft:
            print(f"  SKIP {v['slug']}: nothing captured"); continue
        call("PATCH", f"/cms/v3/pages/site-pages/{pid}/draft", draft)
        back = fingerprint(call("GET", f"/cms/v3/pages/site-pages/{pid}/draft"))
        ok = back["icons"] == v["draft"]["icons"]
        print(f"  {'OK  ' if ok else 'FAIL'} {v['slug']:44} icons {back['icons']}/{v['draft']['icons']}")
        if not ok: sys.exit(1)
        n += 1
    print(f"\nrestored {n} page(s)")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--verify":  verify(a[1])
    elif a and a[0] == "--restore": restore(a[1], set(a[2:]))
    else: capture()
