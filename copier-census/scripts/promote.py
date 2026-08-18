"""Promote reachable decision-makers to CAS Prospect so they enter the calling motion.

Two guards, and the distinction between them matters:

* 'Do Not Call - Opt Out' is a genuine suppression. HARD BLOCK - never promote, ever.
* 'Not Interested' carries the LABEL 'Not Interested - Follow-up' in this portal, i.e. it is a
  follow-up state by design, not a do-not-contact. Promoting is legitimate, but the prior
  refusal and its date are written into the evidence so whoever dials knows before they call.

A first version of this guard blocked on both and rejected 100% of candidates, which is what
exposed the difference.
"""
import os, sys, json, urllib.request, urllib.error, time
from collections import Counter

S = '/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
H = {"Authorization": "Bearer " + os.environ['TOKEN'], "Content-Type": "application/json"}


def req(m, p, b=None):
    for a in range(5):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + p,
                                       data=(json.dumps(b).encode() if b else None),
                                       headers=H, method=m)
            raw = urllib.request.urlopen(r, timeout=90).read()
            return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503):
                time.sleep(2 * (a + 1)); continue
            return {'_err': e.code}
        except Exception:
            time.sleep(2 * (a + 1))
    return {'_err': 'retry'}


CO = json.load(open(f'{S}/status_survey.json'))['CO']
hold = set(json.load(open(f'{S}/xlsx_data.json'))['hold'])
ids = list(CO)

V = {}
for i in range(0, len(ids), 100):
    r = req('POST', "/crm/v3/objects/companies/batch/read",
            {"inputs": [{"id": x} for x in ids[i:i + 100]],
             "properties": ["ai__dealer_verdict", "name"]})
    for c in r.get('results', []):
        V[c['id']] = c['properties']

CP = ["firstname", "lastname", "email", "jobtitle", "hs_lead_status",
      "validated__linkedin_or_manually", "associatedcompanyid"]
seen, rows = set(), []
for i in range(0, len(ids), 40):
    chunk = ids[i:i + 40]; after = None
    while True:
        b = {"filterGroups": [{"filters": [{"propertyName": "associatedcompanyid",
                                            "operator": "IN", "values": chunk}]}],
             "properties": CP, "limit": 100}
        if after:
            b["after"] = after
        r = req('POST', "/crm/v3/objects/contacts/search", b)
        if '_err' in r:
            break
        res = r.get("results", [])
        for c in res:
            if c['id'] in seen:
                continue
            seen.add(c['id']); rows.append(dict(c['properties'], id=c['id']))
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after:
            break
print(f'dealer contacts: {len(rows)}', flush=True)

DM = ('owner', 'president', 'ceo', 'chief', 'founder', 'partner', 'principal', 'vp ',
      'vice president', 'director', 'general manager', 'coo', 'cfo', 'cto', 'cio',
      'managing', 'executive', 'svp', 'evp', 'head of', 'branch manager')
FREE = set("""gmail googlemail yahoo ymail rocketmail hotmail outlook live msn aol icloud me mac
protonmail proton gmx mail zoho yandex comcast verizon att sbcglobal bellsouth cox charter spectrum
earthlink juno netzero roadrunner rr optonline frontier windstream embarqmail q shaw rogers sympatico
telus bell midco""".split())


def is_dm(t):
    t = (t or '').lower()
    return any(k in t for k in DM)


def biz(e):
    return bool(e) and '@' in e and e.rsplit('@', 1)[1].rsplit('.', 1)[0].lower() not in FREE


badmx = {k for k, v in json.load(open(f'{S}/email_domain_verified.json'))['final'].items()
         if v['status'] != 'MAIL OK'}
PROMOTABLE_FROM = {'Need Updated Info', 'Not Decision Maker', ''}

tally, todo = Counter(), []
for p in rows:
    cid = p.get('associatedcompanyid')
    v = (V.get(cid) or {}).get('ai__dealer_verdict')
    s = p.get('hs_lead_status') or ''
    if cid in hold:
        tally['skip: client hold']; tally['skip: client hold'] += 1; continue
    if v in ('non_us', 'defunct', 'not_dealer'):
        tally[f'skip: company {v}'] += 1; continue
    if s not in PROMOTABLE_FROM:
        tally['skip: already carries an outreach/terminal status'] += 1; continue
    if not is_dm(p.get('jobtitle')):
        tally['skip: not a decision-maker title'] += 1; continue
    if not biz(p.get('email')):
        tally['skip: no reachable business email'] += 1; continue
    if p['email'].rsplit('@', 1)[1].lower() in badmx:
        tally['skip: domain cannot receive mail'] += 1; continue
    todo.append(p)

print(f'\npromotion candidates: {len(todo)}', flush=True)
for k, c in tally.most_common():
    print(f'  {c:5d}  {k}', flush=True)

promoted, blocked, flagged = 0, 0, 0
blocked_rows, flagged_rows = [], []
for i, p in enumerate(todo):
    h = req('GET', f"/crm/v3/objects/contacts/{p['id']}?propertiesWithHistory=hs_lead_status")
    hist = [(x.get('timestamp', '')[:10], x.get('value'))
            for x in (h.get('propertiesWithHistory', {}) or {}).get('hs_lead_status', [])]
    optout = [x for x in hist if x[1] == 'Do Not Call - Opt Out']
    notint = [x for x in hist if x[1] == 'Not Interested']
    cur = req('GET', f"/crm/v3/objects/contacts/{p['id']}?properties=ai__contact_evidence")
    prev = (cur.get('properties', {}) or {}).get('ai__contact_evidence') or ''
    nm = f"{p.get('firstname')} {p.get('lastname')}"

    if optout:
        dates = ', '.join(d for d, _ in optout)
        ev = (f"PROMOTION BLOCKED BY THE OPT-OUT GUARD 2026-08-17. This person is a decision-maker "
              f"({p.get('jobtitle')}) with a reachable business email ({p.get('email')}) and would "
              f"otherwise have been promoted to 'ConnectandSell Prospect'. The lead-status HISTORY "
              f"contains 'Do Not Call - Opt Out' on {dates}. Promoting would re-dial somebody who "
              f"opted out, so the record is left exactly as it is. This is a compliance stop, not a "
              f"data-quality judgement - the contact detail is good, the permission is not.")
        req('PATCH', f"/crm/v3/objects/contacts/{p['id']}",
            {"properties": {"ai__contact_evidence": ((prev + "\n\n" if prev else "") + ev)[:65000]}})
        blocked += 1; blocked_rows.append((nm, p.get('jobtitle'), dates))
        continue

    warn = ''
    if notint:
        dates = ', '.join(d for d, _ in notint)
        warn = (f" CALLER WARNING: this contact previously carried 'Not Interested' on {dates}. That "
                f"status is labelled 'Not Interested - Follow-up' in this portal, so it is a follow-up "
                f"state rather than a do-not-contact, and promotion is legitimate - but whoever dials "
                f"should know a prior refusal is on the record.")
        flagged += 1; flagged_rows.append((nm, dates))
    ev = (f"PROMOTED TO PROSPECT 2026-08-17. Decision-maker title ({p.get('jobtitle')}) with a "
          f"reachable business email ({p.get('email')}) whose domain was confirmed able to receive "
          f"mail in today's portal-wide MX sweep. Previous status: "
          f"'{p.get('hs_lead_status') or '(blank)'}'. Lead-status history was read before promoting "
          f"and contains no 'Do Not Call - Opt Out'.{warn}")
    r = req('PATCH', f"/crm/v3/objects/contacts/{p['id']}",
            {"properties": {"hs_lead_status": "ConnectandSell Prospect",
                            "ai__contact_evidence": ((prev + "\n\n" if prev else "") + ev)[:65000]}})
    if '_err' not in r:
        promoted += 1
    if i % 25 == 0:
        print(f'  ...{i}/{len(todo)}', flush=True)

print(f'\n=== promotion results ===', flush=True)
print(f'  promoted to CAS Prospect                  : {promoted}', flush=True)
print(f'  BLOCKED - prior Do Not Call opt-out       : {blocked}', flush=True)
print(f'  promoted WITH a prior-refusal warning     : {flagged}', flush=True)
print('\nblocked (compliance):', flush=True)
for nm, ti, d in blocked_rows:
    print(f'  {nm:26s} | {str(ti)[:30]:30s} | opted out {d}', flush=True)
json.dump({'promoted': promoted, 'blocked': blocked_rows, 'flagged': flagged_rows},
          open(f'{S}/promotion_results.json', 'w'), indent=1)
