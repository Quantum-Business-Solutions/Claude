#!/usr/bin/env python3
"""Promote a finished V3 body onto its original V1 page record, in place.

Every check below is a gate. If any gate fails the page is restored from its
pre-promotion snapshot and the script exits non-zero, so a bad page can never
be left behind and the run stops rather than repeating the fault.

usage: promote.py <V3_ID> <V1_ID> [--verify-only]
"""
import json, os, re, sys, time, urllib.request, urllib.error, difflib, html as _html

S   = os.path.dirname(os.path.abspath(__file__)) + '/'
TOK = os.environ['TOKEN']
API = "https://api.hubapi.com"
HJ  = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
TOMBSTONE = 1786126404643
ALLOWED_DELETIONS  = {'+', '−', ''}   # FAQ open/close markers, drawn in CSS

# Per-page exceptions: text present in V1 that is deliberately NOT reproduced,
# because it was a defect in V1 rather than content. Keep these specific and few.
PAGE_EXCEPTIONS = {
    # Home: V1 widget 19 serialised a literal Python None as the FAQ subhead,
    # rendering "None" under "Frequently asked questions". Verified: 1 occurrence.
    '216189433405': {'None'},
}


def _req(url, data=None, method='GET', headers=None, raw=False, tries=4):
    for n in range(tries):
        try:
            r = urllib.request.Request(url, data=data, headers=headers or HJ, method=method)
            with urllib.request.urlopen(r) as f:
                b = f.read()
            return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and n < tries - 1:
                time.sleep(2 ** n); continue
            raise
        except urllib.error.URLError:
            if n < tries - 1:
                time.sleep(2 ** n); continue
            raise


def get_page(pid):   return _req(f"{API}/cms/v3/pages/site-pages/{pid}")
def patch(pid, body):
    return _req(f"{API}/cms/v3/pages/site-pages/{pid}",
                data=json.dumps(body, separators=(',', ':')).encode(), method='PATCH')
def preview_url(pid):
    p = _req(f"{API}/content/api/v2/pages/{pid}")
    return f"https://info.davincilabs.com/{p['slug']}?hs_preview={p['preview_key']}-{pid}"
def render(pid):
    return _req(preview_url(pid), headers={"User-Agent": "Mozilla/5.0"}, raw=True).decode('utf-8', 'replace')


def modules_of(page):
    out = []
    for sec in (page.get('layoutSections') or {}).values():
        for row in sec.get('rows', []):
            for col in row.values():
                for rr in col.get('rows', []):
                    out.extend(rr.values())
    return out


def body_text(html):
    i = html.find('container-fluid')
    if i > 0:
        j = html.find('>', i)
        h = html[j + 1:] if j > 0 else html[i:]
    else:
        h = html
    h = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', h)
    h = re.sub(r'(?s)<!--.*?-->', ' ', h)
    return re.sub(r'\s+', ' ', _html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()


def mask(t):
    t = re.sub(r'\b\d{12,14}\b', 'NUM', t)
    t = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', 'UUID', t)
    return re.sub(r'\b2\d{11}\b', 'ID', t)


def v1_source_text(pre, v1id):
    june_path = S + f'../backup_v1/{v1id}.json'
    jw = []
    if os.path.exists(june_path):
        jw = (json.load(open(june_path)).get('widgetContainers', {})
              .get('main_content', {}).get('widgets', []))
    parts = []
    for i, w in enumerate(pre.get('widgetContainers', {}).get('main_content', {}).get('widgets', [])):
        b = w.get('body') or {}
        t = b.get('html') or b.get('content') or ''
        if not t.strip() and i < len(jw):        # global block -> take June's copy
            jb = jw[i].get('body') or {}
            t = jb.get('html') or jb.get('content') or ''
        parts.append(t)
    joined = re.sub(r'(?s)<!--.*?-->', ' ', ' '.join(parts))
    return re.sub(r'\s+', ' ', _html.unescape(re.sub(r'<[^>]+>', ' ', joined))).strip()


def check(page, v3, pre, html, v3_html, pre_text, v1id=''):
    """Return list of failure strings. Empty list == every gate passed."""
    f = []
    ls  = page.get('layoutSections') or {}
    wc  = (page.get('widgetContainers') or {}).get('main_content', {})
    if json.dumps(ls, sort_keys=True) != json.dumps(v3['layoutSections'], sort_keys=True):
        f.append("layoutSections does not match the V3 source byte-for-byte")
    if page.get('templatePath') != v3['templatePath']:
        f.append(f"templatePath is {page.get('templatePath')!r}, expected {v3['templatePath']!r}")
    for sec in ls.values():
        nr, nm = len(sec.get('rows', [])), len(sec.get('rowMetaData', []))
        if nr != nm:
            f.append(f"rows ({nr}) != rowMetaData ({nm})")
        for md in sec.get('rowMetaData', []):
            if md != {"cssClass": "dnd-section"}:
                f.append(f"unexpected rowMetaData entry {md!r}")
        for row in sec.get('rows', []):
            for col in row.values():
                if col.get('params', {}).get('css_class') != 'dnd-column':
                    f.append("a section cell is missing params.css_class=dnd-column")
    mods = modules_of(page)
    if not mods:
        f.append("no modules found in layoutSections")
    for m in mods:
        if m.get('type') != 'module' or not m.get('params', {}).get('module_id'):
            f.append(f"module cell {m.get('name')!r} is malformed")

    # the combination that previously froze the HubSpot editor
    if wc.get('widgets'):
        f.append("widgetContainers still populated -> editor would see two structures")
    if not wc.get('deleted_at'):
        f.append("widgetContainers is missing its deleted_at tombstone")
    if page.get('widgets'):
        f.append("top-level widgets is not empty")

    # identity must survive untouched: this is the point of promoting in place
    for k in ('id', 'name', 'slug', 'htmlTitle', 'metaDescription', 'domain', 'language'):
        if page.get(k) != pre.get(k):
            f.append(f"{k} changed: {pre.get(k)!r} -> {page.get(k)!r}")
    if page.get('state') != 'DRAFT' or page.get('currentlyPublished'):
        f.append(f"page is not a safe draft (state={page.get('state')}, published={page.get('currentlyPublished')})")

    # render
    if 'hubl error' in html.lower() or 'jinjava' in html.lower():
        f.append("rendered page contains a HubL/Jinjava error")
    nsec = len(re.findall(r'dnd-section', html))
    want = sum(len(s.get('rows', [])) for s in ls.values())
    if nsec != want:
        f.append(f"rendered dnd-section count {nsec} != {want} rows")

    # rendered text must equal the V3's, ignoring HubSpot's own ids/timestamps
    if mask(body_text(html)) != mask(body_text(v3_html)):
        f.append("rendered text differs from the V3 source page")

    # and nothing from the original V1 may have gone missing or been invented
    now = body_text(html).split()
    sm = difflib.SequenceMatcher(None, pre_text.split(), now)
    lost, added = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ('delete', 'replace'):
            lost += pre_text.split()[i1:i2]
        if op in ('insert', 'replace'):
            added += now[j1:j2]
    allowed = ALLOWED_DELETIONS | PAGE_EXCEPTIONS.get(v1id, set())
    bad = [w for w in lost if w.strip() not in allowed]
    if bad:
        f.append(f"{len(bad)} word(s) from V1 missing: {bad[:12]}")
    return f


def main():
    v3id, v1id = sys.argv[1], sys.argv[2]
    verify_only = '--verify-only' in sys.argv
    pre_path = S + f"{v1id}.PRE.json"

    v3 = get_page(v3id)
    if not (v3.get('layoutSections') or {}):
        print(f"SKIP {v1id}: source {v3id} has no layoutSections (not a dnd rebuild)"); return 0

    if not os.path.exists(pre_path):
        pre = get_page(v1id)
        json.dump(pre, open(pre_path, 'w'), indent=1)
        print(f"  snapshot -> {os.path.basename(pre_path)}")
    pre = json.load(open(pre_path))
    pre_text = v1_source_text(pre, v1id)
    json.dump(v3, open(S + f"{v3id}.V3.json", 'w'), indent=1)

    if not verify_only:
        patch(v1id, {"templatePath": v3['templatePath'], "layoutSections": v3['layoutSections']})
        patch(v1id, {"widgetContainers": {"main_content": {"widgets": [], "deleted_at": TOMBSTONE}}})
        time.sleep(2)

    page, html, v3_html = get_page(v1id), render(v1id), render(v3id)
    fails = check(page, v3, pre, html, v3_html, pre_text, v1id)

    if fails:
        print(f"  FAIL {v1id} ({pre.get('name')})")
        for x in fails:
            print("    -", x)
        if not verify_only:
            print("  restoring from snapshot ...")
            patch(v1id, {"templatePath": pre['templatePath'],
                         "layoutSections": pre.get('layoutSections') or {},
                         "widgetContainers": pre['widgetContainers']})
            print("  restored.")
        return 1

    json.dump(page, open(S + f"{v1id}.POST.json", 'w'), indent=1)
    print(f"  PASS {v1id}  {pre['name']}")
    print(f"       slug {page['slug']}  |  {len(modules_of(page))} modules  |  {page['state']}")
    print(f"       {preview_url(v1id)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
