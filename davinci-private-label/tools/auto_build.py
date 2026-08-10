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
FORM_WIDGET = 1155238         # the stock form module V1 uses for a bare form + title
STAT      = 218940115735      # PL - Stat Band, not in the category family's module set
# what the shared Heritage global renders, headline then body: it takes no
# fields, so a page whose V1 heritage type differs cannot use it
GLOBAL_HERITAGE_TYPE = (34, 17)


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


def wrap_style(h):
    """The style of the element that actually wraps the section.

    The shared reader searched for the first styled <div> anywhere in the
    markup. On a legacy pillar-page section -- copy pasted in as bare headings
    and paragraphs, with a grey callout partway down -- that match is the
    callout, so the section took the callout's background, its padding and its
    measure as its own and rendered a whole page of copy on grey. A wrapper has
    to be the section's first element to be the section's wrapper."""
    for e in elements(decomment(h)):
        m = re.match(r'\s*<div\b([^>]*)>', e)
        if not m:
            if txt(e) or '<img' in e:
                return ''            # the section opens with content: no wrapper
            continue                 # a leading <hr> or <br> is not content
        s = re.search(r'\sstyle="([^"]*)"', m.group(1))
        return s.group(1) if s else ''
    return ''


# --------------------------------------------------------------- classifying

def stat_row(cells):
    """Is this grid a row of statistics rather than a grid of cards?

    A stat reads value / uppercase label / optional sentence: a big figure over
    a letter-spaced caps line. A card reads title / sentence, and a numbered
    step reads number / title / sentence -- in neither of those is the second
    line set in caps.

    Distinguishing them on the size of the figure alone does not work. The
    facility spec row sets its values at 28px, under the 36px the old test
    needed, so it was built as a card grid: the card module decides between its
    56px numeral slot and its 13px eyebrow slot on the LENGTH of the string, so
    `7` came out at 56px while `100%`, `FDA` and `50+` came out at 13px in the
    same row, and the caps labels lost their capitals. The stat module is the
    one that has a value, a caps label and a description."""
    if len(cells) < 2:
        return False
    for c in cells:
        ps = _paras_in(c)
        if len(ps) < 2:
            return False
        big = px_of(ps[0][0], r'font-size:\s*(\d+)px', 0)
        small = px_of(ps[1][0], r'font-size:\s*(\d+)px', 0)
        capsish = ('letter-spacing' in ps[1][0]
                   and re.search(r'text-transform:\s*uppercase', ps[1][0]))
        if not (capsish and big >= 22 and small and big >= 1.6 * small):
            return False
    return True


def headline_el(h):
    """The section's real heading element, as a match: attributes and inner
    markup. The eyebrow is a heading on some pages, so it is skipped here the
    same way `headline` skips it."""
    for m in re.finditer(r'<(h1|h2)(?=[\s>])([^>]*)>(.*?)</\1>', h, re.S):
        if 'letter-spacing' in m.group(2): continue
        return m
    return None


def heading_markup(h):
    """Does the section's heading carry markup a plain text field would lose?

    A <br>, a link or an inline span is part of what V1 paints; the text fields
    the heading modules expose keep only the words."""
    for m in re.finditer(r'<(h1|h2|h3)(?=[\s>])([^>]*)>(.*?)</\1>', h, re.S):
        if 'letter-spacing' in m.group(2): continue
        if re.search(r'<(br|a|span|strong|em|b|i|sup|sub)\b', m.group(3), re.I):
            return True
    return False


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
    # a legacy form widget: no module_id and no markup, but a form and a title
    # that V1 renders. Skipped, it took its heading off the page with it.
    if w.get('type') == 'form' and (w.get('body') or {}).get('form_to_use'):
        return 'formwidget'
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
        if stat_row(cells):
            return 'statband'
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
    # a flex row of logos under a kicker is not a content split: read as one, only
    # its first image survives and the certification mark beside it disappears
    if (h.count('<img') >= 2 and re.search(r'display:\s*flex', h)
            and not re.search(r'<h[123](?=[\s>])', h)):
        return 'logoband'
    if re.search(r'<img', h) and re.search(r'display:\s*flex', h):
        return 'contentsplit'
    if re.search(r'<a[^>]*display:\s*inline-block', h):
        return 'cta'
    body = [p for p in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', h, re.S)
            if 'letter-spacing' not in p[0] and txt(p[1])]
    if len(body) <= 1 and re.search(r'<h[23](?=[\s>])', h) and '<img' not in h:
        # the section header's headline is a plain text field, so anything the
        # heading carries inside it is dropped: onboarding-guide's "Grab the ...
        # Guide" ends in <br><br>, and losing them took a blank line -- 29px --
        # out of the section. A heading with markup goes through rich text,
        # which keeps it.
        return 'richtext' if heading_markup(h) else 'sectionheader'
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
        # Only an anchor that wraps the whole cell is the card's own link. Taking
        # the first anchor anywhere inside it made every resource card a link to
        # whichever blog post its body listed first, and wrapped the card in an
        # <a> whose own text is the title -- so the title measured as the link.
        href = (re.match(r'\s*<a[^>]+href="([^"]+)"', blk)
                or re.match(r'\s*<div[^>]*>\s*<a[^>]+href="([^"]+)"', blk))
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


def _subhead_match(h):
    head = head_of(h)
    m = re.search(r'<p([^>]*max-width:\s*\d+px[^>]*)>(.*?)</p>', head, re.S)
    if not m:
        m = re.search(r'</h[123]>\s*<p(?=[\s>])([^>]*)>(.*?)</p>', head, re.S)
    return m if m and txt(m.group(2)) else None


TYPE_DECLS = ('font-size', 'line-height', 'color', 'font-weight', 'font-style',
              'letter-spacing', 'text-transform', 'opacity')


def keep_type(attrs):
    """V1's typographic declarations for one element, and only those.

    Carrying a paragraph's whole style attribute through is tempting -- it makes
    the copy render exactly as V1 painted it -- but it also carries the layout:
    V1's card-grid subhead sets `margin: 0 auto 48px`, and the module's header
    already puts 48px under the block, so the gap before the grid came out
    double. Size, weight, colour and leading are what the modules get wrong and
    what a reader sees; margin and max-width stay with the module."""
    m = re.search(r'\bstyle="([^"]*)"', attrs or '')
    out = []
    for d in re.split(r';', m.group(1) if m else ''):
        k = d.split(':', 1)[0].strip().lower()
        if k in TYPE_DECLS and ':' in d:
            out.append(d.strip())
    return '; '.join(out)


def subhead_of(h):
    """The capped, centred paragraph V1 uses under a section heading.

    Its type is carried inline, so the leading and the colour V1 paints hold
    even where the module has no field for them -- the contact and request-quote
    form sections read 18px/1.6 in V1 and rendered at the module's 17px/1.65."""
    m = _subhead_match(h)
    if not m: return ""
    st = keep_type(m.group(1))
    open_tag = '<p style="%s">' % st if st else '<p>'
    return open_tag + m.group(2).strip() + '</p>'


def subhead_attrs(h):
    """The style attribute of the very paragraph `subhead_of` picked, so its size
    and its colour are read off the element the module will actually render."""
    m = _subhead_match(h)
    return m.group(1) if m else ''


def sub_px(h, dflt=17):
    """V1's subhead size.

    The old reader only matched a subhead that declared max-width and font-size
    on one element. Where V1 puts the max-width on the section wrapper instead --
    which it does on every thank-you page -- it fell back to the module's 17px
    and quietly shrank an 18px subhead."""
    return px_of(subhead_attrs(h), r'font-size:\s*(\d+)px',
                 px_of(head_of(h),
                       r"max-width:\s*\d+px[^\"]*font-size:\s*(\d+)px"
                       r"|font-size:\s*(\d+)px[^\"]*max-width:\s*\d+px", dflt))


def subhead_colour(h, dflt="#555555"):
    c = own_colour(subhead_attrs(h))
    if not c: return body_colour(h, dflt)
    v = _hexpand(c)
    return v.upper() if re.fullmatch(r'#[0-9a-f]{6}', v) else body_colour(h, dflt)


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


# ------------------------------------------------------------ reading colour
#
# Every module drives its whole palette from one `text_color` choice. Leaving it
# at the module default painted eight content splits -- all authored
# `background: #012638; color: white` -- in near-black on near-black. So the
# choice is read from V1 like every other value, never assumed.

def _hexpand(v):
    v = (v or '').strip().lower().rstrip(';')
    if v in ('white', '#fff', '#ffffff'): return '#ffffff'
    if v in ('black', '#000', '#000000'): return '#000000'
    if re.fullmatch(r'#[0-9a-f]{3}', v):  return '#' + ''.join(c * 2 for c in v[1:])
    return v


def _lum(v):
    """Perceived luminance 0..1, or None for anything that is not a plain hex."""
    m = re.fullmatch(r'#([0-9a-f]{6})', _hexpand(v) or '')
    if not m: return None
    r, g, b = (int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def own_colour(style):
    """A `color:` declaration, never the `background-color:` that contains it.

    The boundary has to admit the opening quote as well as `;` and the start of
    the string, because callers pass whole attribute strings -- ` style="color:
    #333; ..."` -- as often as they pass a bare style value."""
    m = re.search(r'(?:^|[;"])\s*color:\s*([^;"]+)', style or '')
    return m.group(1).strip() if m else None


def text_col(h, dflt_bg="#FFFFFF"):
    """'light' or 'dark', read from V1: its own text colour first, its own
    background second. Nothing here is a guess about the design."""
    s = wrap_style(h)
    c = own_colour(s)
    if c is None:
        # a section that paints no colour on its wrapper paints it on the heading
        for m in re.finditer(r'<(h1|h2|h3)(?=[\s>])([^>]*)>', h):
            if 'letter-spacing' in m.group(2): continue
            c = own_colour(m.group(2))
            break
    if c is not None and _lum(c) is not None:
        return "light" if _lum(c) > 0.6 else "dark"
    l = _lum(bg(s, dflt_bg))
    return "light" if (l is not None and l < 0.45) else "dark"


def weight_of(style, dflt=None):
    m = re.search(r'font-weight:\s*(\w+)', style or '')
    if not m: return dflt
    return {'normal': '400', 'bold': '700'}.get(m.group(1), m.group(1))


def align_of(h, dflt="left"):
    """How V1 aligns the section's own copy.

    V1 writes it two ways: the hero and the CTA declare `text-align: center` on
    the outer band, while the facility card grid leaves the band alone and
    centres its h2 and subhead individually. Reading only the band missed the
    second kind; reading the whole section would let a centred card below the
    grid re-align the header. So the wrappers and the heading are read, and
    nothing below it.

    Where V1 declares nothing, the browser's own default applies -- left. The
    old `center` default put every plain section header in the middle of the
    page: `guides` is authored flush left and was rebuilt centred."""
    head = head_of(h)
    m = re.search(r'<(h1|h2)(?=[\s>])[^>]*>', head)
    seg = head[:m.end()] if m else ''
    seg += ' ' + ' '.join(re.findall(r'<div[^>]*?\sstyle="([^"]*)"', head)[:2])
    a = re.search(r'text-align:\s*(left|center)', seg)
    return a.group(1) if a else dflt


def screen_of(style, dflt=("#c9dbe2", 85)):
    """The rgba() screen V1 lays over a hero photograph, as colour + opacity.
    Hard-coding 85% of #c9dbe2 would repaint any hero screened a different way."""
    m = re.search(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(0?\.\d+|[01])\s*\)', style or '')
    if not m: return dflt
    return ('#%02X%02X%02X' % tuple(int(m.group(i)) for i in (1, 2, 3)),
            int(round(float(m.group(4)) * 100)))


def eyebrow_colour(h, dflt="heading"):
    m = re.search(r'<(?:p|div|span|h1|h2|h3)(?=[\s>])([^>]*letter-spacing[^>]*)>', h)
    c = own_colour(m.group(1)) if m else None
    if not c: return dflt
    return "accent" if _hexpand(c) == "#6ba644" else "heading"


def min_col(h, bound, gap_px, dflt):
    """The grid's own minimum column.

    V1 writes columns two ways. `minmax(Npx, 1fr)` is the module's own field,
    read straight across. A fixed `repeat(N, 1fr)` has no equivalent field, so
    the minimum that yields exactly N columns inside the section's bound is
    computed -- leaving the module's 260px default there gave a four-column V1
    row three columns."""
    m = re.search(r'minmax\((\d+)px', h)
    if m: return int(m.group(1))
    c = re.search(r'grid-template-columns:\s*repeat\((\d+),', h)
    if c and bound:
        n = int(c.group(1))
        return max(1, (int(bound) - (n - 1) * int(gap_px)) // n)
    return dflt


def ratio_of(h, dflt="1fr 1.2fr"):
    m = re.search(r'grid-template-columns:\s*([^;"}]+)', h)
    if not m: return dflt
    v = re.sub(r'\s+', ' ', m.group(1)).strip()
    return v if v in ("1fr 1.2fr", "1fr 1fr", "1.2fr 1fr") else dflt


def subhead_maxw(h, dflt=0):
    m = re.search(r'<p[^>]*max-width:\s*(\d+)px', head_of(h))
    return int(m.group(1)) if m else dflt


# Main.css -- the site stylesheet V1 and V3 both load -- sizes any heading and
# paragraph that declares nothing of its own. That rendered size is V1's, so it
# is what the rebuild has to reproduce; falling back to the module's own default
# put a 48px hero headline where the reader sees 40, and 17px body copy where
# the reader sees 16.
THEME_HEADING = {'h1': 50, 'h2': 40}
THEME_BODY = 16


def span_px(inner):
    """The size an inline <span> imposes on the text it wraps.

    The rich-text editor writes a resize as a span inside the heading rather
    than as a change to the heading's own declaration, so `onboarding-guide`
    reads `<h1 style="font-size:48px"><span style="font-size:40px">...`. The
    reader sees 40px. Only counted when the span carries the element's whole
    text, otherwise a highlighted phrase would resize the heading."""
    m = re.search(r'<span(?=[\s>])([^>]*font-size:\s*(\d+)px[^>]*)>(.*?)</span>', inner or '', re.S)
    if not m: return None
    return int(m.group(2)) if txt(m.group(3)) == txt(inner) else None


def headline_px(h, dflt=32):
    for m in re.finditer(r'<(h1|h2)([^>]*)>(.*?)</\1>', h, re.S):
        if 'letter-spacing' in m.group(2): continue
        inner = span_px(m.group(3))
        if inner: return inner
        px = re.search(r'font-size:\s*(\d+)px', m.group(2))
        return int(px.group(1)) if px else THEME_HEADING[m.group(1).lower()]
    return dflt


def body_px(h, dflt=17):
    """The size of the section's first real paragraph.

    It stops at that paragraph rather than scanning on for one that happens to
    declare a size: on a legacy page the next declaration belongs to a callout
    halfway down, and adopting it set every paragraph on the page to 19px."""
    for m in re.finditer(r'<p(?=[\s>])([^>]*)>', h):
        if 'letter-spacing' in m.group(1): continue
        px = re.search(r'font-size:\s*(\d+)px', m.group(1))
        return int(px.group(1)) if px else THEME_BODY
    return dflt


def eyebrow_px(h, dflt=13):
    """The kicker's own size, whichever order V1 wrote its declarations in.
    The old pattern required font-size before letter-spacing and returned the
    default whenever V1 wrote them the other way round; where the kicker
    declares nothing at all it still defers to that reader."""
    m = re.search(r'<(p|div|span|h1|h2|h3)(?=[\s>])([^>]*letter-spacing[^>]*)>(.*?)</\1>', h, re.S)
    if m:
        # an inline span the editor left behind repaints the kicker: onboarding
        # declares 13px on the <p> and 18px on the span that holds its text
        inner = span_px(m.group(3))
        if inner: return inner
        px = re.search(r'font-size:\s*(\d+)px', m.group(2))
        if px: return int(px.group(1))
    return px_of(h, r"font-size:\s*(\d+)px[^>]*letter-spacing", dflt)


def own_hex(attrs, dflt):
    """An element's own `color:` as a six-digit hex, or `dflt`."""
    c = own_colour(re.search(r'\bstyle="([^"]*)"', attrs or '').group(1)
                   if re.search(r'\bstyle="', attrs or '') else attrs)
    if not c: return dflt
    v = _hexpand(c)
    return v.upper() if re.fullmatch(r'#[0-9a-f]{6}', v) else dflt


def lh_of(attrs, dflt=None):
    """The line-height a reader actually sees on a V1 element.

    A declaration on the element wins. Where V1 declares none, Main.css's
    `p{line-height:27px}` is what paints -- which is why the modules' own 1.1,
    1.35 and 1.4 made every kicker, stat label and FAQ question a few pixels
    shorter than V1 and walked everything below them up the page. `dflt` is
    returned only when there is no element to read at all."""
    if not attrs: return dflt
    m = re.search(r'line-height:\s*([0-9.]+(?:px|em|rem)?)', attrs)
    return m.group(1) if m else '27px'


def card_body_colour(h, dflt="#555555"):
    """The colour of the very paragraph the card body is built from.

    Read off the first grid cell, past its title, and past the big step number a
    numbered card opens with -- that number is painted brand green, and taking
    its colour turned five sections of body copy green."""
    cells = grid_cells(h)
    seg = cells[0] if cells else h
    m = re.search(r'<h3(?=[\s>])[^>]*>', seg)
    if m: seg = seg[m.end():]
    cands = [a for a, i in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', seg, re.S)
             if txt(i) and 'letter-spacing' not in a]
    if not m and len(cands) > 1: cands = cands[1:]
    for a in cands:
        c = own_colour(a)
        if not c: break
        v = _hexpand(c)
        return v.upper() if re.fullmatch(r'#[0-9a-f]{6}', v) else body_colour(h, dflt)
    return body_colour(h, dflt)


def cell_boxed(h):
    """Does V1 draw a box around each card?

    Tested on the first grid cell, not on the whole section: `our-process` sets
    `background: white` on the section wrapper while its cards are bare, and
    reading the section put the module's 34x30 card padding round every one of
    them -- sixty pixels off the measure of every card on the page."""
    cells = grid_cells(h)
    if not cells: return 'background: white' in h
    m = re.match(r'\s*<\w+[^>]*\sstyle="([^"]*)"', cells[0])
    return bool(m and re.search(r'background(?:-color)?:\s*(?:white|#[0-9a-fA-F]{3,6})', m.group(1)))


def cell_shadow(h):
    """Does V1 drop a shadow under each card?"""
    cells = grid_cells(h)
    m = re.match(r'\s*<\w+[^>]*\sstyle="([^"]*)"', cells[0]) if cells else None
    return bool(m and 'box-shadow' in m.group(1))


def cell_align(h, dflt="left"):
    """A grid cell's own alignment. Reading `text-align: center` anywhere in the
    section instead picks up the centred section header above the grid and
    centres every card under it."""
    cells = grid_cells(h)
    if not cells: return dflt
    m = re.match(r'\s*<\w+[^>]*\sstyle="([^"]*)"', cells[0])
    if not m: return dflt
    a = re.search(r'text-align:\s*(\w+)', m.group(1))
    return a.group(1) if a and a.group(1) in ('left', 'center') else dflt


def section(kind, h, w):
    s = wrap_style(h)
    t, b = pad(s, (70, 70))
    base = lambda dflt: {"style": style_of(t, b, bg(s, dflt)),
                         "text_color": text_col(h, dflt)}

    if kind == 'global':
        # A global block stores nothing on the page and needs only its id. A
        # stock module stores its field values on the widget, and passing the id
        # alone rendered an empty form with no heading on five pages.
        own = {k2: v2 for k2, v2 in (w.get('body') or {}).items()
               if k2 not in ('html', 'content', 'value')}
        return {"module_id": w['module_id'], **own}

    if kind == 'formwidget':
        b2 = w.get('body') or {}
        return {"module_id": FORM_WIDGET,
                "title": b2.get('title', ''),
                "form": {"form_id": b2.get('form_to_use', ''),
                         "form_type": b2.get('form_type', 'HUBSPOT'),
                         "message": b2.get('response_message', ''),
                         "response_type": b2.get('response_response_type', 'inline')}}

    if kind == 'hero':
        t, b = pad(s, (90, 90))
        bgimg = re.search(r"url\('([^']+)'\)", s)
        hl = headline(h)
        subm = re.search(r'</h[12]>\s*<p(?=[\s>])([^>]*)>(.*?)</p>', h, re.S)
        scr_col, scr_op = screen_of(s)
        p = {**base(scr_col), "module_id": MOD['hero'], "align": align_of(h, "center"),
             "max_width": maxw(h, 900), "eyebrow": eyebrow(h),
             "eyebrow_color": eyebrow_colour(h),
             "headline_size": headline_px(h, 48),
             "eyebrow_size": eyebrow_px(h, 13),
             "subhead_size": px_of(subm.group(1), r'font-size:\s*(\d+)px', 19) if subm else 19,
             "headline": f"<h1>{hl}</h1>" if hl else "",
             "subhead": f"<p>{txt(subm.group(2))}</p>" if subm and txt(subm.group(2)) else "",
             "button_size": px_of(h, r"<a[^>]*font-size:\s*(\d+)px", 16)}
        if bgimg:
            p["background_image"] = {"src": bgimg.group(1)
                .replace('https://4087538.fs1.hubspotusercontent-na1.net/hubfs/4087538/',
                         'https://info.davincilabs.com/hubfs/'),
                "alt": "", "loading": "lazy"}
            p["background_screen"] = {"color": scr_col, "opacity": scr_op}
        # an omitted button group falls back to the module's default, which
        # renders a "Schedule a Consultation" the page never had
        p["buttons"] = [bt] if (bt := button(h)) else []
        return p

    if kind == 'richtext':
        hl = headline(h)
        hpx = headline_px(h, 32)
        hm = headline_el(h)
        # The module sizes its h2 from a stylesheet rule, so `heading_size` alone
        # would hold V1's size at one width and lose it at another. An inline
        # declaration on the heading itself is the one that holds everywhere --
        # and it carries V1's leading and colour with it. The heading's own inner
        # markup is kept too: a <br> the text of the heading does not record is
        # still a blank line the reader sees.
        htype = keep_type(hm.group(2)) if hm else ''
        hstyle = '; '.join(x for x in (htype, '' if 'font-size' in htype
                                       else f'font-size: {hpx}px') if x)
        inner = hm.group(3).strip() if hm else hl
        htag = f'<h2 style="{hstyle}">{inner}</h2>'
        content = (htag if hl else '') + paras(h)
        # if rebuilding from headings and paragraphs would lose anything -- copy
        # or an inline photograph -- carry the section's own markup instead of an
        # approximation
        if set(words_of(h)) - set(words_of(content)) or '<img' in h:
            content = inner_html(h)
        return {**base("#FFFFFF"), "module_id": MOD['rt'],
                "align": align_of(h, "left"),
                # no measure declared in V1 means no measure: the section runs
                # the full width less its gutter. Falling back to 850 capped
                # onboarding-guide's full-width heading at a little over half it.
                "max_width": maxw(h, 0), "top_border": False,
                "heading_size": hpx,
                "body_size": body_px(h, 17), "content": content}

    if kind == 'logoband':
        t, b = pad(s, (60, 60))
        logos = [{"image": img_of(m.group(0)),
                  "max_height": px_of(m.group(0), r'height:\s*(\d+)px', 80)}
                 for m in re.finditer(r'<img[^>]+>', h) if img_of(m.group(0))]
        return {"style": style_of(t, b, bg(s, "#FFFFFF")), "text_color": text_col(h, "#FFFFFF"),
                "module_id": MOD['sh'], "align": align_of(h, "center"),
                "eyebrow": eyebrow(h), "headline": "", "subhead": "",
                "headline_size": headline_px(h, 34), "max_width": maxw(h, 0),
                # V1's own flex gap between the marks, not the module's 40px
                "logo_gap": px_of(h, r'display:\s*flex[^"]*gap:\s*(\d+)px'
                                     r'|gap:\s*(\d+)px[^"]*display:\s*flex', 40),
                "logos": logos}

    if kind == 'sectionheader':
        return {**base("#FFFFFF"), "module_id": MOD['sh'], "align": align_of(h),
                "headline_size": headline_px(h, 34), "eyebrow": eyebrow(h),
                "headline": headline(h), "subhead": subhead_of(h),
                "subhead_size": sub_px(h), "max_width": maxw(h, 0),
                "subhead_color": {"color": subhead_colour(h), "opacity": 100}}

    if kind == 'cardgrid':
        cards = cards_in(h)
        bound = maxw(h, 1100)
        gap = px_of(h, r"gap:\s*(\d+)px", 24)
        # a big figure above the card title -- V1 sizes it itself, and 56px was
        # the family's number, not this page's
        num = px_of(h, r'<p[^>]*font-size:\s*(\d\d)px[^>]*>\s*\d+\s*</p>', 0)
        p = {**base("#FFFFFF"), "module_id": MOD['cg'], "max_width": bound,
             "header_width": bound, "section_eyebrow": eyebrow(h),
             "section_headline": headline(h), "headline_size": headline_px(h, 32),
             "section_subhead": subhead_of(h), "subhead_size": sub_px(h),
             # V1 caps the heading at the grid's measure but the sentence under
             # it at its own, narrower one -- a different number of lines
             "subhead_width": subhead_maxw(h, 0),
             "title_size": card_px(h, 'title', 19), "body_size": card_px(h, 'body', 15),
             "body_color": {"color": card_body_colour(h), "opacity": 100},
             # V1's numbered steps title their cards with a 15px letter-spaced
             # caps paragraph, which is exactly what the module's caps style is;
             # forcing "heading" rendered them at the module's 19px
             "title_style": "heading" if '<h3' in h else "eyebrow-caps",
             "card_style": "card" if cell_boxed(h) else "plain",
             "card_align": cell_align(h, "left"), "gap": gap,
             "min_column_width": min_col(h, bound, gap, 260),
             "cards": cards}
        if num: p["number_size"] = num
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
        tg_bound = maxw(h, 1200)
        tg_gap = px_of(h, r"gap:\s*(\d+)px", 24)
        p = {**base("#f7f7f6"), "module_id": MOD['tg'],
             "style": style_of(t2, b2, bg(s, "#f7f7f6")),
             "max_width": tg_bound, "section_eyebrow": eyebrow(h),
             "section_headline": headline(h), "headline_size": headline_px(h, 32),
             "section_subhead": subhead_of(h), "subhead_size": sub_px(h),
             "subhead_width": subhead_maxw(h, 0),
             "subhead_color": {"color": subhead_colour(h), "opacity": 100},
             "min_column_width": min_col(h, tg_bound, tg_gap, 180),
             # the tile photograph's own radius, not the card's around it
             "image_radius": px_of(h, r'<img[^>]*border-radius:\s*(\d+)px', 8),
             "tile_style": "card", "image_max_width": 0, "row_gap": 0,
             "image_fit": fit.group(2) if fit else "cover",
             "image_height": int(fit.group(1)) if fit else 160,
             "gap": tg_gap,
             "label_size": px_of(labm.group(1), r'font-size:\s*(\d+)px', 17) if labm else 17,
             "label_weight": (lambda m: {'normal': '400', 'bold': '700'}.get(m.group(1), m.group(1))
                              if m else "700")(re.search(r'font-weight:\s*(\w+)',
                                                         labm.group(1) if labm else '')),
             "tiles": tiles}
        if cols: p["columns"] = cols.group(1)
        return p

    if kind == 'statband':
        stats, cells = [], (grid_cells(h) or re.split(r'(?=<div)', h))
        vala = laba = ''
        for cell in cells:
            ps = _paras_in(cell)
            if len(ps) < 2:
                continue
            if not vala:
                vala, laba = ps[0][0], ps[1][0]
            st = {"value": txt(ps[0][1]), "stat_label": txt(ps[1][1])}
            # V1's stat bands carry a third line under the label; the module
            # has a `description` for it and reading only two dropped it
            if len(ps) > 2:
                st["description"] = ''.join(f'<p>{i.strip()}</p>' for _, i in ps[2:])
            # V1 sets an icon over the value in its spec rows; read from the cell,
            # because the section heading may carry a decorative one of its own
            sv = re.search(r'<svg\b.*?</svg>', cell, re.S)
            if sv: st["icon"] = {"src": icon_url(sv.group(0)), "alt": "", "loading": "lazy"}
            stats.append(st)
        if not laba:
            lab = re.search(r'<p(?=[\s>])([^>]*letter-spacing[^>]*)>', h)
            laba = lab.group(1) if lab else ''
        st_bound = maxw(h, 1100)
        st_gap = px_of(h, r"gap:\s*(\d+)px", 24)
        return {**base("#012638"), "module_id": STAT,
                "max_width": st_bound, "section_headline": headline(h),
                "headline_size": headline_px(h, 32),
                "section_subhead": subhead_of(h), "subhead_size": sub_px(h),
                "subhead_width": subhead_maxw(h, 0),
                "subhead_color": {"color": subhead_colour(h), "opacity": 100},
                # a cell that declares no alignment is left-aligned, which is
                # what the browser does; centring by default put V1's flush-left
                # spec cards in the middle of their boxes
                "align": cell_align(h, "left"),
                "card_style": "card" if cell_boxed(h) else "plain",
                # V1's spec cards are a top rule on white with nothing under
                # them; the module's own soft drop shadow is not on the page
                "card_shadow": cell_shadow(h),
                # read off the value paragraph itself. Scanning the section for
                # the first two-digit size found the 32px section heading and
                # sized every figure in the row to it.
                "value_size": px_of(vala, r'font-size:\s*(\d+)px',
                                    px_of(h, r"font-size:\s*(\d\d)px", 48)),
                "label_size": px_of(laba, r'font-size:\s*(\d+)px', 14),
                # V1 sets its stat labels at 600; the module's own default is 700
                "label_weight": weight_of(laba, "700"),
                # a bare <p> in V1 takes Main.css's p{line-height:27px}; the
                # module's own 1.1 / 1.35 made every row of the band taller
                "value_lh": lh_of(vala, "1.1"),
                "label_lh": lh_of(laba, "1.35"),
                # V1's own grid, not the module's: gap 40 against a default 24
                # narrowed every column on every stat band by twelve pixels
                "min_column_width": min_col(h, st_bound, st_gap, 180),
                "gap": st_gap,
                "stats": stats}

    if kind == 'contentsplit':
        t, b = pad(s, (90, 90))
        body = paras(h)
        im = img_of(h)
        left = bool(re.search(r'<img', h[:len(h) // 2]))
        p = {**base("#FFFFFF"), "module_id": MOD['cs'], "max_width": maxw(h, 1100),
             "image_side": "left" if left else "right",
             "ratio": ratio_of(h, "1fr 1.2fr"),
             "gap": px_of(h, r"gap:\s*(\d+)px", 56),
             "image_radius": px_of(h, r'border-radius:\s*(\d+)px', 8),
             "image_shadow": False, "eyebrow": eyebrow_all(h),
             "headline": headline(h), "headline_size": headline_px(h, 32),
             "content": body, "body_size": body_px(h, 16)}
        if im: p["image"] = im
        return p

    if kind in ('cta', 'imageband'):
        t, b = pad(s, (80, 80))
        ps = [(a, i) for a, i in re.findall(r'<p(?=[\s>])([^>]*)>(.*?)</p>', h, re.S)
              if 'letter-spacing' not in a and txt(i)]
        a0 = ps[-1][0] if ps else ''
        # the band's copy is carried with its own type, so its leading and its
        # colour come off the paragraph the module actually renders. Reading the
        # colour off the section instead matched on a size pattern the paragraph
        # did not have, and painted ingredients-testing's #012638 line in #333.
        c0 = keep_type(a0)
        p = {**base("#e6e5e3"), "module_id": MOD['cta'], "max_width": maxw(h, 720),
             "eyebrow": eyebrow(h), "headline": headline(h),
             "headline_size": headline_px(h, 32),
             "content": (('<p style="%s">' % c0 if c0 else '<p>')
                         + ps[-1][1].strip() + '</p>') if ps else "",
             "content_size": px_of(a0, r'font-size:\s*(\d+)px', 17),
             "content_color": {"color": own_hex(a0, body_colour(h, "#333333")),
                               "opacity": 100},
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
        # 'form-only' is not one of the module's two choices, so HubSpot silently
        # fell back to 'split' and put V1's centred heading beside the form
        layout = "split" if re.search(r'display:\s*grid|display:\s*flex', h) else "centered"
        hm = re.search(r'<(h1|h2)(?=[\s>])([^>]*)>', h)
        return {**base("#f7f7f6"), "module_id": FORM, "layout": layout,
                "headline": headline(h), "content": subhead_of(h),
                # V1 sets the form heading at 36px on contact and request-quote;
                # the module's own 32px is not this page's measurement
                "headline_size": headline_px(h, 32),
                "headline_lh": lh_of(hm.group(2) if hm else '', "1.25"),
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
        # or it silently replaces the page's own wording (this happened on Home).
        # The same argument applies to its type: the global block carries no
        # fields, so it renders 34/17 on every page that uses it. Three thank-you
        # pages set their heritage copy at 18px, and on those the global is the
        # wrong block -- the local twin holds V1's own size at every width.
        if (all(mk in txt(h) for mk in HERITAGE_MARKERS)
                and (headline_px(h, 34), body_px(h, 17)) == GLOBAL_HERITAGE_TYPE):
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
    # Five V1 pages carry two to five kilobytes of their own CSS in headHtml --
    # it is what centres and styles their embedded form. Left behind, the form
    # rendered full-bleed at browser defaults instead of 560px at 22px.
    req(f"{API}/cms/v3/pages/site-pages/{v3id}", method='PATCH', data=json.dumps(
        {"templatePath": "Private Label/Templates/Page - DND.html", "layoutSections": ls,
         "headHtml": v1.get('headHtml') or "", "footerHtml": v1.get('footerHtml') or ""},
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
