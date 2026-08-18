import json,subprocess,os
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_ls2.json','w').write(json.dumps(body)); c+=['-d','@_ls2.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
def total(lid):
    r=call('GET',"https://api.hubapi.com/crm/v3/lists/"+lid+"/memberships?limit=1")
    return r.get('total')
NAMES={"5243":"source list (CAS ZoomInfo/Hubspot used - Head of Marketing)",
       "8260":"calling list (verified current only)",
       "8262":"Claude - Moved Companies",
       "8263":"Claude - No Primary Associated Company"}
for lid,nm in NAMES.items():
    print("  list "+lid+"  "+str(total(lid)).rjust(6)+"   "+nm)
# did the two no-dial contacts drop off 5243 as predicted?
ids=[];after=None
while True:
    u="https://api.hubapi.com/crm/v3/lists/5243/memberships?limit=250"+(("&after="+after) if after else "")
    q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
    after=(q.get('paging') or {}).get('next',{}).get('after')
    if not after: break
m=set(ids)
print()
for cid,nm,co in json.load(open('no_dial.json')):
    print("  "+nm[:20].ljust(20)+("STILL on 5243" if cid in m else "dropped off 5243 as predicted"))
