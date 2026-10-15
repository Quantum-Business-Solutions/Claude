"""Maps model output to HubSpot property values. Legacy QBS property names are configurable for other portals."""
import os, re, datetime

COACH = os.environ.get('CI_COACH_PREFIX', 'cas_coach_')          # QBS keeps legacy names; other portals can use e.g. ci_coach_
TRANSCRIPT = os.environ.get('CI_TRANSCRIPT_PROP', 'cas_transcript')
AI_NOTES = os.environ.get('CI_AI_NOTES_PROP', 'cas_ai_call_notes')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

ENUMS = {'hubspot_status': {'active', 'considering', 'churned', 'never', 'unconfirmed', 'not_discussed'},
         'hubspot_dedicated_admin': {'yes', 'no', 'hiring_considering', 'unclear'},
         'hubspot_partner': {'yes_active', 'ex_partner', 'no', 'unclear'},
         'outsources_marketing': {'yes', 'no', 'unclear'}, 'outsources_seo': {'yes', 'no', 'unclear'},
         'outsources_appt_setting': {'yes', 'no', 'unclear'}, 'confidence': {'high', 'medium', 'low'},
         'budget_status': {'stated', 'discussed_no_figure', 'no_budget', 'not_mentioned'}}
TEXT = ['crm_name', 'dialer_name', 'data_tool_name', 'team_size', 'website_project', 'contract_timing_note', 'budget_amount']
VENDORS = ['equipment_lease', 'crm', 'marketing_agency', 'seo_agency', 'data_tool', 'dialer', 'appt_setting']
RATIONALES = ['crm', 'dialer', 'data_tool', 'hubspot_status', 'hubspot_admin', 'hubspot_partner', 'marketing_agency',
              'seo_agency', 'appt_setting', 'team_size', 'website_project', 'equipment_lease', 'contract_timing', 'budget']
BUDGETS = ['marketing', 'seo', 'paid_ads', 'website', 'crm', 'data_tool', 'lead_gen', 'dialer']
YN = {'yes', 'no'}


def signal_props(x, source='transcript_api', today=None):
    today = today or datetime.date.today().isoformat()
    p = {}
    for k, allowed in ENUMS.items():
        if x.get(k) in allowed: p['ai__signal_' + k] = x[k]
    for k in TEXT:
        if x.get(k): p['ai__signal_' + k] = str(x[k])[:250]
    if DATE.match(str(x.get('contract_estimated_date', ''))): p['ai__signal_contract_estimated_date'] = x['contract_estimated_date']
    for v in VENDORS:
        if DATE.match(str(x.get(v + '_contract_end', ''))): p['ai__signal_%s_contract_end' % v] = x[v + '_contract_end']
        if x.get(v + '_contract_note'): p['ai__signal_%s_contract_note' % v] = str(x[v + '_contract_note'])[:250]
    r = x.get('rationale') or {}
    for k in RATIONALES:
        if r.get(k): p['ai__signal_%s_rationale' % k] = str(r[k])[:1000]
    for b in BUDGETS:
        v = x.get('budget_%s_monthly' % b)
        if isinstance(v, (int, float)) and v > 0: p['ai__signal_budget_%s_monthly' % b] = round(v, 2)
    p.update({'ai__signal_scan_status': 'processed', 'ai__signal_source': source, 'ai__signal_scan_date': today,
              'call_intel': 'true', 'call_intel_date': today})
    return p


def coach_props(x):
    p = {}

    def put(k, v, allowed=None):
        if v in (None, '') or (allowed and v not in allowed): return
        p[COACH + k] = v
    put('opener', x.get('opener'), {'strong', 'ok', 'weak', 'not_reached'})
    put('got_to_pitch', x.get('got_to_pitch'), YN); put('asked_for_meeting', x.get('asked_for_meeting'), YN)
    if isinstance(x.get('close_attempts'), int): p[COACH + 'close_attempts'] = x['close_attempts']
    put('alternative_close', x.get('alternative_close'), YN); put('assumptive_close', x.get('assumptive_close'), YN)
    ob = [o for o in (x.get('objections') or []) if o in {'not_interested', 'no_time', 'send_info', 'already_have_vendor', 'no_budget',
          'not_decision_maker', 'call_back_later', 'gatekeeper', 'take_me_off_list', 'other', 'none'}]
    p[COACH + 'objections'] = ';'.join(ob) if ob else 'none'
    put('objection_handling', x.get('objection_handling'), {'handled_well', 'partial', 'not_handled', 'no_objection'})
    put('outcome_reason', str(x.get('outcome_reason', ''))[:250]); put('objection_summary', str(x.get('objection_summary', ''))[:5000])
    put('invite_confirmed', x.get('invite_confirmed'), {'yes', 'no', 'not_applicable'})
    st = x.get('stage_reached')
    if isinstance(st, str) and re.match(r's\d\d_', st): p[COACH + 'stage_reached'] = st
    put('decision_maker', x.get('decision_maker'), {'yes', 'no', 'unclear'})
    put('decision_maker_rationale', str(x.get('decision_maker_rationale', ''))[:1500])
    if isinstance(x.get('discovery_questions'), int): p[COACH + 'discovery_questions'] = x['discovery_questions']
    put('prospect_interest', x.get('prospect_interest'), {'hot', 'warm', 'neutral', 'cold', 'hostile'})
    put('next_step_set', x.get('next_step_set'), {'meeting', 'callback', 'send_info', 'none'})
    if isinstance(x.get('rep_talk_pct'), int): p[COACH + 'rep_talk_pct'] = x['rep_talk_pct']
    put('ask_stage', x.get('ask_stage'), {'a1_in_opener', 'a2_after_pitch', 'a3_after_discovery', 'a4_after_objection', 'a5_late_or_rushed', 'a6_never_asked'})
    if isinstance(x.get('ask_position_pct'), int): p[COACH + 'ask_position_pct'] = x['ask_position_pct']
    put('note', str(x.get('coaching_note', ''))[:1000])
    return p
