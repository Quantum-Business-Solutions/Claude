"""Nightly sync of ConnectAndSell pickup counts onto HubSpot contacts.

Maintains: cas_user_not_available_count, cas_last_user_not_available_date,
cas_conversation_count_est, last_pickup_date.

Idempotent: finds contacts touched by a pickup-type call in the last N days, then
recounts ALL of each such contact's calls and overwrites the four properties.
Safe to re-run. Needs env QBS_HUBSPOT_TOKEN and the CA bundle at /root/.ccr/ca-bundle.crt
(falls back to the default store).

Usage: python3 pickup_sync.py [days=5]
"""
import os, sys, re, json, ssl, time, datetime as dt, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

TOKEN = os.environ['QBS_HUBSPOT_TOKEN']
CA = '/root/.ccr/ca-bundle.crt'
CTX = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else ssl.create_default_context()
HUMD = {'Connected','Meeting scheduled','Interest, Call Back Later','Interest, Send Info','Not Interested, Follow up','No Pitch','Busy, Call Back Later','Busy, Send Information','Not Decision Maker','Referral','Blocked By Gatekeeper','Disqualified, Reason in Notes','Quantum More Info Email','Meeting Rescheduled','Do Not Call','Incorrect Contact','No Longer with Company','Wrong number','Voicemail Pick-up','Interest, Send Info - OFI','Busy, Send Information - OFI','Referral - Partial Info','Retired - Remove from All Lists'}

def call(method, path, body=None):
    for a in range(7):
        req = urllib.request.Request('https://api.hubapi.com' + path, json.dumps(body).encode() if body is not None else None,
                                     {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}, method=method)
        try:
            return json.load(urllib.request.urlopen(req, context=CTX, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504): time.sleep(2 + a * 2); continue
            raise
        except Exception:
            time.sleep(2 + a)
    raise RuntimeError('failed ' + path)

def chunks(l, n):
    for i in range(0, len(l), n): yield l[i:i + n]

def classify(p, disp_map):
    """-> 'conv' | 'una' | 'hum' | None"""
    b = p.get('hs_call_body') or ''
    if b.startswith('ConnectAndSell Agent'):
        m = re.search(r'Agent Disposition:\s*([^<\n]+)', b)
        cd = m.group(1).strip() if m else None
        return 'conv' if cd == 'Conversation' else ('una' if cd == 'User Not Available' else None)
    return 'hum' if disp_map.get(p.get('hs_call_disposition')) in HUMD else None

def assoc(frm, to, ids):
    out = {}
    for ch in chunks(ids, 100):
        j = call('POST', f'/crm/v4/associations/{frm}/{to}/batch/read', {'inputs': [{'id': str(x)} for x in ch]})
        for r in j.get('results', []): out[str(r['from']['id'])] = [str(t['toObjectId']) for t in r.get('to', [])]
    return out

def main(days):
    disp = {d['id']: d['label'] for d in call('GET', '/calling/v1/dispositions')}
    props = ['hs_timestamp', 'hs_call_body', 'hs_call_disposition']
    start = (dt.datetime.utcnow() - dt.timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    touched_calls = []
    d = start
    while d < dt.datetime.utcnow() + dt.timedelta(days=1):
        w0, w1 = d.strftime('%Y-%m-%dT%H:%M:%SZ'), (d + dt.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        after = None
        while True:
            body = {'filterGroups': [{'filters': [{'propertyName': 'hs_timestamp', 'operator': 'GTE', 'value': w0}, {'propertyName': 'hs_timestamp', 'operator': 'LT', 'value': w1}]}],
                    'properties': props, 'limit': 200, 'sorts': [{'propertyName': 'hs_timestamp', 'direction': 'ASCENDING'}]}
            if after: body['after'] = after
            j = call('POST', '/crm/v3/objects/calls/search', body)
            touched_calls += [r['id'] for r in j['results'] if classify(r['properties'], disp)]
            after = j.get('paging', {}).get('next', {}).get('after')
            if not after: break
            if len(touched_calls) > 60000: break
        d += dt.timedelta(days=1)
    print('pickup-type calls in window:', len(touched_calls))
    c_of = assoc('calls', 'contacts', touched_calls)
    contacts = sorted({c for v in c_of.values() for c in v})
    print('contacts to recount:', len(contacts))
    if not contacts: return

    def recount(ch):
        calls_of = assoc('contacts', 'calls', ch)
        allc = sorted({c for v in calls_of.values() for c in v})
        info = {}
        for cc in chunks(allc, 100):
            r = call('POST', '/crm/v3/objects/calls/batch/read', {'properties': props, 'inputs': [{'id': x} for x in cc]})
            for x in r['results']: info[x['id']] = x['properties']
        updates = []
        for cid in ch:
            conv = hum = una = 0; lc = lh = lu = ''
            for callid in calls_of.get(cid, []):
                p = info.get(callid)
                if not p: continue
                k = classify(p, disp); ts = (p.get('hs_timestamp') or '')[:10]
                if k == 'conv': conv += 1; lc = max(lc, ts)
                elif k == 'hum': hum += 1; lh = max(lh, ts)
                elif k == 'una': una += 1; lu = max(lu, ts)
            pr = {}
            pr['cas_conversation_count_est'] = str(max(conv, hum))
            pr['cas_user_not_available_count'] = str(una)
            pr['cas_last_user_not_available_date'] = lu
            pr['last_pickup_date'] = max([x for x in (lc, lh, lu) if x] or [''])
            updates.append({'id': cid, 'properties': pr})
        call('POST', '/crm/v3/objects/contacts/batch/update', {'inputs': updates})
        return len(updates)

    done = 0
    with ThreadPoolExecutor(3) as ex:
        for n in ex.map(recount, list(chunks(contacts, 50))): done += n
    print('contacts updated:', done)

if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
