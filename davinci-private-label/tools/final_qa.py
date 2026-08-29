#!/usr/bin/env python3
"""Quality-check the finished icon work against every way it has gone wrong here.

Each check exists because that failure actually happened on this project:
a row left half-new, a filename mapped instead of a slot, an icon nobody could
see because the detector only matched one path, a colour left over from the old
set, a glyph repeated across a row, a URL that 404s.

usage: TOKEN=... final_qa.py
"""
import io, json, os, re, sys, time, collections, urllib.request, urllib.error
import concurrent.futures as cf
from PIL import Image

T = os.environ["TOKEN"]
S = os.path.dirname(os.path.abspath(__file__)) + "/"
sys.path.insert(0, S + "iconplan")
from build import disposition

def get(u, tr=5):
    if u.startswith("/"): u = "https://api.hubapi.com" + u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(
            u, headers={"Authorization": "Bearer " + T})))
        except Exception:
            if i == tr - 1: raise
            time.sleep(2 * (i + 1))

idx = json.load(open(S + "../reference/page_index.json"))
pages = [p for p in idx["production"]]

def rows_of(pid):
    d = get(f"/cms/v3/pages/site-pages/{pid}/draft")
    g = collections.defaultdict(list)
    def walk(o, path, grp):
        if isinstance(o, dict):
            ic = o.get("icon")
            if isinstance(ic, dict) and "src" in ic:
                src = str(ic.get("src") or "")
                lab = ((o.get("number_or_eyebrow") or "").strip()
                       or re.sub(r"<[^>]+>", "", o.get("title") or "").strip()
                       or re.sub(r"<[^>]+>", "", o.get("stat_label") or "").strip())
                g[grp].append({"label": lab, "src": src})
            for k, v in o.items():
                if k != "icon": walk(v, path + "/" + k, grp)
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, f"{path}[{i}]", path)
    walk(d.get("layoutSections"), "", "")
    return d, g

with cf.ThreadPoolExecutor(5) as ex:
    data = list(ex.map(lambda p: (p["slug"], *rows_of(p["id"])), pages))

old_refs, halfrows, mixedcut, dups, allsrc = [], [], [], [], collections.Counter()
for slug, d, groups in data:
    for grp, cards in groups.items():
        withicon = [c for c in cards if c["src"]]
        if not withicon: continue
        for c in withicon: allsrc[c["src"]] += 1
        # 1. any survivor of the old set
        for c in withicon:
            if "/icons/" in c["src"]: old_refs.append((slug, c["label"], c["src"].rsplit("/",1)[-1]))
        # 2. a row where some cards kept an icon and others lost one
        if 0 < len(withicon) < len(cards):
            halfrows.append((slug, len(cards), len(withicon),
                             [c["label"][:20] for c in cards if not c["src"]]))
        # 3. a row mixing the old set with the new
        cuts = {"new" if "/Praxera/" in c["src"] else "old" for c in withicon}
        if len(cuts) > 1:
            mixedcut.append((slug, len(withicon),
                             [c["label"][:20] for c in withicon if "/Praxera/" not in c["src"]]))
        # 4. one glyph on more than two different labels in a row
        by = collections.defaultdict(set)
        for c in withicon: by[c["src"].rsplit("/",1)[-1]].add(c["label"].upper())
        for f, labs in by.items():
            if len(labs) > 2: dups.append((slug, f, sorted(labs)))

def show(title, rows, fmt, ok="none"):
    print(f"\n{'PASS' if not rows else 'CHECK'}  {title}: {len(rows) or ok}")
    for r in rows[:8]: print("        " + fmt(r))

show("old-set icons still on a page", old_refs, lambda r: f"{r[0]:30} {r[1][:26]:28} {r[2]}")
show("rows where only some cards kept an icon", halfrows,
     lambda r: f"{r[0]:30} {r[2]} of {r[1]} kept   missing: {r[3]}")
show("rows mixing the old cut with the new", mixedcut,
     lambda r: f"{r[0]:30} {r[1]} icons, old: {r[2]}")
show("one glyph on 3+ different labels in a row", dups,
     lambda r: f"{r[0]:30} {r[1]:34} {r[2]}")

# 5. does every referenced file actually resolve, and is it the right colour?
print(f"\n--- {len(allsrc)} distinct icon files referenced; fetching each ---")
def probe(u):
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=25).read()
    except Exception as e: return u, None, None, str(e)[:40]
    try:
        if b"<svg" in b[:300]:
            c = collections.Counter(re.findall(rb"#[0-9A-Fa-f]{6}", b))
            return u, len(b), (c.most_common(1)[0][0].decode().upper() if c else "svg"), None
        im = Image.open(io.BytesIO(b)).convert("RGBA")
        px = [p for p in im.getdata() if p[3] > 150]
        c = collections.Counter((p[0],p[1],p[2]) for p in px).most_common(1)[0][0]
        return u, len(b), "#%02X%02X%02X" % c, None
    except Exception as e: return u, len(b), None, str(e)[:40]
with cf.ThreadPoolExecutor(8) as ex: probes = list(ex.map(probe, allsrc))
broken = [p for p in probes if p[1] is None]
colours = collections.Counter(p[2] for p in probes if p[2])
print(f"{'PASS' if not broken else 'CHECK'}  files that fail to load: {len(broken) or 'none'}")
for p in broken[:6]: print("        ", p[0][-60:], p[3])
print(f"        colours in use: {dict(colours)}")

tot = sum(allsrc.values())
print(f"\nslots carrying an icon: {tot}   distinct files: {len(allsrc)}")
