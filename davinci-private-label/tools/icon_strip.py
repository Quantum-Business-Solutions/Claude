#!/usr/bin/env python3
"""Remove icons from named rows, and change nothing else.

The swap tool can only replace an icon; it has no way to take one away. That gap
is why a third of the site could not be touched, and why swapping alone would
have left old navy icons sitting beside new ink ones.

Removal here means blanking icon.src and nothing more. The card module renders
its badge behind {% if item.icon.src %}, so an empty src drops the whole 56px
tile and its 18px margin -- the card closes up rather than leaving a grey hole.
The icon object itself is kept so the field still exists for anyone editing the
page in HubSpot afterwards.

Rows are named by the labels they contain, taken from reference/icon_inventory.json,
because a row's position in layoutSections moves when anyone adds a module above it.
Every label in a target must be found or the page is skipped: a partial match means
the row is not the row we meant.

usage: TOKEN=... icon_strip.py <targets.json>            show every change, write nothing
       TOKEN=... icon_strip.py <targets.json> --apply    write, verifying each page
       TOKEN=... icon_strip.py --selftest                prove the guard refuses bad writes
"""
import copy, json, os, sys, time, urllib.request

TOK = os.environ.get("TOKEN", "")
API = "https://api.hubapi.com"
H   = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
STAMPS = {"authorName", "updatedById", "updatedAt", "updated"}

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

def label_of(card):
    import re
    return ((card.get("number_or_eyebrow") or "").strip()
            or re.sub(r"<[^>]+>", "", card.get("title") or "").strip()
            or re.sub(r"<[^>]+>", "", card.get("stat_label") or "").strip())

def strip_rows(page, wanted, report):
    """Blank icon.src on the named cards of any card array matching a target.

    A target is (labels that identify the row, labels to clear). The second is
    separate because a row can mix icons that go with icons that stay -- the ads
    pages keep "U.S. manufacturing" and lose the two beside it -- and clearing
    the whole array there would take an icon we mean to replace."""
    hit = set()
    def walk(o):
        if isinstance(o, dict):
            for key in ("cards", "stats"):
                arr = o.get(key)
                if isinstance(arr, list) and arr:
                    labels = [label_of(c) for c in arr if isinstance(c, dict)]
                    for i, (want, clear) in enumerate(wanted):
                        if i in hit: continue
                        if all(w in labels for w in want):
                            hit.add(i)
                            for c in arr:
                                if not isinstance(c, dict): continue
                                lab = label_of(c)
                                if clear is not None and lab not in clear: continue
                                ic = c.get("icon")
                                if isinstance(ic, dict) and ic.get("src"):
                                    report.append((lab, ic["src"].rsplit("/", 1)[-1]))
                                    ic["src"] = ""
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(page)
    return hit

def run(targets, apply_):
    total = pages = 0
    for t in targets:
        slug = t["slug"]
        wanted = [(set(r["match"]), set(r["clear"]) if r.get("clear") is not None else None)
                  if isinstance(r, dict) else (set(r), None) for r in t["rows"]]
        live = call("GET", f"/cms/v3/pages/site-pages/{t['id']}/draft")
        after = copy.deepcopy(live); rep = []
        hit = strip_rows(after, wanted, rep)
        if len(hit) != len(wanted):
            print(f"  SKIPPED {slug}: matched {len(hit)} of {len(wanted)} target row(s) "
                  f"-- the page has changed, re-read the inventory")
            continue
        bad = [d for d in differences(live, after) if not d[0].endswith("/icon/src")]
        if bad:
            print(f"  REFUSED on {slug}: {len(bad)} non-icon change(s)")
            for k, a, b in bad[:5]: print(f"      {k}")
            sys.exit(1)
        n = len(rep); total += n; pages += 1
        print(f"\n{slug}  —  {n} icon(s) removed")
        for lab, was in rep: print(f"       {lab[:44]:46} {was}  ->  (none)")
        if not apply_: continue
        fresh = call("GET", f"/cms/v3/pages/site-pages/{t['id']}/draft")
        if fresh.get("updatedAt") != live.get("updatedAt"):
            print(f"  SKIPPED {slug}: edited by someone else since this run started"); continue
        call("PATCH", f"/cms/v3/pages/site-pages/{t['id']}/draft", after)
        back = call("GET", f"/cms/v3/pages/site-pages/{t['id']}/draft")
        stray = [d for d in differences(live, back)
                 if not d[0].endswith("/icon/src") and d[0].lstrip("/") not in STAMPS]
        if stray:
            print(f"  READBACK MISMATCH on {slug} — restore from the snapshot and stop")
            for k, a, b in stray[:5]: print(f"      {k}")
            sys.exit(1)
        print(f"     verified: {n} removed, 0 other fields touched")
    print(f"\n{'REMOVED' if apply_ else 'WOULD REMOVE'}: {total} icon(s) on {pages} page(s)")

def selftest():
    """The guard has to refuse anything that is not an icon src going blank."""
    base = {"layoutSections": {"m": {"params": {"cards": [
        {"title": "Guide A", "content": "<p>keep me</p>", "icon": {"src": "x/a.svg", "alt": ""}},
        {"title": "Guide B", "content": "<p>keep me too</p>", "icon": {"src": "x/b.svg", "alt": ""}}]}}}}
    cases = [
      ("icon only (should pass)", lambda p: strip_rows(p, [({"Guide A","Guide B"}, None)], [])),
      ("edits body copy",  lambda p: (strip_rows(p, [({"Guide A","Guide B"}, None)], []),
          p["layoutSections"]["m"]["params"]["cards"][0].__setitem__("content", "<p>changed</p>"))),
      ("edits a title",    lambda p: (strip_rows(p, [({"Guide A","Guide B"}, None)], []),
          p["layoutSections"]["m"]["params"]["cards"][1].__setitem__("title", "Guide C"))),
      ("edits alt text",   lambda p: (strip_rows(p, [({"Guide A","Guide B"}, None)], []),
          p["layoutSections"]["m"]["params"]["cards"][0]["icon"].__setitem__("alt", "new"))),
      ("drops a card",     lambda p: (strip_rows(p, [({"Guide A","Guide B"}, None)], []),
          p["layoutSections"]["m"]["params"]["cards"].pop())),
    ]
    ok = True
    for name, mutate in cases:
        after = copy.deepcopy(base); mutate(after)
        bad = [d for d in differences(base, after) if not d[0].endswith("/icon/src")]
        expect_refuse = name != "icon only (should pass)"
        got_refuse = bool(bad)
        mark = "ok " if got_refuse == expect_refuse else "FAIL"
        if mark == "FAIL": ok = False
        print(f"  {mark}  {name:24} -> {'REFUSED' if got_refuse else 'passed'}"
              + (f"  ({bad[0][0]})" if bad else ""))
    print("\nself-test:", "all guards behave" if ok else "A GUARD IS WRONG")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    targets = json.load(open(sys.argv[1]))
    run(targets, "--apply" in sys.argv)
