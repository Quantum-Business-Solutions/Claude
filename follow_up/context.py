"""Pull the real relationship history for each contact so a draft can be specific.

    python3 -m follow_up.context pool.json <contactId,contactId,...> [--out ctx.json]

Read-only. Keeps meetings, human replies and outbound subjects. CAS 'Attempt' call logs are
noise and are summarised as counts only; calls with a 'Conversation' disposition are listed by date.
"""
import sys, re, json
from call_intel.clients import hs

SPEC = {'notes': ['hs_note_body', 'hs_timestamp'],
        'emails': ['hs_email_subject', 'hs_email_text', 'hs_email_direction', 'hs_timestamp'],
        'calls': ['hs_call_title', 'hs_call_body', 'hs_timestamp'],
        'meetings': ['hs_meeting_title', 'hs_meeting_body', 'hs_meeting_start_time', 'hs_meeting_outcome', 'hs_internal_meeting_notes']}


def _t(h):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h or '')).strip()


def history(cid):
    ev = []
    for ot, props in SPEC.items():
        a = hs('GET', '/crm/v4/objects/contacts/%s/associations/%s?limit=100' % (cid, ot))
        ids = [x['toObjectId'] for x in a['results']]
        if not ids:
            continue
        for x in hs('POST', '/crm/v3/objects/%s/batch/read' % ot, {'inputs': [{'id': str(i)} for i in ids[:100]], 'properties': props})['results']:
            p = x['properties']
            ev.append({'type': ot, 'date': (p.get('hs_timestamp') or p.get('hs_meeting_start_time') or '')[:10],
                       'title': p.get('hs_email_subject') or p.get('hs_call_title') or p.get('hs_meeting_title') or '',
                       'dir': p.get('hs_email_direction') or p.get('hs_meeting_outcome'),
                       'text': _t(p.get('hs_note_body') or p.get('hs_email_text') or p.get('hs_call_body') or p.get('hs_meeting_body') or p.get('hs_internal_meeting_notes'))[:700]})
    ev.sort(key=lambda e: e['date'], reverse=True)
    return ev


def brief(ev):
    return {'meetings': [e for e in ev if e['type'] == 'meetings'][:6],
            'replies': [e for e in ev if e['type'] == 'emails' and e['dir'] == 'INCOMING_EMAIL'
                        and not e['title'].startswith(('Read:', 'Not read', 'Accepted', 'Declined', 'Out of', 'Automatic'))][:6],
            'out_emails': [(e['date'], e['title'][:60]) for e in ev if e['type'] == 'emails' and e['dir'] == 'EMAIL'][:8],
            'conversation_calls': [e['date'] for e in ev if e['type'] == 'calls' and 'Disposition: Conversation' in e['text']][:5],
            'call_attempts': sum(1 for e in ev if e['type'] == 'calls')}


if __name__ == '__main__':
    pool = {r['id']: r for r in json.load(open(sys.argv[1]))['pool']}
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'ctx.json'
    res = {}
    for cid in sys.argv[2].split(','):
        r = pool.get(cid, {})
        res[cid] = dict(name='%s %s' % (r.get('firstname'), r.get('lastname')), email=r.get('email'), title=r.get('jobtitle'),
                        company=r.get('company'), mrae=r.get('mrae'), deals=r.get('deals'), **brief(history(cid)))
    json.dump(res, open(out, 'w'), indent=1)
    print(len(res), 'contacts ->', out)
