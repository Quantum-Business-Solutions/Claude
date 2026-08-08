#!/usr/bin/env python3
"""Give an already-converted page V1's type scale, without touching its content.

The dosage pages and Home were converted before the browser diff existed, so
their modules carry the module defaults -- a type scale tuned to the category
family. Their copy, links, images and structure are correct; what is wrong is
sizes, weights and two text colours.

This reads each size back out of the pre-promotion snapshot and patches only
those keys. Content keys are compared before and after and the page is restored
if any of them moved, so a restyle can never rewrite copy.

usage: restyle.py <V1_ID> [--dry]
"""
import os, re, sys, json, copy, html as _html, urllib.request

TOK = os.environ['TOKEN']
API = "https://api.hubapi.com"
S   = os.path.dirname(os.path.abspath(__file__)) + '/'

HERO, RT, CG, SH, CS, TG, CTA, FAQ, STAT, HERITAGE = (
    218939846507, 218940115784, 218940115759, 218940115771, 218939846527,
    218940115743, 218940115731, 218940115739, 218940115735, 218954101913)

# every key this tool is allowed to write; anything else on a module is content
STYLE_KEYS = {
    'headline_size', 'subhead_size', 'eyebrow_size', 'button_size', 'body_size',
    'title_size', 'content_size', 'question_size', 'answer_size', 'value_size',
    'label_size', 'label_weight', 'body_color', 'subhead_color',
    'content_weight', 'content_color', 'subhead_width',
    'heading_size', 'number_size',
}


def req(url, method='GET', data=None):
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + TOK, "Content-Type": "application/json"})
    with urllib.request.urlopen(r) as f:
        return json.loads(f.read() or b'{}')


# ---------------------------------------------------------------- extractors

def tags(h, name):
    """(attributes, inner) for every <name> in document order."""
    return re.findall(r'<%s(?=[\s>])([^>]*)>(.*?)</%s>' % (name, name), h, re.S)


def px(attrs, dflt=None):
    m = re.search(r'font-size:\s*(\d+)px', attrs)
    return int(m.group(1)) if m else dflt


def weight(attrs, dflt=None):
    m = re.search(r'font-weight:\s*(\w+)', attrs)
    if not m: return dflt
    return {'normal': '400', 'bold': '700'}.get(m.group(1), m.group(1))


def colour(attrs, dflt=None):
    m = re.search(r'(?<!background-)color:\s*(#[0-9a-fA-F]{3,6}|white|black)', attrs)
    if not m: return dflt
    c = {'white': '#FFFFFF', 'black': '#000000'}.get(m.group(1), m.group(1))
    if len(c) == 4:                      # #abc -> #aabbcc
        c = '#' + ''.join(ch * 2 for ch in c[1:])
    return c.upper()


def heading_px(h, dflt):
    """First real heading. An eyebrow is sometimes marked up as a heading, and it
    always carries letter-spacing -- that is what separates the two."""
    for attrs, _ in re.findall(r'<(?:h1|h2)(?=[\s>])([^>]*)>(.*?)</(?:h1|h2)>', h, re.S):
        if 'letter-spacing' in attrs: continue
        return px(attrs, dflt)
    return dflt


def paras(h):
    """Paragraphs that are body copy: not eyebrows (letter-spacing) and not empty."""
    out = []
    for attrs, inner in tags(h, 'p'):
        if 'letter-spacing' in attrs: continue
        if not re.sub(r'<[^>]+>', '', inner).strip(): continue
        out.append((attrs, inner))
    return out


def eyebrow_px(h, dflt):
    for attrs, _ in tags(h, 'p'):
        if 'letter-spacing' in attrs:
            return px(attrs, dflt)
    return dflt


def subhead(h, dflt_size, dflt_colour):
    """The section subhead: the first body paragraph that sits above any card,
    which V1 marks by capping its measure."""
    for attrs, _ in paras(h):
        if re.search(r'max-width:\s*\d+px', attrs) or 'text-align: center' in attrs:
            return px(attrs, dflt_size), colour(attrs, dflt_colour)
    p = paras(h)
    return (px(p[0][0], dflt_size), colour(p[0][0], dflt_colour)) if p else (dflt_size, dflt_colour)


def card_type(h, dflt_title, dflt_body, dflt_colour):
    """Card title and body, read from the markup after the first <h3>.

    The numbered-step layout has no <h3> at all -- eyebrow, title and body are
    three stacked paragraphs -- so that shape is read separately. Without this
    those cards fall back to the default grey and V1's navy is lost."""
    m = re.search(r'<h3(?=[\s>])([^>]*)>', h)
    if not m:
        for blk in re.findall(r'<div style="text-align: left;">(.*?)</div>', h, re.S):
            ps = [(a, i) for a, i in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', blk, re.S)
                  if re.sub(r'<[^>]+>', '', i).strip()]
            if len(ps) >= 3:
                # the middle paragraph is a letter-spaced caps eyebrow, not a
                # heading -- the module sizes it from a different rule, so no
                # title size is reported rather than a wrong one
                return None, px(ps[2][0], dflt_body), colour(ps[2][0], dflt_colour)
        return dflt_title, dflt_body, dflt_colour
    t = px(m.group(1), dflt_title)
    tail = h[m.end():]
    for attrs, inner in tags(tail, 'p'):
        if 'letter-spacing' in attrs: continue
        if not re.sub(r'<[^>]+>', '', inner).strip(): continue
        return t, px(attrs, dflt_body), colour(attrs, dflt_colour)
    return t, dflt_body, dflt_colour


def tile_label(h, dflt_size, dflt_weight):
    at = h.find('grid-template-columns')
    for attrs, _ in tags(h[at:] if at > 0 else h, 'p'):
        if 'letter-spacing' in attrs: continue
        s, w = px(attrs), weight(attrs)
        if s or w: return s or dflt_size, w or dflt_weight
    return dflt_size, dflt_weight


def button_px(h, dflt):
    """V1's buttons are inline-block anchors; the size lives on the anchor."""
    m = re.search(r'<a(?=[\s>])([^>]*display:\s*inline-block[^>]*)>', h)
    return px(m.group(1), dflt) if m else dflt


def col(c):
    return {"color": c, "opacity": 100}


# ------------------------------------------------------------------ per type

def style_for(mid, h):
    if mid == HERO:
        p = paras(h)
        return {"headline_size": heading_px(h, 48),
                "eyebrow_size": eyebrow_px(h, 13),
                "subhead_size": px(p[-1][0], 19) if p else 19,
                "button_size": button_px(h, 16)}
    if mid == RT:
        p = paras(h)
        return {"body_size": px(p[0][0], 17) if p else 17,
                "heading_size": heading_px(h, 32)}
    if mid == CG:
        ss, sc = subhead(h, 17, '#555555')
        t, b, bc = card_type(h, 19, 15, '#555555')
        # the big step number, which V1 also holds at every width
        nm = max((px(a, 0) or 0 for a, _ in tags(h, 'p')), default=0)
        out = {"headline_size": heading_px(h, 32), "subhead_size": ss,
               "title_size": t, "body_size": b, "body_color": col(bc)}
        if nm >= 30: out["number_size"] = nm
        return out
    if mid == SH:
        ss, sc = subhead(h, 17, '#555555')
        return {"headline_size": heading_px(h, 34), "subhead_size": ss,
                "subhead_color": col(sc)}
    if mid == CS:
        p = paras(h)
        return {"body_size": px(p[-1][0], 16) if p else 16,
                "headline_size": heading_px(h, 32)}
    if mid == TG:
        ss, sc = subhead(h, 17, '#555555')
        ls, lw = tile_label(h, 17, '700')
        w = re.search(r'<p[^>]*max-width:\s*(\d+)px', h)
        return {"headline_size": heading_px(h, 32), "subhead_size": ss,
                "subhead_color": col(sc), "subhead_width": int(w.group(1)) if w else 0,
                "label_size": ls, "label_weight": lw}
    if mid == CTA:
        p = paras(h)
        a = p[-1][0] if p else ''
        return {"headline_size": heading_px(h, 32),
                "content_size": px(a, 17), "content_weight": weight(a, ''),
                "content_color": col(colour(a, '#333333')),
                "button_size": button_px(h, 16)}
    if mid == FAQ:
        q = re.search(r'<summary(?=[\s>])([^>]*)>', h)
        a = re.search(r'</summary>.*?<p(?=[\s>])([^>]*)>', h, re.S)
        return {"headline_size": heading_px(h, 32),
                "question_size": px(q.group(1), 17) if q else 17,
                "answer_size": px(a.group(1), 15) if a else 15}
    if mid == STAT:
        ps = [a for a, _ in tags(h, 'p')]
        big = max((px(a, 0) or 0 for a in ps), default=48) or 48
        lab = [a for a in ps if 'letter-spacing' in a]
        return {"value_size": big, "headline_size": heading_px(h, 32),
                "label_size": px(lab[0], 14) if lab else 14,
                "label_weight": weight(lab[0], '700') if lab else '700'}
    if mid == HERITAGE:
        p = paras(h)
        return {"headline_size": heading_px(h, 34),
                "body_size": px(p[0][0], 17) if p else 17}
    return {}


# --------------------------------------------------------------------- apply

def plain(s):
    return re.sub(r'\s+', ' ', _html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def anchor_of(params):
    """A string distinctive enough to locate this module's section in V1."""
    for k in ('section_headline', 'headline', 'form_title'):
        t = plain(params.get(k))
        if len(t) > 12: return t
    for key, sub in (('cards', 'title'), ('items', 'question'),
                     ('tiles', 'tile_label'), ('stats', 'stat_label')):
        arr = params.get(key) or []
        if arr and isinstance(arr[0], dict):
            t = plain(arr[0].get(sub))
            if len(t) > 6: return t
    for k in ('content', 'subhead', 'section_subhead'):
        t = plain(params.get(k))
        if len(t) > 24: return t[:60]
    return ''


def pair_up(mods, H):
    """Match each module to the V1 section it came from, by content.

    Matching by position is what broke the dosage pages: their hand-built
    conversion did not keep V1's section order, so module i was restyled from a
    section it has nothing to do with. A module that cannot be matched to
    exactly one section is left alone rather than guessed at."""
    plains = [plain(h) for h in H]
    out, used = [], set()
    for m in mods:
        a = anchor_of(m.get('params', {}))
        hits = [i for i, t in enumerate(plains) if a and a in t]
        out.append(hits[0] if len(hits) == 1 else None)
        if len(hits) == 1: used.add(hits[0])
    return out


def modules(page):
    out = []
    c = (page.get('layoutSections') or {}).get('main_content')
    for row in c['rows']:
        for ck in sorted(row, key=int):
            for sr in row[ck]['rows']:
                for mk in sorted(sr, key=int):
                    out.append(sr[mk])
    return out


def content_of(mods):
    """Everything that is not a style key -- the part a restyle must not move."""
    return json.dumps([{k: v for k, v in m.get('params', {}).items()
                        if k not in STYLE_KEYS} for m in mods],
                      sort_keys=True, separators=(',', ':'))


def main():
    v1id = sys.argv[1]
    dry  = '--dry' in sys.argv

    snap = json.load(open(f"{S}promote/{v1id}.PRE.json"))
    ws = (snap.get('widgetContainers') or {}).get('main_content', {}).get('widgets', [])
    H = [(w.get('body', {}).get('html') or w.get('body', {}).get('value') or '') for w in ws]
    if not H:
        print(f"  ABORT {v1id}: snapshot has no widgets"); return 2

    page = req(f"{API}/cms/v3/pages/site-pages/{v1id}")
    mods = modules(page)
    pairs = pair_up(mods, H)
    matched = sum(1 for x in pairs if x is not None)
    if matched < max(3, len(mods) // 2):
        print(f"  ABORT {v1id}: only {matched}/{len(mods)} modules could be matched to a "
              f"V1 section by content -- restyling the rest would be guesswork")
        return 2
    if page.get('state') != 'DRAFT' or page.get('published'):
        print(f"  ABORT {v1id}: page is {page.get('state')} / published={page.get('published')}")
        return 2

    # the layout exactly as it is now, kept aside before anything is mutated --
    # restoring from the edited copy would restore the damage
    original = copy.deepcopy(page['layoutSections'])
    before = content_of(mods)
    changed = 0
    skipped = []
    for m, si in zip(mods, pairs):
        p = m.setdefault('params', {})
        if si is None:
            skipped.append(p.get('module_id'))
            continue
        h = H[si]
        want = style_for(p.get('module_id'), h)
        # a size read for content the module does not carry is a guess, not a
        # measurement -- a grid with no subhead has nothing to read it from
        if not (p.get('section_subhead') or p.get('subhead')):
            want.pop('subhead_size', None); want.pop('subhead_color', None)
        if not p.get('cards'):
            for k in ('title_size', 'body_size', 'body_color'):
                if p.get('module_id') == CG: want.pop(k, None)
        if not (p.get('tiles') or p.get('stats')):
            want.pop('label_size', None); want.pop('label_weight', None)
        for k, v in want.items():
            if v is None: continue
            if p.get(k) != v:
                if not dry:
                    p[k] = v
                changed += 1
                print(f"      {p.get('module_id')} {k}: {p.get(k)!r} -> {v!r}")

    if dry:
        print(f"  DRY {v1id}: {changed} values would change; "
              f"{matched}/{len(mods)} modules matched to a V1 section"); return 0
    if not changed:
        print(f"  {v1id}: already matches V1"); return 0

    req(f"{API}/cms/v3/pages/site-pages/{v1id}", 'PATCH',
        json.dumps({"layoutSections": page['layoutSections']}, separators=(',', ':')).encode())

    back = modules(req(f"{API}/cms/v3/pages/site-pages/{v1id}"))
    if len(back) != len(mods) or content_of(back) != before:
        print(f"  CONTENT MOVED on {v1id} -- restoring the layout captured before the edit")
        req(f"{API}/cms/v3/pages/site-pages/{v1id}", 'PATCH',
            json.dumps({"layoutSections": original}, separators=(',', ':')).encode())
        again = modules(req(f"{API}/cms/v3/pages/site-pages/{v1id}"))
        print("  restored and verified" if content_of(again) == before
              else "  RESTORE DID NOT VERIFY -- page needs manual repair")
        return 3
    print(f"  OK {v1id}  {changed} values restyled from {matched}/{len(mods)} matched "
          f"sections, content unchanged" + (f", {len(skipped)} modules left alone" if skipped else ""))
    return 0


if __name__ == '__main__':
    sys.exit(main())
