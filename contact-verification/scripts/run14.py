import json,subprocess,os,sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'.')
from patmail2 import resolve_all,learn,nicks
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_14.json','w').write(json.dumps(body)); c+=['-d','@_14.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}

L=json.load(open('reassoc_log.json'))
rows={}
for r in L:
    cid=r.get('id') or r.get('cid')
    rows[cid]={"cid":cid,"coid":r.get('companyId') or r.get('company_id')}
ids=list(rows)
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],
       "properties":["email","firstname","lastname","associatedcompanyid"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]): rows[x['id']].update(x['properties'])
coids=sorted({v.get('associatedcompanyid') or v.get('coid') for v in rows.values() if (v.get('associatedcompanyid') or v.get('coid'))})
dom={}
for i in range(0,len(coids),100):
    b={"inputs":[{"id":x} for x in coids[i:i+100]],"properties":["domain","name"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/batch/read',b)
    for x in r.get('results',[]): dom[x['id']]=(x['properties'].get('domain'),x['properties'].get('name'))

targets=[]
for v in rows.values():
    if v.get('email'): continue
    d,cn=dom.get(v.get('associatedcompanyid') or v.get('coid'),(None,None))
    if not d or not v.get('firstname') or not v.get('lastname'): continue
    targets.append({"cid":v['cid'],"first":v['firstname'],"last":v['lastname'],"codom":d,"coname":cn})
print("contacts with an empty Email field:",len(targets))

samples=json.load(open('domain_samples.json'))
pat={d:learn(v) for d,v in samples.items()}
def work(t):
    em,verdict,tried=resolve_all(t['first'],t['last'],t['codom'],
                                 learned=pat.get(t['codom']),nicknames=nicks(t['first']))
    return dict(cid=t['cid'],name=t['first']+" "+t['last'],codom=t['codom'],coname=t['coname'],
                email=em,verdict=verdict[0] if verdict else None,
                pattern=verdict[1] if verdict else None,n_tried=len(tried),
                tried=[{"e":a,"r":b,"p":c} for a,b,c in tried])
with ThreadPoolExecutor(max_workers=6) as ex:
    out=list(ex.map(work,targets))
json.dump(out,open('email_found3.json','w'),indent=1)
from collections import Counter
print(Counter(r['verdict'] for r in out))
for r in sorted(out,key=lambda x:str(x['verdict'])):
    print(str(r['verdict'] or 'NONE').upper().ljust(9)+" "+r['name'][:20].ljust(20)+" "
          +str(r['email'] or '-').ljust(40)+" pat="+str(r['pattern'] or '-').ljust(22)+" tried="+str(r['n_tried']))
