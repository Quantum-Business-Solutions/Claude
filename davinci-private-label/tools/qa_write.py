#!/usr/bin/env python3
"""QA one icon write: what changed on the page, and confirmation nothing else moved.

Two questions, answered at the cost each deserves.

The page you touched gets a full field-by-field diff against the snapshot --
every leaf compared, so a stray edit anywhere in it shows up by name.

Every other page in the portal gets its draft timestamp checked. That is the
whole question for them: a page whose draft has not been written cannot have
changed. 137 pages take about six seconds in parallel, which is cheap enough
that there is no reason to skip it and find out later.

Deliberately not the check the swap tool runs on itself. That one compares the
page it just wrote against the copy it held in memory, so it cannot see a page
it never opened -- and the first pass after the design-team swap looked only at
the 65 production pages, leaving the 63 V3 duplicates and the v1ref set
unexamined.

usage: TOKEN=... qa_write.py <snapshot-dir> --expect <slug> [slug ...] [--deep-all]
"""
import concurrent.futures as cf
import gzip, json, os, sys, urllib.request

T    = os.environ["TOKEN"]
S    = os.path.dirname(os.path.abspath(__file__)) + "/"
SNAP = sys.argv[1].rstrip("/")
DEEP_ALL = "--deep-all" in sys.argv
EXPECT = set(a for a in sys.argv[sys.argv.index("--expect") + 1:]
             if not a.startswith("-")) if "--expect" in sys.argv else set()

# HubSpot stamps these on any write; they are its bookkeeping, not page content.
STAMPS = {"authorName", "updatedById", "updatedAt", "updated"}

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

def snapshot(pid):
    f = f"{SNAP}/{pid}.json.gz"
    return json.loads(gzip.open(f).read().decode()) if os.path.exists(f) else None

idx   = json.load(open(S + "../reference/page_index.json"))
pages = [(b, p) for b, v in idx.items() if isinstance(v, list) for p in v]
deep  = [(b, p) for b, p in pages if DEEP_ALL or p["slug"] in EXPECT]
light = [(b, p) for b, p in pages if (b, p) not in deep]

print(f"snapshot : {SNAP}")
print(f"deep diff: {len(deep)} page(s)   timestamp check: {len(light)} page(s)\n")

# ---- the page(s) under test: every field ------------------------------------
moved = []
for bucket, p in deep:
    s = snapshot(p["id"])
    if s is None:
        moved.append((bucket, p["slug"], "draft", [], ["NOT IN SNAPSHOT"], [])); continue
    for kind in ("draft", "base"):
        new = get(f"/cms/v3/pages/site-pages/{p['id']}" + ("/draft" if kind == "draft" else ""))
        A, B = walk(s[kind]), walk(new)
        fields = sorted(k for k in set(A) | set(B) if A.get(k) != B.get(k))
        icons  = [k for k in fields if k.endswith("/icon/src")]
        other  = [k for k in fields if k not in icons and k.lstrip("/") not in STAMPS]
        if fields:
            moved.append((bucket, p["slug"], kind, icons, other,
                          [(k, A.get(k), B.get(k)) for k in icons]))
        if kind == "draft":
            print(f"  {p['slug']}  ({len(A)} fields)")
            for k, a, b in [(k, A.get(k), B.get(k)) for k in icons]:
                print(f"      {k.split('/params/')[-1]}")
                print(f"         - {str(a).rsplit('/', 1)[-1]}")
                print(f"         + {str(b).rsplit('/', 1)[-1]}")
            print(f"      icons changed: {len(icons)}   other fields changed: {len(other)}"
                  + (f"  {other}" if other else ""))

# ---- everything else: did its draft move? -----------------------------------
def check(arg):
    bucket, p = arg
    s = snapshot(p["id"])
    was = s["draft"]["updatedAt"] if s else None
    now = get(f"/cms/v3/pages/site-pages/{p['id']}/draft").get("updatedAt")
    return bucket, p["slug"], was, now

drifted, unbaselined = [], []
with cf.ThreadPoolExecutor(8) as ex:
    for bucket, slug, was, now in ex.map(check, light):
        if was is None: unbaselined.append((bucket, slug, now))
        elif was != now: drifted.append((bucket, slug, was, now))

print(f"\nother pages whose draft moved: {len(drifted)}")
for b, slug, was, now in drifted:
    print(f"   [{b}] {slug:34} {was[:19]} -> {now[:19]}")
if unbaselined:
    # The snapshot covers production only; for the rest, compare against the run.
    since = max((s["draft"]["updatedAt"] for _, p in deep
                 for s in [snapshot(p["id"])] if s), default="")
    late = [(b, s_, n) for b, s_, n in unbaselined if n and n >= since]
    print(f"not in the snapshot ({len(unbaselined)} pages, non-production):")
    print(f"   last written before this run, so untouched : {len(unbaselined)-len(late)}")
    print(f"   written since                              : {len(late)}")
    for b, s_, n in late: print(f"      [{b}] {s_:32} {n[:19]}")
    drifted += [(b, s_, "?", n) for b, s_, n in late]

bad = [m for m in moved if m[4] or (EXPECT and m[1] not in EXPECT)] + drifted
print("\n" + "=" * 62)
print(f"VERDICT: {'PASS' if not bad else 'REVIEW'}")
print(f"  non-icon fields changed on the page(s) under test : {sum(len(m[4]) for m in moved)}")
print(f"  any other page whose draft moved                  : {len(drifted)}")
