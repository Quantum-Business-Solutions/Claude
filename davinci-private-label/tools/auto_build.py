#!/usr/bin/env python3
"""Convert a hand-authored Private Label page to modules by reading its markup.

The 16-page category family was converted by a generator that knew the page shape
in advance -- section 5 is always the product grid, section 12 is always the FAQ.
That does not scale: the remaining pages share a vocabulary of section types but
not a fixed order or count.

So this classifies each section by what its markup actually is, then extracts it
with the same readers that got the category family to zero visual differences.
Every size, weight and colour is read from V1 rather than assumed -- assuming is
what put a family-wide type scale on Home.

usage: build.py <V1_ID> [--dry]
"""
import os, re, sys, json, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../fam16')
import build as F                              # the proven extractors
from build import (txt, tag, paras, eyebrow, headline, headline_px, body_px,
                   px_of, body_colour, maxw, pad, pad_span, wrap_style, bg,
                   style_of, img_of, button, req, MOD, GLOBAL,
                   HERITAGE_LOCAL, HERITAGE_MARKERS, layout_sections)

API = "https://api.hubapi.com"
S   = os.path.dirname(os.path.abspath(__file__)) + '/'
TOMBSTONE = 1786126404643
FORM      = 218940115793      # PL - Form Section
STAT      = 218940115735      # PL - Stat Band, not in the category family's module set


# ------------------------------------------------------------------- icons

_LIB = None

def _geom(svg):
    """Everything that draws: path data plus the shape primitives. The category
    family's lookup hashed only d= attributes, so an icon built from circles
    hashed to the empty string and every such icon collided."""
    g = re.findall(r'\sd="([^"]+)"', svg)
    g += [re.sub(r'\s+', ' ', m) for m in
          re.findall(r'<(?:circle|rect|line|polyline|polygon|ellipse)\b[^>]*>', svg)]
    return '|'.join(g)


def icon_url(svg):
    """Match an inline SVG to the hosted library by its geometry."""
    global _LIB
    if _LIB is None:
        _LIB = json.load(open(S + 'icon_lib.json'))
    name = _LIB.get(_geom(svg))
    if not name:
        raise RuntimeError(f"icon not in the hosted library: {svg[:90]!r}")
    return "https://info.davincilabs.com/hubfs/private-label/icons/pl-icon-%s.svg" % name


# ------------------------------------------------------------- html scanning
#
# Everything below walks the markup by balanced tags instead of splitting on a
# style declaration. Splitting was what lost the copy: a card whose wrapper is an
# <a>, or declares no padding of its own, never started a new block, so the whole
# grid collapsed into one "card" and every card after the first disappeared.

_TAG = re.compile(r'<(/?)([a-zA-Z][\w:-]*)((?:"[^"]*"|\'[^\']*\'|[^>"\'])*?)(/?)>')
VOID = {'img', 'br', 'hr', 'input', 'meta', 'link', 'source', 'col', 'area', 'base',
        'embed', 'param', 'track', 'wbr', 'path', 'circle', 'rect', 'line',
        'polyline', 'polygon', 'ellipse', 'use', 'stop'}


def decomment(h):
    return re.sub(r'(?s)<!--.*?-->', '', h)


def elements(h):
    """Top-level balanced elements of a fragment.

    Unmatched closing tags -- what any regex split through a grid leaves behind --
    are dropped rather than carried into a richtext field, where a stray </div>
    would tear the page layout open."""
    out, depth, start = [], 0, None
    for m in _TAG.finditer(h):
        closing, name, self_close = m.group(1), m.group(2).lower(), m.group(4)
        if closing:
            # an SVG primitive may be written <path/> or <path></path>; skipping
            # the open tag but honouring the close unbalances the whole scan
            if name in VOID: continue
            if depth:
                depth -= 1
                if depth == 0 and start is not None:
                    out.append(h[start:m.end()]); start = None
            continue
        if name in VOID or self_close:
            if depth == 0: out.append(m.group(0))
            continue
        if depth == 0: start = m.start()
        depth += 1
    return out


def element_inner(e):
    """What is inside a single balanced element."""
    m = _TAG.match(e)
    if not m or m.group(4) or m.group(2).lower() in VOID:
        return ''
    j = e.rstrip().rfind('</')
    return e[m.end():j] if j > m.end() else ''


def direct_text(e):
    """An element's own text, with the text of its children taken out."""
    inner = element_inner(e)
    for k in elements(inner):
        inner = inner.replace(k, ' ', 1)
    return txt(inner)


def text_units(h):
    """One entry per element that carries its own text, in document order.
    Each entry is (markup, text) so a caller can still look inside for a
    sublabel that V1 nested in a <span>."""
    out = []
    for e in elements(decomment(h)):
        d = direct_text(e)
        if d:
            out.append((e, d))
        else:
            out += text_units(element_inner(e))
    return out


def grid_open(h):
    """The opening tag of the section's grid container."""
    for want in ('grid-template-columns', None):
        for m in _TAG.finditer(h):
            if m.group(1) or m.group(4): continue
            a = m.group(3)
            if want and want in a: return m
            if not want and re.search(r'display:\s*grid', a): return m
    return None


def grid_cells(h):
    """The direct children of the section's grid container -- its cards or tiles.

    V1 writes grids three ways: a styled `grid-template-columns`, a bare
    `display: grid` with the columns in a stylesheet class, and cells wrapped in
    <a>. All three have to split the same way or the cards vanish."""
    h = decomment(h)
    m = grid_open(h)
    if not m: return []
    depth, end = 0, None
    for t in _TAG.finditer(h, m.start()):
        name = t.group(2).lower()
        if t.group(1):
            if name in VOID: continue
            depth -= 1
            if depth <= 0: end = t.start(); break
        elif not (name in VOID or t.group(4)):
            depth += 1
    inner = h[m.end():end] if end else h[m.end():]
    return [e for e in elements(inner) if txt(e) or '<img' in e]


def _paras_in(h):
    return [(a, i) for a, i in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', h, re.S) if txt(i)]


# --------------------------------------------------------------- classifying

def kind_of(h, w):
    """What sort of section this is. Order matters: the tests run most specific
    first, because a card grid also contains paragraphs and a hero also contains
    a heading."""
    # A `module` widget is only a global block when its body is empty -- that is
    # what "the copy comes from the global at render time" means. Several pages
    # hold their own copy inside a generic module, and passing those through as a
    # bare module_id threw the copy away and rendered the module's placeholder.
    if w.get('module_id') and not h.strip():
        return 'global'
    if not h.strip():
        return 'skip'
    if 'hbspt.forms.create' in h or re.search(r'<form(?=[\s>])', h):
        return 'form'
    if '<details' in h:
        return 'faq'
    if all(m in txt(h) for m in HERITAGE_MARKERS[:1]) or 'Developed by us' in h:
        return 'heritage'
    cells = grid_cells(h)
    if cells:
        # one photo beside one column of copy is a content split, not a one-card
        # grid -- read as a grid its eyebrow is emitted twice, as the section's
        # and again as the single card's title
        if h.count('<img') == 1 and '<h3' not in h:
            return 'contentsplit'
        if '<h3' in h:
            return 'cardgrid'
        if re.search(r'<a[^>]*>\s*(?:<div[^>]*>)?\s*<img', h, re.S) or h.count('<img') >= 3:
            return 'tilegrid'
        if re.search(r'font-size:\s*(?:3[6-9]|[4-9]\d)px', h):
            # a stat is a value and a label, optionally a description. A third
            # paragraph under a section heading is a numbered step, and the stat
            # band has nowhere to put the step's eyebrow or its body copy.
            if max(len(_paras_in(c)) for c in cells) >= 3 and (eyebrow(h) or headline(h)):
                return 'cardgrid'
            return 'statband'
        return 'cardgrid'
    if re.search(r'<h1(?=[\s>])', h):
        return 'hero'
    if re.search(r'<img', h) and re.search(r'display:\s*flex', h):
        return 'contentsplit'
    if re.search(r'<a[^>]*display:\s*inline-block', h):
        return 'cta'
    body = [p for p in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', h, re.S)
            if 'letter-spacing' not in p[0] and txt(p[1])]
    if len(body) <= 1 and re.search(r'<h[23](?=[\s>])', h) and '<img' not in h:
        return 'sectionheader'
    return 'richtext'


# ---------------------------------------------------------------- extracting

def words_of(x):
    return re.findall(r"[a-z0-9\u2713\u2714][a-z0-9'&/\u2013-]*",
                      txt(x).lower())


def inner_html(h):
    """The section's own markup with its outer wrapper removed.

    Used when a section contains something the extractors do not model -- the
    request-quote checklist is a green badge div beside each line, and rebuilding
    it from paragraphs alone silently drops the badge. Carrying V1's markup
    through renders identically and is still editable; inventing a shape that
    merely looks close is not worth the regression."""
    body = h.strip()
    for _ in range(2):
        m = re.match(r'\s*<div\b([^>]*)>\s*', body)
        if not m: break
        # a wrapper that declares the section's alignment is part of the design,
        # not scaffolding: strip it and centred copy silently goes left
        if 'text-align' in m.group(1): break
        rest = body[m.end():]
        j = rest.rstrip().rfind('</div>')
        if j < 0: break
        body = rest[:j]
    return body.strip()


def head_of(h):
    """Everything above the grid. A section's own heading and subhead live here;
    below it are the cards. Searching the whole section for a subhead picks up
    the first card's body copy and emits it twice."""
    m = grid_open(h)
    return h[:m.start()] if m and m.start() > 0 else h


def _blocks(h):
    """A grid's cards."""
    cells = grid_cells(h)
    if len(cells) > 1: return cells
    parts = re.split(r'(?=<div style="[^"]*padding:\s*\d+px\s+\d+px[^"]*")', h)
    return parts[1:] if len(parts) > 1 else [h]


def _kickers(seg):
    """Every letter-spaced kicker stacked above the headline, in V1's order.

    Some sections carry two: a coloured `STEP 01` pill authored as a <div> over a
    letter-spaced <p>. Matching a single <p ... letter-spacing: 2px> -- which is
    what the category family needed -- drops the pill."""
    for m in re.finditer(r'<(h1|h2)(?=[\s>])([^>]*)>', seg):
        if 'letter-spacing' not in m.group(2):
            seg = seg[:m.start()]; break
    out = []
    for m in re.finditer(r'<(p|div|span|h1|h2|h3)(?=[\s>])([^>]*letter-spacing[^>]*)>(.*?)</\1>',
                         seg, re.S):
        t = txt(m.group(3))
        if t and t not in out: out.append(t)
    return out


def eyebrow(h):
    """The section's kicker: read from above the grid, so a card's own kicker is
    never mistaken for the section's."""
    return ' '.join(_kickers(head_of(h)))


def eyebrow_all(h):
    """For sections whose heading sits inside the grid, e.g. a content split."""
    return ' '.join(_kickers(h))


def _eyebrows(blk):
    """A card's kicker."""
    return _kickers(blk)


def card_body(seg):
    """A card's copy below its title, exactly as V1 wrote it.

    Taking only the first <p> drops the link list under a resource card, the
    second paragraph of a two-paragraph card, and the caps line some cards set
    between the title and the body. Lifting those into separate module fields
    would re-order them, which the copy gate reads as words both lost and
    invented -- so the markup is carried through instead, inline styles and all,
    and renders identically."""
    return ''.join(e.strip() for e in elements(decomment(seg)) if txt(e))


def cards_in(h):
    """Every card in a grid, across the three shapes V1 uses:
    a heading card, a numbered-step card, and a figure card (big value, caps
    label, body). A shape that is not recognised returns nothing, and the copy
    gate then fails the page rather than letting the cards disappear quietly."""
    out = []
    for blk in _blocks(h):
        blk = decomment(blk)
        photo = img_of(blk)
        href = re.search(r'<a[^>]+href="([^"]+)"', blk)
        for m in re.finditer(r'<h3(?=[\s>])[^>]*>(.*?)</h3>', blk, re.S):
            seg = blk[m.end():]
            nxt = re.search(r'<h3(?=[\s>])', seg)
            if nxt: seg = seg[:nxt.start()]
            head = blk[:m.start()]
            c = {"title": txt(m.group(1))}
            eb = _eyebrows(head)
            if eb: c["number_or_eyebrow"] = ' '.join(eb)
            body = card_body(seg)
            if body: c["content"] = body
            sv = re.search(r'<svg\b.*?</svg>', head + seg[:400], re.S)
            if sv: c["icon"] = {"src": icon_url(sv.group(0)), "alt": "", "loading": "lazy"}
            if photo: c["image"] = photo
            if href:
                c["link"] = {"url": {"href": href.group(1), "type": "EXTERNAL"},
                             "open_in_new_tab": False}
            out.append(c)
    if out:
        return out

    # no headings: the card's title is a caps paragraph, usually under a figure
    for blk in _blocks(h):
        ps = [(a, i) for a, i in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', blk, re.S) if txt(i)]
        if len(ps) < 2:
            continue
        c = {}
        big = px_of(ps[0][0], r'font-size:\s*(\d+)px', 0)
        if big >= 22 or txt(ps[0][1]).isdigit():
            c["number_or_eyebrow"] = txt(ps[0][1])
            rest = ps[1:]
        else:
            rest = ps
        if not rest:
            continue
        c["title"] = txt(rest[0][1])
        if len(rest) > 1:
            # every remaining paragraph, in V1's order -- a numbered step whose
            # body was read as `the last <p>` lost anything in between
            c["content"] = ''.join(f'<p{a}>{i.strip()}</p>' for a, i in rest[1:])
        sv = re.search(r'<svg\b.*?</svg>', blk, re.S)
        if sv: c["icon"] = {"src": icon_url(sv.group(0)), "alt": "", "loading": "lazy"}
        out.append(c)
    return out


def subhead_of(h):
    """The capped, centred paragraph V1 uses under a section heading."""
    head = head_of(h)
    m = re.search(r'<p[^>]*max-width:\s*\d+px[^>]*>(.*?)</p>', head, re.S)
    if not m:
        m = re.search(r'</h[123]>\s*<p(?=[\s>])[^>]*>(.*?)</p>', head, re.S)
    return f"<p>{m.group(1).strip()}</p>" if m and txt(m.group(1)) else ""


def sub_px(h, dflt=17):
    return px_of(head_of(h),
                 r"max-width:\s*\d+px[^\"]*font-size:\s*(\d+)px"
                 r"|font-size:\s*(\d+)px[^\"]*max-width:\s*\d+px", dflt)


def card_px(h, which, dflt):
    m = re.search(r'<h3(?=[\s>])([^>]*)>', h)
    if not m: return dflt
    if which == 'title':
        return px_of(m.group(1), r'font-size:\s*(\d+)px', dflt)
    seg = h[m.end():]
    for a, inner in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', seg, re.S):
        if 'letter-spacing' in a or not txt(inner): continue
        return px_of(a, r'font-size:\s*(\d+)px', dflt)
    return dflt


def section(kind, h, w):
    s = wrap_style(h)
    t, b = pad(s, (70, 70))
    base = lambda dflt: {"style": style_of(t, b, bg(s, dflt)), "text_color": "dark"}

    if kind == 'global':
        return {"module_id": w['module_id']}

    if kind == 'hero':
        t, b = pad(s, (90, 90))
        bgimg = re.search(r"url\('([^']+)'\)", s)
        hl = headline(h)
        subm = re.search(r'</h[12]>\s*<p(?=[\s>])([^>]*)>(.*?)</p>', h, re.S)
        p = {**base("#c9dbe2"), "module_id": MOD['hero'], "align": "center",
             "max_width": maxw(h, 900), "eyebrow": eyebrow(h), "eyebrow_color": "heading",
             "headline_size": headline_px(h, 48),
             "eyebrow_size": px_of(h, r"font-size:\s*(\d+)px[^>]*letter-spacing", 13),
             "subhead_size": px_of(subm.group(1), r'font-size:\s*(\d+)px', 19) if subm else 19,
             "headline": f"<h1>{hl}</h1>" if hl else "",
             "subhead": f"<p>{txt(subm.group(2))}</p>" if subm and txt(subm.group(2)) else "",
             "button_size": px_of(h, r"<a[^>]*font-size:\s*(\d+)px", 16)}
        if bgimg:
            p["background_image"] = {"src": bgimg.group(1)
                .replace('https://4087538.fs1.hubspotusercontent-na1.net/hubfs/4087538/',
                         'https://info.davincilabs.com/hubfs/'),
                "alt": "", "loading": "lazy"}
            p["background_screen"] = {"color": "#c9dbe2", "opacity": 85}
        # an omitted button group falls back to the module's default, which
        # renders a "Schedule a Consultation" the page never had
        p["buttons"] = [bt] if (bt := button(h)) else []
        return p

    if kind == 'richtext':
        hl = headline(h)
        content = (f"<h2>{hl}</h2>" if hl else '') + paras(h)
        # if rebuilding from headings and paragraphs would lose anything -- copy
        # or an inline photograph -- carry the section's own markup instead of an
        # approximation
        if set(words_of(h)) - set(words_of(content)) or '<img' in h:
            content = inner_html(h)
        return {**base("#FFFFFF"), "module_id": MOD['rt'], "align": "left",
                "max_width": maxw(h, 850), "top_border": False,
                "body_size": body_px(h, 17), "content": content}

    if kind == 'sectionheader':
        return {**base("#f7f7f6"), "module_id": MOD['sh'], "align": "center",
                "headline_size": headline_px(h, 34), "eyebrow": eyebrow(h),
                "headline": headline(h), "subhead": subhead_of(h),
                "subhead_size": sub_px(h), "max_width": maxw(h, 0),
                "subhead_color": {"color": body_colour(h), "opacity": 100}}

    if kind == 'cardgrid':
        cards = cards_in(h)
        cols = re.search(r'grid-template-columns:\s*repeat\((\d+),', h)
        p = {**base("#FFFFFF"), "module_id": MOD['cg'], "max_width": maxw(h, 1100),
             "header_width": maxw(h, 1100), "section_eyebrow": eyebrow(h),
             "section_headline": headline(h), "headline_size": headline_px(h, 32),
             "section_subhead": subhead_of(h), "subhead_size": sub_px(h),
             "title_size": card_px(h, 'title', 19), "body_size": card_px(h, 'body', 15),
             "body_color": {"color": body_colour(h), "opacity": 100},
             "card_style": "card" if 'background: white' in h else "plain",
             "title_style": "heading", "gap": px_of(h, r"gap:\s*(\d+)px", 24),
             "cards": cards}
        if cols: p["min_column_width"] = 0
        return p

    if kind == 'tilegrid':
        tiles = []
        # read the grid's own cells: V1 links only some of its tile grids, and
        # matching on <a href> alone dropped every tile of the unlinked ones
        for cell in grid_cells(h):
            im = img_of(cell)
            a = re.search(r'<a[^>]+href="([^"]+)"', cell)
            link = ({"url": {"href": a.group(1), "type": "EXTERNAL"}, "open_in_new_tab": False}
                    if a else {"url": {"href": "", "type": "EXTERNAL"}, "open_in_new_tab": False})
            gl = re.search(r'<(\w+)[^>]*style="([^"]*font-size:\s*(\d+)px[^"]*)"[^>]*>\s*\+\s*</\1>',
                           cell, re.S)
            body = cell[:gl.start()] + cell[gl.end():] if gl else cell
            units = text_units(body)
            label = units[0][1] if units else (im.get('alt', '') if im else '')
            sub = ''
            if units:
                # V1's "+ AND MORE" tile nests its second line in a smaller span
                # inside the label; the module has a `sublabel` for exactly that
                inner0 = element_inner(units[0][0]) or units[0][0]
                sm = re.search(r'<span[^>]*>(.*?)</span>\s*$', inner0.rstrip(), re.S)
                if sm and txt(sm.group(1)) and txt(sm.group(1)) != label:
                    sub = txt(sm.group(1))
                    label = txt(re.sub(r'<span[^>]*>.*?</span>\s*$', '', inner0.rstrip(),
                                       flags=re.S))
            if im:
                t3 = {"image": im, "tile_label": label, "link": link}
                if sub: t3["sublabel"] = sub
                tiles.append(t3)
            elif gl or label:
                cbg = next((bg(st) for st in re.findall(r'style="([^"]*)"', cell)
                            if re.search(r'background(?:-color)?:\s*(#[0-9a-fA-F]{3,6}|white)', st)),
                           "#012638")
                t3 = {"tile_label": label, "link": link,
                      "accent_glyph": "+" if gl else "",
                      "glyph_size": int(gl.group(3)) if gl else 56,
                      "tile_bg": {"color": cbg, "opacity": 100},
                      "tile_text_color": "light" if re.search(r'color:\s*(white|#fff)', cell, re.I)
                                         else "dark"}
                if sub: t3["sublabel"] = sub
                tiles.append(t3)
        gm = grid_open(h)
        labm = re.search(r'<p(?=[\s>])([^>]*font-size:\s*\d+px[^>]*)>', h[gm.start():] if gm else h)
        cols = re.search(r'grid-template-columns:\s*repeat\((\d+),', h)
        fit  = re.search(r'height:\s*(\d+)px;\s*object-fit:\s*(\w+)', h)
        t2, b2 = pad_span(h, (80, 80))
        p = {**base("#f7f7f6"), "module_id": MOD['tg'],
             "style": style_of(t2, b2, bg(s, "#f7f7f6")),
             "max_width": maxw(h, 1200), "section_eyebrow": eyebrow(h),
             "section_headline": headline(h), "headline_size": headline_px(h, 32),
             "section_subhead": subhead_of(h), "subhead_size": sub_px(h),
             "tile_style": "card", "image_max_width": 0, "row_gap": 0,
             "image_fit": fit.group(2) if fit else "cover",
             "image_height": int(fit.group(1)) if fit else 160,
             "gap": px_of(h, r"gap:\s*(\d+)px", 24),
             "label_size": px_of(labm.group(1), r'font-size:\s*(\d+)px', 17) if labm else 17,
             "label_weight": (lambda m: {'normal': '400', 'bold': '700'}.get(m.group(1), m.group(1))
                              if m else "700")(re.search(r'font-weight:\s*(\w+)',
                                                         labm.group(1) if labm else '')),
             "tiles": tiles}
        if cols: p["columns"] = cols.group(1)
        return p

    if kind == 'statband':
        stats = []
        for cell in (grid_cells(h) or re.split(r'(?=<div)', h)):
            ps = _paras_in(cell)
            if len(ps) >= 2:
                st = {"value": txt(ps[0][1]), "stat_label": txt(ps[1][1])}
                # V1's stat bands carry a third line under the label; the module
                # has a `description` for it and reading only two dropped it
                if len(ps) > 2:
                    st["description"] = ''.join(f'<p>{i.strip()}</p>' for _, i in ps[2:])
                stats.append(st)
        lab = re.search(r'<p(?=[\s>])([^>]*letter-spacing[^>]*)>', h)
        return {**base("#012638"), "module_id": STAT, "text_color": "light",
                "max_width": maxw(h, 1100), "section_headline": headline(h),
                "value_size": px_of(h, r"font-size:\s*(\d\d)px", 48),
                "label_size": px_of(lab.group(1), r'font-size:\s*(\d+)px', 14) if lab else 14,
                "stats": stats}

    if kind == 'contentsplit':
        t, b = pad(s, (90, 90))
        body = paras(h)
        im = img_of(h)
        left = bool(re.search(r'<img', h[:len(h) // 2]))
        p = {**base("#FFFFFF"), "module_id": MOD['cs'], "max_width": maxw(h, 1100),
             "image_side": "left" if left else "right", "ratio": "1fr 1fr", "gap": 60,
             "image_radius": 6, "image_shadow": False, "eyebrow": eyebrow_all(h),
             "headline": headline(h), "content": body, "body_size": body_px(h, 16)}
        if im: p["image"] = im
        return p

    if kind in ('cta', 'imageband'):
        t, b = pad(s, (80, 80))
        ps = [(a, i) for a, i in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', h, re.S)
              if 'letter-spacing' not in a and txt(i)]
        a0 = ps[-1][0] if ps else ''
        p = {**base("#e6e5e3"), "module_id": MOD['cta'], "max_width": maxw(h, 720),
             "eyebrow": eyebrow(h), "headline": headline(h),
             "headline_size": headline_px(h, 32),
             "content": f"<p>{ps[-1][1].strip()}</p>" if ps else "",
             "content_size": px_of(a0, r'font-size:\s*(\d+)px', 17),
             "content_color": {"color": body_colour(h, "#333333"), "opacity": 100},
             "button_size": px_of(h, r"<a[^>]*font-size:\s*(\d+)px", 16)}
        wt = re.search(r'font-weight:\s*(\w+)', a0)
        if wt: p["content_weight"] = {'normal': '400', 'bold': '700'}.get(wt.group(1), wt.group(1))
        # explicit empty list: the module's default button is a real one
        p["buttons"] = [bt] if (bt := button(h)) else []
        return p

    if kind == 'form':
        # the embedded HubSpot form is identified by its formId; the module
        # renders the same form rather than re-embedding V1's inline script
        t, b = pad(s, (80, 80))
        fid = re.search(r'formId:\s*"([0-9a-f-]+)"', h)
        return {**base("#f7f7f6"), "module_id": FORM, "layout": "form-only",
                "headline": headline(h), "content": subhead_of(h),
                "eyebrow": eyebrow(h), "section_id": "",
                "form_field": {"form_id": fid.group(1) if fid else "",
                               "response_type": "inline",
                               "message": "Thanks for submitting the form."}}

    if kind == 'faq':
        t, b = pad(s, (80, 80))
        items = []
        for d in re.findall(r'<details\b.*?</details>', h, re.S):
            q = re.search(r'<span>(.*?)</span>', d, re.S)
            parts = re.split(r'</summary>', d, 1)
            ans = (re.sub(r'</?div[^>]*>', '', parts[1]).replace('</details>', '').strip()
                   if len(parts) > 1 else '')
            if q: items.append({"question": txt(q.group(1)), "answer": ans})
        return {**base("#f7f7f6"), "module_id": MOD['faq'], "max_width": maxw(h, 820),
                "section_eyebrow": eyebrow(h), "section_headline": headline(h),
                "headline_size": headline_px(h, 32),
                "question_size": px_of(h, r"<summary[^>]*font-size:\s*(\d+)px", 17),
                "answer_size": px_of(h, r"</summary>.*?<p(?=[\s>])[^>]*font-size:\s*(\d+)px", 15),
                "section_subhead": subhead_of(h), "open_first": False, "items": items}

    if kind == 'heritage':
        # the shared global may only be used where the copy already matches it,
        # or it silently replaces the page's own wording (this happened on Home)
        if all(mk in txt(h) for mk in HERITAGE_MARKERS):
            return {"module_id": GLOBAL['heritage']}
        t, b = pad(s, (90, 90))
        logos = [{"image": img_of(m.group(0)), "max_height": 80}
                 for m in re.finditer(r'<img[^>]+>', h) if img_of(m.group(0))]
        return {**base("#E6E5E3"), "module_id": HERITAGE_LOCAL, "max_width": maxw(h, 900),
                "eyebrow": eyebrow(h), "headline": headline(h), "content": paras(h),
                "images": logos, "body_size": body_px(h, 17),
                "headline_size": headline_px(h, 34)}

    raise RuntimeError(f"unclassified section: {h[:120]!r}")


def build(page):
    ws = page['widgetContainers']['main_content']['widgets']
    out = []
    for w in ws:
        b = w.get('body') or {}
        h = b.get('html') or b.get('content') or b.get('value') or ''
        k = kind_of(h, w)
        if k == 'skip':
            continue
        out.append((k, section(k, h, w)))
    return out


def main():
    v1id = sys.argv[1]
    dry  = '--dry' in sys.argv
    v1 = req(f"{API}/cms/v3/pages/site-pages/{v1id}")
    if not (v1.get('widgetContainers') or {}).get('main_content', {}).get('widgets'):
        raise RuntimeError(f"{v1id} has no widgets -- already promoted? build from its snapshot")
    mods = build(v1)
    print(f"  {v1['slug']:34} {len(mods)} modules  " + ' '.join(k for k, _ in mods))
    if dry:
        return 0

    ls = layout_sections(mods)
    slug = v1['slug'] + '-v3'
    found = req(f"{API}/cms/v3/pages/site-pages?slug={urllib.parse.quote(slug)}")
    if found.get('total'):
        v3id = found['results'][0]['id']
    else:
        v3id = req(f"{API}/cms/v3/pages/site-pages", method='POST', data=json.dumps({
            "name": v1['name'] + " — V3 (New Modules)", "slug": slug,
            "templatePath": "Private Label/Templates/Page.html",
            "domain": v1.get('domain') or "info.davincilabs.com", "state": "DRAFT",
            "htmlTitle": v1.get('htmlTitle'), "metaDescription": v1.get('metaDescription'),
            "widgetContainers": {"main_content": {"widgets": []}},
        }, separators=(',', ':')).encode())['id']
    req(f"{API}/cms/v3/pages/site-pages/{v3id}", method='PATCH', data=json.dumps(
        {"templatePath": "Private Label/Templates/Page - DND.html", "layoutSections": ls},
        separators=(',', ':')).encode())
    req(f"{API}/cms/v3/pages/site-pages/{v3id}", method='PATCH', data=json.dumps(
        {"widgetContainers": {"main_content": {"widgets": [], "deleted_at": TOMBSTONE}}},
        separators=(',', ':')).encode())
    print(f"  BUILT {v1['slug']} -> {v3id}")
    ids = {}
    p = S + 'v3_ids.json'
    if os.path.exists(p): ids = json.load(open(p))
    ids[v1id] = v3id
    json.dump(ids, open(p, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
