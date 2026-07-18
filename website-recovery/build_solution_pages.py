#!/usr/bin/env python3
"""Build 5 new Void landing pages: audit, training, revops, fractional, tech-stack."""
import json, urllib.request, ssl, copy, sys

S = '/tmp/claude-0/-home-user-Claude/afaaa5d3-2de0-5da2-9bf3-affd4e8c30f7/scratchpad/'
TOKEN = [l.split('=', 1)[1].strip() for l in open(S + 'hs_env') if 'HS_TOKEN' in l][0]
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
BASE = 'https://api.hubapi.com/cms/v3/pages/landing-pages'

def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(req, context=CTX)
        txt = r.read().decode()
        return r.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]

HERO_ID, RT_ID, CTA_ID, ROAD_ID = 217248524134, 217248524682, 217248524161, 217324784732
ART = 'https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/quantum-theme/art/'

def mod(name, label, params):
    p = dict(params); p['css_class'] = 'dnd-module'
    return {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "label": label,
            "name": name, "params": p, "rowMetaData": [], "rows": [], "type": "module", "w": 0, "x": 0}

def row(colname, m):
    return {"0": {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "name": colname,
                  "params": {"css_class": "dnd-column"}, "rowMetaData": [],
                  "rows": [{"0": m}], "w": 0, "x": 0}}

def price_row(title, desc, price, href='/pricing'):
    return (f'<a href="{href}" style="display:grid;grid-template-columns:1fr auto;gap:8px 40px;align-items:baseline;'
            f'padding:16px 6px;border-top:1px solid rgba(196,164,74,.14);text-decoration:none;">'
            f'<span><strong style="color:var(--fg);font-size:16px">{title}</strong>'
            f'<span style="display:block;margin-top:4px;color:var(--fg-muted);font-size:14px;max-width:640px">{desc}</span></span>'
            f'<span style="font-family:var(--q-serif);font-size:19px;color:var(--q-gold);white-space:nowrap">{price}</span></a>')

def faq_html(items):
    h = '<h2>Frequently Asked Questions</h2><div class="q-faq">'
    for q, a in items:
        h += f'<details class="q-faq-item"><summary>{q}</summary><div class="q-faq-a">{a}</div></details>'
    return h + '</div>'

def faq_schema(items):
    ents = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]
    return ('<script type="application/ld+json">' +
            json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": ents}) + '</script>')

def card(h, p): return f'<div class=q-card><h4>{h}</h4><p>{p}</p></div>'

scaffold = json.load(open(S + 'seo_aeo_scaffold.json'))
main_shell = copy.deepcopy(scaffold['layoutSections']['main'])

PAGES = []

# ---------- 1. HubSpot Portal Audit ----------
faq_audit = [
 ("What does the HubSpot audit cover?",
  "Everything that makes a portal produce revenue: data quality and duplicates, workflows and automation, reporting and attribution, integrations, pipeline configuration, team adoption, and permissions. You get a prioritized findings report and a remediation roadmap."),
 ("How long does an audit take?",
  "The focused Assessment typically wraps in about a week. The deep-dive Audit usually runs about two weeks from access to readout, depending on portal size."),
 ("What do you need from us?",
  "Admin access to the portal (view-only works for most of the audit) and a short kickoff call so we understand how your team actually uses HubSpot. That's it — your team keeps working while we dig."),
 ("What's the difference between the Assessment and the Audit?",
  "The Assessment is a focused portal review with prioritized findings — the fast way to know where you stand. The deep-dive Audit is a full-portal teardown across data, automation, reporting, integrations, and adoption, with a step-by-step remediation roadmap."),
 ("What happens after the audit?",
  "You own the roadmap. Your team can execute it, or we can fix it for you with discounted blocks of expert hours or ongoing Admin-as-a-Service. Either way, the findings are written so they're actionable, not academic."),
]
audit_rows = [
 row('c_aud_hero', mod('aud_hero', 'quantum-hero', {
   "bg_art": {"alt": "", "src": ART + 'hero-signal.svg'},
   "eyebrow": "HubSpot Portal Audit", "layout": "centered",
   "heading": "You're Paying for HubSpot. Is HubSpot <em>Paying You Back?</em>",
   "subhead": "Most portals we open have the same leaks: dirty data, dead workflows, reports nobody trusts, and licenses nobody uses. We manage HubSpot portals every single day — an audit tells you exactly where yours is leaking revenue, and how to fix it.",
   "primary_label": "Book an Audit Call",
   "secondary_label": "See Pricing", "secondary_url": {"href": "#audit-pricing", "type": "EXTERNAL"},
   "module_id": HERO_ID})),
 row('c_aud_dims', mod('aud_dims', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<h2 style="text-align:center">What we tear down — <em>six dimensions</em></h2><div class=q-cards>' +
   card('Data Quality', 'Duplicates, dead contacts, broken properties, and lifecycle stages that don’t mean anything. Your CRM is only as good as the data your team trusts.') +
   card('Workflows & Automation', 'Every active workflow reviewed: what’s firing, what’s broken, what’s silently emailing prospects from a rep who left in 2023.') +
   card('Reporting & Attribution', 'Do your dashboards answer the questions leadership actually asks? We rebuild the reporting layer around decisions, not vanity metrics.') +
   card('Integrations', 'ZoomInfo, ConnectAndSell, ERP, billing — every connection checked for sync errors, field mismatches, and duplicate-generating loops.') +
   card('Pipeline & Process', 'Deal stages, required fields, handoffs, and forecast hygiene — does the pipeline reflect reality, or what reps remember to type?') +
   card('Adoption & Permissions', 'Who actually logs in, what seats you’re paying for, and whether your permission sets protect the data or just annoy the team.') + '</div>'})),
 row('c_aud_road', mod('aud_road', 'Process roadmap', {
   "axis_labels": "Day 1,Day 5,Day 10,Day 14", "module_id": ROAD_ID,
   "eyebrow": "The Process", "heading": "From access to action plan in two weeks",
   "intro": "No workshops, no 40-page PDF nobody reads. A teardown, a readout, and a roadmap your team can execute Monday morning.",
   "steps": [
     {"chip": "Day 1", "title": "Kickoff & Access", "desc": "A short call on how your team uses HubSpot today, then view-only admin access. Your team keeps working."},
     {"chip": "Days 2-8", "title": "Portal Teardown", "desc": "We work through all six dimensions — every workflow, report, integration, and data set."},
     {"chip": "Day 10", "title": "Findings Readout", "desc": "Live walkthrough of what we found, ranked by revenue impact — not alphabetical order."},
     {"chip": "Days 10-14", "title": "Remediation Roadmap", "desc": "A prioritized, step-by-step plan. Your team executes it, or we do it for you."}]})),
 row('c_aud_price', mod('aud_price', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<div id="audit-pricing" style="position:relative;top:-90px"></div><h2 style="text-align:center">Transparent <em>pricing</em></h2><div>' +
   price_row('HubSpot Assessment', 'A focused assess-and-audit engagement: portal review with prioritized findings — the fast way to know where you stand.', '$1,497') +
   price_row('HubSpot Audit (Deep-Dive)', 'Full-portal teardown across data, automation, reporting, integrations, pipeline, and adoption — with a prioritized remediation roadmap.', '$7,500') +
   price_row('Remediation Hour Blocks', 'Discounted blocks of expert HubSpot hours (10 to 80 hrs) to fix what the audit finds — or hand the roadmap to your team.', 'from $3,500') +
   '</div><p style="text-align:center;color:var(--fg-muted);margin-top:18px">Already know something’s broken? Skip the audit and go straight to <a href="/services/hubspot-admin-as-a-services">HubSpot Admin as a Service</a>.</p>'})),
 row('c_aud_faq', mod('aud_faq', 'quantum-rich-text', {"maxw": "wide", "module_id": RT_ID, "prose": faq_html(faq_audit)})),
 row('c_aud_cta', mod('aud_cta', 'quantum-cta-band', {
   "heading": "Find the leaks before your competitors do.",
   "subhead": "Book a call — we'll scope the right audit for your portal size and walk you through exactly what you'll get back.",
   "cta_label": "Book a call", "module_id": CTA_ID})),
]
PAGES.append({
 "name": "HubSpot Portal Audit", "slug": "hubspot-portal-audit",
 "htmlTitle": "HubSpot Portal Audit — Find the Revenue Leaks | Quantum Business Solutions",
 "metaDescription": "A full HubSpot portal audit from a team that manages portals daily: data quality, workflows, reporting, integrations, and adoption — with a prioritized fix-it roadmap.",
 "headHtml": faq_schema(faq_audit), "rows": audit_rows})

# ---------- 2. HubSpot Training ----------
faq_train = [
 ("Is the training generic HubSpot content or specific to our portal?",
  "Specific to your portal. Sessions are live and interactive, built around your actual pipelines, workflows, and reports — not generic slides. Your team leaves knowing how to do their job in your HubSpot, not a demo account."),
 ("Who should attend?",
  "Whoever touches HubSpot: sales reps, marketers, service teams, and admins. We tailor sessions by role — a rep session looks nothing like an admin session, and that's the point."),
 ("What if we need ongoing help after training?",
  "Monthly HubSpot User Group Coaching keeps a standing session on the calendar for questions as they come up, and HubSpot Admin as a Service covers the ongoing hands-on work."),
 ("What is Quantum Academy?",
  "Our self-paced online training platform with on-demand courses your team can work through anytime — a complement to live training, not a replacement for it."),
 ("Can you train us on the tools connected to HubSpot too?",
  "Yes. We also run dedicated ZoomInfo training, and we work daily with ConnectAndSell, e-automate integrations, and the rest of the modern revenue stack."),
]
train_rows = [
 row('c_trn_hero', mod('trn_hero', 'quantum-hero', {
   "bg_art": {"alt": "", "src": ART + 'hero-signal.svg'},
   "eyebrow": "HubSpot Training", "layout": "centered",
   "heading": "Your Team Uses 10% of HubSpot. Unlock the <em>Other 90%.</em>",
   "subhead": "HubSpot doesn't fail — adoption does. We train your team in your portal, on your pipelines, around the way you actually sell. Live sessions, monthly coaching, and self-paced Academy courses.",
   "primary_label": "Book a Training Call",
   "secondary_label": "Enroll in Quantum Academy",
   "secondary_url": {"href": "https://webservices.lightspeedvt.net/regform/register.aspx?linkid=B36EEFE3C48B02587B912B814114415A", "type": "EXTERNAL"},
   "module_id": HERO_ID})),
 row('c_trn_fmt', mod('trn_fmt', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<h2 style="text-align:center">Training that fits how your team <em>learns</em></h2><div class=q-cards>' +
   card('Live Team Training', 'Role-based sessions built around your portal — reps learn selling motions, marketers learn campaigns and reporting, admins learn to keep it all running.') +
   card('Monthly Group Coaching', 'A standing HubSpot User Group session every month. Bring real questions, screen-share real problems, leave with real answers.') +
   card('Quantum Academy', 'Self-paced, on-demand courses your team works through anytime. New hires onboard without pulling your best people off the floor.') +
   card('Strategy Sessions', 'One hour with a senior consultant to untangle a specific problem — reporting, automation, pipeline design — before it costs you a quarter.') +
   card('ZoomInfo & Stack Training', 'HubSpot doesn’t work alone. We train teams on ZoomInfo, ConnectAndSell, and the rest of the connected revenue stack.') +
   card('Train the Admin', 'We coach your internal admin to run the portal with confidence — and back them up when they get stuck.') + '</div>'})),
 row('c_trn_price', mod('trn_price', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<div id="training-pricing" style="position:relative;top:-90px"></div><h2 style="text-align:center">Transparent <em>pricing</em></h2><div>' +
   price_row('HubSpot Team Training', 'Live, role-based training session built around your portal and your process.', '$1,497') +
   price_row('HubSpot User Group Coaching', 'Monthly group coaching — a standing session for questions, screen-shares, and working sessions.', '$497/mo') +
   price_row('HubSpot Strategy Session', 'One hour, one problem, one senior consultant. Reporting, automation, pipeline — bring your hardest question.', '$497') +
   price_row('ZoomInfo Training', 'Dedicated training on ZoomInfo: search, intent, enrichment, and the workflows that feed your pipeline.', '$1,500') +
   price_row('Quantum Academy', 'Self-paced online courses — enroll your team and let them learn on demand.', 'Enroll', 'https://webservices.lightspeedvt.net/regform/register.aspx?linkid=B36EEFE3C48B02587B912B814114415A') +
   '</div>'})),
 row('c_trn_faq', mod('trn_faq', 'quantum-rich-text', {"maxw": "wide", "module_id": RT_ID, "prose": faq_html(faq_train)})),
 row('c_trn_cta', mod('trn_cta', 'quantum-cta-band', {
   "heading": "Make the tool you already pay for actually pay off.",
   "subhead": "Tell us where your team gets stuck — we'll build the training plan around it.",
   "cta_label": "Book a call", "module_id": CTA_ID})),
]
PAGES.append({
 "name": "HubSpot Training", "slug": "hubspot-training",
 "htmlTitle": "HubSpot Training & Team Enablement | Quantum Business Solutions",
 "metaDescription": "Live HubSpot training in your portal, monthly user-group coaching, strategy sessions, and self-paced Quantum Academy courses. Fix adoption — unlock the tool you already pay for.",
 "headHtml": faq_schema(faq_train), "rows": train_rows})

# ---------- 3. RevOps as a Service ----------
faq_rev = [
 ("What is RevOps, in plain English?",
  "Revenue Operations is the plumbing between marketing, sales, and service: the data, automation, and reporting that turn three departments into one revenue engine. When RevOps is broken, leads leak between teams and nobody trusts the numbers."),
 ("Is this a project or a retainer?",
  "Both. Fixed-price projects cover specific builds — workflow automation, segmentation, list building, ZoomInfo integration. For ongoing ownership of the machine, Admin-as-a-Service retainers keep us in your portal every month."),
 ("What tech stack do you work with?",
  "HubSpot at the center, with the tools revenue teams actually run: ZoomInfo, ConnectAndSell, Orum, Apollo, ERP and billing integrations, and the connectors between them. If it touches your pipeline, we've probably wired it."),
 ("How fast do projects ship?",
  "Most fixed-price RevOps projects — a workflow build, a segmentation overhaul, a ZoomInfo integration — ship in two to four weeks. We scope the timeline before we start, and we hit it."),
 ("Who actually does the work?",
  "Senior consultants who manage HubSpot portals every day — the same team behind our implementations and our Q2 platform for office technology dealers. No handoff to juniors after the sales call."),
]
rev_rows = [
 row('c_rev_hero', mod('rev_hero', 'quantum-hero', {
   "bg_art": {"alt": "", "src": ART + 'hero-signal.svg'},
   "eyebrow": "RevOps as a Service", "layout": "centered",
   "heading": "Marketing, Sales, and Service. <em>One</em> Revenue Engine.",
   "subhead": "Leads leak in the gaps between your teams — the handoffs, the sync errors, the reports that don't agree. We build and run the operations layer that closes those gaps: automation, data, enrichment, and reporting that everyone trusts.",
   "primary_label": "Book a RevOps Call",
   "secondary_label": "See Pricing", "secondary_url": {"href": "#revops-pricing", "type": "EXTERNAL"},
   "module_id": HERO_ID})),
 row('c_rev_what', mod('rev_what', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<h2 style="text-align:center">What we build and <em>run</em></h2><div class=q-cards>' +
   card('Workflow Automation', 'Lead routing, handoffs, follow-up sequences, renewal triggers — automated across your revenue stack so nothing depends on someone remembering.') +
   card('Segmentation & List Building', 'Advanced segmentation strategy plus custom prospect lists built with ZoomInfo, LinkedIn, and proprietary methods — so outreach hits the right accounts.') +
   card('Data Enrichment', 'Full ZoomInfo integration with enrichment workflows: every record complete, current, and ready for reps before they ever pick up the phone.') +
   card('Reporting & Dashboards', 'One version of the truth. Dashboards built around the questions leadership asks — pipeline, velocity, conversion, attribution.') +
   card('Tech-Stack Integration', 'HubSpot connected cleanly to ConnectAndSell, Orum, Apollo, ERP, and billing — without the duplicate-generating sync loops.') +
   card('Ongoing Administration', 'Admin-as-a-Service retainers keep senior operators in your portal every month: maintaining, optimizing, and answering the "can HubSpot do X?" questions.') + '</div>'})),
 row('c_rev_price', mod('rev_price', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<div id="revops-pricing" style="position:relative;top:-90px"></div><h2 style="text-align:center">Transparent <em>pricing</em></h2><div>' +
   price_row('Workflow Automation', 'Design and build automated workflows across your revenue stack.', '$3,500') +
   price_row('List Segmentation', 'Advanced segmentation strategy and implementation for targeted outreach.', '$2,000') +
   price_row('List Building', 'Custom prospect list building using ZoomInfo, LinkedIn, and proprietary methods.', '$1,500') +
   price_row('ZoomInfo Integration', 'Full ZoomInfo integration with your CRM, including enrichment workflows.', '$5,000') +
   price_row('Admin-as-a-Service (Silver)', 'Essential monthly admin support: workflow maintenance, quarterly reviews, email support.', '$2,000/mo', '/services/hubspot-admin-as-a-services') +
   price_row('Admin-as-a-Service (Gold)', 'Mid-tier monthly support: workflow management, monthly reporting, ongoing optimization.', '$3,000/mo', '/services/hubspot-admin-as-a-services') +
   price_row('Admin-as-a-Service (Platinum)', 'Full-service administration: workflows, reporting, integrations, data hygiene, strategic guidance.', '$5,000/mo', '/services/hubspot-admin-as-a-services') +
   '</div><p style="text-align:center;color:var(--fg-muted);margin-top:18px">Not sure what’s broken? Start with a <a href="/hubspot-portal-audit">HubSpot Portal Audit</a> — the findings become the project list.</p>'})),
 row('c_rev_faq', mod('rev_faq', 'quantum-rich-text', {"maxw": "wide", "module_id": RT_ID, "prose": faq_html(faq_rev)})),
 row('c_rev_cta', mod('rev_cta', 'quantum-cta-band', {
   "heading": "Stop losing deals in the gaps between teams.",
   "subhead": "Book a call — we'll map your revenue stack and show you where the leaks are.",
   "cta_label": "Book a call", "module_id": CTA_ID})),
]
PAGES.append({
 "name": "RevOps as a Service", "slug": "revops-services",
 "htmlTitle": "RevOps as a Service — Revenue Operations for HubSpot Teams | Quantum Business Solutions",
 "metaDescription": "Revenue Operations built and run for you: workflow automation, segmentation, ZoomInfo enrichment, reporting, and ongoing HubSpot administration — one revenue engine, one source of truth.",
 "headHtml": faq_schema(faq_rev), "rows": rev_rows})

# ---------- 4. Fractional CRO / CMO / CSO ----------
faq_frac = [
 ("What does a fractional executive actually do?",
  "Everything a full-time CRO, CMO, or CSO does — strategy, team leadership, pipeline accountability, board-level reporting — for a fraction of the cost, on a schedule matched to your stage. You get the experience without the $300K+ salary and equity."),
 ("How is this different from consulting?",
  "A consultant hands you recommendations. A fractional executive owns outcomes: they run the meetings, manage the numbers, coach the team, and answer for the result. It's a seat at your leadership table, not a report."),
 ("CRO vs. CMO vs. CSO — which one do we need?",
  "A CRO owns the whole revenue engine across marketing, sales, and service. A CMO owns demand: brand, content, campaigns, and pipeline creation. A CSO owns the sales organization: process, hiring, coaching, and quota. The 30-Day Assessment usually makes the answer obvious."),
 ("How do engagements start?",
  "Most start with the 30-Day CRO Assessment: a full teardown of your revenue engine that ends with a prioritized plan. From there you pick the level — we tell you what to do, we work alongside your team, or we run it."),
 ("How much of their time do we get?",
  "Engagements are scoped to your stage — typically a fixed weekly rhythm of leadership meetings, pipeline reviews, and working sessions, plus async access in between. We define the cadence together before we start."),
]
frac_rows = [
 row('c_frc_hero', mod('frc_hero', 'quantum-hero', {
   "bg_art": {"alt": "", "src": ART + 'hero-signal.svg'},
   "eyebrow": "Fractional CRO · CMO · CSO", "layout": "centered",
   "heading": "C-Suite Revenue Leadership. <em>Fractional</em> Cost.",
   "subhead": "You need executive-level revenue leadership — the strategy, the accountability, the experience of someone who's done it before. You don't need the $300K salary. Fractional CRO, CMO, and CSO engagements scoped to your stage.",
   "primary_label": "Book a Leadership Call",
   "secondary_label": "See Pricing", "secondary_url": {"href": "#fractional-pricing", "type": "EXTERNAL"},
   "module_id": HERO_ID})),
 row('c_frc_roles', mod('frc_roles', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<h2 style="text-align:center">Three seats. One <em>revenue engine.</em></h2><div class=q-cards>' +
   card('Fractional CRO', 'Owns the whole revenue engine — marketing, sales, and service aligned around one number. Pipeline strategy, forecasting discipline, and the accountability layer between the team and the board.') +
   card('Fractional CMO', 'Executive marketing leadership: positioning, demand generation, content strategy, and a marketing team that ships. Pipeline creation you can measure, not activity you have to admire.') +
   card('Fractional CSO', 'Owns the sales organization: process design, hiring profiles, comp plans, coaching cadence, and quota attainment. Built for teams that have reps but no system.') +
   '</div><p style="text-align:center;margin-top:18px">Every engagement starts with the same question: where does revenue actually break in your business? The 30-Day Assessment answers it with evidence.</p>'})),
 row('c_frc_price', mod('frc_price', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<div id="fractional-pricing" style="position:relative;top:-90px"></div><h2 style="text-align:center">Transparent <em>pricing</em></h2><div>' +
   price_row('CRO 30-Day Assessment', 'A full teardown of your revenue engine — team, process, pipeline, and tooling — ending in a prioritized plan.', '$4,000') +
   price_row('CRO Services — Tell Me', 'We assess, diagnose, and hand you the playbook. Your team executes.', '$3,997') +
   price_row('CRO Services — Help Me', 'We build the plan and work alongside your team to execute it.', '$5,997') +
   price_row('CRO Services — Do It', 'We run it: your fractional revenue leader owns the plan, the meetings, and the number.', '$8,997') +
   price_row('Fractional CMO', 'Executive-level marketing leadership on a monthly fractional basis.', '$7,500/mo') +
   price_row('Fractional CSO', 'Sales organization leadership scoped to your team size and stage.', 'Custom') +
   price_row('GTM Strategic Advisors', 'Weekly strategy sessions, pipeline reviews, and execution coaching — the lighter-weight advisory tier.', '$2,500/mo', '/services/go-to-market-program') +
   '</div>'})),
 row('c_frc_faq', mod('frc_faq', 'quantum-rich-text', {"maxw": "wide", "module_id": RT_ID, "prose": faq_html(faq_frac)})),
 row('c_frc_cta', mod('frc_cta', 'quantum-cta-band', {
   "heading": "Get the executive. Skip the executive search.",
   "subhead": "Book a call — we'll figure out which seat your revenue engine is missing and what filling it looks like.",
   "cta_label": "Book a call", "module_id": CTA_ID})),
]
PAGES.append({
 "name": "Fractional CRO, CMO & CSO", "slug": "fractional-leadership",
 "htmlTitle": "Fractional CRO, CMO & CSO Services | Quantum Business Solutions",
 "metaDescription": "Executive revenue leadership without the executive salary: fractional CRO, CMO, and CSO engagements — from a 30-day assessment to a leader who owns the number.",
 "headHtml": faq_schema(faq_frac), "rows": frac_rows})

# ---------- 5. Tech Stack / Products we sell ----------
def tool_card(name, desc, get_label, get_href, internal=None):
    links = f'<p><a href="{get_href}" rel="sponsored noopener" target="_blank">{get_label} &rarr;</a>'
    if internal:
        links += f'<br><a href="{internal[1]}">{internal[0]} &rarr;</a>'
    links += '</p>'
    return f'<div class=q-card><h4>{name}</h4><p>{desc}</p>{links}</div>'

stack_rows = [
 row('c_stk_hero', mod('stk_hero', 'quantum-hero', {
   "bg_art": {"alt": "", "src": ART + 'hero-signal.svg'},
   "eyebrow": "The Quantum Tech Stack", "layout": "centered",
   "heading": "The Tools We Run <em>Revenue</em> On",
   "subhead": "We don't recommend software we haven't run in the field. These are the platforms we implement, integrate, and manage for clients every day — and where we can get you partner pricing, we will.",
   "primary_label": "Talk Through Your Stack",
   "module_id": HERO_ID})),
 row('c_stk_tools', mod('stk_tools', 'quantum-rich-text', {"maxw": "full", "module_id": RT_ID, "prose":
   '<h2 style="text-align:center">Platforms we sell, implement, and <em>stand behind</em></h2><div class=q-cards>' +
   tool_card('HubSpot', 'The CRM at the center of everything we build — marketing, sales, service, and content on one platform. We’re a HubSpot partner: implementation, onboarding, and admin are our core business.', 'Get HubSpot', 'https://www.hubspot.com', ('Our HubSpot services', '/hubspot-build')) +
   tool_card('ZoomInfo', 'B2B contact and company intelligence: who to call, when, and why. We integrate it, train on it, and run it as a managed service.', 'Get ZoomInfo', 'https://www.zoominfo.com', ('ZoomInfo as a Service', '/zoominfo-as-a-service')) +
   tool_card('ConnectAndSell', 'Live conversation acceleration — 8 to 12 decision-maker conversations per rep per hour instead of 8 to 12 dials. The engine behind our Sales Blitz program.', 'Get ConnectAndSell', 'https://connectandsell.com', ('ConnectAndSell services', '/connect-and-sell')) +
   tool_card('Orum', 'AI-powered parallel dialer that lives inside your CRM — more live connects for teams that want dialing velocity without leaving HubSpot.', 'Get Orum', 'https://www.orum.com') +
   tool_card('Apollo', 'All-in-one prospecting: contact data, sequencing, and outreach in one tool — a strong fit for lean teams building their first outbound motion.', 'Get Apollo', 'https://www.apollo.io') +
   '<div class=q-card><h4>Your stack, wired together</h4><p>Owning the tools is step one. Making them talk to each other — cleanly, without duplicate loops — is where the payoff is. That’s our job.</p><p><a href="/revops-services">RevOps as a Service &rarr;</a></p></div>' +
   '</div><p style="text-align:center;color:var(--fg-muted);font-size:13px;margin-top:22px">Disclosure: some links on this page are partner links — we may earn a commission if you purchase through them, at no extra cost to you. We only list tools we use with clients.</p>'})),
 row('c_stk_cta', mod('stk_cta', 'quantum-cta-band', {
   "heading": "Not sure what belongs in your stack?",
   "subhead": "Book a call — we'll look at what you're paying for today, what's missing, and what should be cut.",
   "cta_label": "Book a call", "module_id": CTA_ID})),
]
PAGES.append({
 "name": "The Quantum Tech Stack", "slug": "tech-stack",
 "htmlTitle": "Sales & Marketing Tech We Sell and Recommend | Quantum Business Solutions",
 "metaDescription": "The revenue tools we implement and manage for clients every day — HubSpot, ZoomInfo, ConnectAndSell, Orum, Apollo — with partner links and the services that make them work together.",
 "headHtml": "", "rows": stack_rows})

# ---------- create + fill ----------
results = []
for p in PAGES:
    st, r = api('GET', BASE + '?slug=' + p['slug'])
    if isinstance(r, dict) and r.get('total', 0) > 0:
        pid = r['results'][0]['id']
        print(p['slug'], 'exists already, id', pid)
    else:
        st, r = api('POST', BASE, {"name": p['name'], "slug": p['slug'],
                                   "templatePath": "Quantum Void/templates/mv-shell.html", "state": "DRAFT"})
        if st not in (200, 201):
            print('CREATE FAIL', p['slug'], st, r); continue
        pid = r['id']
        print('created', p['slug'], pid)
    ls = copy.deepcopy(main_shell)
    ls['rows'] = p['rows']
    body = {"layoutSections": {"main": ls}, "htmlTitle": p['htmlTitle'],
            "metaDescription": p['metaDescription']}
    if p['headHtml']:
        body['headHtml'] = p['headHtml']
    st, r = api('PATCH', f'{BASE}/{pid}/draft', body)
    print('  patch draft:', st if st == 200 else (st, str(r)[:300]))
    results.append({"slug": p['slug'], "id": pid, "patched": st == 200})

json.dump(results, open(S + 'new_solution_pages.json', 'w'), indent=1)
print(json.dumps(results, indent=1))
