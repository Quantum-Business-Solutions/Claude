import re,json,collections,datetime,hsapi
def norm(s): return re.sub(r'[^a-z0-9 ]+',' ',(s or '').lower()).split()
def joined(s): return ' '.join(norm(s))
RAT=['crm','dialer','data_tool','hubspot_status','hubspot_admin','hubspot_partner','marketing_agency','seo_agency','appt_setting','team_size','website_project','equipment_lease','contract_timing','budget']
F=['cas_transcript','ai__signal_hubspot_status','ai__signal_source','cas_coach_decision_maker','cas_coach_decision_maker_rationale','cas_coach_stage_reached','cas_coach_asked_for_meeting','cas_coach_invite_confirmed','cas_coach_next_step_set','cas_coach_objections','cas_coach_objection_handling','cas_coach_objection_summary','ai__signal_budget_status','ai__signal_budget_amount','ai__signal_crm_name','ai__signal_data_tool_name']+['ai__signal_%s_rationale'%r for r in RAT]
ids=[];w=datetime.datetime(2022,1,1)
while w<datetime.datetime(2026,10,17):
    w2=w+datetime.timedelta(days=31);after=0
    while True:
        r=hsapi.call('POST','/crm/v3/objects/calls/search',{'filterGroups':[{'filters':[{'propertyName':'cas_transcript','operator':'HAS_PROPERTY'},{'propertyName':'call_intel','operator':'EQ','value':'true'},{'propertyName':'hs_timestamp','operator':'GTE','value':str(int(w.timestamp()*1000))},{'propertyName':'hs_timestamp','operator':'LT','value':str(int(w2.timestamp()*1000))}]}],'limit':100,'after':after,'properties':['hs_timestamp']})
        ids+=[x['id'] for x in r['results']];nx=r.get('paging',{}).get('next',{}).get('after')
        if not nx: break
        after=nx
    w=w2
print('transcript calls to audit',len(ids),flush=True)
fail=collections.defaultdict(list);tot=collections.Counter();incons=collections.defaultdict(list)
def quotes(t):
    q=[m for m in re.findall(r'"([^"]{12,})"',t or '')]
    if not q and t and len(t)>=12: q=[t.split(' | ')[0]]
    return q
for i in range(0,len(ids),100):
    for r in hsapi.call('POST','/crm/v3/objects/calls/batch/read',{'properties':F,'inputs':[{'id':x} for x in ids[i:i+100]]})['results']:
        p=r['properties'];T=joined(p.get('cas_transcript'));cid=r['id']
        for k in RAT+['decision_maker']:
            f='cas_coach_decision_maker_rationale' if k=='decision_maker' else 'ai__signal_%s_rationale'%k
            v=p.get(f)
            if not v: continue
            for q in quotes(v):
                parts=[x for x in re.split(r'\.\.\.|…',q) if len(x)>=12]
                ok=all(joined(x) in T for x in parts) if parts else True
                tot[k]+=1
                if not ok: fail[k].append(cid)
        # consistency
        st=(p.get('cas_coach_stage_reached') or '')[:3]
        if st in('s11','s12') and p.get('cas_coach_asked_for_meeting')=='no': incons['booked_but_no_ask'].append(cid)
        if p.get('cas_coach_invite_confirmed')=='yes' and st not in('s10','s11','s12'): incons['invite_yes_but_not_booked'].append(cid)
        if p.get('cas_coach_next_step_set')=='meeting' and st not in('s10','s11','s12'): incons['next_meeting_but_stage'].append(cid)
        if p.get('ai__signal_hubspot_status') in('active','considering','churned','never') and not p.get('ai__signal_hubspot_status_rationale'): incons['hubspot_status_no_quote'].append(cid)
        if p.get('cas_coach_decision_maker')=='yes' and not p.get('cas_coach_decision_maker_rationale'): incons['dm_yes_no_rationale'].append(cid)
        if p.get('ai__signal_budget_status')=='stated' and not p.get('ai__signal_budget_amount'): incons['budget_stated_no_amount'].append(cid)
        if 'none' in (p.get('cas_coach_objections') or '').split(';') and len((p.get('cas_coach_objections') or '').split(';'))>1: incons['objection_none_plus_other'].append(cid)
        if p.get('cas_coach_objection_handling')=='no_objection' and (p.get('cas_coach_objections') or 'none')!='none': incons['no_objection_but_listed'].append(cid)
print('QUOTE CHECK (quote text found in the transcript):')
for k in RAT+['decision_maker']:
    if tot[k]: print(f'  {k:18} {1-len(fail[k])/tot[k]:6.1%} verified of {tot[k]}')
print('CONSISTENCY:',{k:len(v) for k,v in incons.items()})
json.dump({'fail':fail,'incons':incons},open('qa_result.json','w'))
