"""Write the hard-dealer findings: 63 people at 24 dealers, plus 11 evidenced negatives.

The validated flag follows the same strict rule set earlier today:
  Yes    <- company_site, sos_filing, corporationwiki (SoS/D&B-derived), linkedin_keyword,
            contract_doc (a dated legal/state filing)
  blank  <- bbb, manta, trade_press, dealer_locator, wayback
Personal emails go to linkedin__email only; a populated business email is never overwritten.
"""
import os, sys, json, re, time, urllib.request, urllib.error
sys.path.insert(0,'/tmp')
from resolver import Companies, first_forms, last_forms, nmz, canon_li
from collections import defaultdict, Counter
S='/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
H={"Authorization":"Bearer "+os.environ['TOKEN'],"Content-Type":"application/json"}
EXECUTE='--execute' in sys.argv
def req(m,p,b=None):
    for a in range(5):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+p,
                data=json.dumps(b).encode() if b else None,headers=H,method=m)
            return json.loads(urllib.request.urlopen(r,timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503): time.sleep(2*(a+1)); continue
            return {'_err':e.code,'_b':e.read().decode()[:300]}
        except Exception: time.sleep(2*(a+1))
    return {}

STRONG={'company_site','sos_filing','corporationwiki','linkedin_keyword','linkedin','contract_doc'}
FREE={'gmail','googlemail','yahoo','ymail','hotmail','outlook','live','msn','aol','icloud','me',
      'mac','protonmail','proton','gmx','mail','zoho','yandex','comcast','verizon','att',
      'sbcglobal','bellsouth','cox','charter','spectrum','earthlink','midco','roadrunner','rr'}
def eclass(e, dealer_dom):
    e=(e or '').strip().lower()
    if not e or '@' not in e: return None,None
    dom=e.split('@')[-1]; root=dom.split('.')[0]
    if root in FREE: return e,'personal'
    dd=(dealer_dom or '').lower().replace('www.','')
    if dd and (dd in dom or dom in dd): return e,'business'
    return e,'business_other_domain'

rows=json.load(open(S+'/w_all.json'))
comps=json.load(open(S+'/dealers_live.json'))
CO=Companies(comps)
D=json.load(open(S+'/xlsx_data.json'))
held=defaultdict(list)
for cid,lst in D['contacts'].items(): held[CO.cluster(cid)] += lst

GONE=re.compile(r'\bformer\b|\bretired\b|no longer|\bex-\b|departed',re.I)
create=[]; fold=[]; conote=[]
for r in rows:
    cid=str(r.get('company_id') or '').strip()
    if not cid:
        # resolve by domain if the agent omitted the id
        dom=(r.get('domain') or '').lower()
        cid=next((k for k,p in comps.items()
                  if (p.get('domain') or '').lower().replace('www.','')==dom.replace('www.','')), '')
    if not cid: print("  no company id for", r.get('company')); continue
    cl=CO.cluster(cid); existing=held.get(cl,[])
    dealer_dom=r.get('domain')
    for p in (r.get('found') or []):
        fn=(p.get('first_name') or '').strip(); ln=(p.get('last_name') or '').strip()
        if not fn or len(ln)<2: continue
        t=(p.get('title') or '').strip()
        if GONE.search(t): continue
        em,ec = eclass(p.get('email'), dealer_dom)
        rec={'first':fn,'last':ln,'title':t,'company_id':cid,'company':r.get('company'),
             'domain':dealer_dom,'email':em,'email_class':ec,'li':p.get('linkedin_url'),
             'phone':p.get('phone'),'source':(p.get('source') or '').lower(),
             'conf':p.get('confidence'),'ev_url':p.get('evidence_url'),
             'ev_q':p.get('evidence_quote'),'legal':r.get('legal_entity')}
        fa,la=first_forms(fn),last_forms(ln)
        m=next((q for q in existing
                if (first_forms(q.get('firstname')) & fa) and (last_forms(q.get('lastname')) & la)), None)
        if m:
            rec['existing_id']=m['id']; rec['existing_title']=m.get('jobtitle')
            rec['existing_email']=m.get('email'); fold.append(rec)
        else: create.append(rec)
    conote.append({'company_id':cid,'outcome':r.get('outcome'),
                   'legal':r.get('legal_entity'),'corr':r.get('company_corrections'),
                   'why':r.get('why_not_found'),'lead':r.get('one_remaining_lead'),
                   'sources':r.get('sources_tried'),'name':r.get('company'),
                   'holds':r.get('suspected_departed') or []})
print(f"CREATE {len(create)}   FOLD {len(fold)}   company notes {len(conote)}")
print("  strong-source (validated=Yes):", sum(1 for c in create+fold if c['source'] in STRONG))
print("  weaker source (left blank)   :", sum(1 for c in create+fold if c['source'] not in STRONG))
print("  email classes:", dict(Counter(c['email_class'] for c in create+fold if c['email'])))
if not EXECUTE:
    for c in create[:10]:
        print(f"   CREATE {c['first']} {c['last']:16} {c['title'][:30]:32} {c['source']:16} "
              f"{c['email'] or '(no email)'}")
    print("\nDRY RUN - add --execute"); sys.exit(0)

def route(rec):
    ex={}
    if not rec['email']: return None, ex
    ex['linkedin__email' if rec['source'].startswith('linkedin') else 'email_other']=rec['email']
    if rec['email_class']=='personal': return None, {'linkedin__email':rec['email']}
    return rec['email'], {}

ins=[]; seen=set()
for c in create:
    k=(nmz(c['first']),nmz(c['last']),c['company_id'])
    if k in seen: continue
    seen.add(k)
    prim,extra=route(c)
    q={'firstname':c['first'][:60],'lastname':c['last'][:60],'jobtitle':c['title'][:200],
       'associatedcompanyid':c['company_id'],'ai__contact_verified_date':'2026-08-17',
       'ai__sources_confirming':1}
    if prim: q['email']=prim
    else: q['hs_lead_status']='Need Updated Info'
    q.update(extra)
    if c['source'] in STRONG: q['validated__linkedin_or_manually']='Yes'
    if c['phone']: q['phone']=str(c['phone'])[:40]
    li=canon_li(c['li'])
    if li: q['linkedin_profile_url__unique_value']=li; q['hs_linkedin_url']=li
    q['ai__contact_evidence']=(
      "CREATED 17 Aug 2026 - hard-dealer sweep (this dealer had defeated every prior attempt)\n\n"
      f"Dealer: {c['company']} ({c['domain'] or 'no domain on record'})\n"
      + (f"Legal entity: {c['legal']}\n" if c.get('legal') else "")
      + f"Source: {c['source']}   Confidence: {c['conf']}\n"
      f"Evidence: {c['ev_url'] or '(see quote)'}\n\"{(c['ev_q'] or '')[:400]}\"\n\n"
      + ("VALIDATED: this source is a live employment check (company site, state officer filing, "
         "LinkedIn, or a dated contract document), so 'Validated - LinkedIn or Manually' is set "
         "to Yes.\n" if c['source'] in STRONG else
         "NOT FLAGGED VALIDATED: the source (BBB / Manta / trade press / dealer locator) shows "
         "the person existed in the role but is not a live employment check. BBB in particular "
         "has carried dead principals for years in this dataset.\n")
      + (f"\nEMAIL: {c['email']} classified '{c['email_class']}'."
         + ("  Personal address - kept OUT of the business email field."
            if c['email_class']=='personal' else "") if c['email'] else
         "\nNo email sourced. Lead status 'Need Updated Info'."))
    ins.append({'properties':q})

def taken(idp,vals):
    hit={}; vals=[v for v in dict.fromkeys(vals) if v]
    for k in range(0,len(vals),100):
        rq=req("POST","/crm/v3/objects/contacts/batch/read",
          {"idProperty":idp,"properties":["firstname","lastname"],
           "inputs":[{"id":v} for v in vals[k:k+100]]})
        for x in rq.get('results',[]):
            key=x['properties'].get(idp)
            hit[(key or '').lower() if idp=='email' else key]=x['id']
        time.sleep(0.2)
    return hit
tl=taken('linkedin_profile_url__unique_value',
         [i['properties'].get('linkedin_profile_url__unique_value') for i in ins])
te=taken('email',[i['properties'].get('email') for i in ins])
drop=0
for i in ins:
    q=i['properties']; u=q.get('linkedin_profile_url__unique_value'); e=(q.get('email') or '').lower()
    if (u and u in tl) or (e and e in te): q['_skip']=1; drop+=1
ins=[i for i in ins if not i['properties'].pop('_skip',None)]
print(f"live pre-check dropped {drop}; creating {len(ins)}")
created=[]
for i in range(0,len(ins),50):
    ch=ins[i:i+50]
    rr=req("POST","/crm/v3/objects/contacts/batch/create",{"inputs":ch})
    if rr.get('results'): created+=[x['id'] for x in rr['results']]; time.sleep(0.4); continue
    for one in ch:
        z=req("POST","/crm/v3/objects/contacts",one)
        if z.get('id'): created.append(z['id'])
        time.sleep(0.12)
print(f"created {len(created)} of {len(ins)}")
byname={(i['properties']['firstname'].lower(),i['properties']['lastname'].lower()):
        i['properties']['associatedcompanyid'] for i in ins}
att=0
for k in range(0,len(created),100):
    rr=req("POST","/crm/v3/objects/contacts/batch/read",
      {"properties":["firstname","lastname","associatedcompanyid"],
       "inputs":[{"id":x} for x in created[k:k+100]]})
    for x in rr.get('results',[]):
        pp=x['properties']
        if (pp.get('associatedcompanyid') or '').strip(): att+=1; continue
        co=byname.get(((pp.get('firstname') or '').lower(),(pp.get('lastname') or '').lower()))
        if co and not req("PUT",f"/crm/v4/objects/contacts/{x['id']}/associations/companies/{co}",
                          [{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":1}]).get('_err'):
            att+=1
        time.sleep(0.12)
print(f"attached {att} of {len(created)}")
json.dump({'created':created}, open(S+'/hard_created.json','w'))
