import json,subprocess,os,re
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_wp.json','w').write(json.dumps(body)); c+=['-d','@_wp.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
def dig(s):
    d=re.sub(r"\D","",s or "")
    if len(d)==11 and d.startswith("1"): d=d[1:]
    return d

aud=json.load(open('phone_audit.json'))
# only the business-line style fields; `phone` is often a direct dial that follows the person
targets=[]
for r in aud:
    for k,val,d in r['suspect']:
        if k in ("business_phone","company_phone","phone"):
            targets.append({"cid":r['cid'],"name":r['name'],"newco":r['newco'],"field":k,"val":val,"dig":d})
print("business-line numbers to identify:",len(targets))

def find_company(d):
    """search companies whose phone contains this number"""
    if not d or len(d)<7: return []
    hits=[]
    for pat in (d, d[:3]+"-"+d[3:6]+"-"+d[6:], "("+d[:3]+") "+d[3:6]+"-"+d[6:]):
        r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
          {"filterGroups":[{"filters":[{"propertyName":"phone","operator":"CONTAINS_TOKEN","value":"*"+pat+"*"}]}],
           "properties":["name","domain","phone"],"limit":3})
        for x in r.get('results',[]):
            if dig(x['properties'].get('phone'))==d:
                hits.append((x['properties'].get('name'),x['properties'].get('domain')))
        if hits: break
    # de-dupe
    seen=set(); out=[]
    for n,dm in hits:
        if n in seen: continue
        seen.add(n); out.append((n,dm))
    return out

rows=[]
for t in targets:
    owners=find_company(t['dig'])
    t['owners']=owners
    rows.append(t)
    tag="UNKNOWN owner"
    if owners:
        names=", ".join(str(n) for n,_ in owners[:2])
        tag=("MATCHES NEW EMPLOYER" if any((t['newco'] or '').lower()[:12] in str(n or '').lower() for n,_ in owners)
             else "belongs to: "+names)
    print(str(t['name'])[:19].ljust(19)+" | now at "+str(t['newco'])[:18].ljust(18)+" | "
          +t['field']+"="+str(t['val'])[:17].ljust(17)+" | "+tag)
json.dump(rows,open('phone_owners.json','w'),indent=1)
known=[r for r in rows if r['owners']]
print()
print("identified an owning company for "+str(len(known))+" of "+str(len(rows))+" business numbers")
