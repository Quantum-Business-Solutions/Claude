import json,subprocess,os
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_p9.json','w').write(json.dumps(body)); c+=['-d','@_p9.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
r=json.load(open('mismatch32_redone.json'))
wrong=[x for x in r if x.get('owner') and (x['co'] or '').lower()[:10] not in str(x['owner']).lower()]
out=[]
for w in wrong:
    # employer domain
    e=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
      {"filterGroups":[{"filters":[{"propertyName":"name","operator":"EQ","value":w['co']}]}],
       "properties":["name","domain"],"limit":1})
    ed=(e.get('results') or [{}])[0].get('properties',{}).get('domain')
    # owner domain
    o=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
      {"filterGroups":[{"filters":[{"propertyName":"name","operator":"EQ","value":w['owner']}]}],
       "properties":["name","domain"],"limit":1})
    od=(o.get('results') or [{}])[0].get('properties',{}).get('domain')
    out.append({"name":w['name'],"employer":w['co'],"employer_domain":ed,
                "number":w['business_phone'],"owner":w['owner'],"owner_domain":od})
    print(str(w['name'])[:19].ljust(19)+" employer="+str(w['co'])[:18].ljust(18)+str(ed or '-')[:22].ljust(22)
          +" number belongs to "+str(w['owner'])[:20].ljust(20)+str(od or '-'))
json.dump(out,open('pairs9.json','w'),indent=1)
