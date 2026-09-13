#!/usr/bin/env python3
"""Write the ad landing-page copy for /alp/ads-mfg-usa, /alp/ads-contract-mfg and
/alp/ads-pl-mfg into the HubSpot DRAFT buffer.

The three pages were published carrying a literal
"[PLACEHOLDER: ... Justin should add the specific value props and CTAs ...]"
paragraph, and the surrounding copy breaks two standing client rules:

  Sarah Miller  - replace "manufacturing"/"manufacturer" with Provider language.
                  "turnkey production" and "US manufacturing" are OK.
  Mindy         - Praxera is never marketed as manufacturing. "Manufactured in
                  the U.S." and "cGMP facility" are approved; never "we produce",
                  "our facilities", "manufacturers".
  Tammy         - CTAs go to Schedule a Consultation (/get-started). No links to
                  DaVinci, no purchase path.

There is no DaVinci original for any of these three pages, so nothing here is
"copy that was already approved on the DaVinci site" - every line is written
fresh against the rules above and against language already approved on
/about, /get-started and the category pages.

Nothing is pushed live. Run push_ads_lp_live.py only on Shawn's explicit go.
"""
import json
import sys

exec(open('/tmp/hs.py').read())

PAGES = {
    '216192983652': 'alp/ads-mfg-usa',
    '216192983654': 'alp/ads-contract-mfg',
    '216194811734': 'alp/ads-pl-mfg',
}

# ---------------------------------------------------------------- shared bits

STATS = [
    {'stat_label': 'years experience', 'value': '50+'},
    {'stat_label': 'stock products', 'value': '190+'},
    {'stat_label': 'to ship', 'value': '3-4 wk'},
    {'stat_label': 'made in the USA', 'value': '100%'},
]

CARD_P = ('<p style="color: #555; font-size: 15px; line-height: 1.6; margin: 0;">'
          '{}</p>')

CARDS = [
    {'title': 'Made in a US facility',
     'content': CARD_P.format('Manufactured in a Vermont facility that is '
                              'FDA-registered and GMP certified to SQF and '
                              'NSF 455-2 standards.')},
    {'title': 'Low minimums, no set-up fees',
     'content': CARD_P.format('Launch your brand without a large upfront '
                              'inventory commitment. Per-unit pricing improves '
                              'with volume.')},
    {'title': 'Fast turnaround',
     'content': CARD_P.format('8 to 12 weeks from first conversation to product '
                              'shipping. 3 to 4 weeks production once labels are '
                              'approved.')},
]

H2 = ('<h2 style="color: #012638; font-size: 32px; font-weight: bold; '
      'line-height: 1.25; margin: 0 0 26px;">{}</h2>')

LEAD = ("<p>Praxera's private label program gives brand-builders access to the "
        "same doctor-formulated supplements that integrative healthcare "
        "professionals have trusted for 50 years. You choose the products. We "
        "handle labelling, quality documentation and supply. You sell under "
        "your own brand.</p>")

# ---------------------------------------------------------------- per page

BODY = {
'alp/ads-mfg-usa': H2.format('What we do, in plain terms.') + '\n' + LEAD + """
<h3 style="color: #012638; font-size: 22px; font-weight: bold; line-height: 1.3; margin: 34px 0 14px;">Why US-made matters for your brand</h3>
<p>Every Praxera product is manufactured in a US facility in Vermont that is FDA-registered and GMP-certified. For your brand that means shorter lead times, fewer supply-chain surprises, and a Made in the USA claim you can substantiate on the label and in your marketing.</p>
<ul>
<li><strong>Manufactured in a US facility</strong> &mdash; FDA-registered and GMP certified to SQF and NSF 455-2 standards.</li>
<li><strong>Doctor-formulated catalogue</strong> &mdash; 190-plus finished products ready to carry your label.</li>
<li><strong>Low minimums, no set-up fees</strong> &mdash; start without committing to a warehouse full of inventory.</li>
<li><strong>8 to 12 weeks</strong> from first conversation to product shipping; 3 to 4 weeks production once labels are approved.</li>
</ul>
<p>Tell us what you want to launch and we will confirm on one call whether we are the right fit.</p>""",

'alp/ads-contract-mfg': H2.format('Contract manufacturing or private label &mdash; what you actually need.') + """
<p>Most people searching for a supplement contract manufacturer want one of two things.</p>
<p><strong>Private label</strong> means taking a proven, doctor-formulated product from the Praxera catalogue and putting your brand on it. It is the fastest route to market and the lowest risk: the formulation already exists, it is already made, and you are buying finished goods with your label on them.</p>
<p><strong>A custom product</strong> means working with our formulators to build something to your own specification, with you owning the positioning. It takes longer and costs more up front, and it is the right call when nothing in an existing catalogue does what you need.</p>
<p>Praxera supports both as your turnkey provider. You get one point of contact from the first consultation through to reorders, and turnkey production runs in an FDA-registered, GMP-certified US facility in Vermont.</p>
<p>Pick products from our catalogue, or bring us a specification. We handle formulation, labelling, quality documentation and supply. You sell.</p>""",

'alp/ads-pl-mfg': H2.format('What we do, in plain terms.') + '\n' + LEAD + """
<h3 style="color: #012638; font-size: 22px; font-weight: bold; line-height: 1.3; margin: 34px 0 14px;">Private label, start to finish</h3>
<p>Choose from 190-plus doctor-formulated products, all manufactured in an FDA-registered, GMP-certified US facility. Our in-house design team builds your label &mdash; template or fully custom &mdash; and every order ships with certificates of analysis and sell sheets. There are no set-up fees. Most brands go from first conversation to shipped inventory in 8 to 12 weeks.</p>
<p>You do not need an existing supplement line or a formulation chemist to start. About half the brands we work with are launching their first product.</p>""",
}

HERO = {
'alp/ads-mfg-usa': {
    'headline': '<h1>Made in the USA. FDA-registered, GMP-certified.</h1>',
    'subhead': ('<p>Doctor-formulated supplements manufactured in a US facility. '
                '190-plus stock products, low minimums and fast turnaround &mdash; '
                'with your brand on the&nbsp;label.</p>')},
'alp/ads-contract-mfg': {
    'headline': '<h1>Your supplement brand. Turnkey production behind&nbsp;it.</h1>',
    'subhead': ('<p>Private label from a 190-plus doctor-formulated catalogue, or a '
                'custom product built with our formulators &mdash; manufactured in a US '
                'facility. 8 to 12 weeks from conversation to product&nbsp;shipping.</p>')},
'alp/ads-pl-mfg': {
    'headline': '<h1>Private label supplements with 50 years of expertise behind you.</h1>',
    'subhead': ('<p>Doctor-formulated catalogue of 190-plus products. Low minimums, no '
                'set-up fees, fast turnaround. Launch your supplement brand in weeks, '
                'not&nbsp;months.</p>')},
}

FAQ = {
'alp/ads-mfg-usa': [
    ('Why does US manufacturing matter for supplement brands?',
     'Three reasons. Quality: US production sites operate under FDA oversight with '
     'consistent enforcement. Supply chain: shorter lead times, lower freight costs '
     'and less disruption risk. Marketing: Made in the USA resonates with a large '
     'share of supplement buyers and is verifiable in your claims.'),
    ('Is the facility FDA-registered?',
     'Yes. Praxera products are made in a Vermont facility that has been continuously '
     'FDA-registered since registration was first required, and that is GMP-certified '
     'to NSF 455-2, the most rigorous supplement-specific GMP standard.'),
    ('Is US manufacturing more expensive than overseas?',
     'Per unit it can be, depending on the formulation. Total landed cost - after '
     'shipping, duties, quality risk and turnaround time - often makes US manufacturing '
     'cost-competitive or better. Most brands that price it out side by side choose US '
     'manufacturing for reasons beyond unit cost.'),
    ('Can I tour the site where my products are made?',
     'Yes. Tours can be arranged for prospective and active clients. Ask your Praxera '
     'contact, or request one using the form on this page.'),
    ("What's the minimum order size to work with you?",
     'Most stock formulations have minimums in the low hundreds of bottles per SKU. The '
     'exact number depends on the formulation and we confirm it during your consultation.'),
],
'alp/ads-contract-mfg': [
    ("What's the difference between private label and contract manufacturing?",
     'Private label uses an existing, doctor-formulated product from the Praxera '
     'catalogue with your brand on the label. Contract manufacturing usually means '
     'producing to your own specification - your formula, your packaging, your '
     'positioning. Praxera supports both routes. Most brands start with private label '
     'and add custom work as they grow.'),
    ('How long does a custom product take?',
     '12 to 16 weeks from project kickoff to first production run. That covers '
     'formulation work, ingredient sourcing, stability testing, production scale-up '
     'and the first batch. Simpler formulations can move faster.'),
    ('Where are the products made?',
     'In a US facility in Vermont that is FDA-registered and GMP certified to SQF and '
     'NSF 455-2 standards.'),
    ('What are the minimum order quantities?',
     'Most stock formulations have minimums in the low hundreds of bottles per SKU. '
     'Custom projects are quoted individually. Exact numbers come out of your '
     'consultation.'),
    ('Who do I deal with day to day?',
     'One Praxera contact, from the first consultation through to reorders, with '
     'in-house design support for labels and sell sheets.'),
],
'alp/ads-pl-mfg': [
    ('How fast can I launch a private label supplement brand?',
     'From signed engagement to shipped inventory, typically 8 to 12 weeks. The fastest '
     'path uses an existing formulation and a template-based label. Custom design or a '
     'custom product extends the timeline.'),
    ('Do you have low minimums?',
     'Yes by industry standards. Most stock formulations have minimums in the low '
     'hundreds of bottles per SKU. We support brands launching a first product line and '
     'scaling brands that need volume.'),
    ("What's included in your private label package?",
     'Production, quality testing, certificates of analysis, label design (template or '
     'custom), packaging selection and fulfilment-ready bottling. Sell sheets are '
     'included for most engagements. There are no set-up fees or hidden charges.'),
    ("Can I work with you if I'm a first-time supplement brand?",
     'Yes. About half our clients are first-time supplement brand builders. We are set '
     'up for that path with educational resources, transparent pricing and consultative '
     'onboarding.'),
    ('Why work with Praxera over other private label providers?',
     '50 years of supplement-specific experience. A doctor-formulated catalogue of '
     '190-plus products, manufactured in an FDA-registered facility that is GMP '
     'certified to NSF 455-2. In-house design included. Transparent pricing with no '
     'set-up fees. We are not the cheapest - we are built for brands that care about '
     'quality and a long-term partnership.'),
],
}

META = {
'alp/ads-mfg-usa': ('Made in the USA. Doctor-formulated supplements manufactured in an '
                    'FDA-registered, GMP-certified Vermont facility. 190-plus products, '
                    'low minimums. Launch your brand.'),
'alp/ads-contract-mfg': ('Your supplement brand, our turnkey production. Private label '
                         'from a 190-plus catalogue or a custom product, manufactured in '
                         'a US facility. 8-12 weeks to ship.'),
'alp/ads-pl-mfg': ('Private label supplements with 50 years of expertise behind you. '
                   '190-plus products, low minimums, no set-up fees, fast turnaround. '
                   'Launch in weeks.'),
}

CTA_HREF = '/get-started'

# ---------------------------------------------------------------- apply


def modules(section):
    """Yield every module node in a layoutSection, in document order."""
    found = []

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get('type') == 'module':
            found.append(node)
            return
        rows = node.get('rows')
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    for cell in row.values():
                        walk(cell)
    walk(section)
    return found


def apply(page):
    slug = page['slug']
    sec = page['layoutSections']['main_content']
    by_name = {m['name']: m for m in modules(sec)}
    changes = []

    def note(where, before, after):
        if before != after:
            changes.append({'module': where, 'before': before, 'after': after})

    hero = by_name['module_0']['params']
    for key, val in HERO[slug].items():
        note(f'module_0.{key}', hero.get(key), val)
        hero[key] = val
    for btn in hero.get('buttons', []):
        url = btn.get('link', {}).get('url', {})
        note('module_0.button.href', url.get('href'), CTA_HREF)
        url['href'] = CTA_HREF

    stats = by_name['module_1']['params']
    note('module_1.stats', json.dumps(stats.get('stats')), json.dumps(STATS))
    stats['stats'] = [dict(s) for s in STATS]

    body = by_name['module_2']['params']
    note('module_2.content', body.get('content'), BODY[slug])
    body['content'] = BODY[slug]

    cards = by_name['module_3']['params']
    old = cards.get('cards') or []
    new = []
    for i, c in enumerate(CARDS):
        merged = dict(old[i]) if i < len(old) else {}
        merged.update(c)
        new.append(merged)
    note('module_3.cards', json.dumps(old), json.dumps(new))
    cards['cards'] = new

    cta = by_name['module_5']['params']
    for btn in cta.get('buttons', []):
        url = btn.get('link', {}).get('url', {})
        note('module_5.button.href', url.get('href'), CTA_HREF)
        url['href'] = CTA_HREF

    faq = by_name['module_7']['params']
    old_items = faq.get('items') or []
    new_items = []
    for i, (q, a) in enumerate(FAQ[slug]):
        merged = dict(old_items[i]) if i < len(old_items) else dict(old_items[0]) if old_items else {}
        merged['question'] = q
        merged['answer'] = a
        new_items.append(merged)
    note('module_7.items', json.dumps(old_items), json.dumps(new_items))
    faq['items'] = new_items

    return changes


def main():
    dry = '--apply' not in sys.argv
    log = {}
    for pid, slug in PAGES.items():
        page = call('GET', f'/cms/v3/pages/site-pages/{pid}')
        assert page['slug'] == slug, f'slug moved: {page["slug"]} != {slug}'
        changes = apply(page)
        meta_before = page.get('metaDescription')
        payload = {
            'layoutSections': page['layoutSections'],
            'metaDescription': META[slug],
        }
        if meta_before != META[slug]:
            changes.append({'module': 'metaDescription',
                            'before': meta_before, 'after': META[slug]})
        log[slug] = changes
        print(f'{slug}: {len(changes)} field(s) changed')
        if not dry:
            call('PATCH', f'/cms/v3/pages/site-pages/{pid}', b=payload)
            print(f'  -> PATCHed draft for {pid} (NOT pushed live)')
    json.dump(log, open('reference/ads_lp_copy_changes.json', 'w'), indent=1)
    print('\nwrote reference/ads_lp_copy_changes.json')
    if dry:
        print('DRY RUN - pass --apply to write the draft buffer.')


if __name__ == '__main__':
    main()
