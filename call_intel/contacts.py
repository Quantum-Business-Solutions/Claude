"""Roll call-level answers up to contact records (newest call wins). All target properties are Call Intel's own - nothing hand-entered is touched."""
import os, datetime
from clients import hs

P = os.environ.get('CI_COACH_PREFIX', 'cas_coach_')
PORTAL = os.environ.get('HUBSPOT_PORTAL_ID', '')
CALL_PROPS = ['hs_timestamp', 'call_intel'] + [P + k for k in ('decision_maker', 'decision_maker_rationale', 'stage_reached', 'prospect_interest', 'objections', 'next_step_set')]


def calls_by_contact(contact_ids):
    ids = list(contact_ids); cmap = {}
    for i in range(0, len(ids), 100):
        b = hs('POST', '/crm/v4/associations/contacts/calls/batch/read', {'inputs': [{'id': c} for c in ids[i:i + 100]]})
        for r in b.get('results', []): cmap[r['from']['id']] = [str(x['toObjectId']) for x in r['to']]
    allc = sorted({c for v in cmap.values() for c in v}); rows = {}
    for i in range(0, len(allc), 100):
        b = hs('POST', '/crm/v3/objects/calls/batch/read', {'properties': CALL_PROPS, 'inputs': [{'id': c} for c in allc[i:i + 100]]})
        for r in b.get('results', []): rows[r['id']] = r
    return {c: [rows[x] for x in v if x in rows and rows[x]['properties'].get(P + 'stage_reached')] for c, v in cmap.items()}


def build(calls):
    cs = sorted(calls, key=lambda r: r['properties']['hs_timestamp']); last = cs[-1]['properties']; out = {}
    out['ai__call_last_date'] = last['hs_timestamp'][:10]; out['ai__call_intel_count'] = len(cs)
    out['ai__call_last_stage'] = last.get(P + 'stage_reached')
    if last.get(P + 'prospect_interest'): out['ai__call_last_interest'] = last[P + 'prospect_interest']
    ob = [o for o in (last.get(P + 'objections') or '').split(';') if o and o != 'none']
    out['ai__call_last_objections'] = ', '.join(ob) if ob else 'none'
    out['ai__call_callback_requested'] = 'yes' if last.get(P + 'next_step_set') == 'callback' else 'no'
    for r in reversed(cs):                       # newest clear decision-maker answer wins
        dm = r['properties'].get(P + 'decision_maker')
        if dm in ('yes', 'no'):
            out['ai__call_decision_maker'] = dm
            if r['properties'].get(P + 'decision_maker_rationale'):
                out['ai__call_decision_maker_rationale'] = '%s - %s - https://app.hubspot.com/contacts/%s/record/0-48/%s' % (
                    r['properties']['hs_timestamp'][:10], r['properties'][P + 'decision_maker_rationale'][:700], PORTAL, r['id'])
            break
    else:
        out['ai__call_decision_maker'] = 'unclear'
    return out


def run(contact_ids, apply=True):
    by = calls_by_contact(contact_ids)
    plans = {c: build(v) for c, v in by.items() if v}
    if apply:
        items = list(plans.items())
        for i in range(0, len(items), 100):
            hs('POST', '/crm/v3/objects/contacts/batch/update', {'inputs': [{'id': c, 'properties': p} for c, p in items[i:i + 100]]})
    return {'contacts_updated': len(plans)}
