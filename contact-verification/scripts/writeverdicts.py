#!/usr/bin/env python3
"""writeverdicts.py <listId> <batch.json> - write a batch of verdicts, verify by read-back,
append to per-list log li_verdicts_<listId>.json, and queue movers to pending_movers_<listId>.json.
batch.json = [{"id","verdict"(yes|no|unreadable),"ev","ls"(optional lead status),"newco"(optional)}]
RULES enforced here so no caller can bypass them:
  - verdict 'yes'  -> NEVER writes hs_lead_status (must stay ConnectandSell Prospect or the
                      contact drops off the calling list). An 'ls' on a yes is refused.
  - lead status    -> only these literals allowed: No Longer with Company / Need Updated Info /
                      Retired - Remove from All Lists / Not Decision Maker
  - evidence       -> written to ai__contact_evidence (<=990 chars). date = today (real date).
Env: TOKEN. Pass DATE=YYYY-MM-DD to override the stamp (else uses `date -u`)."""
import json,subprocess,os,sys
T=os.environ['TOKEN']
D=os.environ.get('DATE') or subprocess.run(['date','-u','+%Y-%m-%d'],capture_output=True,text=True).stdout.strip()
lid=sys.argv[1]; V=json.load(open(sys.argv[2]))
LS_OK={"No Longer with Company","Need Updated Info","Retired - Remove from All Lists","Not Decision Maker"}
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_wv.json','w').write(json.dumps(body)); c+=['-d','@_wv.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
inputs=[];refused=[]
for r in V:
    p={"ai__li_still_at_company":r['verdict'],"ai__contact_evidence":r['ev'][:990],
       "ai__contact_verified_date":D,"ai__sources_confirming":r.get('sources',1)}
    ls=r.get('ls')
    if ls:
        if r['verdict']=='yes': refused.append((r['id'],"ls on a yes verdict")); ls=None
        elif ls not in LS_OK: refused.append((r['id'],"bad ls '"+str(ls)+"'")); ls=None
    if ls: p["hs_lead_status"]=ls
    inputs.append({"id":str(r['id']),"properties":p})
for cid,why in refused: print("REFUSED",cid,why)
# chunk at 100 (HubSpot batch cap), diff requested vs returned
applied=0
for i in range(0,len(inputs),100):
    ch=inputs[i:i+100]
    res=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/update',{"inputs":ch})
    got={str(x['id']) for x in res.get('results',[])}
    applied+=len(got)
    missing=[x['id'] for x in ch if x['id'] not in got]
    if missing: print("WARNING not returned by batch:",missing, json.dumps(res)[:200])
# read-back verification
ids=[str(r['id']) for r in V]
rb=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
   {"inputs":[{"id":i} for i in ids],"properties":["ai__li_still_at_company"]})
ok=sum(1 for x in rb.get('results',[]) if x['properties'].get('ai__li_still_at_company'))
print("applied "+str(applied)+"/"+str(len(inputs))+" | read-back confirms "+str(ok)+"/"+str(len(ids))+" | date "+D)
# per-list verdict log
f="li_verdicts_"+lid+".json"
log=json.load(open(f)) if os.path.exists(f) else []
for r in V: log.append({"id":str(r['id']),"verdict":r['verdict'],"newco":r.get('newco'),"lead_status":r.get('ls'),"date":D})
json.dump(log,open(f,'w'),indent=1)
from collections import Counter
print("li_verdicts_"+lid+" total "+str(len(log))+" "+str(dict(Counter(x['verdict'] for x in log))))
# queue movers (verdict no + a destination)
mv=[{"id":str(r['id']),"newco":r['newco']} for r in V if r['verdict']=='no' and r.get('newco')]
if mv:
    pf="pending_movers_"+lid+".json"
    pend=json.load(open(pf)) if os.path.exists(pf) else []
    pend+=mv; json.dump(pend,open(pf,'w'),indent=1)
    print("queued "+str(len(mv))+" movers -> "+pf+" (total "+str(len(pend))+")")
