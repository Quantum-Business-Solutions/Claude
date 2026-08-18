import json,subprocess,os
T=os.environ['TOKEN']
STAMP="2026-08-17T00:00:00Z"   # datetime properties accept RFC3339
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_bf.json','w').write(json.dumps(body)); c+=['-d','@_bf.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:300]}

ids=set()
# every contact this process wrote a verdict for
for r in json.load(open('li_verdicts.json')): ids.add(str(r['id']))
# every mover re-associated
for r in json.load(open('reassoc_log.json')):
    v=r.get('id') or r.get('cid')
    if v: ids.add(str(v))
# every email write / previous-email filing / persona correction
for f in ('email_write_log.json','previous_email_log.json','unmark_log.json'):
    if os.path.exists(f):
        for r in json.load(open(f)):
            if r.get('cid'): ids.add(str(r['cid']))
for f in ('persona_writes.json',):
    if os.path.exists(f):
        for r in json.load(open(f)):
            if r.get('id'): ids.add(str(r['id']))
ids=sorted(ids)
print("records this process touched:",len(ids))

ok=0; errs=0
for i in range(0,len(ids),100):
    chunk=ids[i:i+100]
    body={"inputs":[{"id":x,"properties":{"ai__last_updated_by_claude":STAMP}} for x in chunk]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/update',body)
    n=len(r.get('results',[]))
    ok+=n
    if r.get('status')!='COMPLETE':
        errs+=1
        print("  chunk",i//100,"->",json.dumps(r)[:200])
print("stamped:",ok,"| chunks with an error:",errs)
