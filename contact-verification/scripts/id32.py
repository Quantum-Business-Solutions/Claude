import json,subprocess,os,re
from collections import Counter
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_i3.json','w').write(json.dumps(body)); c+=['-d','@_i3.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
def dig(s):
    d=re.sub(r"\D","",s or "")
    if len(d)==11 and d.startswith("1"): d=d[1:]
    return d
m=json.load(open('mismatch8260.json'))
print("mismatched business_phone values on the calling list:",len(m))

# how many of these numbers appear on MORE THAN ONE contact in the portal?
def contacts_with(d):
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',
      {"filterGroups":[{"filters":[{"propertyName":"business_phone","operator":"CONTAINS_TOKEN","value":"*"+d+"*"}]}],
       "properties":["firstname","lastname","company"],"limit":6})
    return r.get('total'),[str(x['properties'].get('company')) for x in r.get('results',[])]
def owner_company(d):
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
      {"filterGroups":[{"filters":[{"propertyName":"phone","operator":"CONTAINS_TOKEN","value":"*"+d+"*"}]}],
       "properties":["name","phone"],"limit":3})
    for x in r.get('results',[]):
        if dig(x['properties'].get('phone'))==d: return x['properties'].get('name')
    return None

rows=[]
for x in m:
    d=dig(x['business_phone'])
    n,cos=contacts_with(d)
    own=owner_company(d)
    same=own and (x['co'] or '').lower()[:10] in str(own).lower()
    distinct=len({c for c in cos if c and c!='None'})
    verdict=("SAME COMPANY, alternate line" if same else
             ("SHARED ACROSS "+str(distinct)+" DIFFERENT COMPANIES - bad import" if distinct>1 else
              ("belongs to "+str(own) if own else "no company record owns it - likely a direct line")))
    rows.append(dict(x,digits=d,contacts_sharing=n,owner=own,verdict=verdict,distinct_companies=distinct))
    print("  "+str(x['name'])[:19].ljust(19)+str(x['co'])[:20].ljust(20)+str(x['business_phone'])[:16].ljust(16)+verdict)
json.dump(rows,open('mismatch32.json','w'),indent=1)
print()
c=Counter(r['verdict'].split(' - ')[0].split(',')[0] for r in rows)
for k,v in c.most_common(): print("  "+str(v).rjust(3)+"  "+k)
