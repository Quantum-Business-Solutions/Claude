#!/usr/bin/env python3
"""Order the remaining pages into waves by what could go wrong on each.

Not by size. A page is safe to run when every slot on it gets a confident swap,
no row is left half-iconed, and no row ends up showing the same glyph twice --
the three failures the earlier QA found. Pages missing one of those need a fix
first, and the fix is named here rather than discovered on the page.

usage: TOKEN=... wave_plan.py
"""
import json, os, re, sys, collections, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/iconplan")
from build import disposition

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"
TODAY = "2026-08-28"

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))

def survey(pid):
    d = get(f"/cms/v3/pages/site-pages/{pid}/draft")
    groups = collections.defaultdict(list)
    def walk(o, path, g):
        if isinstance(o, dict):
            ic = o.get("icon")
            if isinstance(ic, dict) and "/icons/" in str(ic.get("src", "")):
                groups[g].append({"eyebrow": (o.get("number_or_eyebrow") or "").strip(),
                    "title": re.sub(r"<[^>]+>", "", o.get("title") or "").strip(),
                    "stat":  re.sub(r"<[^>]+>", "", o.get("stat_label") or "").strip()})
            for k, v in o.items():
                if k != "icon": walk(v, path + "/" + k, g)
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, f"{path}[{i}]", path)
    walk(d.get("layoutSections"), "", "")
    return d, groups

idx = json.load(open(S + "../reference/page_index.json"))
rows = []
for p in idx["production"]:
    if re.match(r"(-temporary-slug-)?blog/", p["slug"]): continue
    d, groups = survey(p["id"])
    slots = [r for g in groups.values() for r in g]
    if not slots: continue
    c = collections.Counter(); icons = []; judged = 0; mixed = 0; dup_rows = 0
    for g in groups.values():
        outs = [disposition(r) for r in g]
        if len({o[0] for o in outs}) > 1: mixed += 1
        # Two cards tagged PRENATAL in one row should get the same icon twice;
        # that is the content repeating, not the rules colliding. Only count a
        # row where DIFFERENT labels land on one glyph.
        by = collections.defaultdict(set)
        for o, r in zip(outs, g):
            if o[0] == "SWAP": by[o[1]].add((r["eyebrow"] or r["title"]).upper())
        if any(len(v) > 1 for v in by.values()): dup_rows += 1
    for r in slots:
        o, ic, j = disposition(r); c[o] += 1
        if o == "SWAP": icons.append(ic); judged += j
    hot = d.get("updatedAt", "")[:10] >= TODAY
    rows.append(dict(slug=p["slug"], n=len(slots), swap=c["SWAP"], strip=c["STRIP"],
                     art=c["ART"], logo=c["LOGO"], judged=judged, mixed=mixed,
                     dup=dup_rows, hot=hot, who=d.get("authorName"),
                     when=d.get("updatedAt", "")[:10]))

def wave(r):
    if r["swap"] == 0:                                    return 5, "nothing to swap -- needs the strip tool"
    if r["mixed"]:                                        return 4, "half-iconed row"
    if r["dup"]:                                          return 3, "repeats an icon in one row"
    if r["strip"] or r["art"] or r["logo"]:               return 2, "needs the strip tool"
    if r["judged"]:                                       return 1, "stretch matches to eyeball"
    return 0, "clean"

for r in rows: r["w"], r["why"] = wave(r)
NAMES = {0: "WAVE 1  run now -- every slot a confident swap",
         1: "WAVE 2  run after eyeballing the marked matches",
         2: "WAVE 3  blocked on the strip tool",
         3: "WAVE 4  blocked on duplicate-icon rows",
         4: "WAVE 5  blocked on half-iconed rows",
         5: "WAVE 6  strip-only pages"}
for w in range(6):
    grp = [r for r in rows if r["w"] == w]
    if not grp: continue
    print(f"\n{NAMES[w]}   {len(grp)} page(s), {sum(r['swap'] for r in grp)} swaps, "
          f"{sum(r['strip'] for r in grp)} strips")
    for r in sorted(grp, key=lambda x: -x["swap"]):
        flag = "  ** being edited today **" if r["hot"] else ""
        print(f"   {r['slug']:34} {r['n']:>2} slots  swap {r['swap']:>2} strip {r['strip']:>2} "
              f"art {r['art']:>2}  {r['why']:<32} {r['who']} {r['when']}{flag}")
t = collections.Counter()
for r in rows:
    t["swap"] += r["swap"]; t["strip"] += r["strip"]; t["art"] += r["art"]; t["logo"] += r["logo"]
print(f"\nremaining across all pages: {dict(t)}")
