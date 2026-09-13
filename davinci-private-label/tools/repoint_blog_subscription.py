"""Repoint the 7 Praxera forms from the DaVinci blog-subscription property to the Praxera one.

RUN THIS ONLY AFTER blog email subscription has been switched on for the Praxera
Supplements Blog in the HubSpot UI:

    Settings -> Content -> Blog -> Praxera Supplements Blog -> Subscriptions
    -> enable email subscription

That toggle provisions the contact property, the "Praxera Blog Subscription"
subscription type and the instant/daily/weekly/monthly lists. None of it can be
created through the API: POST to /communication-preferences/v3/definitions and to
/email/public/v1/subscriptions both return 405 Method Not Allowed (the method does
not exist, so it is not a scope problem), and a PUT to the blog object silently
leaves the subscription fields null - both verified 13 Sep 2026.

The script refuses to run until it can see the new property, so it is safe to run
early. It only ever touches forms whose name contains "Praxera".
"""
import json, sys, copy

exec(open('/tmp/hs.py').read())          # provides call()

BLOG_ID   = '220598739286'
OLD_PROP  = 'i_would_like_to_subscribe_to_the_davinci_blog'
NEW_LABEL = 'I would like to subscribe to the Praxera Blog'


def praxera_property():
    """The property HubSpot creates for the Praxera blog, or None if not yet made."""
    blog = call('GET', '/content/api/v2/blogs/%s' % BLOG_ID)
    prop = blog.get('subscription_contacts_property')
    if prop:
        return prop
    # fall back to a name match in case the blog object lags behind
    for p in call('GET', '/crm/v3/properties/contacts').get('results', []):
        if BLOG_ID in (p.get('name') or ''):
            return p['name']
    return None


def main(apply=False):
    prop = praxera_property()
    if not prop:
        sys.exit('Praxera blog subscription is not set up yet - switch it on in the '
                 'HubSpot UI first (see the docstring). Nothing was changed.')
    print('Praxera subscription property: %s' % prop)

    forms, offset = [], 0
    while True:
        page = call('GET', '/forms/v2/forms', q={'limit': 100, 'offset': offset})
        if not page:
            break
        forms += page
        if len(page) < 100:
            break
        offset += 100

    targets = [f for f in forms
               if 'praxera' in (f.get('name') or '').lower()
               and OLD_PROP in json.dumps(f)]
    print('Praxera forms to repoint: %d' % len(targets))

    for f in targets:
        guid = f['guid']
        live = call('GET', '/marketing/v3/forms/' + guid)      # re-read before writing
        groups = copy.deepcopy(live['fieldGroups'])
        s = json.dumps(groups)
        n = s.count(OLD_PROP)
        if not n:
            print('  %s  %-46s  no field found, skipped' % (guid[:8], (f.get('name') or '')[:46]))
            continue
        s = s.replace(OLD_PROP, prop)
        if not apply:
            print('  %s  %-46s  would repoint %d field(s)' % (guid[:8], (f.get('name') or '')[:46], n))
            continue
        json.dump(live, open('backups/blog-subscription/%s.before.json' % guid, 'w'), indent=1)
        r = call('PATCH', '/marketing/v3/forms/' + guid, b={'fieldGroups': json.loads(s)})
        after = json.dumps(r)
        print('  %s  %-46s  repointed %d | old gone=%s | new present=%s'
              % (guid[:8], (f.get('name') or '')[:46], n, OLD_PROP not in after, prop in after))

    if not apply:
        print('\nDry run. Re-run with --apply to write.')


if __name__ == '__main__':
    main(apply='--apply' in sys.argv)
