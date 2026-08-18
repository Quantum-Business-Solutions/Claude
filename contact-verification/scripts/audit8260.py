import json,subprocess,os,re
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_a8.json','w').write(json.dumps(body)); c+=['-d','@_a8.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
def dig(s):
    d=re.sub(r"\D","",s or "")
    if len(d)==11 and d.startswith("1"): d=d[1:]
    return d
ids=[];after=None
while True:
    u="https://api.hubapi.com/crm/v3/lists/8260/memberships?limit=250"+(("&after="+after) if after else "")
    q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
    after=(q.get('paging') or {}).get('next',{}).get('after')
    if not after: break
print("calling list 8260 members:",len(ids))
rows={}
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],
       "properties":["firstname","lastname","company","phone","mobilephone","business_phone",
                     "associatedcompanyid","ai__contact_evidence"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]): rows[x['id']]=x['properties']
coids=sorted({v.get('associatedcompanyid') for v in rows.values() if v.get('associatedcompanyid')})
co={}
for i in range(0,len(coids),100):
    b={"inputs":[{"id":x} for x in coids[i:i+100]],"properties":["name","phone"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/batch/read',b)
    for x in r.get('results',[]): co[x['id']]=x['properties']
match=0; mismatch=[]; nocophone=0; nobp=0
for cid,p in rows.items():
    c=co.get(p.get('associatedcompanyid')) or {}
    nd=dig(c.get('phone')); bp=p.get('business_phone')
    if not bp: nobp+=1; continue
    if not nd: nocophone+=1; continue
    if dig(bp)==nd: match+=1
    else:
        mismatch.append({"cid":cid,"name":str(p.get('firstname'))+" "+str(p.get('lastname')),
                         "co":c.get('name'),"co_phone":c.get('phone'),"business_phone":bp,
                         "mover":"RE-ASSOCIATED" in (p.get('ai__contact_evidence') or '')})
print()
print("  business_phone matches the associated company : "+str(match))
print("  business_phone does NOT match                 : "+str(len(mismatch)))
print("  company record has no phone to compare        : "+str(nocophone))
print("  contact has no business_phone                 : "+str(nobp))
json.dump(mismatch,open('mismatch8260.json','w'),indent=1)
print()
print("sample of mismatches (none of these are our movers unless flagged):")
for m in mismatch[:25]:
    print("   "+m['name'][:20].ljust(20)+str(m['co'])[:22].ljust(22)+"contact="+str(m['business_phone'])[:16].ljust(16)
          +" company="+str(m['co_phone'])[:16]+("   [MOVER]" if m['mover'] else ""))
