import json,subprocess,os
T=os.environ['TOKEN']; D="2026-08-17"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_p.json','w').write(json.dumps(body)); c+=['-d','@_p.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:300]}

L=json.load(open('email_write_log.json'))
jobs=[]
for x in L:
    if x.get('replaced'):
        jobs.append({"cid":x['cid'],"name":x['name'],"stale":x['replaced'],"clear_email":False})
    elif x.get('stale_left_in_place'):
        jobs.append({"cid":x['cid'],"name":x['name'],"stale":x['stale_left_in_place'],"clear_email":True})
# de-dupe by cid, keeping the clear_email variant if present
seen={}
for j in jobs:
    if j['cid'] in seen and not j['clear_email']: continue
    seen[j['cid']]=j
jobs=list(seen.values())

log=[]
for j in jobs:
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+j['cid']+
        "?properties=email,previous__email,previous__company_domain_name,ai__email_information,hs_lead_status")
    p=cur.get('properties') or {}
    prev_e=p.get('previous__email'); prev_d=p.get('previous__company_domain_name')
    stale=j['stale']; staledom=stale.split('@')[-1].lower()
    props={}; acts=[]
    if not prev_e:
        props['previous__email']=stale; acts.append("previous__email set")
    elif prev_e.lower()!=stale.lower():
        acts.append("previous__email ALREADY HELD "+prev_e+" - left intact")
    else:
        acts.append("previous__email already correct")
    if not prev_d:
        props['previous__company_domain_name']='https://'+staledom; acts.append("prev domain set")
    
    note=("PRIOR-EMPLOYER ADDRESS FILED "+D+": "+stale+" ("+staledom+") moved to Previous - Email."
          + (" The Email field was CLEARED because that address belongs to a former employer and "
             "no deliverable address at the current employer could be established." if j['clear_email']
             else " The Email field holds the confirmed current-employer address."))
    props['ai__email_information']=((p.get('ai__email_information') or '')+" | "+note).strip(' |')[:990]
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+j['cid'],{"properties":props})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+j['name'][:20].ljust(20)+" "+stale.ljust(34)+" | "+"; ".join(acts))
    if not ok: print("     "+json.dumps(u)[:220])
    log.append({"cid":j['cid'],"name":j['name'],"stale":stale,"cleared_email":j['clear_email'],
                "pre_existing_previous_email":prev_e,"ok":ok,"date":D})
f='previous_email_log.json'
prev=json.load(open(f)) if os.path.exists(f) else []
json.dump(prev+log,open(f,'w'),indent=1)
print("\nfiled "+str(len([x for x in log if x['ok']]))+" prior addresses; cleared "
      +str(len([x for x in log if x['ok'] and x['cleared_email']]))+" dead Email fields")
