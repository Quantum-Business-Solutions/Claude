import json,subprocess,os
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_c7.json','w').write(json.dumps(body)); c+=['-d','@_c7.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    return json.loads(o) if o.strip() else {}
NAMES=["Ann Boyd","Rich Wenning","Michele Bedford","Aaron Russo","William Clausen","Judah Guber","Lyndsi Stevens"]
r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',
 {"filterGroups":[{"filters":[{"propertyName":"ai__contact_evidence","operator":"CONTAINS_TOKEN","value":"*NOT-MKT*"}]}],
  "properties":["firstname","lastname","company","jobtitle","hs_lead_status","ai__contact_evidence"],"limit":100})
# list 8260 membership
ids=[];after=None
while True:
    u="https://api.hubapi.com/crm/v3/lists/8260/memberships?limit=250"+(("&after="+after) if after else "")
    q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
    after=(q.get('paging') or {}).get('next',{}).get('after')
    if not after: break
m8260=set(ids)
out=[]
for x in r.get('results',[]):
    p=x['properties']; nm=str(p.get('firstname'))+' '+str(p.get('lastname'))
    if nm in NAMES:
        out.append({"cid":x['id'],"name":nm,"co":p.get('company'),"jt":p.get('jobtitle'),
                    "ls":p.get('hs_lead_status'),"in8260":x['id'] in m8260,
                    "ev":p.get('ai__contact_evidence') or ''})
print("list 8260 size:",len(m8260))
for o in out:
    print(("IN 8260  " if o['in8260'] else "EXCLUDED ")+o['name'][:18].ljust(18)+str(o['co'])[:20].ljust(20)+str(o['jt'])[:34].ljust(34)+str(o['ls']))
json.dump(out,open('stale_marker.json','w'),indent=1)
print("\nwrongly excluded:",sum(1 for o in out if not o['in8260']))
