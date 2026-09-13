"""Brand every Praxera blog-notification email (BLOG_EMAIL on subscription 3608525332).

HubSpot scaffolds each frequency as "New email" from the account defaults, which here means
Shawn's personal from-name/reply-to and the wrong footer office location. This normalises
them to match the other 111 Praxera emails. Safe to re-run: it only writes what is wrong.
"""
import json, sys, re
exec(open('/tmp/hs.py').read())

SUB_ID   = '3608525332'
OFFICE   = '221681937557'            # the Praxera address the other 111 emails use
FROM     = {'fromName': 'Praxera', 'replyTo': 'info@praxerasupplements.com'}
SUBJECTS = {'instant': 'New on the Praxera blog: {{ content.name }}',
            'daily':   'Today on the Praxera blog',
            'weekly':  'This week on the Praxera blog',
            'monthly': 'This month on the Praxera blog'}


def frequency(email):
    """instant / daily / weekly / monthly, from the name HubSpot gave it."""
    n = (email.get('name') or '').lower()
    for f in SUBJECTS:
        if f in n:
            return f
    return None


def main(apply=False):
    emails, after = [], None
    while True:
        q = {'limit': 100, 'archived': 'false'}
        if after:
            q['after'] = after
        r = call('GET', '/marketing/v3/emails', q=q)
        emails += r.get('results', [])
        after = r.get('paging', {}).get('next', {}).get('after')
        if not after:
            break

    mine = [e for e in emails
            if (e.get('type') or '') == 'BLOG_EMAIL'
            and str((e.get('subscriptionDetails') or {}).get('subscriptionId')) == SUB_ID]
    print('Praxera blog-notification emails: %d' % len(mine))

    for e in mine:
        eid = e['id']
        live = call('GET', '/marketing/v3/emails/' + eid)       # re-read before writing
        freq = frequency(live)
        body = {}
        if freq:
            want_name = 'Praxera - Blog: %s notification' % freq.capitalize()
            if live.get('name') != want_name:
                body['name'] = want_name
            if not (live.get('subject') or '').strip():
                body['subject'] = SUBJECTS[freq]
        elif (live.get('name') or '').strip().lower() == 'new email':
            print('  %s  still called "New email" and no frequency in the name — '
                  'left alone, rename it in HubSpot first' % eid)
        if json.dumps(live.get('from')) != json.dumps(FROM):
            body['from'] = FROM
        sd = dict(live.get('subscriptionDetails') or {})
        if sd.get('officeLocationId') != OFFICE:
            sd['officeLocationId'] = OFFICE
            body['subscriptionDetails'] = sd
        if not body:
            print('  %s  %-42s already correct' % (eid, (live.get('name') or '')[:42]))
            continue
        if not apply:
            print('  %s  %-42s would set: %s' % (eid, (live.get('name') or '')[:42], ', '.join(body)))
            continue
        r = call('PATCH', '/marketing/v3/emails/' + eid, b=body)
        print('  %s  %-42s -> from=%s reply=%s office=%s'
              % (eid, (r.get('name') or '')[:42],
                 (r.get('from') or {}).get('fromName'),
                 (r.get('from') or {}).get('replyTo'),
                 (r.get('subscriptionDetails') or {}).get('officeLocationId')))
    if not apply:
        print('\nDry run. Re-run with --apply to write.')


if __name__ == '__main__':
    main(apply='--apply' in sys.argv)
