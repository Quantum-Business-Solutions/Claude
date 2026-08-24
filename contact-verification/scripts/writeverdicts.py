#!/usr/bin/env python3
"""writeverdicts.py <listId> <batch.json> - write a batch of verdicts, verify by read-back,
append to per-list log li_verdicts_<listId>.json, and queue movers to pending_movers_<listId>.json.

batch.json = [{"id","verdict"(yes|no|unreadable),"ev",
               "ls"(optional lead status),"newco"(optional),"sources"(optional),
               "title"(optional - current LinkedIn title -> ai__job_title),
               "li_url"(optional - corrected LinkedIn URL, written to BOTH url fields),
               "changed"(optional - explicit 'what changed in HubSpot' text)}]

RULES enforced here so no caller can bypass them:
  - verdict 'yes'  -> NEVER writes hs_lead_status (must stay ConnectandSell Prospect or the
                      contact drops off the calling list). An 'ls' on a yes is refused.
  - lead status    -> only these literals allowed: No Longer with Company / Need Updated Info /
                      Retired - Remove from All Lists / Not Decision Maker
  - jobtitle       -> NEVER written (3 competing integrations, ~38% oscillation). The current
                      title goes in the AI-owned field ai__job_title instead.
  - validated__linkedin_or_manually -> set from the verdict: yes->Yes, retired->Retired, else->Needs Updated
  - evidence       -> ai__contact_evidence, formatted "Verified - <date> - <evidence> - Changed: <what changed>"
                      (<=990 chars). Appended-safe; the verified date is also stamped structurally.
  - LinkedIn URL   -> when li_url is given it is written to hs_linkedin_url AND
                      linkedin_profile_url__unique_value (the unique field is set per-record so a
                      duplicate-contact collision is flagged, not allowed to block the batch).
Env: TOKEN. Pass DATE=YYYY-MM-DD to override the stamp (else uses `date -u`)."""
import json,subprocess,os,sys,re
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
def slug(u):
    if not u: return None
    m=re.search(r'/in/([^/?#]+)',u); return m.group(1).lower() if m else None
def validated_of(verdict,ls):
    if verdict=='yes': return "Yes"
    if verdict=='no' and ls=='Retired - Remove from All Lists': return "Retired"
    return "Needs Updated"   # any 'no' (moved / not DM / need info) or 'unreadable' -> a human should look
inputs=[];refused=[];urlfix=[]
for r in V:
    verdict=r['verdict']; ls=r.get('ls')
    if ls:
        if verdict=='yes': refused.append((r['id'],"ls on a yes verdict")); ls=None
        elif ls not in LS_OK: refused.append((r['id'],"bad ls '"+str(ls)+"'")); ls=None
    # build the "what changed in HubSpot" clause (explicit if given, else auto)
    if r.get('changed'):
        changed=r['changed']
    else:
        bits=["flag="+verdict]
        if ls: bits.append("lead status='"+ls+"'")
        if r.get('title'): bits.append("ai__job_title='"+r['title']+"'")
        if r.get('li_url'): bits.append("LinkedIn URL corrected")
        if r.get('newco'): bits.append("re-associate queued -> "+r['newco'])
        changed=", ".join(bits)
    ev=("Verified - "+D+" - "+r['ev']+" - Changed: "+changed)[:990]
    p={"ai__li_still_at_company":verdict,"ai__contact_evidence":ev,
       "ai__contact_verified_date":D,"ai__sources_confirming":r.get('sources',1),
       "validated__linkedin_or_manually":validated_of(verdict,ls)}
    if ls: p["hs_lead_status"]=ls
    if r.get('title'): p["ai__job_title"]=r['title']            # AI-owned title (never native jobtitle)
    if r.get('li_url'): p["hs_linkedin_url"]=r['li_url']; urlfix.append((str(r['id']),r['li_url']))
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
# sync the unique LinkedIn field per-record (unique constraint -> collision means a duplicate contact)
usync=0;ucollide=[]
for cid,url in urlfix:
    res=call('PATCH','https://api.hubapi.com/crm/v3/objects/contacts/'+cid,
        {"properties":{"linkedin_profile_url__unique_value":url}})
    if res.get('id'): usync+=1
    else: ucollide.append(cid)
if urlfix: print("LinkedIn unique-value synced "+str(usync)+"/"+str(len(urlfix))+
                 (" | collisions (duplicate contacts) -> "+str(ucollide) if ucollide else ""))
# read-back verification
ids=[str(r['id']) for r in V]
rb=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
   {"inputs":[{"id":i} for i in ids],"properties":["ai__li_still_at_company"]})
ok=sum(1 for x in rb.get('results',[]) if x['properties'].get('ai__li_still_at_company'))
print("applied "+str(applied)+"/"+str(len(inputs))+" | read-back confirms "+str(ok)+"/"+str(len(ids))+" | date "+D)
# per-list verdict log
f="li_verdicts_"+lid+".json"
log=json.load(open(f)) if os.path.exists(f) else []
for r in V: log.append({"id":str(r['id']),"verdict":r['verdict'],"newco":r.get('newco'),
                        "lead_status":r.get('ls'),"title":r.get('title'),"date":D})
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
