import json,subprocess,os
from collections import Counter
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_f3.json','w').write(json.dumps(body)); c+=['-d','@_f3.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    return json.loads(o) if o.strip() else {}
L=json.load(open('reassoc_log.json'))
rows={}
for r in L:
    cid=r.get('id') or r.get('cid')
    rows[cid]={"cid":cid,"coid":r.get('companyId') or r.get('company_id'),"name":r.get('name')}
ids=list(rows)
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],
       "properties":["email","previous__email","firstname","lastname","associatedcompanyid"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']; rows[x['id']].update(p)
        if not rows[x['id']]['name']: rows[x['id']]['name']=str(p.get('firstname'))+' '+str(p.get('lastname'))
coids=sorted({v.get('associatedcompanyid') or v.get('coid') for v in rows.values() if (v.get('associatedcompanyid') or v.get('coid'))})
dom={}
for i in range(0,len(coids),100):
    b={"inputs":[{"id":x} for x in coids[i:i+100]],"properties":["domain","name"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/batch/read',b)
    for x in r.get('results',[]): dom[x['id']]=x['properties'].get('domain')
ALIAS={"dominodatalab.com":"domino.ai","hexagon.com":"hexagonmi.com"}
c=Counter(); bad=[]; blank=[]
for v in rows.values():
    d=dom.get(v.get('associatedcompanyid') or v.get('coid'))
    e=v.get('email')
    if not e:
        c['no email (field empty)']+=1; blank.append((v['name'],v.get('previous__email'))); continue
    ed=e.split('@')[-1].lower()
    if d and (ed==d.lower() or ALIAS.get(ed)==d.lower()): c['email at CURRENT employer']+=1
    else: c['email at PRIOR employer']+=1; bad.append((v['name'],e,d))
pe=sum(1 for v in rows.values() if v.get('previous__email'))
print("MOVERS:",len(rows))
for k,val in c.items(): print("  "+k.ljust(28)+str(val))
print("  previous__email populated   "+str(pe))
print("\nSTILL WRONG:",bad if bad else "NONE")
print("\nblank email (name / prior address preserved):")
for n,p in blank: print("   "+str(n)[:24].ljust(24)+str(p or '-'))
