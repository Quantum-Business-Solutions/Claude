#!/usr/bin/env python3
"""Apply Sarah's and Mindy's Provider-language rules to the JSON-LD in headHtml.

Friday's manufacturer-language pass only read visible body copy. It never looked
at `headHtml`, so the structured data - the part Google and the answer engines
actually quote - still carries the first-person manufacturing claims that were
rewritten on the page itself.

What counts as a violation here is narrow and deliberate: Praxera claiming to own
production or a plant. "production", "turnkey production", "good manufacturing
practices", "GMP-certified", "manufacture date" and passive "can be manufactured"
are all approved or ordinary industry terms and are left exactly as they are.

Every change is an exact-string replacement listed below, so the diff is
auditable line by line - nothing is regex-guessed.

usage: fix_schema_language.py [--apply]
"""
import json
import re
import sys

exec(open('/tmp/hs.py').read())

CATEGORIES = [
    'fitness', 'weight management', "men's health", 'herbal', 'healthy aging',
    "women's health", 'probiotic', 'immune support', 'cognitive support',
    'multivitamin', 'pediatric', 'joint support', 'heart health',
    'detox and liver support', 'energy and vitality', 'prenatal', 'sleep',
]

# exact old -> new. Applied to headHtml only, on every Praxera page that has them.
EDITS = [
    ('and we produce the finished product ready to ship under your brand',
     'and we provide the finished product ready to ship under your brand'),
    ('and we produce finished inventory ready to ship under your brand',
     'and we provide finished inventory ready to ship under your brand'),
    ('a pre-formulated dietary supplement produced by a manufacturer (us) and sold under your brand name',
     'a pre-formulated dietary supplement, manufactured in a US facility and sold under your brand name'),
    ('We handle the manufacturing-side compliance.',
     'We handle the production-side compliance.'),
    ('Our facility is FDA-registered and has been inspected.',
     'The facility is FDA-registered and has been inspected.'),
    ('Our facility is at 929 Harvest Lane, Williston, VT 05495.',
     'Our address is 929 Harvest Lane, Williston, VT 05495.'),
    ('so they can evaluate manufacturing partners (us or anyone else) intelligently',
     'so they can evaluate supplement partners (us or anyone else) intelligently'),
    ('Manufacturing quotes include production, quality testing',
     'Quotes include production, quality testing'),
    ('to price a manufacturing engagement',
     'to price a production engagement'),
]

# "All our <category> formulations are produced in our FDA-registered,
#  GMP-certified Vermont facility."  ->  no first-person plant.
for _c in CATEGORIES:
    EDITS.append((
        f'All our {_c} formulations are produced in our FDA-registered, '
        f'GMP-certified Vermont facility.',
        f'All our {_c} formulations are manufactured in an FDA-registered, '
        f'GMP-certified US facility in Vermont.'))

# Pages deliberately skipped: `facility` and `case-studies` were removed from the
# launch set on the sign-off sheet, so their copy is not ours to rewrite.
SKIP = {'facility', 'case-studies'}

# The three ad landing pages carry a FAQPage block mirroring their old FAQ. Their
# new FAQ lives in build_ads_lp_copy.py, so regenerate rather than patch.
ADS = {'216192983652': 'alp/ads-mfg-usa',
       '216192983654': 'alp/ads-contract-mfg',
       '216194811734': 'alp/ads-pl-mfg'}


def praxera_pages():
    after, out = None, []
    while True:
        q = {'limit': 100}
        if after:
            q['after'] = after
        r = call('GET', '/cms/v3/pages/site-pages', q=q)
        out += [x for x in r.get('results', [])
                if 'praxerasupplements.com' in (x.get('url') or '')]
        after = (r.get('paging') or {}).get('next', {}).get('after')
        if not after:
            return out


def ads_faq_schema(slug, page_url):
    import importlib.util
    argv, sys.argv = sys.argv, [sys.argv[0]]
    spec = importlib.util.spec_from_file_location('b', 'tools/build_ads_lp_copy.py')
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    sys.argv = argv
    return {
        '@context': 'https://schema.org',
        '@graph': [{
            '@type': 'FAQPage',
            '@id': f'{page_url}#faq',
            'mainEntity': [
                {'@type': 'Question', 'name': q,
                 'acceptedAnswer': {'@type': 'Answer', 'text': a}}
                for q, a in b.FAQ[slug]],
        }],
    }


def main():
    dry = '--apply' not in sys.argv
    log = {}
    for page in praxera_pages():
        slug = page['slug'] or '(home)'
        if slug in SKIP:
            continue
        head = page.get('headHtml') or ''
        if not head:
            continue
        new, hits = head, []

        if str(page['id']) in ADS:
            block = ads_faq_schema(ADS[str(page['id'])], page['url'].rstrip('/'))
            new = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)',
                         lambda m: m.group(1) + '\n' +
                         json.dumps(block, indent=2, ensure_ascii=False) + '\n' + m.group(3),
                         new, count=1, flags=re.S)
            if new != head:
                hits.append('FAQPage regenerated from the new page FAQ')
        else:
            for old, rep in EDITS:
                n = new.count(old)
                if n:
                    new = new.replace(old, rep)
                    hits.append(f'{n}x  {old[:72]}')

        if not hits:
            continue
        log[slug] = {'id': page['id'], 'changes': hits}
        print(f'{slug:26} {len(hits)} edit group(s)')
        for h in hits:
            print(f'    {h}')
        if not dry:
            call('PATCH', f"/cms/v3/pages/site-pages/{page['id']}",
                 b={'headHtml': new})

    json.dump(log, open('reference/schema_language_changes.json', 'w'), indent=1)
    print(f'\n{len(log)} page(s) touched -> reference/schema_language_changes.json')
    if dry:
        print('DRY RUN - pass --apply to write the draft buffer.')


if __name__ == '__main__':
    main()
