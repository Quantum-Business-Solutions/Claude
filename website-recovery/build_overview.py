#!/usr/bin/env python3
"""Build /quantum-overview: hero, pain-bridge module, stats, service wheel, entry doors, quote, CTA."""
import json, urllib.request, ssl, math, copy, datetime

S = '/tmp/claude-0/-home-user-Claude/afaaa5d3-2de0-5da2-9bf3-affd4e8c30f7/scratchpad/'
TOKEN = [l.split('=', 1)[1].strip() for l in open(S + 'hs_env') if 'HS_TOKEN' in l][0]
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
BASE = 'https://api.hubapi.com/cms/v3/pages/landing-pages'
HERO_ID, RT_ID, CTA_ID, STATS_ID, BRIDGE_ID = 217248524134, 217248524682, 217248524161, 217248524205, 217438712167
ART = 'https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/quantum-theme/art/'

def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(req, context=CTX); t = r.read().decode()
        return r.status, (json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

def mod_row(name, label, params):
    p = dict(params); p['css_class'] = 'dnd-module'
    m = {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "label": label, "name": name,
         "params": p, "rowMetaData": [], "rows": [], "type": "module", "w": 0, "x": 0}
    return {"0": {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "name": "c_" + name,
                  "params": {"css_class": "dnd-column"}, "rowMetaData": [], "rows": [{"0": m}], "w": 0, "x": 0}}

def rt(name, prose, maxw="full"):
    return mod_row(name, 'quantum-rich-text', {"maxw": maxw, "module_id": RT_ID, "prose": prose})

# ---- service wheel SVG ----
SEGS = [
    ("Q2 Platform", "/q2-revenue-machine"),
    ("HubSpot", "/hubspot-build"),
    ("Sales & Outbound", "/outbound-sales"),
    ("AI", "/ai-solutions"),
    ("Marketing", "/marketing-services"),
]
def pol(cx, cy, r, deg):
    rad = math.radians(deg)
    return (round(cx + r * math.cos(rad), 1), round(cy + r * math.sin(rad), 1))
def seg_path(cx, cy, R, r, a0, a1):
    x0, y0 = pol(cx, cy, R, a0); x1, y1 = pol(cx, cy, R, a1)
    x2, y2 = pol(cx, cy, r, a1); x3, y3 = pol(cx, cy, r, a0)
    return f"M{x0},{y0} A{R},{R} 0 0 1 {x1},{y1} L{x2},{y2} A{r},{r} 0 0 0 {x3},{y3} Z"

cx = cy = 300; R, r = 230, 132
parts = []
for i, (label, href) in enumerate(SEGS):
    a0 = -90 + i * 72 + 1.6; a1 = -90 + (i + 1) * 72 - 1.6
    mid = (a0 + a1) / 2
    lx, ly = pol(cx, cy, (R + r) / 2, mid)
    words = label.split(' ')
    if len(words) > 1 and len(label) > 10:
        text = (f'<text x="{lx}" y="{ly-8}" text-anchor="middle" class="qw-lb">{words[0]}</text>'
                f'<text x="{lx}" y="{ly+12}" text-anchor="middle" class="qw-lb">{" ".join(words[1:])}</text>')
    else:
        text = f'<text x="{lx}" y="{ly+5}" text-anchor="middle" class="qw-lb">{label}</text>'
    parts.append(f'<a href="{href}"><path class="qw-seg" d="{seg_path(cx,cy,R,r,a0,a1)}"></path>{text}</a>')

wheel = ('<style>.qw-seg{fill:#101725;stroke:rgba(196,164,74,.45);stroke-width:1.2;transition:fill .18s}'
 'a:hover .qw-seg{fill:rgba(196,164,74,.22)}'
 '.qw-lb{fill:#e2e5eb;font-size:19px;font-weight:600;font-family:inherit;pointer-events:none}</style>'
 f'<svg viewBox="0 0 600 600" style="max-width:560px;width:100%;display:block;margin:0 auto" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Quantum services wheel">'
 f'{"".join(parts)}'
 f'<circle cx="300" cy="300" r="112" fill="#0d1320" stroke="#c4a44a" stroke-width="1.4"/>'
 f'<text x="300" y="290" text-anchor="middle" style="font-family:var(--q-serif,Georgia),serif;font-size:64px;fill:#c4a44a">Q</text>'
 f'<text x="300" y="330" text-anchor="middle" style="fill:#8a8f9b;font-size:13px;letter-spacing:3px">ONE REVENUE ENGINE</text>'
 '</svg>')

def gcard(title, href, items):
    lis = ''.join(f'<a href="{h}" style="display:block;padding:4px 0;color:var(--fg-muted);text-decoration:none;font-size:14px">{t}</a>' for t, h in items)
    return f'<div class=q-card><h4><a href="{href}" style="color:var(--q-gold);text-decoration:none">{title}</a></h4>{lis}</div>'

wheel_section = ('<h2 style="text-align:center">Everything we do, <em>one wheel</em></h2>'
 '<p style="text-align:center;max-width:700px;margin:0 auto 10px">Five practice areas, one connected revenue engine. Click a segment — or start anywhere and we meet you there.</p>'
 + wheel +
 '<div class=q-cards style="margin-top:34px">'
 + gcard('Q2 Platform', '/q2-revenue-machine', [('Q2: The Revenue Machine', '/q2-revenue-machine'), ('Command Apps', '/q2-revenue-machine'), ('Migration guides', '/blog/migrating-from-saleschain-to-hubspot-dealer-guide')])
 + gcard('HubSpot', '/hubspot-build', [('Implementation & Build', '/hubspot-build'), ('Onboarding', '/services/onboarding'), ('Admin as a Service', '/services/hubspot-admin-as-a-services'), ('Portal Audit', '/hubspot-portal-audit'), ('Training', '/hubspot-training'), ('RevOps', '/revops-services'), ('Migrations', '/services/migration')])
 + gcard('Sales & Outbound', '/outbound-sales', [('Outbound Sales', '/outbound-sales'), ('Sales Blitz as a Service', '/sales-blitz-as-a-service'), ('Sales Training', '/b2b-sales-training'), ('ConnectAndSell', '/connect-and-sell'), ('GTM Program', '/services/go-to-market-program'), ('ZoomInfo Consulting', '/zoominfo-as-a-service'), ('Fractional CRO/CMO/CSO', '/fractional-leadership')])
 + gcard('AI', '/ai-solutions', [('AI Solutions', '/ai-solutions'), ('AI Readiness Assessment (Free)', '/ai-readiness-assessment'), ('AI Workforce Assessment', '/ai-workforce-assessment')])
 + gcard('Marketing & Creative', '/marketing-services', [('Marketing Services', '/marketing-services'), ('SEO & AEO Services', '/seo-aeo-services'), ('Website Design', '/website-services'), ('The Quantum Tech Stack', '/tech-stack')])
 + '</div>')

doors = ('<h2 style="text-align:center">Three easy ways to <em>start</em></h2><div class=q-cards>'
 '<div class=q-card><span style="display:inline-block;border:1px solid rgba(196,164,74,.5);border-radius:999px;padding:4px 14px;font-size:11px;letter-spacing:2px;color:var(--q-gold);margin-bottom:12px">FREE</span>'
 '<h4>AEO Health Check</h4><p>Is AI citing your company? Five-dimension audit with a report in minutes.</p><p><a href="/en/aeo-health-check">Run it free &rarr;</a></p></div>'
 '<div class=q-card><span style="display:inline-block;border:1px solid rgba(196,164,74,.5);border-radius:999px;padding:4px 14px;font-size:11px;letter-spacing:2px;color:var(--q-gold);margin-bottom:12px">$1,497</span>'
 '<h4>HubSpot Assessment</h4><p>A focused portal review with prioritized findings — know exactly where you stand.</p><p><a href="/hubspot-portal-audit">See the audit &rarr;</a></p></div>'
 '<div class=q-card><span style="display:inline-block;border:1px solid rgba(196,164,74,.5);border-radius:999px;padding:4px 14px;font-size:11px;letter-spacing:2px;color:var(--q-gold);margin-bottom:12px">$2,500</span>'
 '<h4>GTM Assessment</h4><p>Your go-to-market strategy audited: ICP, messaging, channels, and competitive position.</p><p><a href="/services/go-to-market-program">See the program &rarr;</a></p></div></div>')

quote = ('<div style="max-width:760px;margin:0 auto;text-align:center;padding:10px 0">'
 '<div style="width:44px;height:2px;background:var(--q-gold);margin:0 auto 26px"></div>'
 '<p style="font-family:var(--q-serif);font-size:26px;line-height:1.45;color:var(--fg);margin:0 0 18px">&ldquo;Our experience has been wonderful. Quantum is a well-run company from top to bottom&hellip; A pleasure to work with.&rdquo;</p>'
 '<p style="color:var(--q-gold);margin:0;font-weight:600">Joe Blatchford</p>'
 '<p style="color:var(--fg-muted);margin:4px 0 0;font-size:14px">QBS client</p></div>')

rows = [
 mod_row('ov_hero', 'quantum-hero', {
   "bg_art": {"alt": "", "src": ART + 'hero-signal.svg'},
   "eyebrow": "Quantum Business Solutions", "layout": "centered",
   "heading": "We Build <em>Revenue Machines</em>",
   "subhead": "Strategy, HubSpot, outbound, AI, and marketing — engineered into one connected system by people who run them every day. This page is the whole company on one screen.",
   "primary_label": "Book a Call",
   "secondary_label": "See Pricing", "secondary_url": {"href": "/pricing", "type": "EXTERNAL"},
   "module_id": HERO_ID}),
 mod_row('ov_bridge', 'Quantum Pain Bridge (pain / system / outcome)', {"module_id": BRIDGE_ID}),
 mod_row('ov_stats', 'quantum-stats-band', {"module_id": STATS_ID}),
 rt('ov_wheel', wheel_section),
 rt('ov_doors', doors),
 rt('ov_quote', quote),
 mod_row('ov_cta', 'quantum-cta-band', {
   "heading": "One call. The whole machine.",
   "subhead": "Thirty minutes with Shawn — we'll find the highest-leverage place to start.",
   "cta_label": "Book with Shawn", "module_id": CTA_ID}),
]

scaffold = json.load(open(S + 'seo_aeo_scaffold.json'))
main = copy.deepcopy(scaffold['layoutSections']['main'])
main['rows'] = rows

st, res = api('GET', BASE + '?slug=quantum-overview')
if isinstance(res, dict) and res.get('total', 0) > 0:
    pid = res['results'][0]['id']; print('exists', pid)
else:
    st, res = api('POST', BASE, {"name": "Quantum Overview", "slug": "quantum-overview",
                                 "templatePath": "Quantum Void/templates/mv-shell.html", "state": "DRAFT"})
    pid = res['id']; print('created', pid)
st, _ = api('PATCH', f'{BASE}/{pid}/draft', {
    "layoutSections": {"main": main},
    "htmlTitle": "Quantum Business Solutions — The One-Page Overview",
    "metaDescription": "Everything Quantum does on one page: the Q2 platform, HubSpot services, sales & outbound, AI, and marketing — one connected revenue engine, with three easy ways to start."})
print('draft patch:', st)
now = (datetime.datetime.utcnow() + datetime.timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
st, r = api('POST', BASE + '/schedule', {"id": pid, "publishDate": now})
print('publish:', st, r if st not in (200, 204) else 'ok')
print('PAGE_ID', pid)
