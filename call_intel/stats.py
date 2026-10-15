"""Aggregate Call Intel results into one JSON document (totals and percentages only - no names, no quotes)."""
import os, json, datetime, collections
from clients import hs

P = os.environ.get('CI_COACH_PREFIX', 'cas_coach_')
CALL_FIELDS = ['hs_timestamp', 'hubspot_owner_id', 'call_intel', 'transcript_source'] + [P + k for k in (
    'stage_reached', 'opener', 'ask_stage', 'asked_for_meeting', 'alternative_close', 'assumptive_close', 'objections',
    'objection_handling', 'prospect_interest', 'decision_maker', 'invite_confirmed', 'next_step_set', 'got_to_pitch')]
CO_FIELDS = ['ai__signal_hubspot_status', 'ai__signal_crm_name', 'ai__signal_data_tool_name', 'ai__signal_outsources_marketing',
             'ai__signal_outsources_seo', 'ai__signal_outsources_appt_setting', 'ai__signal_budget_status', 'currently_using_hubspot_'] + \
            ['ai__signal_%s_contract_end' % v for v in ('crm', 'marketing_agency', 'seo_agency', 'data_tool', 'dialer', 'appt_setting', 'equipment_lease')]


def _pull(obj, filters_for_window, props, start, end, step=31):
    rows, w = [], start
    while w < end:
        w2 = min(w + datetime.timedelta(days=step), end); after = 0
        while True:
            r = hs('POST', '/crm/v3/objects/%s/search' % obj, {'filterGroups': [{'filters': filters_for_window(w, w2)}],
                   'limit': 100, 'after': after, 'properties': props})
            rows += r['results']; nx = (r.get('paging') or {}).get('next', {}).get('after')
            if not nx: break
            after = nx
        w = w2
    return rows


def _ms(d): return str(int(d.timestamp() * 1000))


def _pct(n, d): return round(100 * n / d, 1) if d else 0


def _calls_block(rows):
    g = lambda r, k: r['properties'].get(P + k)
    n = len(rows); c = collections.Counter
    scored = [r for r in rows if g(r, 'stage_reached')]
    ob = c(o for r in scored for o in (g(r, 'objections') or '').split(';') if o and o != 'none')
    booked = [r for r in scored if (g(r, 'stage_reached') or '')[:3] in ('s10', 's11', 's12')]
    return {'calls_scored': len(scored),
            'stage': dict(c(g(r, 'stage_reached') for r in scored)), 'opener': dict(c(g(r, 'opener') for r in scored if g(r, 'opener'))),
            'ask_stage': dict(c(g(r, 'ask_stage') for r in scored if g(r, 'ask_stage'))),
            'interest': dict(c(g(r, 'prospect_interest') for r in scored if g(r, 'prospect_interest'))),
            'decision_maker': dict(c(g(r, 'decision_maker') for r in scored if g(r, 'decision_maker'))),
            'objections': dict(ob.most_common()),
            'rates': {'asked_for_meeting_pct': _pct(sum(g(r, 'asked_for_meeting') == 'yes' for r in scored), len(scored)),
                      'alternative_close_pct': _pct(sum(g(r, 'alternative_close') == 'yes' for r in scored), len(scored)),
                      'assumptive_close_pct': _pct(sum(g(r, 'assumptive_close') == 'yes' for r in scored), len(scored)),
                      'booked_pct': _pct(len(booked), len(scored)),
                      'invite_confirmed_of_booked_pct': _pct(sum(g(r, 'invite_confirmed') == 'yes' for r in booked), len(booked))}}


def build(owner_names=None):
    today = datetime.datetime.utcnow(); start = datetime.datetime(2022, 1, 1)
    calls = _pull('calls', lambda a, b: [{'propertyName': 'call_intel', 'operator': 'EQ', 'value': 'true'},
                  {'propertyName': 'hs_timestamp', 'operator': 'GTE', 'value': _ms(a)}, {'propertyName': 'hs_timestamp', 'operator': 'LT', 'value': _ms(b)}],
                  CALL_FIELDS, start, today + datetime.timedelta(days=2))
    wk = [r for r in calls if r['properties']['hs_timestamp'][:10] >= (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d')]
    by_owner = collections.defaultdict(list)
    for r in calls:
        if r['properties'].get('hubspot_owner_id') and r['properties']['hs_timestamp'] >= (today - datetime.timedelta(days=90)).isoformat(): by_owner[r['properties']['hubspot_owner_id']].append(r)
    names = owner_names or {}
    reps = {}
    for o, rs in by_owner.items():
        b = _calls_block(rs)
        if b['calls_scored'] >= 30: reps[names.get(o, 'Rep %d' % (len(reps) + 1))] = {'calls_scored': b['calls_scored'], **b['rates'], 'opener': b['opener']}
    cos = _pull('companies', lambda a, b: [{'propertyName': 'ai__signal_call_count', 'operator': 'HAS_PROPERTY'},
                {'propertyName': 'createdate', 'operator': 'GTE', 'value': _ms(a)}, {'propertyName': 'createdate', 'operator': 'LT', 'value': _ms(b)}],
                CO_FIELDS, datetime.datetime(2000, 1, 1), today + datetime.timedelta(days=2), step=3650)
    c = collections.Counter; lower = lambda r, k: (r['properties'].get(k) or '').strip().lower()
    soon = {}
    horizon = (today + datetime.timedelta(days=90)).strftime('%Y-%m-%d'); now = today.strftime('%Y-%m-%d')
    for v in ('crm', 'marketing_agency', 'seo_agency', 'data_tool', 'dialer', 'appt_setting', 'equipment_lease'):
        k = 'ai__signal_%s_contract_end' % v
        soon[v] = sum(1 for r in cos if r['properties'].get(k) and now <= r['properties'][k][:10] <= horizon)
    return {'generated': today.strftime('%Y-%m-%d'),
            'all_time': _calls_block(calls), 'last_7_days': _calls_block(wk), 'reps_last_90_days': reps,
            'companies': {'with_signals': len(cos),
                          'hubspot_status': dict(c(lower(r, 'ai__signal_hubspot_status') for r in cos if lower(r, 'ai__signal_hubspot_status'))),
                          'currently_using_hubspot': dict(c(r['properties'].get('currently_using_hubspot_') for r in cos if r['properties'].get('currently_using_hubspot_'))),
                          'crm_top': dict(c(lower(r, 'ai__signal_crm_name')[:24] for r in cos if lower(r, 'ai__signal_crm_name')).most_common(10)),
                          'data_tool_top': dict(c(lower(r, 'ai__signal_data_tool_name')[:24] for r in cos if lower(r, 'ai__signal_data_tool_name')).most_common(8)),
                          'outsources_marketing': dict(c(lower(r, 'ai__signal_outsources_marketing') for r in cos if lower(r, 'ai__signal_outsources_marketing'))),
                          'budget_status': dict(c(lower(r, 'ai__signal_budget_status') for r in cos if lower(r, 'ai__signal_budget_status'))),
                          'contracts_ending_next_90_days': soon}}
