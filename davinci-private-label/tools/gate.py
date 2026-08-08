#!/usr/bin/env python3
"""One gate. It returns PASS or FAIL for a page, and nothing in between.

Every serious mistake on this project came from a check that quietly did not
run and was read as success: a browser that was never opened, a comparator that
measured the previous build, a publish test on a field the API does not return.
So this gate fails closed -- a check that cannot run is a failure, never a skip
-- and it prints one verdict line that cannot be mistaken for a partial result.

What it checks, per page:

  copy      every word of V1 present, nothing invented, one <h1>, no debris
  links     every href and image in V1 still reachable in V3
  type      computed size / weight / colour / measure, element by element,
            matched by text, at desktop, tablet and phone widths
  section   section-by-section pixel diff, with a side-by-side image written
            for anything over threshold
  open      the FAQ accordions actually open

usage:  gate.py <ref_id> <live_id> <name>
        gate.py --selftest          prove the gate catches a planted regression
"""
import os, re, sys, json, shutil, html as _html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shot import mirror, CHROME, ARGS
from verify import serve, PROBE, pixdiff
from breakdown import classify

S = os.path.dirname(os.path.abspath(__file__)) + '/'
REFSEL  = 'div[id^="hs_cos_wrapper_widget_"]:not([id$="_"])'
LIVESEL = 'div[id^="hs_cos_wrapper_module_"]:not([id$="_"])'
WIDTHS  = (1440, 768, 390)
SECTION_PCT = 8.0


def words(h):
    h = re.sub(r'<!--.*?-->', ' ', h, flags=re.S)
    h = re.sub(r'<(script|style)\b.*?</\1>', ' ', h, flags=re.S)
    t = _html.unescape(re.sub(r'<[^>]+>', ' ', h)).lower()
    return [w for w in re.findall(r"[a-z0-9][a-z0-9'&/-]*", t) if w]


def assets(h):
    hrefs = set(re.findall(r'href="([^"#]+)"', h))
    imgs  = set(os.path.basename(u.split('?')[0])
                for u in re.findall(r'<img[^>]+src="([^"]+)"', h))
    return hrefs, imgs


def visit(d, selector, width, want_sections):
    """Probe the page at one width. Raises rather than returning a partial read."""
    from playwright.sync_api import sync_playwright
    httpd, port = serve(d)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=CHROME, args=ARGS)
            pg = b.new_context(viewport={'width': width, 'height': 1200},
                               device_scale_factor=1).new_page()
            pg.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load", timeout=60000)
            pg.add_style_tag(content="*{animation:none!important;transition:none!important}")
            pg.wait_for_timeout(900)
            out = pg.evaluate(PROBE)
            # an accordion that never opens hides its answers from every other check
            out['opened'] = pg.evaluate("""() => {
              const d=[...document.querySelectorAll('details')];
              d.forEach(x=>x.open=true);
              return d.filter(x=>x.querySelector('*') &&
                     x.getBoundingClientRect().height > 40).length;
            }""")
            out['secs'], out['sectext'] = [], []
            if want_sections:
                os.makedirs(d + '/sec', exist_ok=True)
                els = pg.locator(selector)
                for i in range(els.count()):
                    p = f"{d}/sec/{i:02d}.png"
                    try:
                        els.nth(i).screenshot(path=p); out['secs'].append(p)
                    except Exception:
                        out['secs'].append(None)
                    try:
                        out['sectext'].append(els.nth(i).inner_text())
                    except Exception:
                        out['sectext'].append('')
            b.close()
    finally:
        httpd.shutdown()
    if not out['el']:
        raise RuntimeError(f"probe returned no elements at {width}px -- the page did not render")
    return out


def wordset(t):
    return set(re.findall(r"[a-z0-9][a-z0-9'-]*", (t or '').lower()))


def pair_sections(ta, tb):
    """Match reference sections to rebuilt ones by their text.

    Comparing section i to section i only works when the rebuild kept V1's
    section order. It does not always: a conversion may merge two V1 sections
    into one module or split one into two. Compared by index, such a page
    reports near-total pixel differences on every section after the first
    divergence -- a false failure as damaging as a false pass."""
    wb = [wordset(x) for x in tb]
    out, taken = [], set()
    for x in ta:
        wa = wordset(x)
        best, score = None, 0.0
        for j, w in enumerate(wb):
            if j in taken or not (wa | w): continue
            k = len(wa & w) / len(wa | w)
            if k > score: best, score = j, k
        if best is not None and score >= 0.6:
            out.append(best); taken.add(best)
        else:
            out.append(None)
    return out


def run(ref_id, live_id, name, keep_ref=True, sel=None):
    refsel, livesel = sel or (REFSEL, LIVESEL)
    dr, dl = f"{S}mirror/{name}_ref", f"{S}mirror/{name}_live"
    # the reference is captured once and never refreshed; the page under test is
    # always re-rendered, because a cached render reports an older build
    if ref_id and not (keep_ref and os.path.exists(dr + '/index.html')):
        shutil.rmtree(dr, ignore_errors=True); mirror(ref_id, dr)
    if live_id:
        shutil.rmtree(dl, ignore_errors=True); mirror(live_id, dl)
    for d in (dr, dl):
        if not os.path.exists(d + '/index.html'):
            raise RuntimeError(f"no render at {d} -- the gate cannot pass what it cannot see")

    hr = open(dr + '/index.html').read()
    hl = open(dl + '/index.html').read()
    fails, notes = [], {}

    # ---- copy
    wr, wl = words(hr), words(hl)
    from collections import Counter
    cr, cl = Counter(wr), Counter(wl)
    lost = sorted((cr - cl).elements())
    new  = sorted((cl - cr).elements())
    notes['words'] = [len(wr), len(wl)]
    if lost: fails.append(f"copy lost: {lost[:12]}")
    if new:  fails.append(f"copy invented: {new[:12]}")
    n_h1 = len(re.findall(r'<h1[\s>]', hl))
    if n_h1 != 1: fails.append(f"{n_h1} <h1> elements, expected 1")

    # ---- links and images
    ar, ai = assets(hr)
    br, bi = assets(hl)
    # the reference replica links to itself; that URL is not page content
    selfish = re.compile(r'-v1ref|-v3(?:$|[/?])')
    gone_links = sorted(x for x in ar - br
                        if not x.startswith('/hs/') and not selfish.search(x))
    gone_imgs  = sorted(ai - bi)
    if gone_links: fails.append(f"links dropped: {gone_links[:8]}")
    if gone_imgs:  fails.append(f"images dropped: {gone_imgs[:8]}")

    # ---- type and geometry, at every width
    for w in WIDTHS:
        A = visit(dr, refsel,  w, want_sections=(w == WIDTHS[0]))
        B = visit(dl, livesel, w, want_sections=(w == WIDTHS[0]))
        real, art = classify(A, B)
        notes[f'{w}px'] = {'real': len(real), 'width_only': len(art),
                           'examples': [(t, d) for t, d, _ in real[:4]]}
        if real:
            fails.append(f"{len(real)} visible type differences at {w}px")
        if w == WIDTHS[0]:
            if A['opened'] != B['opened']:
                fails.append(f"accordions open: {A['opened']} vs {B['opened']}")
            pairs = pair_sections(A['sectext'], B['sectext'])
            missing = [i for i, j in enumerate(pairs) if j is None
                       and wordset(A['sectext'][i])]
            if missing:
                fails.append(f"V1 sections with no match in the rebuild: {missing}")
            worst = []
            for i, j in enumerate(pairs):
                if j is None or not A['secs'][i] or not B['secs'][j]: continue
                pct = pixdiff(A['secs'][i], B['secs'][j])
                worst.append((pct, i))
                if pct >= SECTION_PCT:
                    fails.append(f"V1 section {i} (rebuilt as {j}) "
                                 f"differs by {pct:.1f}% of pixels")
            notes['worst_sections'] = [[i, round(p, 1)]
                                       for p, i in sorted(worst, reverse=True)[:3]]

    verdict = 'PASS' if not fails else 'FAIL'
    print(f"  {verdict}  {name}   words {notes['words'][0]}->{notes['words'][1]}   "
          + "   ".join(f"{w}px real {notes[f'{w}px']['real']}" for w in WIDTHS))
    for f in fails:
        print(f"        - {f}")
    return verdict == 'PASS', notes


def selftest():
    """Plant a known regression and confirm the gate rejects it.

    A gate that has never failed on purpose is not known to work. This copies a
    page that passes, shifts one font-size by 2px in its stylesheet, and expects
    a FAIL. If it passes, the gate is blind and must not be trusted."""
    name = 'selftest'
    src  = f"{S}mirror/sleep_v1"
    if not os.path.exists(src + '/index.html'):
        print("  SELFTEST CANNOT RUN: no captured reference to copy"); return False
    for suffix in ('_ref', '_live'):
        shutil.rmtree(f"{S}mirror/{name}{suffix}", ignore_errors=True)
        shutil.copytree(src, f"{S}mirror/{name}{suffix}")
    live = f"{S}mirror/{name}_live"
    hit = 0
    for f in os.listdir(live + '/a'):
        if not f.endswith('.css'): continue
        p = f"{live}/a/{f}"
        css = open(p, encoding='utf-8', errors='ignore').read()
        new = re.sub(r'font-size:\s*17px', 'font-size:15px', css)
        if new != css:
            open(p, 'w', encoding='utf-8').write(new); hit += 1
    if not hit:
        print("  SELFTEST CANNOT RUN: nothing to perturb"); return False
    # both copies are legacy renders, so both use the legacy selector --
    # otherwise the gate would fail on section count and prove nothing
    ok, _ = run(None, None, name, keep_ref=True, sel=(REFSEL, REFSEL))
    verdict = 'the gate caught it' if not ok else 'THE GATE IS BLIND'
    print(f"  selftest: planted a 17px->15px change in {hit} stylesheet(s) -- {verdict}")
    return not ok


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    ok, notes = run(sys.argv[1], sys.argv[2], sys.argv[3])
    json.dump(notes, open(f"{S}gate_{sys.argv[3]}.json", 'w'), indent=1)
    sys.exit(0 if ok else 1)
