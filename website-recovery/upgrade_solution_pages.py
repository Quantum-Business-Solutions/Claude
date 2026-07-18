#!/usr/bin/env python3
"""10/10 upgrades: pain bridges, paths, who-for, fractional rebuild, revops visual."""
import json, urllib.request, ssl

S = '/tmp/claude-0/-home-user-Claude/afaaa5d3-2de0-5da2-9bf3-affd4e8c30f7/scratchpad/'
TOKEN = [l.split('=', 1)[1].strip() for l in open(S + 'hs_env') if 'HS_TOKEN' in l][0]
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
RT_ID, ROAD_ID = 217248524682, 217324784732
ART = 'https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/quantum-theme/art/'

def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    r = urllib.request.urlopen(req, context=CTX); t = r.read().decode()
    return r.status, (json.loads(t) if t else {})

def mod_row(name, label, params):
    p = dict(params); p['css_class'] = 'dnd-module'
    m = {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "label": label, "name": name,
         "params": p, "rowMetaData": [], "rows": [], "type": "module", "w": 0, "x": 0}
    return {"0": {"cells": [], "cssClass": "", "cssId": "", "cssStyle": "", "name": "c_" + name,
                  "params": {"css_class": "dnd-column"}, "rowMetaData": [], "rows": [{"0": m}], "w": 0, "x": 0}}

def rt(name, prose, maxw="full"):
    return mod_row(name, 'quantum-rich-text', {"maxw": maxw, "module_id": RT_ID, "prose": prose})

def find_idx(main, name):
    for i, r in enumerate(main['rows']):
        for k, col in r.items():
            if isinstance(col, dict):
                for rr in col.get('rows', []):
                    for kk, vv in rr.items():
                        if isinstance(vv, dict) and vv.get('name') == name: return i
    return None

def get_mod(main, name):
    for r in main['rows']:
        for k, col in r.items():
            if isinstance(col, dict):
                for rr in col.get('rows', []):
                    for kk, vv in rr.items():
                        if isinstance(vv, dict) and vv.get('name') == name: return vv

GOLD_CHIP = 'display:inline-block;border:1px solid rgba(196,164,74,.5);border-radius:999px;padding:4px 14px;font-size:11px;letter-spacing:2px;color:var(--q-gold);margin-bottom:14px'

def pain_bridge(pain, bridge, outcome):
    def c(chip, txt):
        return (f'<div class=q-card><span style="{GOLD_CHIP}">{chip}</span><p style="margin:0">{txt}</p></div>')
    return ('<div class=q-cards>' + c('THE PAIN', pain) + c('THE BRIDGE', bridge) + c('THE OUTCOME', outcome) + '</div>')

def who_for(title_for, items_for, title_not, items_not):
    li_f = ''.join(f'<li>{x}</li>' for x in items_for)
    li_n = ''.join(f'<li>{x}</li>' for x in items_not)
    return ('<h2 style="text-align:center">Is this <em>you?</em></h2><div class="q-cards q-cards-2">'
            f'<div class=q-card><h4 style="color:var(--q-gold)">{title_for}</h4><ul style="margin:0;padding-left:20px">{li_f}</ul></div>'
            f'<div class=q-card><h4 style="color:var(--fg-muted)">{title_not}</h4><ul style="margin:0;padding-left:20px;color:var(--fg-muted)">{li_n}</ul></div></div>')

def quote_block(text, who, role):
    return ('<div style="max-width:760px;margin:0 auto;text-align:center;padding:10px 0">'
            '<div style="width:44px;height:2px;background:var(--q-gold);margin:0 auto 26px"></div>'
            f'<p style="font-family:var(--q-serif);font-size:26px;line-height:1.45;color:var(--fg);margin:0 0 18px">&ldquo;{text}&rdquo;</p>'
            f'<p style="color:var(--q-gold);margin:0;font-weight:600">{who}</p>'
            f'<p style="color:var(--fg-muted);margin:4px 0 0;font-size:14px">{role}</p></div>')

# =========================================================
# 1. AUDIT 217438044208
# =========================================================
def upgrade_audit():
    pid = '217438044208'
    st, d = api('GET', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft')
    main = d['layoutSections']['main']
    main['rows'].insert(find_idx(main, 'aud_hero') + 1, rt('aud_bridge',
        '<h2 style="text-align:center">The portal problem nobody <em>owns</em></h2>' + pain_bridge(
        "You're paying for Professional or Enterprise, but reports contradict each other, automation misfires, and nobody fully trusts what's in the CRM. Everyone works around it; nobody owns it.",
        "A structured teardown by a team that runs HubSpot portals every single day — every workflow, report, integration, and data set inspected and ranked by revenue impact.",
        "A portal your team actually trusts, and a prioritized roadmap that turns HubSpot from a line item back into an asset.")))
    main['rows'].insert(find_idx(main, 'aud_dims') + 1, rt('aud_finds',
        '<h2 style="text-align:center">The classics we find <em>over and over</em></h2><div class=q-cards>'
        '<div class=q-card><h4>Ghost automation</h4><p>Workflows still emailing prospects on behalf of reps who left the company — sometimes years ago.</p></div>'
        '<div class=q-card><h4>Lifecycle chaos</h4><p>Lifecycle stages and lead statuses nobody ever agreed definitions for — so every report built on them is fiction.</p></div>'
        '<div class=q-card><h4>Paying for duplicates</h4><p>Duplicate and dead contacts silently inflating your marketing contact tier — you’re paying HubSpot to store noise.</p></div>'
        '<div class=q-card><h4>Double-counted revenue</h4><p>Dashboards that count the same deal twice — and a leadership team making decisions on the inflated number.</p></div>'
        '<div class=q-card><h4>Integration loops</h4><p>Two systems syncing the same records into duplicates faster than anyone can merge them.</p></div>'
        '<div class=q-card><h4>Seats nobody uses</h4><p>Paid seats that haven’t logged in for a quarter — budget that should be funding the fixes.</p></div></div>'))
    main['rows'].insert(find_idx(main, 'aud_faq'), rt('aud_who', who_for(
        'The audit is for you if…',
        ['You’ve been on HubSpot a year or more and suspect you’re using a fraction of it',
         'You inherited a portal someone else built and nobody documented',
         'Leadership doesn’t trust the reports — so decisions happen on gut feel',
         'You’re about to upgrade tiers and want to fix the foundation first'],
        'It’s not for you if…',
        ['Your portal is brand new — start with <a href="/services/onboarding">onboarding</a> instead',
         'You’re actively migrating off HubSpot',
         'You want a rubber stamp that everything’s fine — we will find things'])))
    st, _ = api('PATCH', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft', {"layoutSections": d['layoutSections']})
    print('audit patch:', st)

# =========================================================
# 2. TRAINING 217438044210
# =========================================================
def upgrade_training():
    pid = '217438044210'
    st, d = api('GET', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft')
    main = d['layoutSections']['main']
    main['rows'].insert(find_idx(main, 'trn_hero') + 1, rt('trn_bridge',
        '<h2 style="text-align:center">The adoption problem, <em>named</em></h2>' + pain_bridge(
        "Your team uses HubSpot as an expensive rolodex. Features you pay for sit untouched, data entry is inconsistent, and every question ends up on the admin’s desk — or yours.",
        "Role-based training inside your portal, on your pipelines and your process — plus a monthly coaching cadence so learning doesn’t evaporate two weeks later.",
        "Reps, marketers, and admins who actually run the machine — cleaner data in, better decisions out, and no more ‘how do I…?’ bottleneck.")))
    idx = find_idx(main, 'trn_fmt') + 1
    main['rows'].insert(idx, rt('trn_outcomes',
        '<h2 style="text-align:center">What your team can do <em>after</em></h2><div class="q-cards q-cards-2">'
        '<div class=q-card><h4>Sales</h4><p>Run their day from HubSpot: pipeline hygiene, sequences, tasks, and meetings — logged automatically instead of reconstructed on Friday.</p></div>'
        '<div class=q-card><h4>Marketing</h4><p>Build campaigns, segment lists, and read attribution — and hand sales leads with context instead of just a name.</p></div>'
        '<div class=q-card><h4>Service</h4><p>Work tickets, pipelines, and customer views so renewals and issues never live in someone’s inbox.</p></div>'
        '<div class=q-card><h4>Admins</h4><p>Maintain workflows, build reports, and answer the team’s questions with confidence — with us as backup, not a dependency.</p></div></div>'))
    main['rows'].insert(idx + 1, mod_row('trn_road', 'Process roadmap', {
        "axis_labels": "Week 1,Week 2,Week 4,Ongoing", "module_id": ROAD_ID,
        "eyebrow": "The Path", "heading": "From bought-it to bought-in",
        "intro": "Training that sticks is a cadence, not an event.",
        "steps": [
          {"chip": "Week 1", "title": "Skills Assessment", "desc": "We map who uses what today — roles, gaps, and the features you pay for but don’t touch."},
          {"chip": "Weeks 1-2", "title": "Role-Based Sessions", "desc": "Live training by team — sales, marketing, service, admin — inside your actual portal."},
          {"chip": "Weeks 2-4", "title": "Academy Reinforcement", "desc": "Self-paced Quantum Academy courses assigned per role, so learning survives the calendar."},
          {"chip": "Monthly", "title": "User Group Coaching", "desc": "A standing monthly session: new questions, new features, new hires — handled."}]}))
    main['rows'].insert(find_idx(main, 'trn_faq'), rt('trn_who', who_for(
        'Training is for you if…',
        ['You just finished onboarding and the team is staring at a blank portal',
         'Adoption is low and the CRM is three different spreadsheets in disguise',
         'New hires learn HubSpot by shoulder-surfing whoever’s nearest',
         'One overloaded person answers every HubSpot question'],
        'It’s not for you if…',
        ['You want the work done <em>for</em> you — that’s <a href="/services/hubspot-admin-as-a-services">Admin as a Service</a> or a <a href="/hubspot-build">Build</a>',
         'You don’t have HubSpot yet — start with <a href="/services/onboarding">onboarding</a>',
         'Your portal itself is the problem — start with the <a href="/hubspot-portal-audit">audit</a>'])))
    main['rows'].insert(find_idx(main, 'trn_faq'), rt('trn_quote', quote_block(
        "That's exactly what I needed to know — you just simplified it so much.",
        "Lucy Graham", "Marketing — QBS client, live training session")))
    st, _ = api('PATCH', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft', {"layoutSections": d['layoutSections']})
    print('training patch:', st)

# =========================================================
# 3. REVOPS 217438141499
# =========================================================
def upgrade_revops():
    pid = '217438141499'
    st, d = api('GET', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft')
    main = d['layoutSections']['main']
    main['rows'].insert(find_idx(main, 'rev_hero') + 1, rt('rev_bridge',
        '<h2 style="text-align:center">Where revenue actually <em>leaks</em></h2>' + pain_bridge(
        "Marketing says the leads are good. Sales says they’re not. Three tools disagree about the same customer, handoffs live in someone’s memory, and month-end reporting is an archaeology project.",
        "One operations layer across the whole stack: clean data, automated handoffs, enriched records, and dashboards built on definitions everyone agreed to.",
        "A revenue engine that runs without heroics — measured, predictable, and boring in the best possible way.")))
    idx = find_idx(main, 'rev_what') + 1
    main['rows'].insert(idx, rt('rev_constellation',
        '<h2 style="text-align:center">Your stack, actually <em>connected</em></h2>'
        '<p style="text-align:center;max-width:720px;margin:0 auto">Most teams own good tools that don’t talk to each other. RevOps is the wiring: HubSpot at the center, every system feeding one clean picture of the customer.</p>'
        f'<div style="text-align:center;padding:20px 0 0"><img src="{ART}feat-integration-constellation.svg" alt="Revenue tech stack constellation — every tool wired into HubSpot at the center" style="max-width:720px;width:100%"></div>'))
    main['rows'].insert(idx + 1, mod_row('rev_road', 'Process roadmap', {
        "axis_labels": "Week 1,Week 3,Week 6,Ongoing", "module_id": ROAD_ID,
        "eyebrow": "The Path", "heading": "From stack sprawl to one engine",
        "intro": "Audit the plumbing, wire it, automate it — then keep it running.",
        "steps": [
          {"chip": "Weeks 1-2", "title": "Stack & Data Audit", "desc": "Every tool, sync, and handoff mapped. Where records break, duplicate, or die."},
          {"chip": "Weeks 2-4", "title": "Wire & Clean", "desc": "Integrations fixed, duplicate loops killed, enrichment flowing, definitions agreed."},
          {"chip": "Weeks 4-6", "title": "Automate & Report", "desc": "Routing, handoffs, and follow-up automated. Dashboards leadership actually uses."},
          {"chip": "Monthly", "title": "Operate", "desc": "Admin-as-a-Service keeps senior operators in the engine room — maintaining, optimizing, answering."}]}))
    main['rows'].insert(find_idx(main, 'rev_faq'), rt('rev_who', who_for(
        'RevOps is for you if…',
        ['You’ve outgrown spreadsheet operations but haven’t hired ops staff',
         'Handoffs between marketing, sales, and service depend on memory',
         'Your tools each tell a different story about the same customer',
         'Reporting takes days and convinces no one'],
        'It’s not for you if…',
        ['You don’t have a CRM yet — start with <a href="/services/onboarding">onboarding</a>',
         'You want another tool — RevOps is operators and process, not more software',
         'You need executive strategy first — that’s <a href="/fractional-leadership">Fractional Leadership</a>'])))
    st, _ = api('PATCH', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft', {"layoutSections": d['layoutSections']})
    print('revops patch:', st)

# =========================================================
# 4. FRACTIONAL 217438044214  (rebuild)
# =========================================================
def upgrade_fractional():
    pid = '217438044214'
    st, d = api('GET', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft')
    main = d['layoutSections']['main']
    main['rows'].insert(find_idx(main, 'frc_hero') + 1, rt('frc_bridge',
        '<h2 style="text-align:center">When revenue has no <em>owner</em></h2>' + pain_bridge(
        "Revenue is a collection of heroic individual efforts. No system, no reliable forecast, and no one below the CEO truly owning the number.",
        "An experienced revenue executive installed in weeks — carrying the playbook from hundreds of engagements instead of one company’s history.",
        "A revenue organization with cadence, accountability, and a forecast you can defend to anyone.")))
    idx = find_idx(main, 'frc_bridge') + 1
    main['rows'].insert(idx, rt('frc_triggers',
        '<h2 style="text-align:center">The moments this <em>call</em> happens</h2><div class="q-cards q-cards-2">'
        '<div class=q-card><h4>“Our VP of Sales just left.”</h4><p>The pipeline is orphaned mid-quarter and a replacement search takes six months. A fractional CSO stabilizes the team in weeks and keeps deals moving while you hire right instead of fast.</p></div>'
        '<div class=q-card><h4>“Founder-led sales hit its ceiling.”</h4><p>You’re the best rep in the company — and the bottleneck. A fractional CRO builds the machine that scales past you: process, people, and pipeline that don’t need you in every deal.</p></div>'
        '<div class=q-card><h4>“We spend on marketing. Where’s the pipeline?”</h4><p>Activity everywhere, revenue nowhere. A fractional CMO ties every dollar and every campaign to pipeline you can count.</p></div>'
        '<div class=q-card><h4>“The board wants a forecast I can’t produce.”</h4><p>A fractional CRO installs forecast discipline — stages that mean something, reviews that catch slippage, a number you’ll stand behind.</p></div></div>'))
    # replace the thin roles section with full definitions
    roles = get_mod(main, 'frc_roles')
    roles['params']['prose'] = (
        '<h2 style="text-align:center">Three seats, <em>defined</em> — what each one owns and does</h2>'
        '<div class=q-cards>'
        '<div class=q-card><span style="' + GOLD_CHIP + '">FRACTIONAL CRO</span>'
        '<h4>Owns the whole revenue number</h4>'
        '<p><strong style="color:var(--fg)">What they do:</strong> run the weekly revenue leadership cadence, own pipeline and forecast, align marketing-to-sales handoffs, set KPIs and comp plans, report to the founder and board.</p>'
        '<p><strong style="color:var(--fg)">How they help:</strong> replaces gut-feel growth with a system. The usual first move when founder-led sales stops scaling or marketing, sales, and service each optimize their own silo.</p></div>'
        '<div class=q-card><span style="' + GOLD_CHIP + '">FRACTIONAL CMO</span>'
        '<h4>Owns demand and the brand</h4>'
        '<p><strong style="color:var(--fg)">What they do:</strong> set positioning and strategy, run the campaign calendar, manage the team and vendors, own lead quality end-to-end, and report marketing’s actual pipeline contribution.</p>'
        '<p><strong style="color:var(--fg)">How they help:</strong> ends random acts of marketing. Every dollar of spend gets a line of sight to pipeline — and the reporting to prove it.</p></div>'
        '<div class=q-card><span style="' + GOLD_CHIP + '">FRACTIONAL CSO</span>'
        '<h4>Owns the sales organization</h4>'
        '<p><strong style="color:var(--fg)">What they do:</strong> design the sales process, define hiring profiles, run onboarding and coaching cadences, lead deal reviews, and build comp plans that drive the right behavior.</p>'
        '<p><strong style="color:var(--fg)">How they help:</strong> turns a group of reps into a system that forecasts — process, accountability, and coaching instead of hero-ball.</p></div></div>')
    main['rows'].insert(find_idx(main, 'frc_roles') + 1, rt('frc_compare',
        '<h2 style="text-align:center">Full-time hire vs. <em>fractional</em></h2>'
        '<div style="overflow-x:auto"><table style="width:100%;max-width:880px;margin:0 auto;border-collapse:collapse;font-size:15px">'
        '<tr><th style="text-align:left;padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.35);color:var(--fg-muted);font-weight:600"></th>'
        '<th style="text-align:left;padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.35);color:var(--fg-muted)">Full-time executive</th>'
        '<th style="text-align:left;padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.35);color:var(--q-gold)">Fractional with Quantum</th></tr>'
        '<tr><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg);font-weight:600">Time to start</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg-muted)">6+ month search, then ramp</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg)">Weeks — assessment starts immediately</td></tr>'
        '<tr><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg);font-weight:600">Annual cost</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg-muted)">$300K+ salary, plus bonus and equity</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg)">A fraction — scoped to the leadership you need</td></tr>'
        '<tr><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg);font-weight:600">Commitment</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg-muted)">Multi-year, severance risk</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg)">Engagement-based — scale up, down, or convert to a full-time hire</td></tr>'
        '<tr><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg);font-weight:600">Experience</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg-muted)">One career’s playbook</td><td style="padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14);color:var(--fg)">Patterns from hundreds of client engagements across industries</td></tr>'
        '<tr><td style="padding:14px 16px;color:var(--fg);font-weight:600">If it’s not working</td><td style="padding:14px 16px;color:var(--fg-muted)">A mis-hire costs a year</td><td style="padding:14px 16px;color:var(--fg)">Adjust the engagement in a conversation</td></tr>'
        '</table></div>'))
    main['rows'].insert(find_idx(main, 'frc_compare') + 1, mod_row('frc_road', 'Process roadmap', {
        "axis_labels": "Day 1,Day 30,Day 90,Quarter 2+", "module_id": ROAD_ID,
        "eyebrow": "The Proven Process", "heading": "From assessment to a number you own",
        "intro": "Every engagement starts with evidence, not a retainer.",
        "steps": [
          {"chip": "Days 1-30", "title": "30-Day Assessment", "desc": "Full teardown of team, process, pipeline, and tooling — ending in a prioritized revenue plan."},
          {"chip": "Days 30-45", "title": "Choose the Level", "desc": "Tell Me (you execute), Help Me (we execute together), or Do It (we own the number)."},
          {"chip": "Days 45-90", "title": "Install the Rhythm", "desc": "Weekly leadership cadence, pipeline reviews, forecast discipline, coaching — the operating system goes in."},
          {"chip": "Quarter 2+", "title": "Compound or Hand Off", "desc": "Quarterly targets and hiring plans — including hiring your full-time executive when it’s time, with a system already running."}]}))
    main['rows'].insert(find_idx(main, 'frc_faq'), rt('frc_who', who_for(
        'Fractional leadership is for you if…',
        ['Founder-led sales is scaling past the founder’s calendar',
         'You’re between revenue leaders and can’t afford a six-month gap',
         'The board or your investors expect forecast discipline you don’t have yet',
         'You need the strategy and the system before you can justify the full-time hire'],
        'It’s not for you if…',
        ['You need a full-time operator on the floor five days a week — we’ll tell you, and help you hire them',
         'You want a silver bullet without changing how the team operates',
         'The gap is execution capacity, not leadership — that’s <a href="/outbound-sales">Sales as a Service</a> or a <a href="/sales-blitz-as-a-service">Sales Blitz</a>'])))
    main['rows'].insert(find_idx(main, 'frc_faq'), rt('frc_quote', quote_block(
        "Our experience has been wonderful. Quantum is a well-run company from top to bottom… A pleasure to work with.",
        "Joe Blatchford", "QBS client")))
    # extend FAQ + schema with definition question
    faq = get_mod(main, 'frc_faq')
    new_q = ('<details class="q-faq-item"><summary>What is a fractional CRO?</summary><div class="q-faq-a">'
             'A fractional CRO (Chief Revenue Officer) is an experienced revenue executive who leads your marketing, sales, and customer revenue strategy part-time — owning the pipeline, the forecast, and the leadership cadence at a fraction of a full-time executive’s cost. Fractional CMOs and CSOs work the same way for marketing and sales leadership specifically.</div></details>')
    faq['params']['prose'] = faq['params']['prose'].replace('<div class="q-faq">', '<div class="q-faq">' + new_q, 1)
    schema_faqs = [
        ("What is a fractional CRO?", "A fractional CRO (Chief Revenue Officer) is an experienced revenue executive who leads your marketing, sales, and customer revenue strategy part-time — owning the pipeline, the forecast, and the leadership cadence at a fraction of a full-time executive's cost."),
        ("What does a fractional executive actually do?", "Everything a full-time CRO, CMO, or CSO does — strategy, team leadership, pipeline accountability, board-level reporting — for a fraction of the cost, on a schedule matched to your stage."),
        ("How is this different from consulting?", "A consultant hands you recommendations. A fractional executive owns outcomes: they run the meetings, manage the numbers, coach the team, and answer for the result."),
        ("CRO vs. CMO vs. CSO — which one do we need?", "A CRO owns the whole revenue engine across marketing, sales, and service. A CMO owns demand: brand, content, campaigns, and pipeline creation. A CSO owns the sales organization: process, hiring, coaching, and quota. The 30-Day Assessment usually makes the answer obvious."),
        ("How do engagements start?", "Most start with the 30-Day CRO Assessment: a full teardown of your revenue engine that ends with a prioritized plan. From there you pick the level — we tell you what to do, we work alongside your team, or we run it."),
        ("How much of their time do we get?", "Engagements are scoped to your stage — typically a fixed weekly rhythm of leadership meetings, pipeline reviews, and working sessions, plus async access in between."),
    ]
    ents = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in schema_faqs]
    head = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": ents}) + '</script>'
    st, _ = api('PATCH', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft',
                {"layoutSections": d['layoutSections'], "headHtml": head})
    print('fractional patch:', st)

# =========================================================
# 5. TECH STACK 217438044216
# =========================================================
def upgrade_stack():
    pid = '217438044216'
    st, d = api('GET', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft')
    main = d['layoutSections']['main']
    main['rows'].insert(find_idx(main, 'stk_hero') + 1, rt('stk_bridge',
        '<h2 style="text-align:center">Why a stack page from a <em>services</em> firm?</h2>' + pain_bridge(
        "Every tool’s website says it does everything. Buying on demos means owning five tools that overlap in three places and connect in none.",
        "Recommendations from operators who implement and run these platforms for clients daily — including which one <em>not</em> to buy for your stage.",
        "A stack where every tool earns its line item — chosen for fit, wired together, and actually adopted.")))
    main['rows'].insert(find_idx(main, 'stk_tools') + 1, rt('stk_choose',
        '<h2 style="text-align:center">Which dialer? An honest <em>answer</em></h2><div class=q-cards>'
        '<div class=q-card><h4>ConnectAndSell</h4><p><strong style="color:var(--fg)">Pick it when:</strong> conversations are the bottleneck. Agent-assisted dialing delivers the most live decision-maker conversations per hour of anything we’ve run — it’s the engine behind our <a href="/sales-blitz-as-a-service">Sales Blitz</a>.</p></div>'
        '<div class=q-card><h4>Orum</h4><p><strong style="color:var(--fg)">Pick it when:</strong> you want AI parallel-dialing velocity living natively inside your CRM, with reps self-serving their own call blocks day to day.</p></div>'
        '<div class=q-card><h4>Apollo</h4><p><strong style="color:var(--fg)">Pick it when:</strong> you’re a lean team building a first outbound motion and want data, sequencing, and dialing in one tool before investing in best-of-breed.</p></div>'
        '</div><p style="text-align:center;color:var(--fg-muted);margin-top:18px">Not sure? That’s literally the call to book — we’ll match the tool to your team, not the other way around.</p>'))
    st, _ = api('PATCH', f'https://api.hubapi.com/cms/v3/pages/landing-pages/{pid}/draft', {"layoutSections": d['layoutSections']})
    print('stack patch:', st)

upgrade_audit()
upgrade_training()
upgrade_revops()
upgrade_fractional()
upgrade_stack()
print('all drafts upgraded')
