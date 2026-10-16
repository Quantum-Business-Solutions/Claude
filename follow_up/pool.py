"""Build the emailable pool for a HubSpot contact list and rank it by company Most Recent Active Engagement.

    python3 -m follow_up.pool <listId> [--out pool.json] [--include-one-to-one-optout]

Read-only. Exclusions (reason is recorded, never silent): no email, global unsubscribe (hs_email_optout),
Instantly bounce/unsubscribe, NeverBounce invalid/disposable, do-not-market, LinkedIn 'moved'
(held for re-check, not dropped), disqualified. 'One to One' opt-out is only a hold unless the
operator has said to include it (default here: INCLUDE, per Shawn 2026-10-16).
"""
import sys, json, datetime as dt
from call_intel.clients import hs

PROPS = ['firstname', 'lastname', 'email', 'jobtitle', 'company', 'lifecyclestage', 'hs_lead_status',
         'hs_email_optout', 'hs_email_optout_21316497', 'instantly_bounced', 'instantly_unsubscribed',
         'neverbouncevalidationresult', 'do_not_market_to_', 'hs_latest_disqualified_lead_date',
         'ai__li_still_at_company', 'hs_linkedin_url', 'first_touch_is_linkedin_connected',
         'notes_last_contacted', 'hs_latest_meeting_activity', 'meeting__most_recent_start_time']
CO_PROPS = ['name', 'most_recent_active_engagement_date_v2', 'most_recent_active_engagement_date']


def _d(s):
    if not s:
        return None
    s = str(s)
    try:
        if s.isdigit() and len(s) > 8:
            return dt.datetime.utcfromtimestamp(int(s) / 1000).date()
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        return None


def members(list_id):
    ids, after = [], None
    while True:
        r = hs('GET', '/crm/v3/lists/%s/memberships?limit=250%s' % (list_id, '&after=%s' % after if after else ''))
        ids += [x['recordId'] for x in r['results']]
        after = r.get('paging', {}).get('next', {}).get('after')
        if not after:
            return ids


def batch(obj, ids, props):
    out = []
    for i in range(0, len(ids), 100):
        out += hs('POST', '/crm/v3/objects/%s/batch/read' % obj,
                  {'inputs': [{'id': str(x)} for x in ids[i:i + 100]], 'properties': props})['results']
    return out


def build(list_id, include_one_to_one=True, today=None):
    today = today or dt.date.today()
    rows = [dict(id=x['id'], **x['properties']) for x in batch('contacts', members(list_id), PROPS)]
    pool, held = [], {}
    for r in rows:
        why = None
        if not r.get('email'): why = 'no email'
        elif r.get('hs_email_optout') == 'true': why = 'unsubscribed from all email'
        elif not include_one_to_one and r.get('hs_email_optout_21316497') == 'true': why = 'one-to-one opt-out'
        elif r.get('instantly_bounced') == 'true' or r.get('instantly_unsubscribed') == 'true': why = 'bounced/unsub (verify before sending)'
        elif r.get('neverbouncevalidationresult') in ('invalid', 'disposable'): why = 'invalid email'
        elif r.get('do_not_market_to_'): why = 'do not market'
        elif r.get('hs_latest_disqualified_lead_date'): why = 'disqualified'
        elif r.get('ai__li_still_at_company') == 'moved': why = 'LinkedIn says moved (re-check full history)'
        if why:
            held.setdefault(why, []).append(r['id']); continue
        pool.append(r)
    ids = [r['id'] for r in pool]
    a = hs('POST', '/crm/v4/associations/contacts/companies/batch/read', {'inputs': [{'id': i} for i in ids]})
    cm = {x['from']['id']: x['to'][0]['toObjectId'] for x in a['results'] if x['to']}
    cp = {x['id']: x['properties'] for x in batch('companies', sorted({str(v) for v in cm.values()}), CO_PROPS)}
    d = hs('POST', '/crm/v4/associations/contacts/deals/batch/read', {'inputs': [{'id': i} for i in ids]})
    dm = {x['from']['id']: [t['toObjectId'] for t in x['to']] for x in d['results']}
    dp = {x['id']: x['properties'] for x in batch('deals', sorted({z for v in dm.values() for z in v}),
          ['dealname', 'dealstage', 'amount', 'hs_is_closed', 'pipeline'])}
    stg = {s['id']: s['label'] for p in hs('GET', '/crm/v3/pipelines/deals')['results'] for s in p['stages']}
    for r in pool:
        c = cp.get(str(cm.get(r['id'], '')), {})
        r['co'] = c.get('name')
        m = _d(c.get('most_recent_active_engagement_date_v2')) or _d(c.get('most_recent_active_engagement_date'))
        r['mrae'] = str(m) if m else ''
        r['mrae_age'] = (today - m).days if m else None
        r['deals'] = [dict(dp[str(z)], stage=stg.get(dp[str(z)].get('dealstage'))) for z in dm.get(r['id'], []) if str(z) in dp]
        r['open_deals'] = [x for x in r['deals'] if x.get('hs_is_closed') != 'true']
    pool.sort(key=lambda r: (0 if r['open_deals'] else 1, r['mrae_age'] if r['mrae_age'] is not None else 10 ** 6))
    return {'pool': pool, 'held': held}


if __name__ == '__main__':
    lid = sys.argv[1]
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'pool.json'
    res = build(lid, include_one_to_one='--exclude-one-to-one' not in sys.argv)
    json.dump(res, open(out, 'w'))
    print(len(res['pool']), 'in pool;', {k: len(v) for k, v in res['held'].items()}, '->', out)
