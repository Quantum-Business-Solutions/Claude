#!/usr/bin/env python3
"""Rebuild a browsable copy of a page as it looked before promotion.

The 16 category pages were photographed in a browser while they were still
rich-text. The 7 dosage pages and Home were not -- they were promoted before the
visual check existed, and a promoted record no longer holds the original markup.

What does still exist is the pre-promotion JSON snapshot. Posting those exact
widgets to a new draft on the legacy template reproduces V1's rendering path
faithfully: same template, same theme CSS, same widget HTML. The replica is a
separate draft at <slug>-v1ref and is never published; it is a reference render,
not a restore, and it touches nothing on the live record.

Widgets alone are not the page. A page also carries its own CSS -- attached
stylesheets and whatever the author put in the head and footer HTML boxes -- and
that CSS is what turns V1's markup into V1's layout. Home is the proof: its
head HTML defines pl-steps-grid, pl-design-grid, pl-cat-grid, pl-forms-grid,
pl-guide-grid and four form rules. A replica built without it stacked every one
of those grids into a single column, and the comparator then blamed the live
page for laying them out the way V1 did. So the replica copies every
page-level style field the snapshot holds, and refuses to report OK unless the
readback proves they stuck -- a reference that silently lost the page's own CSS
is worse than no reference, because its differences look like real regressions.

usage: v1ref.py <V1_ID> [<V1_ID> ...]
"""
import os, sys, json, urllib.request, urllib.parse

TOK = os.environ['TOKEN']
API = "https://api.hubapi.com"
S   = os.path.dirname(os.path.abspath(__file__)) + '/'
PRE = S + '../promote/'

# Everything that decides how the page is styled but lives on the page record
# rather than in a widget. Only the keys the snapshot actually holds are sent:
# the API omits a field it has never been given, and posting an explicit null
# back for one of those would be a change, not a copy.
STYLE_FIELDS = ('attachedStylesheets', 'headHtml', 'footerHtml',
                'includeDefaultCustomCss', 'enableDomainStylesheets',
                'enableLayoutStylesheets', 'cssText', 'css')


def page_style(snap):
    return {k: snap[k] for k in STYLE_FIELDS if k in snap}


def req(url, method='GET', data=None):
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + TOK, "Content-Type": "application/json"})
    with urllib.request.urlopen(r) as f:
        return json.loads(f.read() or b'{}')


def replica(v1id):
    snap = json.load(open(f"{PRE}{v1id}.PRE.json"))
    widgets = (snap.get('widgetContainers') or {}).get('main_content', {}).get('widgets', [])
    if not widgets or (snap.get('layoutSections') or {}):
        raise RuntimeError(f"{v1id}: snapshot is not pre-promotion "
                           f"({len(widgets)} widgets) -- refusing to build a reference from it")

    slug = snap['slug'] + '-v1ref'
    found = req(f"{API}/cms/v3/pages/site-pages?slug={urllib.parse.quote(slug)}")
    style = page_style(snap)
    body = {"widgetContainers": {"main_content": {"widgets": widgets}},
            "templatePath": snap['templatePath'], "layoutSections": {}, **style}
    if found.get('total'):
        rid = found['results'][0]['id']
        req(f"{API}/cms/v3/pages/site-pages/{rid}", 'PATCH',
            json.dumps(body, separators=(',', ':')).encode())
    else:
        rid = req(f"{API}/cms/v3/pages/site-pages", 'POST', json.dumps({
            "name": snap['name'] + " — V1 reference render", "slug": slug,
            "domain": snap.get('domain') or "info.davincilabs.com", "state": "DRAFT",
            "htmlTitle": snap.get('htmlTitle'), "metaDescription": snap.get('metaDescription'),
            **body}, separators=(',', ':')).encode())['id']

    back = req(f"{API}/cms/v3/pages/site-pages/{rid}")
    n = len((back.get('widgetContainers') or {}).get('main_content', {}).get('widgets', []))
    ok = n == len(widgets) and not (back.get('layoutSections') or {}) and back['state'] == 'DRAFT'
    # a style field that did not stick is a silent failure: the replica renders,
    # it just renders something V1 never looked like
    dropped = [k for k, v in style.items() if back.get(k) != v]
    if dropped:
        ok = False
    inline = len(style.get('headHtml') or '') + len(style.get('footerHtml') or '')
    sheets = len(style.get('attachedStylesheets') or [])
    print(f"  {'OK  ' if ok else 'FAIL'} {v1id} -> {rid}  {slug}  {n}/{len(widgets)} widgets  "
          f"{back['state']}  page css: {inline}b head/footer + {sheets} attached sheet(s)"
          + (f"  DROPPED {dropped}" if dropped else ""))
    return rid if ok else None


if __name__ == '__main__':
    out = {}
    for v1id in sys.argv[1:]:
        out[v1id] = replica(v1id)
    path = S + 'v1ref_ids.json'
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(out)
    json.dump(old, open(path, 'w'), indent=1)
