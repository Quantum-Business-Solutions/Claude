"""Pull ConnectAndSell conversations for a date window and write transcripts onto the matching HubSpot call records."""
import datetime, re
from zoneinfo import ZoneInfo
from clients import cas, hs
import props

LA = ZoneInfo('America/Los_Angeles')   # CAS ConversationDate is in the account's local time
CALL_PROPS = ['hs_timestamp', 'hs_call_duration', 'hs_call_body', 'hs_call_recording_url', props.TRANSCRIPT]


def conversations(day_from, day_to):
    """All Quantum seats' conversations in [day_from, day_to] (inclusive). Window must be < 90 days."""
    users = cas('GET', '/api/Reports/GetUsers')
    users = users.get('data') or users.get('Data') or users
    uid = [u['Key'] for u in users if isinstance(u, dict) and u.get('Key')]
    out, p = {}, 1
    while True:
        r = cas('POST', '/api/Reports/ConversationHistoryReport',
                {'FromDate': str(day_from), 'ToDate': str(day_to), 'UserId': uid, 'SessionType': 'All', 'CallType': 'Both',
                 'CallReview': 'Both', 'PageNumber': p, 'PageSize': 500})
        for x in r.get('data') or []: out[x['LeadtransitId']] = x
        if not (r.get('Paging') or {}).get('NextPage'): break
        p += 1
    return list(out.values())


def _calls_for_contacts(contact_ids):
    by = {}
    ids = list(contact_ids)
    for i in range(0, len(ids), 100):
        b = hs('POST', '/crm/v4/associations/contacts/calls/batch/read', {'inputs': [{'id': c} for c in ids[i:i + 100]]})
        for r in b.get('results', []): by[r['from']['id']] = [str(x['toObjectId']) for x in r['to']]
    allc = sorted({c for v in by.values() for c in v}); props_by = {}
    for i in range(0, len(allc), 100):
        b = hs('POST', '/crm/v3/objects/calls/batch/read', {'properties': CALL_PROPS, 'inputs': [{'id': c} for c in allc[i:i + 100]]})
        for r in b.get('results', []): props_by[r['id']] = r['properties']
    return by, props_by


def _utc(ts):
    return datetime.datetime.fromisoformat(ts[:26]).replace(tzinfo=LA).astimezone(datetime.timezone.utc).replace(tzinfo=None)


def match(conv, call_ids, props_by):
    """Best HubSpot call for a CAS conversation. Order: recording-id (exact) > duration+time > notes call > attempt call."""
    lid, talk, t0 = str(conv['LeadtransitId']), float(conv.get('TalkTime') or 0), _utc(conv['ConversationDate'])
    best = None
    for cid in call_ids:
        p = props_by.get(cid)
        if not p: continue
        h = datetime.datetime.fromisoformat(p['hs_timestamp'].replace('Z', '+00:00')).replace(tzinfo=None)
        dm = (h - t0).total_seconds() / 60
        body = p.get('hs_call_body') or ''
        score = None
        if lid in (p.get('hs_call_recording_url') or ''): score = (0, abs(dm))
        elif p.get('hs_call_duration') and abs(float(p['hs_call_duration']) / 1000 - talk) <= 3 and abs(dm) <= 180: score = (1, abs(dm))
        elif body.startswith('CAS Call Notes') and 0 <= dm <= talk / 60 + 25: score = (2, dm)
        elif 'Agent Disposition: Conversation' in body and -1 <= dm <= 2: score = (3, abs(dm))
        if score and (best is None or score < best[0]): best = (score, cid)
    return best[1] if best else None


def sync(day_from, day_to, apply=True):
    """Returns (stats, {call_id: properties written}). Skips calls that already have a transcript."""
    convs = [c for c in conversations(day_from, day_to)
             if c.get('Transcript') and 'not available' not in c['Transcript'] and len(c['Transcript']) >= 40 and c.get('CrmId')]
    for c in convs: c['CrmId'] = re.sub(r'\.0$', '', str(c['CrmId']))
    by, props_by = _calls_for_contacts({c['CrmId'] for c in convs})
    claimed, writes, unmatched = set(), {}, 0
    for c in sorted(convs, key=lambda c: c['ConversationDate']):
        cid = match(c, by.get(c['CrmId'], []), props_by)
        if not cid or cid in claimed: unmatched += 1; continue
        claimed.add(cid)
        if props_by[cid].get(props.TRANSCRIPT): continue
        w = {props.TRANSCRIPT: c['Transcript'][:60000], 'transcript_source': 'connectandsell'}
        if c.get('AICallNotes') and 'No AI Call Notes' not in c['AICallNotes']: w[props.AI_NOTES] = c['AICallNotes'][:60000]
        writes[cid] = w
    if apply:
        items = list(writes.items())
        for i in range(0, len(items), 100):
            hs('POST', '/crm/v3/objects/calls/batch/update', {'inputs': [{'id': k, 'properties': v} for k, v in items[i:i + 100]]})
    return {'conversations_with_transcript': len(convs), 'written': len(writes), 'unmatched': unmatched}, writes
