import json,subprocess,os,re
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_vp.json','w').write(json.dumps(body)); c+=['-d','@_vp.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
def dig(s):
    d=re.sub(r"\D","",s or "")
    if len(d)==11 and d.startswith("1"): d=d[1:]
    return d
L=json.load(open('reassoc_log.json'))
ids=sorted({str(r.get('id') or r.get('cid')) for r in L if (r.get('id') or r.get('cid'))})
rows={}
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],
       "properties":["firstname","lastname","company","phone","mobilephone","business_phone","associatedcompanyid"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]): rows[x['id']]=x['properties']
coids=sorted({v.get('associatedcompanyid') for v in rows.values() if v.get('associatedcompanyid')})
co={}
for i in range(0,len(coids),100):
    b={"inputs":[{"id":x} for x in coids[i:i+100]],"properties":["name","phone"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/batch/read',b)
    for x in r.get('results',[]): co[x['id']]=x['properties']
bad=[];nodial=[];ok=0
for cid,p in rows.items():
    c=co.get(p.get('associatedcompanyid')) or {}
    nd=dig(c.get('phone'))
    bp=p.get('business_phone')
    nm=str(p.get('firstname'))+" "+str(p.get('lastname'))
    if bp and nd and dig(bp)!=nd: bad.append((nm,c.get('name'),bp,c.get('phone')))
    elif bp and not nd: bad.append((nm,c.get('name'),bp,"(company has no phone)"))
    else: ok+=1
    if not (p.get('phone') or p.get('mobilephone') or p.get('business_phone')):
        nodial.append((cid,nm,c.get('name')))
print("movers whose business_phone now matches their employer (or is empty): "+str(ok)+" of "+str(len(rows)))
print("still mismatched: "+str(len(bad)))
for b in bad: print("   "+str(b))
print()
print("movers now with NO dialable number at all: "+str(len(nodial)))
for cid,nm,cn in nodial: print("   "+cid+"  "+nm[:22].ljust(22)+str(cn))
json.dump(nodial,open('no_dial.json','w'),indent=1)
