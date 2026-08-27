#!/usr/bin/env python3
"""Render a card row before and after the icon plan, to see it rather than argue it.

A dry run proves the write tool changes nothing it shouldn't. It says nothing
about whether the page still looks right, and that is where the plan actually
falls down: a row of three cards where one keeps its icon and two lose theirs
comes out with its titles 74px apart, because the icon badge is 56px tall with
an 18px margin and the grid stretches the boxes to match but not the text.

The pages are drafts with no public URL, so the row is rebuilt from the module's
own stylesheet and the card data out of the draft rather than mirrored from the
rendered site. Writes ab.html; screenshot it at a viewport wide enough that the
grid does not collapse, or the wrapping is the harness's fault and not the plan's.

usage: TOKEN=... ab_render.py [slug ...]     default: the mixed rows worth seeing
"""
import base64, html, json, os, re, sys, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/iconplan")
from build import disposition                # the plan's own rules, not a copy

TOK = os.environ["TOKEN"]
H   = {"Authorization": "Bearer " + TOK}
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
IDX = S + "../reference/page_index.json"
SLUGS = sys.argv[1:] or ["pl-demo-certifications", "pl-demo-ads-contract-mfg",
                         "en/pl-demo-resources"]

def get(u):
    if u.startswith("/"): u = "https://api.hubapi.com" + u
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H)))

def source(path):
    """A design-manager file. The published tree is what the pages render from."""
    u = ("https://api.hubapi.com/cms/v3/source-code/published/content/"
         + urllib.parse.quote(path))
    return urllib.request.urlopen(urllib.request.Request(u, headers=H)).read().decode()

def svg_uri(src):
    try:
        return "data:image/svg+xml;base64," + base64.b64encode(urllib.request.urlopen(
            urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=30).read()).decode()
    except Exception:
        return ""

def card_rows(params):
    for c in params["cards"]:
        if not isinstance(c, dict): continue
        ic = c.get("icon")
        if not (isinstance(ic, dict) and "/icons/" in str(ic.get("src", ""))): continue
        yield c, {"eyebrow": (c.get("number_or_eyebrow") or "").strip(),
                  "title": re.sub(r"<[^>]+>", "", c.get("title") or "").strip(),
                  "stat": ""}

def render_card(c, row, mode, new):
    out, icon, _ = disposition(row)
    if mode == "before":            img = svg_uri(c["icon"]["src"])
    elif out == "SWAP" and icon in new: img = new[icon]
    else:                           img = ""   # STRIP/ART: the module drops the span
    s = f'<span class="pl-cg__icon"><img src="{img}" alt=""></span>' if img else ""
    if row["eyebrow"]: s += f'<span class="pl-cg__eyebrow">{html.escape(row["eyebrow"])}</span>'
    if c.get("title"):   s += f'<h3 class="pl-cg__title">{c["title"]}</h3>'
    if c.get("content"): s += f'<div class="pl-cg__content">{c["content"]}</div>'
    return f'<div class="pl-cg__card"><div class="pl-cg__body">{s}</div></div>', out

new = json.load(open(S + "iconplan/cache.json"))["new"]
css = source("Private Label/Modules/PL - Card Grid.module/module.css")
body = ""
for p in json.load(open(IDX))["production"]:
    if p["slug"] not in SLUGS: continue
    found = []
    def walk(o):
        if isinstance(o, dict):
            pr = o.get("params")
            if isinstance(pr, dict) and isinstance(pr.get("cards"), list) and any(True for _ in card_rows(pr)):
                found.append(pr)
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(get(f"/cms/v3/pages/site-pages/{p['id']}/draft").get("layoutSections"))
    for pr in found:
        pairs = list(card_rows(pr))
        halves = []
        for mode in ("before", "after"):
            cells = "".join(render_card(c, r, mode, new)[0] for c, r in pairs)
            halves.append('<div class="pl-cg pl-cg--light pl-cg--boxed pl-cg--align-left '
                'pl-cg--icon-badge pl-cg--eyebrow-text pl-cg--title-heading">'
                f'<div class="pl-cg__grid" style="grid-template-columns:repeat({len(pairs)},1fr);'
                f'gap:{pr.get("gap", 28)}px">{cells}</div></div>')
        outs = [render_card(c, r, "after", new)[1] for c, r in pairs]
        body += (f'<h2>{html.escape(p["slug"])} &middot; {len(pairs)} cards &middot; '
                 f'{" / ".join(outs)}</h2><div class="ab">'
                 f'<div><b>before</b>{halves[0]}</div><div><b>after</b>{halves[1]}</div></div>')

open(S + "ab.html", "w").write(f"""<!doctype html><meta charset=utf-8><style>
body{{background:#fff;font:14px/1.5 -apple-system,Segoe UI,sans-serif;margin:0;padding:28px;max-width:1500px}}
h2{{font:600 12px/1 ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#7a8a90;
   margin:34px 0 10px;padding-bottom:8px;border-bottom:1px solid #e4e9ea}}
.ab{{display:grid;grid-template-columns:1fr 1fr;gap:30px;align-items:start}}
.ab>div>b{{display:block;font:600 11px/1 ui-monospace,monospace;color:#9aa8ad;margin-bottom:8px}}
.pl-cg{{--pl-cg-card-bg:#fff;--pl-cg-card-border:#E4E9EA;--pl-cg-card-shadow:0 1px 3px rgba(1,38,56,.06);
  --pl-cg-badge-bg:#C9DBE2;--pl-cg-heading:#012638;--pl-cg-body:#4a5c63;--pl-cg-accent:#6BA644}}
{css}</style>{body}""")
print("wrote " + S + "ab.html")
