#!/usr/bin/env python3
"""Replace icon images on the Private Label pages, and nothing else.

The whole design of this script is the promise that only icons change. It reads
the live page, walks to each card's icon.src, rewrites that one string, and then
proves the claim: it diffs the page object it is about to send against the one it
read, and if a single difference is anything other than an icon src it refuses to
write. A page is snapshotted before the write and restored if the readback does
not match. Fails closed, every time.

usage: icon_swap.py --dry            show every change, write nothing
       icon_swap.py --apply [slug…]  write, verifying each page
"""
import json, os, sys, copy, time, urllib.request, urllib.error

TOK = os.environ["TOKEN"]
API = "https://api.hubapi.com"
H   = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
SNAP = S + "../snapshots/icon-swap/"

def call(method, path, body=None):
    r = urllib.request.Request(API + path, method=method, headers=H,
                               data=json.dumps(body).encode() if body else None)
    with urllib.request.urlopen(r) as f:
        raw = f.read()
    return json.loads(raw) if raw else {}

# ---------------------------------------------------------------- diffing
def flatten(o, path="", out=None):
    """Every leaf value in the page, addressed by its full path."""
    if out is None: out = {}
    if isinstance(o, dict):
        for k, v in o.items(): flatten(v, path + "/" + str(k), out)
    elif isinstance(o, list):
        for i, v in enumerate(o): flatten(v, path + f"[{i}]", out)
    else:
        out[path] = o
    return out

def differences(before, after):
    """Every leaf that changed, was added, or was removed."""
    A, B = flatten(before), flatten(after)
    diffs = []
    for k in set(A) | set(B):
        if A.get(k, "\0MISSING") != B.get(k, "\0MISSING"):
            diffs.append((k, A.get(k, "\0MISSING"), B.get(k, "\0MISSING")))
    return sorted(diffs)

def is_icon_path(p):
    """Only an icon's own src may move. Not its alt, not the card, not the copy."""
    return p.endswith("/icon/src")

# ---------------------------------------------------------------- the edit
def swap_icons(page, mapping, report):
    """Rewrite icon.src in place. mapping: {current filename: new url}."""
    def walk(o, path=""):
        if isinstance(o, dict):
            ic = o.get("icon")
            if isinstance(ic, dict) and isinstance(ic.get("src"), str):
                cur = ic["src"].rsplit("/", 1)[-1]
                if cur in mapping:
                    key = o.get("number_or_eyebrow") or o.get("title") or ""
                    report.append((key, cur, mapping[cur].rsplit("/", 1)[-1]))
                    ic["src"] = mapping[cur]
            for k, v in o.items(): walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, path + f"[{i}]")
    walk(page)
    return page

def guard(before, after, slug):
    """Refuse to write if anything but an icon src moved."""
    bad = [d for d in differences(before, after) if not is_icon_path(d[0])]
    if bad:
        print(f"  REFUSED on {slug}: {len(bad)} non-icon change(s) would be written")
        for p, a, b in bad[:6]:
            print(f"      {p}\n        was: {str(a)[:90]}\n        now: {str(b)[:90]}")
        return False
    return True

def run(mapping, ids, apply_):
    os.makedirs(SNAP, exist_ok=True)
    total = changed_pages = 0
    for pid, slug in ids:
        live = call("GET", f"/cms/v3/pages/site-pages/{pid}")
        after = copy.deepcopy(live)
        report = []
        swap_icons(after, mapping, report)
        if not report:
            continue
        if not guard(live, after, slug):
            sys.exit(1)
        icon_diffs = differences(live, after)
        total += len(icon_diffs); changed_pages += 1
        print(f"\n{slug}  —  {len(icon_diffs)} icon(s)")
        for key, old, new in report:
            print(f"     {(key or '(no label)')[:38]:40} {old} -> {new}")
        if not apply_:
            continue
        # Someone editing this page in HubSpot right now would have their work
        # overwritten by a blind PATCH, and no diff of mine would show it. Re-read
        # immediately before writing and skip the page if it moved underneath us.
        fresh = call("GET", f"/cms/v3/pages/site-pages/{pid}")
        if fresh.get("updatedAt") != live.get("updatedAt"):
            print(f"  SKIPPED {slug}: edited by someone else since this run started "
                  f"({live.get('updatedAt')} -> {fresh.get('updatedAt')})")
            continue
        json.dump(live, open(f"{SNAP}{pid}.BEFORE.json", "w"))
        call("PATCH", f"/cms/v3/pages/site-pages/{pid}", after)
        back = call("GET", f"/cms/v3/pages/site-pages/{pid}")
        # the readback must differ from the original in icon srcs ONLY
        bad = [d for d in differences(live, back) if not is_icon_path(d[0])
               and not d[0].endswith(("/updatedAt", "/updated"))]
        if bad:
            print(f"  READBACK MISMATCH on {slug} — restoring")
            call("PATCH", f"/cms/v3/pages/site-pages/{pid}", live)
            sys.exit(1)
        print(f"     verified: {len(icon_diffs)} changed, 0 other fields touched")
        time.sleep(0.3)
    print(f"\n{'WOULD CHANGE' if not apply_ else 'CHANGED'}: "
          f"{total} icon(s) on {changed_pages} page(s)")

if __name__ == "__main__":
    apply_ = "--apply" in sys.argv
    mapping = json.load(open(S + "../reference/icon_swap_map.json"))
    idx = json.load(open(S + "../reference/page_index.json"))
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    ids = [(p["id"], p["slug"]) for p in idx["production"]
           if not only or p["slug"] in only]
    run(mapping, ids, apply_)
