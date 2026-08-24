#!/usr/bin/env python3
"""movepipe.py <listId> <movers.json> - re-associate confirmed movers to their new employer,
one HubSpot transaction per contact, with the qbs-list-verification conventions.

movers.json = [{"id","newco",
                "domain"(optional - verified company domain; find-or-create by it),
                "dm"(optional bool - is the person a decision-maker at newco?),
                "ls"(optional lead status override; default: dm->ConnectandSell Prospect else Not Decision Maker),
                "title"(optional - current title -> ai__job_title),
                "li_url"(optional - corrected LinkedIn URL -> BOTH url fields),
                "ev"(evidence string; the mechanism, dates, sources)}]

Per contact: find-or-create company (by domain if given, else by exact name), DELETE stale company
associations, PUT the new one with BOTH associationTypeId 1 AND 279, reconcile the flag to `yes`,
set `company`, set `ai__job_title` + `validated__linkedin_or_manually`, stamp evidence as
`Verified - <date> - <ev> - Changed: RE-ASSOCIATED to <newco> ...` (must contain RE-ASSOCIATED so the
Moved-Companies list picks it up), and set lead status. NEVER writes native `jobtitle`. The phone is
left untouched so a personal/mobile number carries; the evidence flags "verify phone before dialing".
A corrected LinkedIn URL is written to hs_linkedin_url AND (per-record) linkedin_profile_url__unique_value;
a unique-value collision means a duplicate/wrong-linked contact -> logged, not forced.
Env: TOKEN. DATE=YYYY-MM-DD optional. Appends to reassoc_<listId>_log.json; clears pending_movers_<listId>.json."""
import json,subprocess,os,sys,re,tempfile
T=os.environ['TOKEN']; D=os.environ.get('DATE') or subprocess.run(['date','-u','+%Y-%m-%d'],capture_output=True,text=True).stdout.strip()
lid=sys.argv[1]; M=json.load(open(sys.argv[2]))
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
MARKER="RE-"+"ASSOCIATED"   # built at runtime so the source file cannot seed the filter token
def call(m,url,body=None,fatal=True):
    """Returns (data, ok). A timeout or 4xx must never look like an empty result set - that is how
    a failed associations read turns into 'there was nothing stale to remove'."""
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
        return {"__http":code}
    try: return json.loads(body_txt) if body_txt.strip() else {}
    except Exception: return {}
logf='reassoc_'+lid+'_log.json'
log=json.load(open(logf)) if os.path.exists(logf) else []
done={x['id'] for x in log if x.get('ok')}
for m in M:
    cid=str(m['id'])
    if cid in done: continue
    newco=m['newco']; dom=m.get('domain')
    if 'dm' not in m:
        # absent dm used to fall through to "Not Decision Maker", silently ejecting a verified
        # executive from the calling list. Failing closed means "don't write", not "write the
        # ejecting value".
        log.append({"id":cid,"newco":newco,"ok":False,"err":"dm not supplied - refusing to guess"})
        print("SKIP  "+cid+" no dm supplied"); continue
    dm=m['dm']
    if MARKER in (m.get('ev') or ''):
        log.append({"id":cid,"newco":newco,"ok":False,"err":"ev contains the filter token"})
        print("SKIP  "+cid+" evidence contains the mover filter token"); continue
    # 1. find-or-create company
    coid=None; created=False
    if dom:
        r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
          {"filterGroups":[{"filters":[{"propertyName":"domain","operator":"EQ","value":dom}]}],"properties":["name"],"limit":1})
        res=r.get('results',[])
        if res: coid=res[0]['id']
        else:
            c=call('POST','https://api.hubapi.com/crm/v3/objects/companies',{"properties":{"name":newco,"domain":dom}}); coid=c.get('id'); created=True
    else:
        r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
          {"filterGroups":[{"filters":[{"propertyName":"name","operator":"EQ","value":newco}]}],"properties":["name","domain"],"limit":10})
        res=r.get('results',[])
        if len(res)>1:
            # two companies can share a name. Queue, never guess - picking results[0] silently
            # attaches the contact to whichever record sorted first.
            dr='dedupe_review_'+lid+'.json'
            d=json.load(open(dr)) if os.path.exists(dr) else []
            d.append({"contact":cid,"newco":newco,"candidates":[{"id":x['id'],"name":x['properties'].get('name'),"domain":x['properties'].get('domain')} for x in res]})
            tmp=dr+'.tmp'; json.dump(d,open(tmp,'w'),indent=1); os.replace(tmp,dr)
            log.append({"id":cid,"newco":newco,"ok":False,"err":str(len(res))+" companies share this name - queued to "+dr})
            print("QUEUE "+cid+" "+str(len(res))+" companies named '"+newco[:30]+"' -> "+dr); continue
        if res: coid=res[0]['id']
        else:
            c=call('POST','https://api.hubapi.com/crm/v3/objects/companies',{"properties":{"name":newco}}); coid=c.get('id'); created=True
    if not coid:
        log.append({"id":cid,"newco":newco,"ok":False,"err":"no company id"}); json.dump(log,open(logf,'w'),indent=1); print("FAIL company",cid); continue
    # 2. swap associations
    prev=call('GET',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}?properties=company,ai__contact_evidence")
    prev_company=(prev.get('properties') or {}).get('company')
    prev_ev=(prev.get('properties') or {}).get('ai__contact_evidence') or ''
    assoc=call('GET',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies",fatal=False)
    if 'results' not in assoc:
        # a timeout here used to yield old=[] - indistinguishable from "nothing stale to remove" -
        # leaving the contact associated to BOTH employers with the log reading unassoc:0.
        log.append({"id":cid,"newco":newco,"ok":False,"err":"associations read failed: "+str(assoc)[:80]})
        print("FAIL  "+cid+" associations read failed - contact left untouched"); continue
    old=[a['toObjectId'] for a in assoc.get('results',[]) if str(a['toObjectId'])!=str(coid)]
    for o in old: call('DELETE',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies/{o}")
    call('PUT',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies/{coid}",
      [{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":1},{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":279}])
    # 3. reconcile contact
    ls=m.get('ls') or ("ConnectandSell Prospect" if dm else "Not Decision Maker")
    domnote=dom if dom else "UNRESOLVED (verify/enrich)"
    tail=(f" - Changed: {MARKER} to {newco} ({domnote}); was '{prev_company}' (assoc {old}); flag->yes; "
          f"lead status='{ls}'; phone carried (verify before dialing); "
          f"{'ai__job_title set; ' if m.get('title') else ''}{'LinkedIn URL corrected; ' if m.get('li_url') else ''}"
          f"{'decision-maker' if dm else 'not a decision-maker'} at new company.")
    head=f"Verified - {D} - "
    ev=head+str(m.get('ev',''))[:max(0,900-len(head)-len(tail))]+tail
    if prev_ev: ev=(ev+" || "+prev_ev)[:990]
    p={"company":newco,"ai__li_still_at_company":"yes","ai__contact_verified_date":D,
       "ai__sources_confirming":m.get('sources',1),
       "ai__contact_evidence":ev,"hs_lead_status":ls,
       "validated__linkedin_or_manually":("Yes" if dm else "Needs Updated")}
    if m.get('title'): p["ai__job_title"]=m['title']
    if m.get('li_url'): p["hs_linkedin_url"]=m['li_url']
    if prev_company and prev_company!=newco: p["previous__company_domain_name"]=prev_company
    u=call('PATCH',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}",{"properties":p}); ok='id' in u
    ucol=False
    if ok and m.get('li_url'):
        ur=call('PATCH',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}",{"properties":{"linkedin_profile_url__unique_value":m['li_url']}})
        ucol=not ur.get('id')
    log.append({"id":cid,"newco":newco,"companyId":coid,"created":created,"dm":dm,"title":m.get('title'),
                "unassoc":len(old),"unassoc_ids":old,"prev_company":prev_company,"lead_status":ls,"url_unique_collision":ucol,"ok":ok,"err":None if ok else str(u)[:150]})
    print(f"{'OK ' if ok else 'ERR'} {cid} -> {newco[:26]:26} co={coid}{' NEW' if created else ''} ls={ls}"+(" UNIQUE-COLLISION(dup?)" if ucol else ""))
    json.dump(log,open(logf,'w'),indent=1)
okc=sum(1 for x in log if x.get('ok'))
print(f"\nreassoc_{lid}_log: {len(log)} | ok {okc} | companies created {sum(1 for x in log if x.get('created'))}"
      f" | unique-URL collisions (dedupe review) {sum(1 for x in log if x.get('url_unique_collision'))}")
# remove ONLY the movers this run actually completed - blanking the file used to discard every
# mover that was queued but not in this batch, and they are already flagged so nothing resurfaces them.
pf='pending_movers_'+lid+'.json'
if os.path.exists(pf):
    okids={x['id'] for x in log if x.get('ok')}
    rest=[x for x in json.load(open(pf)) if str(x['id']) not in okids]
    tmp=pf+'.tmp'; json.dump(rest,open(tmp,'w'),indent=1); os.replace(tmp,pf)
    print(f"pending_movers: {len(rest)} still queued")
