"""Find duplicate dealer records by SHARED PHONE NUMBER.

Shawn spotted Equipment Brokers Unlimited / 'Ebu' as duplicates. Domain-union missed them
because one record holds the web domain and the other the mail domain. What they share is a
phone number - an axis the clustering never used.
"""
import os, sys, json, re, time, urllib.request, urllib.error
sys.path.insert(0,'/tmp')
from resolver import Companies
from collections import defaultdict
S='/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
H={"Authorization":"Bearer "+os.environ['TOKEN'],"Content-Type":"application/json"}
def post(p,b):
    for a in range(4):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+p,data=json.dumps(b).encode(),headers=H)
            return json.loads(urllib.request.urlopen(r,timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503): time.sleep(2*(a+1)); continue
            return {'_err':e.code}
        except Exception: time.sleep(2*(a+1))
    return {}

PROPS=["name","domain","city","state","phone","copier_company","numberofemployees",
       "ai__dealer_verdict","ai__acquired_by","createdate"]
comps={}; after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"copier_company","operator":"EQ","value":"true"}]}],
       "properties":PROPS,"limit":100}
    if after: b["after"]=after
    r=post("/crm/v3/objects/companies/search",b)
    for c in r.get("results",[]): comps[c["id"]]=c["properties"]
    after=(r.get('paging') or {}).get('next',{}).get('after')
    if not after: break
    time.sleep(0.1)
print(f"dealer companies: {len(comps)}")
CO=Companies(comps)

def digits(p):
    d=re.sub(r'\D','',p or '')
    if len(d)==11 and d.startswith('1'): d=d[1:]
    return d if len(d)==10 else ''

byph=defaultdict(list)
for cid,p in comps.items():
    d=digits(p.get('phone'))
    if d: byph[d].append(cid)

# a shared phone across records ALREADY in one cluster is not news
pairs=[]
for ph,ids in byph.items():
    if len(ids)<2: continue
    cls={CO.cluster(i) for i in ids}
    if len(cls)<2: continue          # already clustered together
    pairs.append((ph,ids))
print(f"\nphone numbers shared across DIFFERENT clusters: {len(pairs)}\n")
out=[]
for ph,ids in sorted(pairs, key=lambda x:-len(x[1])):
    print(f"  {ph}  ({len(ids)} records)")
    rec=[]
    for i in ids:
        p=comps[i]
        print(f"      [{i}] {str(p.get('name'))[:38]:40} dom={str(p.get('domain'))[:28]:30} "
              f"{str(p.get('city'))[:14]:16} emp={p.get('numberofemployees')} "
              f"created={str(p.get('createdate'))[:10]}")
        rec.append({'id':i,'name':p.get('name'),'domain':p.get('domain'),'city':p.get('city'),
                    'state':p.get('state'),'employees':p.get('numberofemployees'),
                    'verdict':p.get('ai__dealer_verdict'),'acquired_by':p.get('ai__acquired_by')})
    # how many contacts sit on each half?
    for r_ in rec:
        a=post("/crm/v3/objects/contacts/search",
          {"filterGroups":[{"filters":[{"propertyName":"associatedcompanyid","operator":"EQ",
                                        "value":r_['id']}]}],
           "properties":["firstname","lastname","jobtitle","email"],"limit":30})
        cs=a.get('results') or []
        r_['contacts']=[{'id':c['id'],'name':f"{c['properties'].get('firstname')} {c['properties'].get('lastname')}",
                         'title':c['properties'].get('jobtitle'),'email':c['properties'].get('email')} for c in cs]
        time.sleep(0.1)
    tot=sum(len(r_['contacts']) for r_ in rec)
    names={(c['name'] or '').strip().lower() for r_ in rec for c in r_['contacts']}
    shared=sum(1 for r_ in rec for c in r_['contacts']) - len(names)
    print(f"      -> {tot} contacts across the group; {shared} duplicated person name(s)")
    out.append({'phone':ph,'records':rec,'total_contacts':tot,'duplicated_names':shared})
    print()
json.dump(out, open(S+'/phone_duplicate_clusters.json','w'), indent=1)
print(f"saved phone_duplicate_clusters.json ({len(out)} groups)")
