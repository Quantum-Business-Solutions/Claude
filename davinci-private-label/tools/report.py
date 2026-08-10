#!/usr/bin/env python3
"""Rebuild the page-by-page reproduction report from whatever the gates last said.

Reads every gate result on disk, keeps the newest per page, and writes the HTML.
Re-run it whenever an agent lands; it always reflects the latest measurement
rather than the one that happened to be quoted in conversation.

usage: report.py
"""
import json, os, glob, html, datetime

S   = os.path.dirname(os.path.abspath(__file__)) + '/'
OUT = '/home/user/Claude/pl-conversion-report.html'

CAT = ("aging herbal cognitive detox energy fitness heart-health immune-support "
       "joint-support mens-health multivitamin prenatal probiotics sleep "
       "weight-management womens-health").split()
DOSE = "capsules tablets soft-gels gummies powders liquids home".split()
# the 16 category pages were last measured by a desktop-only tool
CATRES = {"aging": 7, "multivitamin": 4, "energy": 2,
          "mens-health": 1, "prenatal": 1, "sleep": 1}


def newest():
    """The most recent gate result for every page that has one."""
    best = {}
    for f in (glob.glob(S + 'vis/gate_*.json') + glob.glob(S + 'vis/*/json/gate_*.json')
              + glob.glob(S + 'run26/*/gate_*.json')):
        n = os.path.basename(f)[5:-5]
        # skip anything that is not a page: post-promotion re-checks, and the
        # baselines agents save alongside a run (gate_home.BEFORE.json and the like)
        if n.endswith('_post') or '.' in n or n == 'selftest':
            continue
        if n not in best or os.path.getmtime(f) > os.path.getmtime(best[n]):
            best[n] = f
    out = {}
    for n, f in best.items():
        try:
            d = json.load(open(f))
        except Exception:
            continue
        out[n] = {w: (d.get(w) or {}).get('real') for w in ('1440px', '768px', '390px')}
        out[n]['words'] = d.get('words')
    return out


def rows():
    g = newest()
    r = []
    for n in CAT:
        r.append(dict(page=n, group="Category", state="converted",
                      d=CATRES.get(n, 0), t=None, m=None,
                      note="desktop only — tablet and phone not yet measured"))
    for n in DOSE:
        x = g.get(n)
        if not x:
            continue
        r.append(dict(page=n, group="Home + dosage", state="converted",
                      d=x['1440px'], t=x['768px'], m=x['390px'],
                      note=("reference render unusable — this number is not trustworthy"
                            if n == "home" else "")))
    for n, x in g.items():
        if n in CAT or n in DOSE:
            continue
        r.append(dict(page=n, group="Draft — not yet on the live record", state="draft",
                      d=x['1440px'], t=x['768px'], m=x['390px'], note=""))
    r.sort(key=lambda x: (x['group'] != "Category", -(x['d'] or 0), x['page']))
    return r


def sev(r):
    if r['note'].startswith('reference'):
        return 'unknown'
    vals = [v for v in (r['d'], r['t'], r['m']) if v is not None]
    if r['d'] is None:
        return 'unknown'
    if r['d'] == 0 and max(vals) == 0:
        return 'clean'
    if r['d'] == 0:
        return 'desktop'
    return 'near' if r['d'] <= 3 else 'work'


LABEL = {'clean': 'matches V1 at every width', 'desktop': 'matches at desktop',
         'near': 'close', 'work': 'differences remain', 'unknown': 'not measurable'}


def build():
    rs = rows()
    counts = {k: sum(1 for r in rs if sev(r) == k) for k in LABEL}
    body, group = [], None
    for r in rs:
        if r['group'] != group:
            group = r['group']
            body.append(f'<tr class="grp"><th colspan="6">{html.escape(group)}</th></tr>')
        s = sev(r)
        n = lambda v: '<span class="n">%s</span>' % ('—' if v is None else v)
        body.append(
            f'<tr class="s-{s}"><td class="pg"><span class="dot"></span>'
            f'{html.escape(r["page"])}</td><td class="st">{html.escape(r["state"])}</td>'
            f'<td class="num">{n(r["d"])}</td><td class="num">{n(r["t"])}</td>'
            f'<td class="num">{n(r["m"])}</td>'
            f'<td class="note">{html.escape(r["note"]) or LABEL[s]}</td></tr>')
    stamp = datetime.datetime.now().strftime('%d %B, %H:%M')
    tpl = open(S + 'report_template.html').read()
    for tok, val in (('@@ROWS@@', "".join(body)), ('@@STAMP@@', stamp),
                     ('@@TOTAL@@', len(rs)), ('@@CLEAN@@', counts['clean']),
                     ('@@DESKTOP@@', counts['desktop']),
                     ('@@DIFFER@@', counts['near'] + counts['work'])):
        tpl = tpl.replace(tok, str(val))
    open(OUT, 'w').write(tpl)
    print(f"{len(rs)} pages -> {OUT}")
    print(f"  clean {counts['clean']}   desktop-only {counts['desktop']}   "
          f"differ {counts['near'] + counts['work']}   unmeasurable {counts['unknown']}")


if __name__ == '__main__':
    build()
