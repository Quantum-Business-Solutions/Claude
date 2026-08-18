import json,subprocess,os
from collections import Counter
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_sp.json','w').write(json.dumps(body)); c+=['-d','@_sp.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    return json.loads(o) if o.strip() else {}
d=json.load(open('out_of_5243.json'))
ids=[x['cid'] for x in d]
info={}
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],
       "properties":["currently_use_zoominfo_","hubspot_tech_used","associatedcompanyid","firstname","lastname","company"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]): info[x['id']]=x['properties']
coids=sorted({(info.get(x['cid']) or {}).get('associatedcompanyid') for x in d if (info.get(x['cid']) or {}).get('associatedcompanyid')})
co={}
for i in range(0,len(coids),100):
    b={"inputs":[{"id":x} for x in coids[i:i+100]],
       "properties":["name","domain","currently_use_zoominfo_","hubspot_tech_used","createdate","zi_c_company_id"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/batch/read',b)
    for x in r.get('results',[]): co[x['id']]=x['properties']
c=Counter(); newco=[]
for x in d:
    p=info.get(x['cid']) or {}
    cp=co.get(p.get('associatedcompanyid')) or {}
    zi=cp.get('currently_use_zoominfo_')
    fresh=(cp.get('createdate') or '').startswith('2026-08')
    k=("company record CREATED by me - ICP signal UNKNOWN" if fresh
       else ("company enriched, uses ZoomInfo = "+str(zi)))
    c[k]+=1
    if fresh: newco.append((x['name'],cp.get('name'),cp.get('domain')))
for k,v in c.most_common(): print("  "+str(v).rjust(3)+"  "+k)
print("\ncompanies I created this month - ICP flags never enriched, so 'out of profile' is UNPROVEN:")
seen=set()
for n,cn,cd in newco:
    if cn in seen: continue
    seen.add(cn); print("   "+str(cn)[:28].ljust(28)+str(cd))
