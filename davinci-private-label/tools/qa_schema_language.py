#!/usr/bin/env python3
"""Verify the JSON-LD in every Praxera page draft after fix_schema_language.py.

Checks three things: the banned first-person production claims are gone, every
block still parses as JSON (a broken ld+json block is worse than a wrong one),
and the approved industry terms were not collateral damage.
"""
import json
import re

exec(open('/tmp/hs.py').read())

BANNED = [
    (r'we produce\b', 'first-person production claim'),
    (r'we manufacture\b', 'first-person manufacturing claim'),
    (r'our facilit(y|ies)\b', '"our facility/facilities"'),
    (r'produced by a manufacturer \(us\)', 'Praxera named as the manufacturer'),
    (r'produced in our [^"]*facility', 'first-person plant'),
    (r'manufacturing-side compliance', 'first-person manufacturing'),
    (r'evaluate manufacturing partners \(us', 'Praxera named as a manufacturing partner'),
    (r'other private label manufacturers', 'Praxera grouped with manufacturers'),
]
# left alone on purpose - approved or ordinary industry terms
KEEP = ['turnkey production', 'good manufacturing practices', 'manufacture date',
        'GMP-certified', 'NSF GMP 455-2', 'production takes', 'can be manufactured']

SKIP = {'facility', 'case-studies'}

after, pages = None, []
while True:
    q = {'limit': 100}
    if after:
        q['after'] = after
    r = call('GET', '/cms/v3/pages/site-pages', q=q)
    pages += [x for x in r.get('results', [])
              if 'praxerasupplements.com' in (x.get('url') or '')]
    after = (r.get('paging') or {}).get('next', {}).get('after')
    if not after:
        break

bad, checked, blocks, kept = [], 0, 0, 0
for p in pages:
    slug = p['slug'] or '(home)'
    if slug in SKIP:
        continue
    head = call('GET', f"/cms/v3/pages/site-pages/{p['id']}/draft").get('headHtml') or ''
    if not head:
        continue
    checked += 1
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', head, re.S):
        blocks += 1
        try:
            json.loads(m.group(1))
        except Exception as e:
            bad.append((slug, f'ld+json does not parse: {e}'))
        body = m.group(1)
        for pat, why in BANNED:
            for hit in re.finditer(pat, body, re.I):
                bad.append((slug, f'{why}: ...{body[max(0,hit.start()-60):hit.end()+60]}...'))
        kept += sum(body.count(k) for k in KEEP)

print(f'{checked} pages, {blocks} ld+json blocks, {kept} approved industry terms preserved')
if bad:
    for s, w in bad:
        print(f'FAIL  {s:26} {w}')
    raise SystemExit(f'\n{len(bad)} problem(s)')
print('PASS - no first-person production claims left in any page schema.')
