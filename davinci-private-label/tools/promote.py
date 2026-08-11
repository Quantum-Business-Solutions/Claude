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
    # Home and the 16 category pages each serialised a literal Python None as their
    # FAQ subhead. Verified per page: exactly one occurrence, in the FAQ widget,
    # as <p ...>None</p>. Dropping it is deliberate.
    '216189433405': {'None'},
    '216179449410': {'None'},
    '216188836111': {'None'},
    '216188836114': {'None'},
    '216189432990': {'None'},
    '216189432992': {'None'},
    '216189433007': {'None'},
    '216189433092': {'None'},
    '216189433094': {'None'},
    '216189433236': {'None'},
    '216189433251': {'None'},
    '216189433267': {'None'},
    '216189433270': {'None'},
    '216189433371': {'None'},
    '216189433373': {'None'},
    '216189433375': {'None'},
    '216189433390': {'None'},
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
    cut = h.find('global_footer')
    if cut > 0:
        h = h[:h.rfind('<', 0, cut)]      # back up to the tag start, or we truncate mid-tag
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
    # A global block's body is empty by design, and reconstructing its text from
    # the June backup was only ever a guess: the two files are aligned by list
    # position, and design-services gained a global after that backup was taken,
    # so it counted its heritage twice and lost its FDA disclaimer -- 106 words
    # that were never missing. Globals render from one shared definition, so they
    # are identical on both sides by construction; leaving them out of the
    # comparison removes the guess and loses no coverage. The rendered-page diff
    # still sees them.
    parts = []
    for w in pre.get('widgetContainers', {}).get('main_content', {}).get('widgets', []):
        b = w.get('body') or {}
        parts.append(b.get('html') or b.get('content') or '')
    joined = re.sub(r'(?s)<!--.*?-->', ' ', ' '.join(parts))
    return re.sub(r'\s+', ' ', _html.unescape(re.sub(r'<[^>]+>', ' ', joined))).strip()


def none_artifacts(pre):
    """Count the stray literal 'None' tokens V1 rendered, and only those.

    A token is an artifact when it stands alone between two tags. Counting every
    occurrence would let real prose disappear: two sentences on quality-standards
    begin with the word."""
    h = ' '.join((w.get('body', {}).get('html') or w.get('body', {}).get('value') or '')
                 for w in (pre.get('widgetContainers') or {})
                     .get('main_content', {}).get('widgets', []))
    n = 0
    for m in re.finditer(r'(?<![A-Za-z])None(?![A-Za-z])', h):
        if re.search(r'>\s*$', h[max(0, m.start() - 60):m.start()]) \
           and re.search(r'^\s*<', h[m.end():m.end() + 40]):
            n += 1
    return n


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
        nmod = 0
        for row in sec.get('rows', []):
            if list(row.keys()) != ['0']:
                f.append(f"section row keys are {list(row.keys())!r}, expected ['0']")
            for col in row.values():
                if col.get('type') != 'cell':
                    f.append(f"section cell type is {col.get('type')!r}, expected 'cell'")
                if col.get('params', {}).get('css_class') != 'dnd-column':
                    f.append("a section cell is missing params.css_class=dnd-column")
                if col.get('w') != 0 or col.get('x') != 0:
                    f.append(f"section cell has non-zero geometry w={col.get('w')} x={col.get('x')}")
                for inner in col.get('rows', []):
                    if list(inner.keys()) != ['0']:
                        f.append(f"module row keys are {list(inner.keys())!r}, expected ['0']")
                    nmod += len(inner)
        if nmod != len(sec.get('rows', [])):
            f.append(f"module count ({nmod}) != row count ({len(sec.get('rows', []))})")
    mods = modules_of(page)
    if not mods:
        f.append("no modules found in layoutSections")
    for m in mods:
        if m.get('type') != 'module' or not m.get('params', {}).get('module_id'):
            f.append(f"module cell {m.get('name')!r} is malformed")
        if m.get('w') != 0 or m.get('x') != 0:
            f.append(f"module {m.get('name')!r} has non-zero geometry w={m.get('w')} x={m.get('x')}")

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
    # currentlyPublished is not a field this API returns, so testing it was
    # vacuously true. state / currentState / published are the real ones, and
    # archivedAt is checked so an archived page cannot slip through as a draft.
    if (page.get('state') != 'DRAFT' or page.get('published')
            or page.get('currentState') not in (None, 'DRAFT')
            or (page.get('archivedAt') or '1970')[:4] != '1970'):
        f.append(f"page is not a safe draft (state={page.get('state')}, "
                 f"currentState={page.get('currentState')}, published={page.get('published')})")

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
    # V1's FAQ widget serialised a literal None on most pages. That is an
    # artifact and may go -- but quality-standards genuinely starts two
    # sentences with the word, so the page is allowed to lose exactly as many
    # as V1 rendered standalone between tags, and not one more.
    budget = none_artifacts(pre)
    bad = []
    for w in lost:
        t = w.strip()
        if t in allowed:
            continue
        if t == 'None' and budget > 0:
            budget -= 1
            continue
        bad.append(w)
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
    pre_widgets = (pre.get('widgetContainers') or {}).get('main_content', {}).get('widgets', [])
    if not pre_widgets or (pre.get('layoutSections') or {}):
        print(f"  ABORT {v1id}: {os.path.basename(pre_path)} is not a pre-promotion snapshot "
              f"({len(pre_widgets)} widgets, {len(pre.get('layoutSections') or {})} layoutSections). "
              f"Restoring from it would destroy the page. Delete it and re-snapshot from a known-good source.")
        return 2
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
            back = get_page(v1id)
            n = len((back.get('widgetContainers') or {}).get('main_content', {}).get('widgets', []))
            if n == len(pre_widgets) and not (back.get('layoutSections') or {}):
                print(f"  restored and verified ({n} widgets back).")
            else:
                print(f"  RESTORE DID NOT VERIFY -- {n} widgets, "
                      f"{len(back.get('layoutSections') or {})} layoutSections. Page needs manual repair.")
                return 3
        return 1

    json.dump(page, open(S + f"{v1id}.POST.json", 'w'), indent=1)
    print(f"  PASS {v1id}  {pre['name']}")
    print(f"       slug {page['slug']}  |  {len(modules_of(page))} modules  |  {page['state']}")
    print(f"       {preview_url(v1id)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
