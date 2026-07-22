#!/usr/bin/env python3
"""Copier Dealer AEO Guide landing page — converted from the Claude Design doc."""
import json, urllib.request, ssl, copy, datetime

S = '/tmp/claude-0/-home-user-Claude/afaaa5d3-2de0-5da2-9bf3-affd4e8c30f7/scratchpad/'
TOKEN = [l.split('=', 1)[1].strip() for l in open(S + 'hs_env') if 'HS_TOKEN' in l][0]
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
BASE = 'https://api.hubapi.com/cms/v3/pages/landing-pages'
HERO, RT, CTA, ROAD = 217248524134, 217248524682, 217248524161, 217324784732

def api(m, u, b=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(u, data=d, method=m, headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    try:
        x = urllib.request.urlopen(r, context=CTX); t = x.read().decode()
        return x.status, (json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

def mod_row(name, label, params):
    p = dict(params); p['css_class'] = 'dnd-module'
    m = {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "label": label, "name": name, "params": p,
         "rowMetaData": [], "rows": [], "type": "module", "w": 0, "x": 0}
    return {"0": {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "name": "c_" + name,
                  "params": {"css_class": "dnd-column"}, "rowMetaData": [], "rows": [{"0": m}], "w": 0, "x": 0}}
def rt(name, prose): return mod_row(name, 'quantum-rich-text', {"maxw": "full", "module_id": RT, "prose": prose})

TH = 'text-align:left;font-weight:700;color:var(--q-gold);font-size:11px;letter-spacing:.1em;text-transform:uppercase;padding:11px 14px;border-bottom:1px solid rgba(196,164,74,.28)'
TD = 'padding:11px 14px;border-bottom:1px solid rgba(196,164,74,.12);color:var(--fg-muted);vertical-align:top'
TDW = 'padding:11px 14px;border-bottom:1px solid rgba(196,164,74,.12);color:var(--fg);vertical-align:top'
CHIP = 'display:inline-block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--q-gold);font-weight:700;margin-bottom:8px'

rows = [
 mod_row('ag_hero', 'quantum-hero', {
   "eyebrow": "A Quantum Playbook", "layout": "centered",
   "heading": "The Copier Dealer's Guide to <em>AEO</em>",
   "subhead": "How office-equipment and managed-print dealers become the answer that AI engines cite. Search is being replaced by answers — this is the field guide to winning that shift.",
   "primary_label": "Run Your Free AEO Health Check",
   "primary_url": {"href": "https://www.thequantumleap.business/en/aeo-health-check", "type": "EXTERNAL"},
   "secondary_label": "Book a Strategy Call",
   "secondary_url": {"href": "https://meetings.hubspot.com/shawn-peterson", "type": "EXTERNAL"},
   "module_id": HERO}),

 rt('ag_whynow',
   '<h2 style="text-align:center">Your buyers stopped searching. They started <em>asking.</em></h2>'
   '<p style="text-align:center;max-width:720px;margin:0 auto">An IT director no longer types &ldquo;managed print services Jacksonville&rdquo; and scrolls ten blue links. They ask ChatGPT, Gemini, or Google’s AI Overview a full question — and read the answer it assembles. If your dealership is not in that answer, you were never in the room. Answer Engine Optimization (AEO) is how you get cited: same discipline as SEO, new surface.</p>'
   '<div class=q-cards style="margin-top:26px">'
   '<div class=q-card><p style="font-family:var(--q-serif);font-size:30px;color:var(--q-gold);margin:0 0 10px">Search</p><p style="margin:0">Ten links — the user does the work of comparing and deciding.</p></div>'
   '<div class=q-card><p style="font-family:var(--q-serif);font-size:30px;color:var(--q-gold);margin:0 0 10px">Answers</p><p style="margin:0">One synthesized response citing a handful of trusted sources.</p></div>'
   '<div class=q-card style="border-left:3px solid var(--q-gold)"><p style="font-family:var(--q-serif);font-size:30px;color:var(--q-gold);margin:0 0 10px">The gap</p><p style="margin:0">Most dealers publish product pages. Engines cite guides. That gap is the opportunity.</p></div></div>'),

 rt('ag_engines',
   '<h2 style="text-align:center">An engine <em>decomposes</em> a question before it answers it</h2>'
   '<p style="text-align:center;max-width:720px;margin:0 auto 22px">When someone asks a broad question, the engine breaks it into sub-questions, retrieves the best-sourced answer to each, and stitches them together with citations. Winning AEO means being the cleanest, best-structured answer to each sub-question.</p>'
   '<div class="q-cards q-cards-2">'
   '<div class=q-card><h4>Direct answers</h4><p>A 40-to-60-word response in the first paragraph, before any preamble.</p></div>'
   '<div class=q-card><h4>Structure</h4><p>Clear headings, Q&amp;A blocks, lists, and tables the machine can parse.</p></div>'
   '<div class=q-card><h4>Entity clarity</h4><p>Schema and consistent naming so the engine knows exactly who you are.</p></div>'
   '<div class=q-card><h4>Authority</h4><p>Citations, reviews, and links that signal you can be trusted.</p></div></div>'),

 rt('ag_blindspot',
   '<h2 style="text-align:center">You sell managed print. You rank for <em>cartridges.</em></h2>'
   '<p style="text-align:center;max-width:720px;margin:0 auto 8px">Almost every copier dealer we audit shows the same pattern: the whole search footprint is transactional product terms, while the buyers who sign MPS contracts — the CFO, the IT director, the office manager — find nothing. The fix is not more product pages. It is answer content aimed at the people who actually buy.</p>'
   '<div style="overflow-x:auto"><table style="width:100%;max-width:880px;margin:18px auto 0;border-collapse:collapse;font-size:14px">'
   f'<tr><th style="{TH}">What dealers usually rank for</th><th style="{TH}">Who actually signs the contract</th></tr>'
   f'<tr><td style="{TD}">&ldquo;hp414a toner&rdquo;, &ldquo;best document scanner&rdquo;, &ldquo;canon copier&rdquo;</td><td style="{TDW}">&ldquo;What is managed print services?&rdquo;</td></tr>'
   f'<tr><td style="{TD}">Researchers and one-off cartridge buyers</td><td style="{TDW}">&ldquo;How do we reduce office printing costs?&rdquo; (CFO)</td></tr>'
   f'<tr><td style="{TD}">Bottom-value, transactional intent</td><td style="{TDW}">&ldquo;Are office printers a security risk?&rdquo; (IT / compliance)</td></tr>'
   f'<tr><td style="{TD}"></td><td style="{TDW}">&ldquo;How do I choose an MPS provider?&rdquo; (ready to buy)</td></tr>'
   '</table></div>'),

 rt('ag_trees',
   '<h2 style="text-align:center">Six question trees every dealer should <em>own</em></h2>'
   '<p style="text-align:center;max-width:720px;margin:0 auto 22px">Each tree starts with a root question a real buyer asks, then branches into the sub-questions engines decompose it into. Publish a genuine answer to each leaf and you become the cited source. Swap the city and brand names and this maps onto any dealer.</p>'
   '<div class="q-cards q-cards-2">'
   f'<div class=q-card><span style="{CHIP}">Tree 1 &middot; CFO / Ops &middot; cost control</span><h4 style="font-family:var(--q-serif);font-weight:400">&ldquo;How much should our business spend on printing?&rdquo;</h4><p style="font-size:13px">how much does office printing really cost &middot; how do we reduce printing costs &middot; how much does managed print save (typical %)</p></div>'
   f'<div class=q-card><span style="{CHIP}">Tree 2 &middot; IT Director &middot; relief</span><h4 style="font-family:var(--q-serif);font-weight:400">&ldquo;How do I stop printers eating my IT team’s time?&rdquo;</h4><p style="font-size:13px">what is managed print services (MPS) &middot; what does MPS include &middot; managed print vs. buying outright &middot; why so many printer help-desk tickets</p></div>'
   f'<div class=q-card><span style="{CHIP}">Tree 3 &middot; IT / Compliance &middot; security</span><h4 style="font-family:var(--q-serif);font-weight:400">&ldquo;Are office printers a security risk?&rdquo;</h4><p style="font-size:13px">can a network printer be hacked &middot; how do I secure office printers &middot; HIPAA printing requirements &middot; document security for law firms</p></div>'
   f'<div class=q-card><span style="{CHIP}">Tree 4 &middot; Ops / IT &middot; workflow</span><h4 style="font-family:var(--q-serif);font-weight:400">&ldquo;How do we move from paper to digital workflows?&rdquo;</h4><p style="font-size:13px">how to scan a document &middot; what is an ADF &middot; how to choose a document scanner &middot; document management basics</p></div>'
   f'<div class=q-card><span style="{CHIP}">Tree 5 &middot; All buyers &middot; vendor selection</span><h4 style="font-family:var(--q-serif);font-weight:400">&ldquo;Who’s the best copier / printer provider near me?&rdquo;</h4><p style="font-size:13px">copier dealer near me &middot; how do I choose an MPS provider &middot; copier lease vs. buy &middot; where to buy toner locally</p></div>'
   f'<div class=q-card><span style="{CHIP}">Tree 6 &middot; Transactional bridge &middot; consumables</span><h4 style="font-family:var(--q-serif);font-weight:400">&ldquo;How do I handle printer toner and ink?&rdquo;</h4><p style="font-size:13px">how to change / replace toner (by brand) &middot; what is printer toner &middot; how to recycle toner &rarr; take-back program</p></div>'
   '</div>'),

 rt('ag_flows',
   '<h2 style="text-align:center">Seven repeatable content <em>flows</em></h2>'
   '<p style="text-align:center;max-width:720px;margin:0 auto 8px">The trees tell you what to publish. These flows are how you produce it, over and over, by swapping the inputs.</p>'
   '<div style="overflow-x:auto"><table style="width:100%;max-width:880px;margin:18px auto 0;border-collapse:collapse;font-size:14px">'
   f'<tr><th style="{TH};width:36%">Flow</th><th style="{TH}">What it produces</th></tr>'
   f'<tr><td style="{TDW}">1 &middot; Question Harvest &rarr; Answer Block</td><td style="{TD}">Question keywords become 40-to-60-word answers with FAQPage schema, built to capture People-Also-Ask.</td></tr>'
   f'<tr><td style="{TDW}">2 &middot; Thin Page &rarr; Best-of Guide</td><td style="{TD}">Turn product grids into genuinely reviewed guides with ItemList, Product, and FAQ schema.</td></tr>'
   f'<tr><td style="{TDW}">3 &middot; Consumables How-To Engine</td><td style="{TD}">Toner and ink how-tos with HowTo schema and a buy / service CTA on every page.</td></tr>'
   f'<tr><td style="{TDW}">4 &middot; Entity &amp; Schema Hygiene</td><td style="{TD}">Organization / LocalBusiness schema, clean titles, consistent NAP, and Google Business Profile.</td></tr>'
   f'<tr><td style="{TDW}">5 &middot; AI-Citation Monitoring</td><td style="{TD}">Track who gets cited across engines, month over month, against named competitors.</td></tr>'
   f'<tr><td style="{TDW}">6 &middot; Keyword-Gap &rarr; Backlog</td><td style="{TD}">Mine competitor footprints for low-difficulty terms and turn them into a content backlog.</td></tr>'
   f'<tr><td style="{TDW}">7 &middot; Local AEO</td><td style="{TD}">&ldquo;Near me&rdquo; content, Local Pack presence, and GBP Q&amp;A for each dealer’s region.</td></tr>'
   '</table></div>'),

 rt('ag_schema',
   '<h2 style="text-align:center">Make the machine <em>sure</em> of who you are</h2>'
   '<p style="text-align:center;max-width:720px;margin:0 auto 22px">Great answers still lose if the engine cannot identify or trust the source. Two foundations make dealer content citable.</p>'
   '<div class="q-cards q-cards-2">'
   '<div class=q-card><h4>Structured data</h4><p>Organization / LocalBusiness on the homepage and contact page &middot; FAQPage on every guide and service page &middot; HowTo on every consumables tutorial &middot; Product / ItemList on best-of and comparison guides.</p></div>'
   '<div class=q-card><h4>Entity clarity</h4><p>One consistent name, address, and phone everywhere &middot; sameAs links to GBP, LinkedIn, and industry directories &middot; disambiguate name collisions &middot; a real &ldquo;about&rdquo; entity page the engine can anchor to.</p></div></div>'),

 rt('ag_measure',
   '<h2 style="text-align:center">AEO has a <em>scoreboard</em>. Use it.</h2>'
   '<p style="text-align:center;max-width:720px;margin:0 auto 8px">Most dealers start at zero citations — which makes progress easy to prove. Track these monthly against a named competitor set.</p>'
   '<div style="overflow-x:auto"><table style="width:100%;max-width:880px;margin:18px auto 0;border-collapse:collapse;font-size:14px">'
   f'<tr><th style="{TH}">Metric</th><th style="{TH}">What it tells you</th></tr>'
   f'<tr><td style="{TDW}">AI-Overview presence</td><td style="{TD}">How often you appear in Google’s AI answer for target questions.</td></tr>'
   f'<tr><td style="{TDW}">People-Also-Ask ownership</td><td style="{TD}">How many PAA boxes your content answers.</td></tr>'
   f'<tr><td style="{TDW}">Engine citations</td><td style="{TD}">Mentions in ChatGPT, Perplexity, and Gemini on buyer questions.</td></tr>'
   f'<tr><td style="{TDW}">Referring domains</td><td style="{TD}">Authority trend — the long-game lever behind citability.</td></tr>'
   f'<tr><td style="{TDW}">Non-branded question rankings</td><td style="{TD}">Positions on the tree questions, not just product terms.</td></tr>'
   '</table></div>'),

 mod_row('ag_road', 'Process roadmap', {
   "module_id": ROAD, "axis_labels": "Day 0,Day 30,Day 60,Day 90",
   "eyebrow": "Putting it to work", "heading": "The first 90 days",
   "intro": "Quick wins land first and compound while the structural and authority work builds underneath.",
   "steps": [
     {"chip": "Days 0-30", "title": "Quick Wins", "desc": "FAQ schema on scanner and toner pages, three consumables how-tos with CTAs, entity signals fixed, and the “What is Managed Print Services?” cornerstone published."},
     {"chip": "Days 30-90", "title": "Structural", "desc": "Rebuild the thinnest ranking page into a real guide and clone the pattern; stand up the MPS-buyer question trees as cornerstone content; clean up entity collisions."},
     {"chip": "Ongoing", "title": "Authority", "desc": "Earn citations through directories, B2B listings, and digital PR; Product schema across guides; localized pages and Google Business Profile."},
     {"chip": "Monthly", "title": "Measure", "desc": "Track AI citations against the baseline of zero — and against named competitors. Progress is visible fast because the category is wide open."}]}),

 rt('ag_checklist',
   '<h2 style="text-align:center">Is this dealer ready to be <em>cited?</em></h2>'
   '<div class="q-cards q-cards-2" style="margin-top:22px">'
   '<div class=q-card><p style="margin:0">&#9633;&nbsp; Homepage has Organization / LocalBusiness schema<br><br>&#9633;&nbsp; Every service page opens with a 40-60 word direct answer<br><br>&#9633;&nbsp; FAQ schema on all guides and service pages<br><br>&#9633;&nbsp; A &ldquo;What is MPS?&rdquo; category cornerstone exists</p></div>'
   '<div class=q-card><p style="margin:0">&#9633;&nbsp; Consumables how-tos with HowTo schema and CTAs<br><br>&#9633;&nbsp; Consistent NAP across site, GBP, and directories<br><br>&#9633;&nbsp; Content targets CFO, IT, and ops buyers — not just shoppers<br><br>&#9633;&nbsp; Monthly AI-citation tracking is in place</p></div></div>'
   '<div class=q-card style="max-width:880px;margin:18px auto 0;border-left:3px solid var(--q-gold)"><p style="margin:0"><strong style="color:var(--fg)">The takeaway.</strong> Dealers who publish answers, not just products, become the source AI engines trust. The category is wide open — the first mover in each market wins it.</p></div>'
   '<p style="text-align:center;margin-top:26px;color:var(--fg-muted)">Go deeper: <a href="/seo-aeo-services">our SEO &amp; AEO services</a> &middot; <a href="/q2-revenue-machine">Q2 for dealers</a> &middot; <a href="/blog/what-is-aeo-answer-engine-optimization-guide">the complete AEO guide</a></p>'),

 mod_row('ag_cta', 'quantum-cta-band', {
   "heading": "Find out if AI engines cite your dealership today.",
   "subhead": "Run the free AEO Health Check — schema, llms.txt, content signals, and live citation tests across ChatGPT, Perplexity, and Gemini. Report in minutes.",
   "cta_label": "Run the free Health Check",
   "cta_url": {"href": "https://www.thequantumleap.business/en/aeo-health-check", "type": "EXTERNAL"},
   "module_id": CTA}),
]

scaffold = json.load(open(S + 'seo_aeo_scaffold.json'))
main = copy.deepcopy(scaffold['layoutSections']['main']); main['rows'] = rows
st, res = api('GET', BASE + '?slug=copier-dealer-aeo-guide')
if isinstance(res, dict) and res.get('total', 0) > 0:
    pid = res['results'][0]['id']; print('exists', pid)
else:
    st, res = api('POST', BASE, {"name": "The Copier Dealer's Guide to AEO", "slug": "copier-dealer-aeo-guide",
                                 "templatePath": "Quantum Void/templates/mv-shell.html", "state": "DRAFT"})
    pid = res['id']; print('created', pid)
st, _ = api('PATCH', f'{BASE}/{pid}/draft', {
  "layoutSections": {"main": main},
  "htmlTitle": "The Copier Dealer's Guide to AEO | Quantum Business Solutions",
  "metaDescription": "How copier, office-equipment, and managed-print dealers become the answer AI engines cite: buyer question trees, seven content flows, schema foundations, and a 90-day rollout."})
print('patch:', st)
now = (datetime.datetime.utcnow() + datetime.timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
st, r = api('POST', BASE + '/schedule', {"id": pid, "publishDate": now})
print('publish:', st, r if st not in (200, 204) else 'ok')
print('PAGE_ID', pid)
