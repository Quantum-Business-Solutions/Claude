#!/usr/bin/env python3
"""Build the Revolution Office logo (closed circle) as font-independent SVG + PNG variants."""
import os, sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = HERE
os.makedirs(OUT, exist_ok=True)

_fonts = {}
def font(weight):
    if weight not in _fonts:
        _fonts[weight] = TTFont(os.path.join(FONTS, f"Montserrat-{weight}.ttf"))
    return _fonts[weight]

def measure(weight, text, size, tracking=0.0):
    f = font(weight); cmap = f.getBestCmap(); hmtx = f["hmtx"]
    scale = size / f["head"].unitsPerEm
    w = sum(hmtx[cmap[ord(c)]][0] * scale for c in text) + tracking * (len(text) - 1)
    return w

def cap_height(weight, size):
    f = font(weight)
    return f["OS/2"].sCapHeight * size / f["head"].unitsPerEm

def text_path(weight, text, size, x, y, tracking=0.0):
    """Return SVG path data for `text` with baseline at (x, y)."""
    f = font(weight); gs = f.getGlyphSet(); cmap = f.getBestCmap(); hmtx = f["hmtx"]
    scale = size / f["head"].unitsPerEm
    parts = []; cur = x
    for c in text:
        g = cmap[ord(c)]
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, cur, y)))
        d = pen.getCommands()
        if d: parts.append(d)
        cur += hmtx[g][0] * scale + tracking
    return " ".join(parts)

def fmt(v): return f"{v:.2f}".rstrip("0").rstrip(".")

# ---------------------------------------------------------------- geometry
# Design canvas (horizontal lockup)
R_SIZE = 142            # "R" mark
RING_R = 105            # ring radius (to stroke centre)
RING_W = 20             # ring stroke width
CX = CY = 130           # ring centre
GAP = 40                # gap between ring and wordmark
NAME_SIZE = 108         # REVOLUTION (ExtraBold)
OFFICE_SIZE = 70        # OFFICE (Bold, wide tracking)
TAG_SIZE = 42           # tagline (Medium)

def layout():
    x0 = CX + RING_R + RING_W / 2 + GAP
    name_w = measure(800, "REVOLUTION", NAME_SIZE, tracking=1.5)
    # OFFICE tracked to span the same width as REVOLUTION
    off_nat = measure(700, "OFFICE", OFFICE_SIZE)
    off_track = (name_w - off_nat) / (len("OFFICE") - 1)
    # tagline tracked to span the same width too
    tag = "A Managed Print Company"
    tag_nat = measure(500, tag, TAG_SIZE)
    tag_track = (name_w - tag_nat) / (len(tag) - 1)
    name_cap = cap_height(800, NAME_SIZE)
    off_cap = cap_height(700, OFFICE_SIZE)
    tag_cap = cap_height(500, TAG_SIZE)
    # vertical rhythm
    y_name = 30 + name_cap                 # baseline
    y_office = y_name + 22 + off_cap
    y_tag = y_office + 26 + tag_cap
    block_top = 30; block_bottom = y_tag + (TAG_SIZE * 0.24)  # descender allowance
    total_h = block_bottom + 30
    # centre ring on the text block
    cy = (block_top + y_tag) / 2 + 4
    width = x0 + name_w + 30
    return dict(x0=x0, name_w=name_w, off_track=off_track, tag=tag, tag_track=tag_track,
                y_name=y_name, y_office=y_office, y_tag=y_tag, cy=cy, width=width, height=total_h)

L = layout()

def ring_and_r(cx, cy, accent, letter_fill):
    r_w = measure(800, "R", R_SIZE)
    r_cap = cap_height(800, R_SIZE)
    rx = cx - r_w / 2 - 2   # optical centring (R is heavier on the left)
    ry = cy + r_cap / 2
    return (f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{RING_R}" fill="none" stroke="{accent}" stroke-width="{RING_W}"/>\n'
            f'<path fill="{letter_fill}" d="{text_path(800, "R", R_SIZE, rx, ry)}"/>')

def wordmark(x0, dy, name_fill, office_fill, tag_fill):
    return (f'<path fill="{name_fill}" d="{text_path(800, "REVOLUTION", NAME_SIZE, x0, L["y_name"] + dy, tracking=1.5)}"/>\n'
            f'<path fill="{office_fill}" d="{text_path(700, "OFFICE", OFFICE_SIZE, x0, L["y_office"] + dy, tracking=L["off_track"])}"/>\n'
            f'<path fill="{tag_fill}" d="{text_path(500, L["tag"], TAG_SIZE, x0, L["y_tag"] + dy, tracking=L["tag_track"])}"/>')

def svg_doc(w, h, body, bg=None):
    bg_rect = f'<rect width="{fmt(w)}" height="{fmt(h)}" fill="{bg}"/>\n' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(w)} {fmt(h)}" width="{fmt(w)}" height="{fmt(h)}">\n'
            f'<title>Revolution Office</title>\n{bg_rect}{body}\n</svg>\n')

def horizontal(c, bg=None):
    body = ring_and_r(CX, L["cy"], c["accent"], c["mark"]) + "\n" + wordmark(L["x0"], 0, c["name"], c["office"], c["tag"])
    return svg_doc(L["width"], L["height"], body, bg)

def stacked(c, bg=None):
    w = L["name_w"] + 80
    ring_cy = 30 + RING_R + RING_W / 2
    dy = ring_cy + RING_R + RING_W / 2 + 40 - 30
    x0 = (w - L["name_w"]) / 2
    h = L["height"] + dy - 10
    body = ring_and_r(w / 2, ring_cy, c["accent"], c["mark"]) + "\n" + wordmark(x0, dy, c["name"], c["office"], c["tag"])
    return svg_doc(w, h, body, bg)

def icon(c, bg=None):
    s = 2 * (RING_R + RING_W / 2) + 40
    body = ring_and_r(s / 2, s / 2, c["accent"], c["mark"])
    return svg_doc(s, s, body, bg)

# ---------------------------------------------------------------- colourways
ORANGE = "#E8872B"; INK = "#141414"; WHITE = "#FFFFFF"
def cw(accent, text, mark=None, office=None, tag=None):
    return dict(accent=accent, mark=mark or accent, name=text, office=office or text, tag=tag or text)

VARIANTS = {
    # name: (colours, preview background for the "on-bg" PNG, is_light_artwork)
    "01-original-orange-black":  (cw(ORANGE, INK), WHITE),
    "02-all-black":              (cw(INK, INK), WHITE),
    "03-all-white":              (cw(WHITE, WHITE), INK),
    "04-orange-white":           (cw(ORANGE, WHITE), INK),
    "05-navy-orange":            (cw(ORANGE, "#1B2A4A"), WHITE),
    "06-charcoal-orange":        (cw(ORANGE, "#3A3A3A"), WHITE),
    "07-all-orange":             (cw(ORANGE, ORANGE), WHITE),
    "08-grey-black":             (cw("#8A8F98", INK), WHITE),
    "09-teal-black":             (cw("#0E8A8A", INK), WHITE),
    "10-blue-black":             (cw("#1F5FBF", INK), WHITE),
    "11-green-black":            (cw("#2E8B57", INK), WHITE),
    "12-red-black":              (cw("#C8402E", INK), WHITE),
    "13-orange-on-navy":         (cw(ORANGE, WHITE), "#1B2A4A"),
    "14-black-on-orange":        (cw(INK, INK), ORANGE),
    "15-white-on-orange":        (cw(WHITE, WHITE), ORANGE),
}

LAYOUTS = {"horizontal": horizontal, "stacked": stacked, "icon": icon}
PNG_WIDTH = 2400

def write(path, text):
    with open(path, "w") as f: f.write(text)

manifest = []
for name, (colours, bg) in VARIANTS.items():
    for lname, fn in LAYOUTS.items():
        base = f"revolution-office_{lname}_{name}"
        d = os.path.join(OUT, lname); os.makedirs(d, exist_ok=True)
        svg_t = fn(colours)                 # transparent
        svg_b = fn(colours, bg=bg)          # on solid background
        p_svg = os.path.join(d, base + ".svg"); write(p_svg, svg_t)
        p_svg_bg = os.path.join(d, base + "_bg.svg"); write(p_svg_bg, svg_b)
        p_png = os.path.join(d, base + "_transparent.png")
        p_png_bg = os.path.join(d, base + "_bg.png")
        scale = PNG_WIDTH / (float(svg_t.split('viewBox="0 0 ')[1].split()[0]))
        cairosvg.svg2png(bytestring=svg_t.encode(), write_to=p_png, scale=scale)
        cairosvg.svg2png(bytestring=svg_b.encode(), write_to=p_png_bg, scale=scale)
        manifest.append(dict(variant=name, layout=lname, svg=os.path.relpath(p_svg, OUT),
                             svg_bg=os.path.relpath(p_svg_bg, OUT), png_transparent=os.path.relpath(p_png, OUT),
                             png_bg=os.path.relpath(p_png_bg, OUT), colours=colours, bg=bg))
        # remove unused background svg to keep the package lean (keep PNG on bg)
        os.remove(p_svg_bg)

# small preview for the chat / reference (original, horizontal, on white)
cairosvg.svg2png(bytestring=horizontal(VARIANTS["01-original-orange-black"][0], bg=WHITE).encode(),
                 write_to=os.path.join(OUT, "preview_original.png"), scale=1200 / L["width"])
with open(os.path.join(OUT, "manifest.json"), "w") as f: json.dump(dict(layout=L, files=manifest), f, indent=2)
print(json.dumps(L, indent=1)); print(len(manifest), "variant files written to", OUT)
