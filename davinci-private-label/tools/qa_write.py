#!/usr/bin/env python3
"""Independent QA on an icon write: prove one page moved and nothing else did.

Deliberately not the check the swap tool runs on itself. That one compares the
page it just wrote against the copy it held in memory, so it cannot see a page
it never opened -- and the first pass after the design-team swap only looked at
the 65 production pages, leaving the 63 V3 duplicates and the v1ref set
unverified. This reads every page in the portal index, both records, against a
snapshot, and compares canonical JSON rather than reusing the swap tool's own
flattening.

usage: TOKEN=... qa_write.py <snapshot-dir> [--expect slug]
"""
import json, os, sys, gzip, urllib.request, collections

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"
SNAP = sys.argv[1].rstrip("/")
EXPECT = sys.argv[sys.argv.index("--expect") + 1] if "--expect" in sys.argv else None

# HubSpot stamps these on any write; they are the API's bookkeeping, not content.
STAMPS = {"authorName", "updatedById", "updatedAt", "updated"}

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))

def canon(o, drop_stamps=True):
    """Canonical JSON with the audit stamps optionally lifted out."""
    if drop_stamps and isinstance(o, dict):
        o = {k: v for k, v in o.items() if k not in STAMPS}
    return json.dumps(o, sort_keys=True, separators=(",", ":"))

def walk(o, p=""):
    d = {}
    if isinstance(o, dict):
        for k, v in o.items(): d.update(walk(v, f"{p}/{k}"))
    elif isinstance(o, list):
        for i, v in enumerate(o): d.update(walk(v, f"{p}[{i}]"))
    else: d[p] = o
    return d

idx = json.load(open(S + "../reference/page_index.json"))
buckets = [(b, v) for b, v in idx.items() if isinstance(v, list)]
missing, moved, clean = [], [], 0
for bucket, pages in buckets:
    for p in pages:
        f = f"{SNAP}/{p['id']}.json.gz"
        if not os.path.exists(f): missing.append((bucket, p["slug"])); continue
        s = json.loads(gzip.open(f).read().decode())
        for kind in ("draft", "base"):
            new = get(f"/cms/v3/pages/site-pages/{p['id']}" + ("/draft" if kind == "draft" else ""))
            if canon(s[kind]) == canon(new): clean += 1; continue
            A, B = walk(s[kind]), walk(new)
            fields = sorted(k for k in set(A) | set(B) if A.get(k) != B.get(k))
            icons = [k for k in fields if k.endswith("/icon/src")]
            other = [k for k in fields if k not in icons
                     and k.lstrip("/") not in STAMPS]
            moved.append((bucket, p["slug"], kind, icons, other,
                          [(k, A.get(k), B.get(k)) for k in icons]))

print(f"snapshot   : {SNAP}")
print(f"pages read : {sum(len(v) for _, v in buckets)} across {len(buckets)} buckets "
      f"({', '.join(f'{b} {len(v)}' for b, v in buckets)})")
print(f"records identical (ignoring audit stamps): {clean}")
if missing:
    print(f"\nNOT IN SNAPSHOT -- unverifiable: {len(missing)}")
    for b, s_ in missing[:10]: print(f"   {b:11} {s_}")

print(f"\nrecords that moved: {len(moved)}")
for bucket, slug, kind, icons, other, detail in moved:
    flag = "" if slug == EXPECT else "   <-- NOT THE PAGE UNDER TEST"
    print(f"\n  [{bucket}] {slug}  ({kind}){flag}")
    print(f"      icon srcs changed: {len(icons)}")
    for k, a, b in detail:
        print(f"        {k.split('/params/')[-1]}")
        print(f"           - {str(a).rsplit('/',1)[-1]}")
        print(f"           + {str(b).rsplit('/',1)[-1]}")
    print(f"      other fields changed: {len(other)}" + (f"  {other}" if other else ""))

bad = [m for m in moved if m[4] or (EXPECT and m[1] != EXPECT)]
print("\n" + "="*64)
print(f"VERDICT: {'PASS' if not bad and not missing else 'REVIEW'}")
print(f"  pages other than the one under test that moved : "
      f"{len({m[1] for m in moved if EXPECT and m[1] != EXPECT})}")
print(f"  non-icon content fields changed anywhere       : {sum(len(m[4]) for m in moved)}")
print(f"  pages that could not be verified               : {len(missing)}")
