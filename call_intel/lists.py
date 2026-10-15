"""Create the Call Intel lists (dynamic, so they stay current). Idempotent: skips any list whose name already exists."""
from clients import hs

VENDORS = [('crm', 'CRM'), ('marketing_agency', 'Marketing agency'), ('seo_agency', 'SEO/AEO agency'), ('data_tool', 'Data tool (ZoomInfo etc.)'),
           ('dialer', 'Dialer'), ('appt_setting', 'Appointment-setting provider'), ('equipment_lease', 'Equipment lease')]
BOOKED = ['s10_meeting_agreed', 's11_time_set', 's12_invite_confirmed']


def any_of(prop, values): return {'filterType': 'PROPERTY', 'property': prop, 'operation': {'operationType': 'ENUMERATION', 'operator': 'IS_ANY_OF', 'includeObjectsWithNoValueSet': False, 'values': values}}
def none_of(prop, values): return {'filterType': 'PROPERTY', 'property': prop, 'operation': {'operationType': 'ENUMERATION', 'operator': 'IS_NONE_OF', 'includeObjectsWithNoValueSet': True, 'values': values}}
def contains(prop, text): return {'filterType': 'PROPERTY', 'property': prop, 'operation': {'operationType': 'STRING', 'operator': 'CONTAINS', 'includeObjectsWithNoValueSet': False, 'value': text}}
def branch(*groups):   # OR of AND-groups
    return {'filterBranchType': 'OR', 'filterBranchOperator': 'OR', 'filters': [],
            'filterBranches': [{'filterBranchType': 'AND', 'filterBranchOperator': 'AND', 'filters': list(g), 'filterBranches': []} for g in groups]}


def definitions():
    L = []
    co = '0-2'
    L += [('Call Intel - Considering HubSpot', co, branch([any_of('currently_using_hubspot_', ['Considering'])])),
          ('Call Intel - Uses HubSpot (confirmed by the prospect)', co, branch([any_of('ai__signal_hubspot_status', ['active'])])),
          ('Call Intel - Uses HubSpot, no dedicated admin', co, branch([any_of('ai__signal_hubspot_status', ['active']), any_of('ai__signal_hubspot_dedicated_admin', ['no'])])),
          ('Call Intel - Left HubSpot (churned)', co, branch([any_of('ai__signal_hubspot_status', ['churned'])])),
          ('Call Intel - HubSpot mentioned but unconfirmed (verify)', co, branch([any_of('ai__signal_hubspot_status', ['unconfirmed'])])),
          ('Call Intel - Uses ZoomInfo', co, branch([contains('ai__signal_data_tool_name', 'zoominfo')])),
          ('Call Intel - Outsources marketing', co, branch([any_of('ai__signal_outsources_marketing', ['yes'])])),
          ('Call Intel - Outsources marketing and uses ZoomInfo', co, branch([any_of('ai__signal_outsources_marketing', ['yes']), contains('ai__signal_data_tool_name', 'zoominfo')])),
          ('Call Intel - Prospect stated a budget', co, branch([any_of('ai__signal_budget_status', ['stated'])]))]
    soon = ['past_due', 'next_30', 'next_90']
    for v, label in VENDORS:
        L.append(('Call Intel - %s contract ends within 90 days (or past due)' % label, co, branch([any_of('ai__signal_%s_contract_window' % v, soon)])))
    L.append(('Call Intel - Any contract ends within 90 days (or past due)', co, branch(*[[any_of('ai__signal_%s_contract_window' % v, soon)] for v, _ in VENDORS])))
    ct = '0-1'
    L += [('Call Intel - Decision makers, no meeting booked', ct, branch([any_of('ai__call_decision_maker', ['yes']), none_of('ai__call_last_stage', BOOKED)])),
          ('Call Intel - Callback requested', ct, branch([any_of('ai__call_callback_requested', ['yes'])])),
          ('Call Intel - Warm or hot on last call, no meeting', ct, branch([any_of('ai__call_last_interest', ['hot', 'warm']), none_of('ai__call_last_stage', BOOKED)])),
          ('Call Intel - Redirected to someone else (wrong person)', ct, branch([contains('ai__call_last_objections', 'not_decision_maker')])),
          ('Call Intel - Meeting agreed, invite not yet confirmed', ct, branch([any_of('ai__call_last_stage', ['s10_meeting_agreed', 's11_time_set'])]))]
    return L


def create_all():
    out = {}
    for name, obj, fb in definitions():
        ex = hs('POST', '/crm/v3/lists/search', {'query': name, 'count': 10})
        hit = [l for l in ex.get('lists', []) if l['name'] == name]
        if hit: out[name] = ('exists', hit[0]['listId']); continue
        try:
            r = hs('POST', '/crm/v3/lists', {'name': name, 'objectTypeId': obj, 'processingType': 'DYNAMIC', 'filterBranch': fb})
            out[name] = ('created', r['list']['listId'])
        except Exception as e:
            out[name] = ('ERROR', str(e)[:200])
    return out


if __name__ == '__main__':
    for n, (st, i) in create_all().items(): print(st.ljust(8), i, n)
