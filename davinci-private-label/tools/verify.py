#!/usr/bin/env python3
"""One browser visit per page: section pixel-diff, text-matched geometry, and tile boxes.

Compares each promoted page against the V1 render captured *before* promotion —
those captures are the only remaining record of what V1 looked like.

usage: verify.py [page-name ...]
"""
import os, sys, json, functools, threading, http.server, socketserver
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shot import mirror, CHROME, ARGS
from PIL import Image, ImageChops

S = os.path.dirname(os.path.abspath(__file__)) + '/'
V1SEL = 'div[id^="hs_cos_wrapper_widget_"]:not([id$="_"])'
V3SEL = 'div[id^="hs_cos_wrapper_module_"]:not([id$="_"])'


def serve(d):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=d)
    class Q(socketserver.TCPServer):
        allow_reuse_address = True
        def log_message(self, *a): pass
    s = Q(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, s.server_address[1]


PROBE = """() => {
  const el=[];
  document.querySelectorAll('h1,h2,h3,p,span,a').forEach(e=>{
    const r=e.getBoundingClientRect(), c=getComputedStyle(e);
    const t=(e.innerText||'').replace(/\\s+/g,' ').trim();
    if(!t||r.width<2) return;
    // own: does this element paint any text itself, or is every glyph inside it
    // drawn by a child that sets its own colour and size? A wrapper with no text
    // node of its own can differ in computed colour and look identical.
    const own=[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
    el.push({t:t.slice(0,70),w:Math.round(r.width),h:Math.round(r.height),
             fs:c.fontSize,fw:c.fontWeight,color:c.color,own:own});
  });
  const tiles=[...document.querySelectorAll('img')].map(i=>{
    const r=i.getBoundingClientRect(),c=getComputedStyle(i);
    return {w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.x),fit:c.objectFit};
  }).filter(o=>o.w>80&&o.w<420&&o.h>80);
  return {el,tiles,height:document.body.scrollHeight};
}"""


def visit(d, selector):
    from playwright.sync_api import sync_playwright
    httpd, port = serve(d)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=CHROME, args=ARGS)
            pg = b.new_context(viewport={'width': 1440, 'height': 1200},
                               device_scale_factor=1).new_page()
            pg.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load", timeout=60000)
            pg.add_style_tag(content="*{animation:none!important;transition:none!important}")
            pg.wait_for_timeout(900)
            out = pg.evaluate(PROBE)
            os.makedirs(d + '/sec', exist_ok=True)
            secs, els = [], pg.locator(selector)
            for i in range(els.count()):
                p = f"{d}/sec/{i:02d}.png"
                try:
                    els.nth(i).screenshot(path=p); secs.append(p)
                except Exception:
                    secs.append(None)
            out['secs'] = secs
            b.close()
    finally:
        httpd.shutdown()
    return out


def pixdiff(p1, p2, thresh=14):
    a, b = Image.open(p1).convert('RGB'), Image.open(p2).convert('RGB')
    W, H = min(a.width, b.width), min(a.height, b.height)
    d = ImageChops.difference(a.crop((0, 0, W, H)), b.crop((0, 0, W, H))).convert('L')
    d = d.point(lambda v: 255 if v > thresh else 0)
    return 100.0 * sum(d.histogram()[255:]) / (W * H)


if __name__ == '__main__':
    pm  = json.load(open(S + 'pagemap.json'))
    ids = json.load(open(S + '../fam16/v3_ids.json'))
    only = sys.argv[1:] or list(pm)
    report = {}
    for name in only:
        v1id = pm[name]; v3id = ids[v1id]
        d1, d3 = f"{S}mirror/{name}_v1", f"{S}mirror/{name}_v3"
        if not os.path.exists(d1 + '/index.html'): mirror(v1id, d1)
        if not os.path.exists(d3 + '/index.html'): mirror(v3id, d3)
        A, B = visit(d1, V1SEL), visit(d3, V3SEL)

        n = min(len(A['secs']), len(B['secs']))
        pcts = [(i, pixdiff(A['secs'][i], B['secs'][i])) for i in range(n)
                if A['secs'][i] and B['secs'][i]]
        worst = sorted(pcts, key=lambda x: -x[1])[:2]

        MA = {e['t']: e for e in A['el']}; MB = {e['t']: e for e in B['el']}
        gd = [t for t in MA if t in MB and (
              MA[t]['fs'] != MB[t]['fs'] or MA[t]['fw'] != MB[t]['fw']
              or MA[t]['color'] != MB[t]['color'] or abs(MA[t]['w'] - MB[t]['w']) > 6)]

        ta, tb = A['tiles'], B['tiles']
        tdiff = [(i, ta[i], tb[i]) for i in range(min(len(ta), len(tb)))
                 if abs(ta[i]['w'] - tb[i]['w']) > 3 or abs(ta[i]['h'] - tb[i]['h']) > 3]

        report[name] = {'sections': [len(A['secs']), len(B['secs'])],
                        'worst': [[i, round(p, 1)] for i, p in worst],
                        'geom_diffs': len(gd), 'geom_examples': gd[:3],
                        'tiles': [len(ta), len(tb)],
                        'tile_size_diffs': len(tdiff),
                        'tile_example': tdiff[:1],
                        'height': [A['height'], B['height']]}
        r = report[name]
        print(f"  {name:20} sec {r['sections'][0]}/{r['sections'][1]}  worst {r['worst']}  "
              f"geom {r['geom_diffs']}  tiles {r['tiles'][0]}/{r['tiles'][1]} "
              f"szdiff {len(tdiff)}  h {r['height'][0]}->{r['height'][1]}")
        if gd: print(f"       geom: {gd[:2]}")
        if tdiff: print(f"       tile: {tdiff[0][1]} -> {tdiff[0][2]}")
    json.dump(report, open(f"{S}verify_report.json", 'w'), indent=1)
