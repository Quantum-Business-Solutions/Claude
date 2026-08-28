#!/usr/bin/env python3
"""Every icon slot on the site, page by page, with its state and what holds it.

Written to be read by people who are not going to run any of this: each row is
a card on a page, named by the label the page shows, with the icon it is headed
for and -- when it is not moving yet -- the one reason it is not.

usage: TOKEN=... inventory.py > inventory.json
"""
import json, os, re, sys, collections, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/iconplan")
from build import disposition

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))

def rows_of(page):
    """Icon slots grouped by the card array they render in -- the row a reader sees."""
    groups = collections.defaultdict(list)
    def walk(o, path, g):
        if isinstance(o, dict):
            ic = o.get("icon"); src = str(ic.get("src", "")) if isinstance(ic, dict) else ""
            if "/icons/" in src or "/Praxera/" in src:
                groups[g].append({
                    "eyebrow": (o.get("number_or_eyebrow") or "").strip(),
                    "title":   re.sub(r"<[^>]+>", "", o.get("title") or "").strip(),
                    "stat":    re.sub(r"<[^>]+>", "", o.get("stat_label") or "").strip(),
                    "file":    src.rsplit("/", 1)[-1],
                    "done":    "/Praxera/" in src})
            for k, v in o.items():
                if k != "icon": walk(v, path + "/" + k, g)
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, f"{path}[{i}]", path)
    walk(page.get("layoutSections"), "", "")
    return groups

def hold_reason(outs, slots):
    """One reason a row is not moving, or None. Order matters: report the reason
    that would have to be settled first."""
    kinds = {o[0] for o in outs}
    if not any(o[0] == "SWAP" and not s["done"] for o, s in zip(outs, slots)):
        return "nothing to swap -- these slots are for stripping or need artwork"
    by = collections.defaultdict(set)
    for o, s in zip(outs, slots):
        if o[0] == "SWAP": by[o[1]].add((s["eyebrow"] or s["title"]).upper())
    worst = max((len(v) for v in by.values()), default=1)
    if "SWAP" in kinds and len(kinds) > 1:
        return "row mixes icons that stay with icons that go -- needs the strip ruling"
    if worst > 2:
        return f"{worst} different labels land on one icon -- needs Sarah's ruling"
    if worst == 2:
        return "two labels share an icon -- Sarah's consolidation, likely fine"
    return None

idx = json.load(open(S + "../reference/page_index.json"))
out = []
for p in idx["production"]:
    if re.match(r"(-temporary-slug-)?blog/", p["slug"]): continue
    d = get(f"/cms/v3/pages/site-pages/{p['id']}/draft")
    groups = rows_of(d)
    if not groups: continue
    prows = []
    for g, slots in groups.items():
        outs = [disposition(s) for s in slots]
        prows.append({
            "cards": len(slots),
            "hold": hold_reason(outs, slots),
            "slots": [{"label": s["eyebrow"] or s["title"] or s["stat"] or "(no label)",
                       "kind": "tag" if s["eyebrow"] else ("stat" if s["stat"] else "claim"),
                       "action": o[0], "icon": o[1], "stretch": bool(o[2]),
                       "done": s["done"], "now": s["file"]}
                      for s, o in zip(slots, outs)]})
    out.append({"slug": p["slug"], "id": p["id"], "name": p.get("name"),
                "editor": d.get("authorName"), "edited": d.get("updatedAt", "")[:10],
                "rows": prows})
json.dump(out, sys.stdout, indent=1)
