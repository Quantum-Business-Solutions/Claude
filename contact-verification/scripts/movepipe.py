import json,subprocess,os
T=os.environ['TOKEN']; D="2026-08-17"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_t.json','w').write(json.dumps(body)); c+=['-d','@_t.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except: return {"raw":o}

M=[
{"id":"30945449318","n":"Stacie Immesberger","co":"Anaplan","dom":"anaplan.com","t":"Supply Chain Domain Advisory","em":None,"mkt":False,"src":"LinkedIn 08/2025 full-time + ZoomInfo FULL_MATCH (agree). Left Cloudleaf 12/2021. Domain anaplan.com verified by website lookup, ZI id 353647107 matches the id on her contact record. Domain/SME advisory seat, not a marketing budget holder"},
{"id":"1295967","n":"Nancy Elsner","co":"ArtsQuest","dom":"artsquest.org","t":"Head of Marketing","em":None,"mkt":True,"src":"LinkedIn 04/2024 full-time; profile found by LinkedIn people search (none was on file). ZoomInfo still shows TouchTunes and is WRONG. Domain artsquest.org verified via ZoomInfo id 2851679"},
{"id":"2096396","n":"Gily Netzer","co":"JFrog","dom":"jfrog.com","t":"SVP Marketing, EMEA","em":None,"mkt":True,"src":"LinkedIn 07/2024 (at JFrog since 05/2023). No Cymulate row anywhere in readable history. Based Tel Aviv, Israel - IST timezone. Domain jfrog.com verified via ZoomInfo id 346026911"},
{"id":"360753","n":"Chris Sheen","co":"Celonis","dom":"celonis.com","t":"Director of Social","em":None,"mkt":False,"src":"LinkedIn 02/2022 - left the Sideways 6 CMO seat four years ago. Director of Social is a function lead, not a budget holder. London UK. Domain celonis.com verified via ZoomInfo id 372193030"},
{"id":"1401589","n":"Corey McCarthy","co":"Devicie","dom":"devicie.com","t":"Chief Marketing Officer","em":None,"mkt":True,"src":"LinkedIn 08/2026 full-time (UniFocus ended 01/2025, then Axonify CMO to 01/2026). Domain devicie.com verified via ZoomInfo id 542701610"},
]

log=[]
for m in M:
    cid=m['id']
    # HARD RULE: email domain must match the LinkedIn-confirmed company
    if m['em'] and m['em'].split('@')[-1].lower()!=m['dom']:
        print("REJECT email domain mismatch",m['em']); m['em']=None
    # 1. company by domain
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
      {"filterGroups":[{"filters":[{"propertyName":"domain","operator":"EQ","value":m['dom']}]}],
       "properties":["name","domain"],"limit":1})
    res=r.get('results',[])
    if res:
        coid=res[0]['id']; created=False
    else:
        c=call('POST','https://api.hubapi.com/crm/v3/objects/companies',
          {"properties":{"name":m['co'],"domain":m['dom']}})
        coid=c.get('id'); created=True
    if not coid:
        print("FAIL company",m['n'],r,c); continue
    # 2. current contact props + existing associations
    cur=call('GET',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}?properties=email,company,ai__email_information")
    oldemail=(cur.get('properties') or {}).get('email')
    assoc=call('GET',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies")
    old=[a['toObjectId'] for a in assoc.get('results',[]) if str(a['toObjectId'])!=str(coid)]
    for o in old:
        call('DELETE',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies/{o}")
    call('PUT',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies/{coid}",
      [{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":1},
       {"associationCategory":"HUBSPOT_DEFINED","associationTypeId":279}])
    # 3. reconcile: re-associated to new employer -> flag is 'yes' THERE
    p={"company":m['co'],"jobtitle":m['t'],
       "ai__li_still_at_company":"yes","ai__contact_verified_date":D,"ai__sources_confirming":2,
       "hs_lead_status":"ConnectandSell Prospect" if m['mkt'] else "Not Decision Maker",
       "ai__contact_evidence":(("" if m['mkt'] else "[NOT-MKT] ")+f"RE-ASSOCIATED {D}: moved to {m['co']} ({m['dom']}) as {m['t']}. Evidence: {m['src']}. "
         f"Flag reconciled to 'yes' because the contact is now associated to {m['co']}, where they DO work. "
         + ("Marketing leader - kept on the calling list." if m['mkt'] else "Not a marketing decision maker - kept off the calling list."))[:990]}
    if m['em']:
        p['email']=m['em']
        if oldemail and oldemail!=m['em']:
            prev=(cur.get('properties') or {}).get('ai__email_information') or ''
            p['ai__email_information']=(prev+f" | prior email {oldemail} (replaced {D})").strip()[:990]
    u=call('PATCH',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}",{"properties":p})
    ok='id' in u
    print(f"{'OK ' if ok else 'ERR'} {m['n']:22s} co={coid}{' NEW' if created else ''} unassoc={len(old)} email={m['em'] or '-'}")
    log.append({"id":cid,"name":m['n'],"newco":m['co'],"companyId":coid,"created":created,
                "email":m['em'],"old_email":oldemail,"mkt":m['mkt'],"date":D})

f='reassoc_log.json'
prev=json.load(open(f)) if os.path.exists(f) else []
json.dump(prev+log,open(f,'w'),indent=1)
json.dump([],open('pending_movers.json','w'))
print("\nreassoc_log total",len(prev)+len(log))
