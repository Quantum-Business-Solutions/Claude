#!/usr/bin/env python3
"""Build a V3 drag-and-drop draft for a page in the 16-page category family.

The family is structurally identical across all 16 pages: 14 widgets in a fixed
order. Everything below extracts from the page's own V1 markup rather than
assuming values, so a page that deviates fails loudly instead of silently
inheriting the reference page's content.

usage: build.py <V1_ID>
"""
import json, os, re, sys, time, hashlib, urllib.request, urllib.parse, urllib.error, html as _html

S    = os.path.dirname(os.path.abspath(__file__)) + '/'
TOK  = os.environ['TOKEN']
API  = "https://api.hubapi.com"
HJ   = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
ICON = "https://info.davincilabs.com/hubfs/private-label/icons/pl-icon-%s.svg"
TOMBSTONE = 1786126404643

MOD = {'hero':218939846507,'rt':218940115784,'cg':218940115759,'sh':218940115771,
       'cs':218939846527,'tg':218940115743,'cta':218940115731,'faq':218940115739}
GLOBAL = {'pgl':218942529660,'go':218944099153,'fda':218942529652,'heritage':218944099156}
HERITAGE_LOCAL = 218954101913   # PL - Heritage (Section): non-global twin, for pages whose copy diverges

# the wording the shared Heritage global renders; a page may only use the global
# if its own copy matches, otherwise it would be silently overwritten (see Home)
HERITAGE_MARKERS = ["50+ YEARS OF SUPPLEMENT MANUFACTURING",
                    "most trusted dietary supplement manufacturers",
                    "FoodScience is an FDA-registered food facility"]


def req(url, data=None, method='GET', tries=4):
    for n in range(tries):
        try:
            r = urllib.request.Request(url, data=data, headers=HJ, method=method)
            with urllib.request.urlopen(r) as f:
                return json.loads(f.read())
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and n < tries-1:
                time.sleep(2**n); continue
            raise RuntimeError(f"{e.code} {e.read()[:400]}")
        except urllib.error.URLError:
            if n < tries-1: time.sleep(2**n); continue
            raise


# ---------- html helpers ----------
def txt(h):
    if not h: return ""
    return re.sub(r'\s+',' ', _html.unescape(re.sub(r'<[^>]+>','',h))).strip()

def tag(h, name, n=0):
    m = re.findall(rf'<{name}\b[^>]*>(.*?)</{name}>', h, re.S)
    return m[n] if len(m) > n else None

def inner_by_style(h, needle):
    """first element whose style attribute contains needle -> its inner html"""
    for m in re.finditer(r'<(\w+)[^>]*style="([^"]*)"[^>]*>', h):
        if needle in m.group(2):
            close = re.search(rf'</{m.group(1)}>', h[m.end():])
            return h[m.end(): m.end()+close.start()] if close else None
    return None

def wrap_style(h):
    m = re.search(r'<div[^>]*?\sstyle="([^"]*)"', h)
    return m.group(1) if m else ''

def pad(style, dflt=(80,80)):
    m = re.search(r'padding:\s*([^;"]+)', style)
    if not m: return dflt
    parts = m.group(1).split()
    def px(v):
        n = re.match(r'(\d+)', v)
        return int(n.group(1)) if n else None
    vals = [px(v) for v in parts]
    if not vals or vals[0] is None: return dflt
    t = vals[0]
    b = vals[2] if len(vals) >= 3 and vals[2] is not None else t
    return t, b

def pad_span(h, dflt=(80,80)):
    """Top/bottom for a section V1 split into stacked bands. A band is a wrapper that
    sets BOTH a background and a padding -- that excludes inner elements like a tile
    caption, which shares the same `Npx 20px` padding shape but paints nothing."""
    bands = [st for st in re.findall(r'<div[^>]*?\sstyle="([^"]*)"', h)
             if 'padding:' in st and re.search(r'background(-color)?:', st)]
    if not bands: return dflt
    top = pad(bands[0], dflt)[0]
    bot = None
    for st in reversed(bands):
        v = pad(st, (None, None))[1]
        if v is not None: bot = v; break
    return top, (bot if bot is not None else dflt[1])


def px_of(h, pattern, dflt):
    """First font-size V1 declares for a thing matching `pattern`. Used instead of
    assuming the family's usual value -- Aging sets body copy at 18px where every
    other page uses 17px, and that kind of deviation is the whole failure mode."""
    m = re.search(pattern, h, re.S)
    if not m: return dflt
    for g in m.groups():          # alternations leave the unmatched branch as None
        if g: return int(g)
    return dflt


def body_colour(h, dflt="#555555"):
    """V1's own body colour for a card section: #012638 on the numbered steps,
    #555 on advantage and product cards. Three-char hex is expanded."""
    m = re.search(r'color:\s*(#[0-9a-fA-F]{3,6})\s*;\s*font-size:\s*1[456]px', h)
    if not m: return dflt
    v = m.group(1)
    if len(v) == 4: v = '#' + ''.join(ch*2 for ch in v[1:])
    return v.upper()


def bg(style, dflt="#FFFFFF"):
    m = re.search(r'background(?:-color)?:\s*(#[0-9a-fA-F]{3,6}|white)', style)
    if not m: return dflt
    v = m.group(1)
    return "#FFFFFF" if v == 'white' else v.upper()

def maxw(h, dflt=0):
    """Widest CONTENT width the section allows.

    The theme sets box-sizing: border-box, so an element's rendered width is its
    max-width -- padding sits inside it. An unpadded bound therefore measures
    exactly its max-width, and that is the number the module needs. Only where
    V1 puts max-width and horizontal padding on the SAME element does the usable
    measure fall below the declared one, and only then is the padding taken off.
    Subtracting unconditionally set six dosage pages to 900px where V1 renders
    1100, and every card body in the section gained a line."""
    plain, padded = [], []
    for m in re.finditer(r'style="([^"]*max-width:\s*(\d+)px[^"]*)"', h):
        style, mw = m.group(1), int(m.group(2))
        pm = re.search(r'padding:\s*([^;"]+)', style)
        side = 0
        if pm:
            parts = pm.group(1).split()
            if len(parts) >= 2:
                sm = re.match(r'(\d+)', parts[1])
                if sm: side = int(sm.group(1))
        (padded if side else plain).append(mw - 2 * side)
    if plain:  return max(plain)
    if padded: return max(padded)
    return dflt


def paras(h):
    """all <p> that carry real copy, as html, skipping eyebrows and empties"""
    out=[]
    for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', h, re.S):
        t = txt(m.group(1))
        if t and t != 'None' and 'letter-spacing' not in (m.group(0)[:160]):
            out.append(f"<p>{m.group(1).strip()}</p>")
    return ''.join(out)

def eyebrow(h):
    """The kicker above the headline. Most pages mark it up as <p>, but some author
    it as an <h1>/<h2> -- Aging does, which is why V1 has two h1s on that page."""
    m = re.search(r'<(p(?=[\s>])|h1|h2|h3)[^>]*letter-spacing:\s*2px[^>]*>(.*?)</\1>', h, re.S)
    return txt(m.group(2)) if m else ""


def body_px(h, dflt=17):
    """Size of the first real body paragraph. The eyebrow is a <p> too and comes
    first in the markup, so it has to be skipped -- and it declares letter-spacing
    after its font-size, which is why the whole tag is tested rather than a prefix."""
    for m in re.finditer(r'<p(?=[\s>])([^>]*)>', h):
        if 'letter-spacing' in m.group(1): continue
        px = re.search(r'font-size:\s*(\d+)px', m.group(1))
        if px: return int(px.group(1))
    return dflt


def headline_px(h, dflt=32):
    """V1's own size for the headline element, so the rebuild doesn't flatten pages
    that deviate (Aging's tile-grid headline is 34px, its hero headline 40px)."""
    for m in re.finditer(r'<(h1|h2)([^>]*)>', h):
        if 'letter-spacing' in m.group(2): continue
        px = re.search(r'font-size:\s*(\d+)px', m.group(2))
        return int(px.group(1)) if px else dflt
    return dflt


def headline(h):
    """The real headline, whatever tag it was authored with. Skips any element that
    is actually the eyebrow (identified by its letter-spacing)."""
    for m in re.finditer(r'<(h1|h2)([^>]*)>(.*?)</\1>', h, re.S):
        if 'letter-spacing' in m.group(2): continue
        return txt(m.group(3))
    return ""

def button(h):
    m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S)
    if not m: return None
    style = 'primary' if '#6BA644' in m.group(0) else 'dark'
    return {"text": txt(m.group(2)), "style": style,
            "link": {"url": {"href": m.group(1), "type": "EXTERNAL"}, "open_in_new_tab": False}}


ICONS = None
def icon_url(svg):
    global ICONS
    if ICONS is None:
        ICONS = json.load(open(S+'icon_reuse.json'))
    d = hashlib.sha1('|'.join(re.findall(r'\sd="([^"]+)"', svg)).encode()).hexdigest()[:12]
    name = ICONS.get(d)
    if not name:
        raise RuntimeError(f"icon geometry {d} is not in the hosted library")
    return ICON % name


def img_of(h):
    m = re.search(r'<img[^>]+src="([^"]+)"[^>]*>', h)
    if not m: return None
    alt = re.search(r'alt="([^"]*)"', m.group(0))
    src = m.group(1).replace('https://4087538.fs1.hubspotusercontent-na1.net/hubfs/4087538/',
                             'https://info.davincilabs.com/hubfs/')
    src = src.replace('https://www.pettechlabs.com/hubfs/', 'https://info.davincilabs.com/hubfs/')
    return {"src": src, "alt": _html.unescape(alt.group(1)) if alt else "", "loading": "lazy"}


def style_of(t, b, colour):
    return {"padding": {"padding_top": t, "padding_bottom": b},
            "background_color": {"color": colour, "opacity": 100}}


# ---------- per-widget extraction ----------
def build(page):
    W = [ (w.get('body') or {}) for w in page['widgetContainers']['main_content']['widgets'] ]
    H = [ (b.get('html') or b.get('content') or '') for b in W ]
    raw = page['widgetContainers']['main_content']['widgets']
    if len(H) != 14:
        raise RuntimeError(f"expected 14 widgets, found {len(H)}")
    out = []

    # 0 — hero over a screened background photo
    s = wrap_style(H[0]); t,b = pad(s, (90,90))
    bgimg = re.search(r"url\('([^']+)'\)", s)
    screen = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*\.?(\d+)\)', s)
    sub_m  = re.search(r'</h[12]>\s*<p(?=[\s>])[^>]*font-size:\s*(\d+)px', H[0], re.S)
    sub_tx = txt((re.findall(r'</h[12]>\s*<p(?=[\s>])[^>]*>(.*?)</p>', H[0], re.S) or [''])[0])
    hl     = headline(H[0])
    # headline and subhead are richtext fields: they must carry their own markup, or
    # the page renders with no <h1> and the size rules (which bind to h1/h2) never apply
    hero = {"module_id":MOD['hero'],"style":style_of(t,b,"#c9dbe2"),"text_color":"dark","align":"center",
            "max_width":maxw(H[0],900),"eyebrow":eyebrow(H[0]),"eyebrow_color":"heading",
            "headline_size":headline_px(H[0],48),
            "eyebrow_size":(lambda m: int(m.group(1)) if m else 13)(
                re.search(r'<(?:p|h1|h2)[^>]*font-size:\s*(\d+)px[^>]*letter-spacing:\s*2px', H[0])),
            "subhead_size":int(sub_m.group(1)) if sub_m else 19,
            "headline":f"<h1>{hl}</h1>" if hl else "",
            "subhead":f"<p>{sub_tx}</p>" if sub_tx else ""}
    if bgimg:
        src = (bgimg.group(1)
               .replace('https://4087538.fs1.hubspotusercontent-na1.net/hubfs/4087538/',
                        'https://info.davincilabs.com/hubfs/')
               .replace('https://www.pettechlabs.com/hubfs/',
                        'https://info.davincilabs.com/hubfs/'))
        hero["background_image"] = {"src":src,"alt":"","loading":"lazy"}
    if screen:
        hero["background_screen"] = {"color":"#c9dbe2","opacity":85}
    hero["button_size"] = px_of(H[0], r"<a[^>]*font-size:\s*(\d+)px", 16)
    bt = button(H[0])
    if bt: hero["buttons"] = [bt]
    out.append(('hero', hero))

    # 1 — intro rich text
    s = wrap_style(H[1]); t,b = pad(s,(80,50))
    out.append(('rt', {"module_id":MOD['rt'],"style":style_of(t,b,"#FFFFFF"),"text_color":"dark",
        "align":"left","max_width":maxw(H[1],850),"top_border":False,
        "body_size":(lambda m: int(m.group(1)) if m else 17)(
            re.search(r'<p(?=[\s>])[^>]*font-size:\s*(\d+)px', H[1])),
        "content": (f"<h2>{headline(H[1])}</h2>" if headline(H[1]) else '') + paras(H[1])}))

    # 2 — HOW IT WORKS, three numbered steps
    s = wrap_style(H[2]); t,b = pad(s,(70,70))
    cards=[]
    for blk in re.findall(r'<div style="text-align: left;">(.*?)</div>', H[2], re.S):
        ps = re.findall(r'<p(?=[\s>])[^>]*>(.*?)</p>', blk, re.S)
        if len(ps) >= 3:
            cards.append({"number_or_eyebrow":txt(ps[0]),"title":txt(ps[1]),
                          "content":f"<p>{ps[2].strip()}</p>"})
    out.append(('cg', {"module_id":MOD['cg'],"style":style_of(t,b,"#c9dbe2"),"text_color":"dark",
        "max_width":maxw(H[2],1100),"header_width":maxw(H[2],1100),"body_color":{"color":body_colour(H[2]),"opacity":100},"section_eyebrow":eyebrow(H[2]),
        "section_headline":headline(H[2]),"headline_size":headline_px(H[2]),
        "card_style":"plain","title_style":"eyebrow-caps","gap":40,"cards":cards}))

    # 3 — "WHY <category>" section header
    s = wrap_style(H[3]); t,b = pad(s,(70,30))
    out.append(('sh', {"module_id":MOD['sh'],"style":style_of(t,b,"#f7f7f6"),"text_color":"dark",
        "align":"center","headline_size":headline_px(H[3],32),"eyebrow":eyebrow(H[3]),
        "headline":headline(H[3])}))

    # 4 — three advantage cards, 56px icon tiles
    s = wrap_style(H[4]); t,b = pad(s,(20,70))
    cards=[]
    for blk in re.split(r'(?=<div style="background: white; padding: 34px 30px)', H[4])[1:]:
        sv = re.search(r'<svg\b.*?</svg>', blk, re.S)
        h3 = tag(blk,'h3'); p = re.search(r'<p(?=[\s>])[^>]*>(.*?)</p>', blk, re.S)
        if not h3: continue
        c = {"title":txt(h3), "content":f"<p>{p.group(1).strip()}</p>" if p else ""}
        if sv: c["icon"] = {"src":icon_url(sv.group(0)),"alt":"","loading":"lazy"}
        cards.append(c)
    out.append(('cg', {"module_id":MOD['cg'],"style":style_of(t,b,"#f7f7f6"),"text_color":"dark",
        "max_width":maxw(H[4],1100),"body_color":{"color":body_colour(H[4]),"opacity":100},"card_style":"card","title_style":"heading",
        "title_size":px_of(H[4], r"<h3[^>]*font-size:\s*(\d+)px", 19),
        "card_density":"standard","icon_badge":True,
        "icon_badge_color":{"color":"#c9dbe2","opacity":100},
        "accent_color":{"color":"#6BA644","opacity":100},"show_accent":True,
        "gap":28,"cards":cards}))

    # 5 — product formulations, compact cards with 48px icon tiles
    s = wrap_style(H[5]); t,b = pad(s,(80,80))
    sub = re.search(r'<p[^>]*max-width: 760px[^>]*>(.*?)</p>', H[5], re.S)
    cards=[]
    for blk in re.split(r'(?=<div style="background: white; border-radius: 8px)', H[5])[1:]:
        sv = re.search(r'<svg\b.*?</svg>', blk, re.S)
        eb = re.search(r'<p[^>]*letter-spacing: 1\.5px[^>]*>(.*?)</p>', blk, re.S)
        h3 = tag(blk,'h3')
        ps = [m for m in re.findall(r'<p(?=[\s>])[^>]*>(.*?)</p>', blk, re.S)
              if 'letter-spacing' not in m and txt(m)]
        if not h3: continue
        c = {"title":txt(h3)}
        if eb: c["number_or_eyebrow"] = txt(eb.group(1))
        if ps: c["content"] = f"<p>{ps[-1].strip()}</p>"
        # V1 closes each product card with a row of pill tags
        chips = [txt(x) for x in re.findall(r'<span[^>]*border-radius: 100px[^>]*>(.*?)</span>', blk, re.S)]
        if chips: c["tags"] = ', '.join(chips)
        if sv: c["icon"] = {"src":icon_url(sv.group(0)),"alt":"","loading":"lazy"}
        cards.append(c)
    out.append(('cg', {"module_id":MOD['cg'],"style":style_of(t,b,"#FFFFFF"),"text_color":"dark",
        "max_width":maxw(H[5],1200),"header_width":maxw(H[5],1200),"body_color":{"color":body_colour(H[5]),"opacity":100},
        "section_headline":headline(H[5]),"headline_size":headline_px(H[5]),
        "section_subhead":f"<p>{sub.group(1).strip()}</p>" if sub else "",
        "card_style":"card","title_style":"heading","card_density":"compact",
        "subhead_size":px_of(H[5], r"font-size:\s*(\d+)px[^\"]*max-width:\s*760px"
                                   r"|max-width:\s*760px[^\"]*font-size:\s*(\d+)px", 17),
        "title_size":px_of(H[5], r"<h3[^>]*font-size:\s*(\d+)px", 18),
        "icon_badge":True,"icon_badge_color":{"color":"#c9dbe2","opacity":100},
        "show_accent":False,"gap":24,"cards":cards}))

    # 6 — dark split, image on the left
    s = wrap_style(H[6]); t,b = pad(s,(90,90))
    body = re.findall(r'<p[^>]*font-size: 16px[^>]*>(.*?)</p>', H[6], re.S)
    out.append(('cs', {"module_id":MOD['cs'],"style":style_of(t,b,"#012638"),"text_color":"light",
        "max_width":maxw(H[6],1100),"image_side":"left","ratio":"1fr 1fr","gap":60,
        "image_radius":6,"image_shadow":False,"eyebrow":eyebrow(H[6]),"body_size":(lambda m: int(m.group(1)) if m else 16)(re.search(r'<p(?=[\s>])[^>]*font-size:\s*(\d+)px[^>]*opacity', H[6])),
        "headline":headline(H[6]),
        "content":f"<p>{body[0].strip()}</p>" if body else paras(H[6]),
        "image":img_of(H[6])}))

    # 7 — cross-category tiles
    s = wrap_style(H[7]); t,b = pad_span(H[7],(80,80))
    sub = re.search(r'<p[^>]*max-width: 760px[^>]*>(.*?)</p>', H[7], re.S)
    tiles=[]
    for a in re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', H[7], re.S):
        im = img_of(a[1]); lab = re.search(r'<p(?=[\s>])[^>]*>(.*?)</p>', a[1], re.S)
        label = txt(lab.group(1)) if lab else (im.get('alt','') if im else '')
        link = {"url":{"href":a[0],"type":"EXTERNAL"},"open_in_new_tab":False}
        if im:
            tiles.append({"image":im,"tile_label":label,"link":link})
            continue
        # V1's "+ AND MORE" tile: a large accent glyph on a navy panel, no image
        gl = re.search(r'<div style="([^"]*font-size:\s*(\d+)px[^"]*)">\s*\+\s*</div>', a[1], re.S)
        if gl or label:
            # this tile's label is sized independently of the image tiles' labels
            lst = lab.group(0)[:lab.group(0).find('>')] if lab else ''
            lsz = re.search(r'font-size:\s*(\d+)px', lst)
            lwt = re.search(r'font-weight:\s*(\w+)', lst)
            tiles.append({"tile_label":label,"link":link,
                          "accent_glyph":"+" if gl else "",
                          "glyph_size":int(gl.group(2)) if gl else 56,
                          "label_size":int(lsz.group(1)) if lsz else 0,
                          "label_weight":{"normal":"400","bold":"700"}.get(
                              lwt.group(1), lwt.group(1)) if lwt else "",
                          "tile_bg":{"color":"#012638","opacity":100},
                          "tile_text_color":"light"})
    cols   = re.search(r'grid-template-columns:\s*repeat\((\d+),', H[7])
    mincol = re.search(r'minmax\((\d+)px', H[7])
    gapm   = re.search(r'gap:\s*(\d+)px', H[7])
    fitm   = re.search(r'height:\s*(\d+)px;\s*object-fit:\s*(\w+)', H[7])
    # look only inside the tiles grid, so the section eyebrow above it can't match
    grid_at = H[7].find('grid-template-columns')
    labm   = re.search(r'<p(?=[\s>])[^>]*font-size:\s*(\d+)px[^>]*font-weight[^>]*>',
                       H[7][grid_at:] if grid_at > 0 else H[7])
    radm   = re.search(r'border-radius:\s*(\d+)px;\s*overflow', H[7])
    headm = re.search(r'max-width:\s*(\d+)px', H[7])
    tg = {"module_id":MOD['tg'],"style":style_of(t,b,bg(wrap_style(H[7]),"#f7f7f6")),"text_color":"dark",
        "header_width": int(headm.group(1)) if headm and int(headm.group(1)) < maxw(H[7],1200) else 0,
        "max_width":maxw(H[7],1200),"section_headline":headline(H[7]),"headline_size":headline_px(H[7]),
        "section_eyebrow":eyebrow(H[7]),
        "section_subhead":f"<p>{sub.group(1).strip()}</p>" if sub else "",
        "tile_style":"card","image_max_width":0,"row_gap":0,
        "image_fit": fitm.group(2) if fitm else "cover",
        "image_height": int(fitm.group(1)) if fitm else 160,
        "gap": int(gapm.group(1)) if gapm else 24,
        "subhead_size": px_of(H[7], r"max-width:\s*760px[^>]*font-size:\s*(\d+)px|font-size:\s*(\d+)px[^>]*max-width:\s*760px", 17),
        "label_size": int(labm.group(1)) if labm else 17,
        "label_weight": (lambda m: m.group(1) if m else "700")(
            re.search(r'font-size:\s*\d+px;\s*font-weight:\s*(\d+)',
                      H[7][H[7].find('grid-template-columns'):] if 'grid-template-columns' in H[7] else H[7])),
        "tiles":tiles}
    if cols: tg["columns"] = cols.group(1)
    else:    tg["min_column_width"] = int(mincol.group(1)) if mincol else 180
    if radm: tg["image_radius"] = int(radm.group(1))
    out.append(('tg', tg))

    # 8 — global product guide link
    out.append(('global', {"module_id":GLOBAL['pgl']}))

    # 9 — CTA band, carries the #get-started anchor
    s = wrap_style(H[9]) or ''
    anchor = 'get-started' if 'id="get-started"' in H[9] else ''
    t,b = pad(s,(80,80))
    body = [m for m in re.findall(r'<p(?=[\s>])[^>]*>(.*?)</p>', H[9], re.S) if txt(m)]
    cta = {"module_id":MOD['cta'],"style":style_of(t,b,bg(s,"#e6e5e3")),"text_color":"dark",
           "max_width":maxw(H[9],720),"section_id":anchor,"eyebrow":eyebrow(H[9]),
           "content_size":px_of(H[9], r"<p(?=[\s>])[^>]*font-size:\s*(\d+)px", 17),
           "button_size":px_of(H[9], r"<a[^>]*font-size:\s*(\d+)px", 16),
           "headline":headline(H[9]),
           "content":f"<p>{body[0].strip()}</p>" if body else ""}
    bt = button(H[9])
    if bt: cta["buttons"] = [bt]
    out.append(('cta', cta))

    # 10 — global guide offer
    out.append(('global', {"module_id":GLOBAL['go']}))

    # 11 — heritage. Only safe to share the global if this page's copy matches it.
    plain = txt(H[11])
    if all(mk in plain for mk in HERITAGE_MARKERS):
        out.append(('global', {"module_id":GLOBAL['heritage']}))
    else:
        # This page's heritage copy is its own. Using the shared global here would
        # silently replace it with the majority wording -- the mistake made on Home.
        s = wrap_style(H[11]); t,b = pad(s,(90,90))
        logos=[]
        for m in re.finditer(r'<img[^>]+>', H[11]):
            im = img_of(m.group(0))
            if im: logos.append({"image":im, "max_height":80})
        out.append(('heritage-local', {"module_id":HERITAGE_LOCAL,
            "style":style_of(t,b,bg(s,"#E6E5E3")),"text_color":"dark",
            "max_width":maxw(H[11],900),"eyebrow":eyebrow(H[11]),
            "headline":headline(H[11]),"content":paras(H[11]),"images":logos,
            "body_size":body_px(H[11], 17),
            "headline_size":headline_px(H[11], 34)}))

    # 12 — FAQ
    s = wrap_style(H[12]); t,b = pad(s,(80,80))
    items=[]
    for d in re.findall(r'<details\b.*?</details>', H[12], re.S):
        q = re.search(r'<span>(.*?)</span>', d, re.S)
        a = re.split(r'</summary>', d, 1)
        ans = re.sub(r'</?div[^>]*>','', a[1]).replace('</details>','').strip() if len(a)>1 else ''
        if q: items.append({"question":txt(q.group(1)), "answer":ans})
    out.append(('faq', {"module_id":MOD['faq'],"style":style_of(t,b,"#f7f7f6"),"text_color":"dark",
        "max_width":maxw(H[12],820),"section_eyebrow":eyebrow(H[12]),
        "question_size":px_of(H[12], r"<summary[^>]*font-size:\s*(\d+)px", 17),
        "answer_size":px_of(H[12], r"</summary>.*?<p(?=[\s>])[^>]*font-size:\s*(\d+)px", 15),
        # Aging authored its FAQ heading as a second <h1> at 18px; the module emits a
        # single well-formed <h2>, which fixes the duplicate h1 as a side effect --
        # but it has to keep V1's size, or the heading grows from 18px to 32px.
        "section_headline":headline(H[12]),
        "headline_size":headline_px(H[12], 32),
        "section_subhead":"","open_first":False,"items":items}))

    # 13 — global FDA disclaimer
    out.append(('global', {"module_id":GLOBAL['fda']}))
    return out


def layout_sections(mods):
    rows, meta = [], []
    for i,(_kind,params) in enumerate(mods):
        m = {"type":"module","name":f"module_{i}","label":f"module_{i}","params":params,
             "w":0,"x":0,"cells":[],"rows":[],"rowMetaData":[],"cssClass":""}
        col = {"type":"cell","name":f"column_{i}","params":{"css_class":"dnd-column"},
               "w":0,"x":0,"cells":[],"rows":[{"0":m}],"rowMetaData":[],"cssClass":""}
        rows.append({"0":col}); meta.append({"cssClass":"dnd-section"})
    return {"main_content":{"type":"cell","name":"main_content","params":{},"w":0,"x":0,
                            "cells":[],"rows":rows,"rowMetaData":meta,"cssClass":""}}


def main():
    v1id = sys.argv[1]
    v1 = req(f"{API}/cms/v3/pages/site-pages/{v1id}")
    # Once a page has been promoted its record no longer holds the original rich text,
    # so rebuild from the pre-promotion snapshot -- which is exactly why it is taken.
    if not (v1.get('widgetContainers') or {}).get('main_content', {}).get('widgets'):
        for cand in (f"{S}../promote/{v1id}.PRE.json",
                     f"{S}../backup_v1_2026-08-07/{v1id}.json",
                     f"{S}../backup_v1/{v1id}.json",
                     f"{S}{v1id}.json"):
            if os.path.exists(cand):
                snap = json.load(open(cand))
                if (snap.get('widgetContainers') or {}).get('main_content', {}).get('widgets'):
                    print(f"  (rebuilding {v1id} from {os.path.basename(cand)} -- page is already promoted)")
                    v1 = {**v1, 'widgetContainers': snap['widgetContainers']}
                    break
        else:
            raise RuntimeError(f"{v1id} has no widgets live and no usable snapshot")
    mods = build(v1)
    ls = layout_sections(mods)

    slug = v1['slug'] + '-v3'
    existing = req(f"{API}/cms/v3/pages/site-pages?slug={urllib.parse.quote(slug)}")
    if existing.get('total'):
        v3id = existing['results'][0]['id']
    else:
        created = req(f"{API}/cms/v3/pages/site-pages", method='POST', data=json.dumps({
            "name": v1['name'] + " — V3 (New Modules)", "slug": slug,
            "templatePath": "Private Label/Templates/Page.html",
            "domain": v1.get('domain') or "info.davincilabs.com", "state": "DRAFT",
            "htmlTitle": v1.get('htmlTitle'), "metaDescription": v1.get('metaDescription'),
            "widgetContainers": {"main_content": {"widgets": []}},
        }, separators=(',',':')).encode())
        v3id = created['id']
    # the proven three-step path: a page POSTed straight to layoutSections renders an empty editor
    req(f"{API}/cms/v3/pages/site-pages/{v3id}", method='PATCH', data=json.dumps(
        {"templatePath":"Private Label/Templates/Page - DND.html","layoutSections":ls},
        separators=(',',':')).encode())
    req(f"{API}/cms/v3/pages/site-pages/{v3id}", method='PATCH', data=json.dumps(
        {"widgetContainers":{"main_content":{"widgets":[],"deleted_at":TOMBSTONE}}},
        separators=(',',':')).encode())

    counts = {}
    for k,p in mods:
        for f in ('cards','tiles','items'):
            if f in p: counts[f] = counts.get(f,0) + len(p[f])
    print(f"  BUILT {v1['slug']:26} -> {v3id}  {len(mods)} modules  "
          f"cards:{counts.get('cards',0)} tiles:{counts.get('tiles',0)} faq:{counts.get('items',0)}")
    return 0


if __name__ == '__main__':
    import urllib.parse
    sys.exit(main())
