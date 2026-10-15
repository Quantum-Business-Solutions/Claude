"""Roll call-level answers up to company records (newest call wins), protect hand-entered values, and create tasks."""
import os, datetime, collections
from clients import hs

PORTAL = os.environ.get('HUBSPOT_PORTAL_ID', '')
TASK_OWNER = os.environ.get('CI_TASK_OWNER_ID', '')          # HubSpot owner id that receives 'considering HubSpot' tasks
TASK_PREFIX = 'Company considering HubSpot'
VENDORS = ['crm', 'marketing_agency', 'seo_agency', 'data_tool', 'dialer', 'appt_setting', 'equipment_lease']
ENUM = ['hubspot_status', 'hubspot_dedicated_admin', 'hubspot_partner', 'outsources_marketing', 'outsources_seo',
        'outsources_appt_setting', 'budget_status']
TXT = ['crm_name', 'dialer_name', 'data_tool_name', 'team_size', 'website_project', 'contract_timing_note', 'budget_amount']
DATES = ['contract_estimated_date'] + [v + '_contract_end' for v in VENDORS]
BUDGETS = ['budget_%s_monthly' % b for b in ('marketing', 'seo', 'paid_ads', 'website', 'crm', 'data_tool', 'lead_gen', 'dialer')]
PAIRS = {'crm': 'crm_name', 'dialer': 'dialer_name', 'data_tool': 'data_tool_name', 'team_size': 'team_size', 'website_project': 'website_project',
         'contract_timing': 'contract_timing_note', 'hubspot_partner': 'hubspot_partner', 'hubspot_admin': 'hubspot_dedicated_admin',
         'marketing_agency': 'outsources_marketing', 'seo_agency': 'outsources_seo', 'appt_setting': 'outsources_appt_setting',
         'equipment_lease': 'equipment_lease_contract_end', 'budget': 'budget_status'}
SKIP = {'unclear', 'not_discussed', 'not_mentioned'}
GUARD = ['currently_using_hubspot_', 'hubspot_intent_company_']      # existing hand-managed company properties
CALL_PROPS = (['hs_timestamp', 'call_intel', 'ai__signal_confidence', 'ai__signal_scan_date', 'ai__signal_hubspot_status_rationale']
              + ['ai__signal_' + k for k in ENUM + TXT + DATES + BUDGETS] + ['ai__signal_%s_rationale' % r for r in list(PAIRS)]
              + [os.environ.get('CI_COACH_PREFIX', 'cas_coach_') + k for k in ('next_step_set', 'stage_reached')])


def calls_by_company(company_ids):
    ids = list(company_ids); cmap = {}
    for i in range(0, len(ids), 100):
        b = hs('POST', '/crm/v4/associations/companies/calls/batch/read', {'inputs': [{'id': c} for c in ids[i:i + 100]]})
        for r in b.get('results', []): cmap[r['from']['id']] = [str(x['toObjectId']) for x in r['to']]
    allc = sorted({c for v in cmap.values() for c in v}); rows = {}
    for i in range(0, len(allc), 100):
        b = hs('POST', '/crm/v3/objects/calls/batch/read', {'properties': CALL_PROPS, 'inputs': [{'id': c} for c in allc[i:i + 100]]})
        for r in b.get('results', []): rows[r['id']] = r
    return {c: [rows[x] for x in v if x in rows and rows[x]['properties'].get('call_intel') == 'true'] for c, v in cmap.items()}


def _link(call_id): return 'https://app.hubspot.com/contacts/%s/record/0-48/%s' % (PORTAL, call_id)


def build_plan(calls):
    """calls: list of call records for ONE company. Returns (company_properties, meta, considering_event|None)."""
    cs = sorted(calls, key=lambda r: r['properties']['hs_timestamp'])
    out, meta, event = {}, {}, None

    def newest(field, skip=SKIP):
        for r in reversed(cs):
            v = r['properties'].get('ai__signal_' + field)
            if v and v not in skip: return r, v
        return None, None
    for f in ENUM + TXT + DATES + BUDGETS:
        r, v = newest(f, SKIP if f != 'hubspot_status' else {'not_discussed'})
        if v: out['ai__signal_' + f] = v
    for rat, fld in PAIRS.items():
        r, v = newest(fld)
        q = r and r['properties'].get('ai__signal_%s_rationale' % rat)
        if q: out['ai__signal_%s_rationale' % rat] = '%s - "%s" - %s' % (r['properties']['hs_timestamp'][:10], q, _link(r['id']))
    r, st = newest('hubspot_status', {'not_discussed'})
    if st:
        q = r['properties'].get('ai__signal_hubspot_status_rationale') or ''
        d = r['properties']['hs_timestamp'][:10]
        out['ai__signal_hubspot_verdict_rationale'] = '%s - %s - "%s" - %s' % (d, st, q, _link(r['id']))
        out['ai__signal_hubspot_verdict_date'] = d
        meta = {'date': r['properties']['hs_timestamp'], 'conf': r['properties'].get('ai__signal_confidence')}
        m = {'active': 'Yes', 'churned': 'No', 'never': 'No', 'considering': 'Considering'}.get(st)
        if m: out['currently_using_hubspot_'] = m
        if st == 'churned': out['hubspot_intent_company_'] = 'Past'
        if st == 'considering':
            pre = os.environ.get('CI_COACH_PREFIX', 'cas_coach_')
            booked = (r['properties'].get(pre + 'next_step_set') == 'meeting'
                      or (r['properties'].get(pre + 'stage_reached') or '')[:3] in ('s10', 's11', 's12'))
            event = {'call': r['id'], 'date': d, 'booked': booked, 'quote': q}
    out['ai__signal_call_count'] = len(cs)
    out['ai__signal_last_scan_date'] = max((r['properties'].get('ai__signal_scan_date') or '')[:10] for r in cs) or None
    out['ai__signal_source_call_id'] = cs[-1]['id']
    return {k: v for k, v in out.items() if v not in (None, '')}, meta, event


def protect_manual(plans, metas):
    """Hand-entered values change only if the call is newer than the edit AND high confidence. Returns counters."""
    ids = list(plans); kept = overridden = filled = 0
    for i in range(0, len(ids), 50):
        b = hs('POST', '/crm/v3/objects/companies/batch/read', {'properties': ['ai__signal_hubspot_verdict_date'],
               'propertiesWithHistory': GUARD, 'inputs': [{'id': c} for c in ids[i:i + 50]]})
        for r in b.get('results', []):
            p = plans[r['id']]; ai_managed = bool(r['properties'].get('ai__signal_hubspot_verdict_date'))
            for g in GUARD:
                if g not in p: continue
                hist = (r.get('propertiesWithHistory') or {}).get(g) or []
                if not hist: filled += 1; continue
                last = hist[0]
                if last.get('value') == p[g]: continue
                if ai_managed and (last.get('sourceType') or '') != 'CRM_UI': continue
                m = metas.get(r['id']) or {}
                if m.get('date', '')[:19] > (last.get('timestamp') or '')[:19] and m.get('conf') == 'high': overridden += 1
                else: del p[g]; kept += 1
    return {'filled': filled, 'overridden': overridden, 'kept': kept}


def _due():
    d, n = datetime.date.today(), 0
    while n < 2:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5: n += 1
    return datetime.datetime.combine(d, datetime.time(15, 0)).strftime('%Y-%m-%dT%H:%M:%S.000Z')


def _already_tasked(company_id):
    b = hs('POST', '/crm/v4/associations/companies/tasks/batch/read', {'inputs': [{'id': company_id}]})
    ids = [str(x['toObjectId']) for r in b.get('results', []) for x in r['to']]
    if not ids: return False
    t = hs('POST', '/crm/v3/objects/tasks/batch/read', {'properties': ['hs_task_subject'], 'inputs': [{'id': i} for i in ids[:100]]})
    return any((x['properties'].get('hs_task_subject') or '').startswith(TASK_PREFIX) for x in t.get('results', []))


def create_tasks(events, apply=True):
    """events: {company_id: considering_event}. One task per company, only if no meeting booked and none exists yet."""
    todo = [(c, e) for c, e in events.items() if not e['booked'] and TASK_OWNER]
    made = []
    for c, e in todo:
        if _already_tasked(c): continue
        if apply:
            t = hs('POST', '/crm/v3/objects/tasks', {'properties': {
                'hs_task_subject': '%s (said %s)' % (TASK_PREFIX, e['date']),
                'hs_task_body': 'Prospect said they are considering HubSpot on %s.\nQuote: "%s"\nCall: %s' % (e['date'], e['quote'], _link(e['call'])),
                'hs_timestamp': _due(), 'hs_task_status': 'NOT_STARTED', 'hs_task_type': 'CALL', 'hs_task_priority': 'HIGH',
                'hubspot_owner_id': TASK_OWNER}})
            hs('PUT', '/crm/v4/objects/tasks/%s/associations/default/companies/%s' % (t['id'], c))
        made.append(c)
    return made


def run(company_ids, apply=True):
    by = calls_by_company(company_ids)
    plans, metas, events = {}, {}, {}
    for c, calls in by.items():
        if not calls: continue
        plans[c], metas[c], ev = build_plan(calls)
        if ev: events[c] = ev
    prot = protect_manual(plans, metas)
    if apply:
        items = list(plans.items())
        for i in range(0, len(items), 100):
            hs('POST', '/crm/v3/objects/companies/batch/update', {'inputs': [{'id': c, 'properties': p} for c, p in items[i:i + 100]]})
    tasks = create_tasks(events, apply)
    return {'companies_updated': len(plans), 'manual_values': prot, 'considering_events': len(events), 'tasks_created': len(tasks)}


WINDOWS = ['crm', 'marketing_agency', 'seo_agency', 'data_tool', 'dialer', 'appt_setting', 'equipment_lease']


def _window(end, today):
    d = (datetime.date.fromisoformat(end[:10]) - today).days
    return 'past_due' if d < 0 else 'next_30' if d <= 30 else 'next_90' if d <= 90 else 'next_180' if d <= 180 else 'later'


def refresh_contract_windows(apply=True):
    """Recompute every company's 'contract window' dropdowns from the stored end dates (HubSpot lists can't do 'in the next N days')."""
    today = datetime.date.today(); plans = {}
    props = ['ai__signal_%s_contract_end' % v for v in WINDOWS] + ['ai__signal_%s_contract_window' % v for v in WINDOWS]
    for chunk in (WINDOWS[:5], WINDOWS[5:]):          # HubSpot allows at most 5 filter groups per search
        filt = [{'filters': [{'propertyName': 'ai__signal_%s_contract_end' % v, 'operator': 'HAS_PROPERTY'}]} for v in chunk]
        after = 0
        while True:
            r = hs('POST', '/crm/v3/objects/companies/search', {'filterGroups': filt, 'limit': 100, 'after': after, 'properties': props})
            for c in r['results']:
                upd = plans.setdefault(c['id'], {})
                for v in WINDOWS:
                    e = c['properties'].get('ai__signal_%s_contract_end' % v)
                    if e:
                        w = _window(e, today)
                        if c['properties'].get('ai__signal_%s_contract_window' % v) != w: upd['ai__signal_%s_contract_window' % v] = w
            nx = (r.get('paging') or {}).get('next', {}).get('after')
            if not nx or int(nx) >= 9900: break
            after = nx
    plans = {c: p for c, p in plans.items() if p}
    if apply:
        items = list(plans.items())
        for i in range(0, len(items), 100):
            hs('POST', '/crm/v3/objects/companies/batch/update', {'inputs': [{'id': c, 'properties': p} for c, p in items[i:i + 100]]})
    return {'windows_refreshed': len(plans)}
