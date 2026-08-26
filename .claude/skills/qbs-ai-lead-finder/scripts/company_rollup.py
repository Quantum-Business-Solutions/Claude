import json,os,re,time,datetime,urllib.request,collections
PAT=os.environ['PAT']
sigs={x['engagement_id']:x for x in json.load(open("v2_clean.json"))}
amap=json.load(open("v2_assoc.json")); info=json.load(open("v2_companies.json"))
EXCLUDE={"customer","96368288"}          # Customer, Team UBEO
SRCRANK={"stated date":3,"computed from remaining term":2,"computed from just-signed":1}
def excerpt(b,basis,w=140):
    b=re.sub(r'\s+',' ',b).strip()
    key=(basis or '').split(' term,')[0]
    i=b.lower().find(key.lower()) if key else -1
    if i>=0:
        s=max(0,i-w);e=min(len(b),i+len(key)+w)
        return ("..." if s>0 else "")+b[s:e].strip()+("..." if e<len(b) else "")
    return b[:280]
def score(x):
    return (SRCRANK.get(x['src'],0), 1 if x['oem'] else 0, x['ts'])
percomp=collections.defaultdict(list)
for eid,cid in amap.items():
    if eid in sigs: percomp[str(cid)].append(sigs[eid])
writes={};skipped_cust=0;skipped_existing=0
for cid,rows in percomp.items():
    p=info.get(cid) or {}
    if (p.get("lifecyclestage") or "") in EXCLUDE: skipped_cust+=1; continue
    existing=(p.get("ai_lease_information") or "").strip()
    best=max(rows,key=score)
    # never clobber a human-authored value (ours always carries a [source: ...] tag)
    if existing and "[source:" not in existing: skipped_existing+=1; continue
    d=datetime.date(*map(int,best['end'].split('-')))
    prov=best['oem'][0] if best['oem'] else "Provider unknown"
    ev=excerpt(best['body'],best['basis']).replace('"',"'")
    logged=datetime.date(*map(int,best['ts'].split('-'))).strftime('%m/%d/%Y')
    others=len(rows)-1
    extra=f" (+{others} other engagement{'s' if others>1 else ''} with lease signal)" if others else ""
    flags=(" ** FLAGS: "+",".join(best['flags'])) if best['flags'] else ""
    val=("%s - %s - %s [source: %s id %s, logged %s, %s: \"%s\"]%s%s"%(
        d.strftime('%m/%Y'),prov,ev,best['engagement_type'],best['engagement_id'],
        logged,best['src'],best['basis'],extra,flags))[:65000]
    writes[cid]=val
print("companies eligible for write : %d"%len(writes))
print("  skipped - lifecycle=customer/TeamUBEO : %d"%skipped_cust)
print("  skipped - human-authored value present: %d"%skipped_existing)
print("  companies with >1 supporting engagement: %d"%sum(1 for c,r in percomp.items() if len(r)>1 and c in writes))
print("\nsample values:")
for cid,v in list(writes.items())[:6]:
    print("\n  company %s (%s | %s)"%(cid,(info.get(cid) or {}).get('name','?'),(info.get(cid) or {}).get('lifecyclestage')))
    print("    "+v[:260])
json.dump(writes,open("v2_company_writes.json","w"))
