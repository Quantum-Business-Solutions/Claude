#!/usr/bin/env python3
"""Ask what the icon plan does to each ROW of cards, not to each icon.

The plan decides one slot at a time, so it can leave a four-card row with two
icons and two holes -- which reads as a bug to anyone looking at the page even
though every individual decision was right. This walks the same draft content
the swap tool writes to and groups the slots the way the page renders them: by
the array of cards they sit in. A group whose slots do not all get the same
outcome is where the page breaks.

usage: TOKEN=... group_check.py
"""
import json, os, re, sys, collections, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/iconplan")
from build import disposition, match          # the plan's own rules, not a copy

TOK = os.environ["TOKEN"]
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
IDX = S + "../reference/page_index.json"

def get(u):
    if u.startswith("/"): u = "https://api.hubapi.com" + u
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={
        "Authorization": "Bearer " + TOK})))

def slots_by_group(page, slug):
    """Every icon slot, tagged with the list it belongs to.

    Reads the draft: /cms/v3/pages/site-pages/{id} returns the base record, which
    on this project sat five days behind the content the site was rendering."""
    out = collections.defaultdict(list)
    def walk(o, path, group):
        if isinstance(o, dict):
            src = None; ic = o.get("icon")
            if isinstance(ic, dict) and "/icons/" in str(ic.get("src", "")): src = ic["src"]
            elif isinstance(o.get("src"), str) and "/icons/" in o["src"]: src = o["src"]
            if src:
                t = next((o[k] for k in ("title","label","heading","name","headline")
                          if isinstance(o.get(k), str) and o[k].strip()), "")
                out[group].append({"slug": slug, "icon": src.rsplit("/",1)[-1],
                    "title": re.sub(r"<[^>]+>", "", t).strip(),
                    "eyebrow": (o.get("number_or_eyebrow") or o.get("eyebrow") or "").strip(),
                    "stat": re.sub(r"<[^>]+>", "", o.get("stat_label") or "").strip()})
            for k, v in o.items():
                if k == "icon": continue
                walk(v, path + "/" + k, group)
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, f"{path}[{i}]", path)
    walk(page.get("layoutSections") or page.get("widgets") or page, "", "")
    return out

idx = json.load(open(IDX))
split, wiped, clean, allg = [], [], 0, 0
for p in idx["production"]:
    pg = get(f"/cms/v3/pages/site-pages/{p['id']}/draft")
    for group, rows in slots_by_group(pg, p["slug"]).items():
        if not rows: continue
        allg += 1
        outs = [disposition(r) for r in rows]
        kinds = {o[0] for o in outs}
        label = re.sub(r"^.*widgets/", "", group)[:58]
        item = (p["slug"], label, len(rows),
                [(r["eyebrow"] or r["title"] or r["stat"] or "(blank)", o[0], o[1])
                 for r, o in zip(rows, outs)])
        if kinds == {"STRIP"} and len(rows) > 1: wiped.append(item)
        elif len(kinds) > 1:                     split.append(item)
        else:                                    clean += 1

def show(title, items):
    print(f"\n=== {title}: {len(items)} group(s) ===")
    for slug, label, n, cells in sorted(items, key=lambda x: -x[2]):
        print(f"\n  {slug}  ({n} cards)  {label}")
        for k, out, ic in cells:
            print(f"      {out:5} {ic or '':24} {k[:52]}")

show("MIXED - some cards keep an icon, some lose it", split)
show("WIPED - every card in the row loses its icon", wiped)
print(f"\nclean groups (one outcome throughout): {clean} of {allg}")
