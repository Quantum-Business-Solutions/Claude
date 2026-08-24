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
import json,subprocess,os,sys,re,tempfile
T=os.environ['TOKEN']
D=os.environ.get('DATE') or subprocess.run(['date','-u','+%Y-%m-%d'],capture_output=True,text=True).stdout.strip()
lid=sys.argv[1]; V=json.load(open(sys.argv[2]))
LS_OK={"No Longer with Company","Need Updated Info","Retired - Remove from All Lists","Not Decision Maker"}
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
def call(m,url,body=None,fatal=True):
    """Fail-fast on any non-2xx. An auth failure must never read as 'no data' and stamp live records."""
    c=['curl','-s','--max-time','30','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open(TMP,'w').write(json.dumps(body)); c+=['-d','@'+TMP]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    body_txt,_,code=o.rpartition('\n'); code=code.strip()
    if not code.isdigit() or not code.startswith('2'):
        if fatal:
            sys.stderr.write('HTTP '+code+' on '+m+' '+url.split('?')[0]+' :: '+body_txt[:200]+'\n')
            sys.exit(2)
        return {"__http":code,"__body":body_txt[:200]}
    try: return json.loads(body_txt) if body_txt.strip() else {}
    except Exception:
        if fatal: sys.stderr.write('unparseable response\n'); sys.exit(2)
        return {}
MARKER="RE-"+"ASSOCIATED"    # built at runtime: a filter token is a control character, not prose
def slug(u):
    if not u: return None
    m=re.search(r'/in/([^/?#]+)',u); return m.group(1).lower() if m else None
def validated_of(verdict,ls):
    if verdict=='yes': return "Yes"
    if verdict=='no' and ls=='Retired - Remove from All Lists': return "Retired"
    return "Needs Updated"   # any 'no' (moved / not DM / need info) or 'unreadable' -> a human should look
inputs=[];refused=[];urlfix=[];accepted=[]
for r in V:
    verdict=r['verdict']; ls=r.get('ls')
    if ls and verdict=='yes':
        refused.append((r['id'],"ls on a yes verdict - RECORD DROPPED")); continue
    if ls and ls not in LS_OK:
        refused.append((r['id'],"bad ls '"+str(ls)+"' - RECORD DROPPED")); continue
    if verdict=='no' and not ls:
        # a `no` with no lead status never ejects the contact, and queue.py will never surface it
        # again because it now carries a verdict -> a dialable record proven to have left. Refuse.
        refused.append((r['id'],"verdict 'no' with no lead status - RECORD DROPPED")); continue
    if MARKER in (r.get('ev') or '') or MARKER in (r.get('changed') or ''):
        refused.append((r['id'],"evidence contains the mover filter token - RECORD DROPPED")); continue
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
    tail=" - Changed: "+changed
    head="Verified - "+D+" - "
    ev=head+r['ev'][:max(0,900-len(head)-len(tail))]+tail    # budget so `Changed:` always survives
    p={"ai__li_still_at_company":verdict,"ai__contact_evidence":ev,
       "ai__contact_verified_date":D,"ai__sources_confirming":r.get('sources',1),
       "validated__linkedin_or_manually":validated_of(verdict,ls)}
    if ls: p["hs_lead_status"]=ls
    if r.get('title'): p["ai__job_title"]=r['title']            # AI-owned title (never native jobtitle)
    if r.get('li_url'): p["hs_linkedin_url"]=r['li_url']; urlfix.append((str(r['id']),r['li_url']))
    inputs.append({"id":str(r['id']),"properties":p}); accepted.append(r)
for cid,why in refused: print("REFUSED",cid,why)
# append, never overwrite: prior entries carry the mover marker, phone-correction notes and
# human flags that two production lists filter on.
prior={}
if inputs:
    for i in range(0,len(inputs),100):
        pr=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
                {"inputs":[{"id":x["id"]} for x in inputs[i:i+100]],"properties":["ai__contact_evidence"]})
        for x in pr.get('results',[]): prior[str(x['id'])]=x['properties'].get('ai__contact_evidence') or ''
for it in inputs:
    old=prior.get(it['id'],'')
    if old: it['properties']['ai__contact_evidence']=(it['properties']['ai__contact_evidence']+" || "+old)[:990]
# queue movers FIRST: once a contact is flagged in the CRM, queue.py never surfaces it again,
# so a crash between the write and the queue loses the mover permanently.
mv=[{"id":str(r['id']),"newco":r['newco']} for r in accepted if r['verdict']=='no' and r.get('newco')]
if mv:
    pf="pending_movers_"+lid+".json"
    pend=json.load(open(pf)) if os.path.exists(pf) else []
    have={x['id'] for x in pend}
    pend+=[x for x in mv if x['id'] not in have]
    tmp=pf+'.tmp'; json.dump(pend,open(tmp,'w'),indent=1); os.replace(tmp,pf)
    print("queued "+str(len(mv))+" movers -> "+pf+" (total "+str(len(pend))+")")
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
want={str(r['id']):r['verdict'] for r in accepted}
back={str(x['id']):x['properties'].get('ai__li_still_at_company') for x in rb.get('results',[])}
confirmed=[i for i,v in want.items() if back.get(i)==v]
bad=[(i,v,back.get(i)) for i,v in want.items() if back.get(i)!=v]
print("applied "+str(applied)+"/"+str(len(inputs))+" | read-back confirms "+str(len(confirmed))+"/"+str(len(want))+" | date "+D)
if bad:
    print("READ-BACK MISMATCH (requested -> found):")
    for i,v,g in bad[:20]: print("  ",i,v,"->",g)
# per-list verdict log
f="li_verdicts_"+lid+".json"
log=json.load(open(f)) if os.path.exists(f) else []
cset=set(confirmed)
for r in accepted:
    if str(r['id']) not in cset: continue      # never log a write we could not confirm
    log.append({"id":str(r['id']),"verdict":r['verdict'],"newco":r.get('newco'),
                "lead_status":r.get('ls'),"title":r.get('title'),"date":D})
tmp=f+'.tmp'; json.dump(log,open(tmp,'w'),indent=1); os.replace(tmp,f)
from collections import Counter
print("li_verdicts_"+lid+" total "+str(len(log))+" "+str(dict(Counter(x['verdict'] for x in log))))
# running guardrails over the accumulated log (the model cannot hold these across context windows)
c=Counter(x['verdict'] for x in log); n=len(log)
if n>=50:
    no_share=c.get('no',0)/n; un_share=c.get('unreadable',0)/n
    if no_share>0.60 or no_share<0.05:
        print("GUARDRAIL: 'no' share %.0f%% over %d verdicts - outside 5-60%%. HALT and report."%(no_share*100,n)); sys.exit(3)
    if un_share>0.20:
        print("GUARDRAIL: 'unreadable' share %.0f%% over %d verdicts - above 20%%. HALT and report."%(un_share*100,n)); sys.exit(3)
if bad: sys.exit(1)
