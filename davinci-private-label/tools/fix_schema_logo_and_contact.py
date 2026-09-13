#!/usr/bin/env python3
"""Two targeted corrections Shawn asked for on 13 Sep.

1. Schema logo. `/` and `/health-categories` carry an Organization JSON-LD block
   in headHtml whose `logo` and `image` point at
   https://www.pettechlabs.com/hubfs/Praxera/Praxera%20Logo.png. That is the URL
   Google and the answer engines record as Praxera's logo. The identical file is
   served from the Praxera domain (same 2,442 bytes, HTTP 200), so this is a
   host swap and nothing else. Image *hosting* on pettechlabs.com is normal
   shared-portal behaviour and is deliberately left alone everywhere else - the
   17 other pages only carry a CSS selector `img[src*="pettechlabs"]`, which is
   styling, not structured data.

2. Contact page mailto. The email card linked to
   mailto:info@praxerasuapplements.com - "suapplements". One character class,
   nothing else on the page touched.

/contact is QBS-approved by Patrick and `/` by Shawn; both edits are the exact
ones Shawn asked for, and each is a single string replacement.

usage: fix_schema_logo_and_contact.py [--apply] [--push]
"""
import json
import sys

exec(open('/tmp/hs.py').read())

OLD_LOGO = 'https://www.pettechlabs.com/hubfs/Praxera/Praxera%20Logo.png'
NEW_LOGO = 'https://www.praxerasupplements.com/hubfs/Praxera/Praxera%20Logo.png'
OLD_MAIL = 'mailto:info@praxerasuapplements.com'
NEW_MAIL = 'mailto:info@praxerasupplements.com'

SCHEMA_PAGES = {'216189433405': '(home)', '221518507280': 'health-categories'}
CONTACT = '216192983650'


def patch(pid, label, build, field):
    page = call('GET', f'/cms/v3/pages/site-pages/{pid}')
    before = json.dumps(page.get(field)) if field != 'layoutSections' else json.dumps(page[field])
    payload, n = build(page)
    if not n:
        print(f'{label}: nothing to change')
        return False
    print(f'{label}: {n} replacement(s) in {field}')
    if '--apply' in sys.argv:
        call('PATCH', f'/cms/v3/pages/site-pages/{pid}', b=payload)
        if '--push' in sys.argv:
            call('POST', f'/cms/v3/pages/site-pages/{pid}/draft/push-live', b={})
            print(f'  -> pushed live')
        else:
            print(f'  -> draft updated (not pushed)')
    return True


def schema(page):
    head = page.get('headHtml') or ''
    n = head.count(OLD_LOGO)
    return {'headHtml': head.replace(OLD_LOGO, NEW_LOGO)}, n


def contact(page):
    blob = json.dumps(page['layoutSections'])
    n = blob.count(OLD_MAIL)
    return {'layoutSections': json.loads(blob.replace(OLD_MAIL, NEW_MAIL))}, n


for pid, label in SCHEMA_PAGES.items():
    patch(pid, f'schema logo {label}', schema, 'headHtml')
patch(CONTACT, 'contact mailto', contact, 'layoutSections')

if '--apply' not in sys.argv:
    print('\nDRY RUN - pass --apply (and --push to publish).')
