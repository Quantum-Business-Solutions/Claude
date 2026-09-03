#!/usr/bin/env python3
"""moverqueue.py - turn every contact carrying `ai__pending_mover_to` into a movepipe queue.

The verdict step records WHERE somebody went; this closes the loop by resolving that destination to
a real HubSpot company and preparing the re-association. It exists because the gap between those
two steps is where people got lost: measured 2026-09-03, 450 contacts carried verdict `no` and 446
had no destination or association anywhere, because a portal workflow detaches the company twenty
seconds after the ejection status is written and nothing ever put them anywhere else.

Run it in the same pass as the verdicts:

    TOKEN=... python3 moverqueue.py [--overrides overrides.json] [--out movers.json]
    TOKEN=... python3 movepipe.py <listId> movers.json

What it does, and the reason for each part:

* Reads the queue FROM HUBSPOT, never a local file. A scheduled container is destroyed after the
  run, so `pending_movers_<lid>.json` is gone by the next fire; `ai__pending_mover_to` survives.
* Resolves the destination by EXACT company name in HubSpot, and accepts it only when exactly one
  record matches AND it carries a domain. movepipe needs a proven domain to write native
  `jobtitle`, and one company name matching several records is the classic silent mis-association.
* Everything it cannot resolve is written to <out>.unresolved.json rather than guessed. Enrich
  those names (ZoomInfo `enrich_companies` works well) and feed the domains back through
  --overrides as {"Company Name": "domain.com"}. A destination with no proven domain still gets
  re-associated by movepipe, but by name only and flagged `ambiguous_destination`.
* Clears the ejected lead status BEFORE movepipe associates anything. The workflow above enrolls on
  `hs_lead_status = 'No Longer with Company'`; re-associating while that value is still on the
  record races it. --no-preclear skips this if you want to inspect first.
* Carries `ai__job_title` through as the title at `title_conf` 0.95, but only when the banked
  evidence contains no hedge word. The verdict step already refused to write a native title on a
  hedged read; re-asserting it here at high confidence would launder that refusal.

Env: TOKEN (HubSpot PAT). DRY=1 resolves and writes the queue without touching HubSpot."""
import os,sys,json,subprocess,tempfile
T=os.environ['TOKEN']
DRY=os.environ.get('DRY')=='1'
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
OUT='movers.json'; OVER={}; PRECLEAR=True
a=sys.argv[1:]
while a:
    k=a.pop(0)
    if k=='--out': OUT=a.pop(0)
    elif k=='--overrides': OVER=json.load(open(a.pop(0)))
    elif k=='--no-preclear': PRECLEAR=False
    else: sys.exit("unknown argument "+k)
def call(m,url,body=None,fatal=True):
    c=['curl','-s','--max-time','30','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open(TMP,'w').write(json.dumps(body)); c+=['-d','@'+TMP]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    txt,_,code=o.rpartition('\n'); code=code.strip()
    if not code.isdigit() or not code.startswith('2'):
        if fatal:
            sys.stderr.write('HTTP '+code+' on '+m+' '+url.split('?')[0]+' :: '+txt[:200]+'\n'); sys.exit(2)
        return {}
    try: return json.loads(txt) if txt.strip() else {}
    except Exception: return {}
# hedge words: identical list to writeverdicts/movepipe. A title read off a hedged verdict is not a
# 0.95 title no matter how confident this script is about the company.
AMBIG=("caution","ambig","uncertain","unclear","probably","possibly","perhaps","assumed","appears to",
       "may be","might be","succession","dormant","not updated","stale profile","conflict","unsure","?")
M=[];after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"ai__pending_mover_to","operator":"HAS_PROPERTY"}]}],
       "properties":["firstname","lastname","ai__pending_mover_to","ai__job_title",
                     "ai__contact_evidence","hs_lead_status","ai__li_still_at_company"],"limit":100}
    if after: b["after"]=after
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',b)
    M+=r.get('results',[])
    after=((r.get('paging') or {}).get('next') or {}).get('after')
    if not after: break
print("pending movers in HubSpot: "+str(len(M)))
if not M: sys.exit(0)
cache={}
def resolve(name):
    """(domain, why-not). Exactly one named record carrying a domain, or nothing."""
    if name in OVER: return (OVER[name],None)
    if name in cache: return cache[name]
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
      {"filterGroups":[{"filters":[{"propertyName":"name","operator":"EQ","value":name}]}],
       "properties":["name","domain"],"limit":10},fatal=False)
    res=r.get('results',[])
    if len(res)>1:
        out=(None,"%d HubSpot companies are named %r - pick one"%(len(res),name))
    elif not res:
        out=(None,"no HubSpot company named %r"%name)
    elif not (res[0]['properties'].get('domain') or '').strip():
        out=(None,"HubSpot company %s (%r) carries no domain"%(res[0]['id'],name))
    else:
        out=((res[0]['properties']['domain'] or '').strip(),None)
    cache[name]=out; return out
queue=[];unres=[];preclear=[]
for x in M:
    p=x['properties']; dest=(p.get('ai__pending_mover_to') or '').strip()
    who=((p.get('firstname') or '')+' '+(p.get('lastname') or '')).strip()
    if not dest: continue
    dom,why=resolve(dest)
    ev=(p.get('ai__contact_evidence') or '')
    hedged=[t for t in AMBIG if t in ev.lower()]
    item={"id":x['id'],"newco":dest,
          "ev":("Destination banked by the verdict step as ai__pending_mover_to; re-associated by "
                "moverqueue. The employer they left may already have been detached by the ejection "
                "workflow and is recovered from property history.")}
    if dom: item["domain"]=dom
    t=(p.get('ai__job_title') or '').strip()
    if t and t.lower()!='none':
        item["title"]=t
        if not hedged and dom: item["title_conf"]=0.95
    if why: unres.append({"id":x['id'],"who":who,"newco":dest,"why":why})
    if (p.get('hs_lead_status') or '')=='No Longer with Company': preclear.append(x['id'])
    queue.append(item)
json.dump(queue,open(OUT,'w'),indent=1)
if unres: json.dump(unres,open(OUT+'.unresolved.json','w'),indent=1)
res_n=sum(1 for q in queue if q.get('domain'))
print("queued %d -> %s | domain resolved %d | UNRESOLVED %d"%(len(queue),OUT,res_n,len(unres)))
for u in unres: print("  UNRESOLVED "+u['id']+" "+u['who'][:22].ljust(22)+" -> "+u['newco'][:30].ljust(30)+" :: "+u['why'])
tw=sum(1 for q in queue if q.get('title_conf'))
print("native jobtitle eligible %d/%d (needs a resolved domain and unhedged evidence)"%(tw,len(queue)))
if preclear and PRECLEAR and not DRY:
    # Away from the ejected value first, in one batch, so the workflow is not mid-flight while
    # movepipe is swapping associations.
    for i in range(0,len(preclear),100):
        chunk=preclear[i:i+100]
        call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/update',
             {"inputs":[{"id":c,"properties":{"hs_lead_status":"Need Updated Info"}} for c in chunk]})
    print("pre-cleared 'No Longer with Company' on %d contact(s) -> 'Need Updated Info'"%len(preclear))
    print("      movepipe sets the final status, and checks the destination before calling it a prospect")
elif preclear:
    print("NOT pre-cleared (%d still 'No Longer with Company') - the ejection workflow may undo the "
          "re-association"%len(preclear))
print("\nnext: TOKEN=... python3 movepipe.py <listId> "+OUT)
