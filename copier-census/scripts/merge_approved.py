"""Merge the acquirer duplicates Shawn explicitly approved.

APPROVED : DEX Imaging, Visual Edge (both records), Applied Imaging, Gordon Flesch
HELD BACK: Datamax of Texas - Shawn: "there are two companies"
           ImageNet Miami + dba stub - Shawn: "ImageNet runs off divisions"
NOT YET ANSWERED, so untouched: Kelley Imaging (merge direction is in question),
           Konica Minolta stub, FlexTG www-variant.

A merge shifts the survivor's object id, so the current canonical id is resolved immediately
before each merge instead of trusting one recorded minutes ago.
"""
import os, sys, json, time, urllib.request, urllib.error
S='/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
H={"Authorization":"Bearer "+os.environ['TOKEN'],"Content-Type":"application/json"}
EXECUTE='--execute' in sys.argv
def req(m,p,b=None):
    for a in range(4):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+p,
                data=json.dumps(b).encode() if b else None,headers=H,method=m)
            return json.loads(urllib.request.urlopen(r,timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503): time.sleep(2*(a+1)); continue
            return {'_err':e.code,'_b':e.read().decode()[:300]}
        except Exception: time.sleep(2*(a+1))
    return {}
def canonical(cid):
    """A merged id redirects; ask HubSpot what the record's id is NOW."""
    g=req("GET",f"/crm/v3/objects/companies/{cid}?properties=name,domain")
    return (g.get('id') or cid), (g.get('properties') or {})

APPROVED=[
 ("DEX Imaging",            "38803684505", "53557996443", "field-identical twin, 18 contacts + 3 deails"),
 ("DEX Imaging",            "38803684505", "35404860332", "name-only stub 'DEX imaging:Document Solutions'"),
 ("Visual Edge",            "53544039989", "53549078092", "identical name, domain and city, 10 contacts"),
 ("Visual Edge",            "53544039989", "35394743143", "former name 'Visual Edge Technology', legacy domain"),
 ("Applied Imaging",        "53535903346", "6930380335",  "pre-June-2022 name, 7 contacts + 2 deals"),
 ("Gordon Flesch",          "8499133352",  "35411116952", "same company, the record I just gave gflesch.com"),
]
print("resolving current ids and pre-checking each losing record\n")
work=[]
for label, keep, dup, why in APPROVED:
    k,kp = canonical(keep)
    d,dp = canonical(dup)
    if k==d:
        print(f"  ALREADY MERGED  {label:18} [{dup}] now resolves to the survivor - skipping")
        continue
    a=req("GET",f"/crm/v4/objects/companies/{d}/associations/contacts")
    b=req("GET",f"/crm/v4/objects/companies/{d}/associations/deals")
    nc,nd=len(a.get('results') or []),len(b.get('results') or [])
    print(f"  {label:18} keep [{k}] {str(kp.get('name'))[:26]:28} <- [{d}] "
          f"{str(dp.get('name'))[:26]:28} contacts={nc} deals={nd}")
    work.append((label,k,d,nc,nd,why))
    time.sleep(0.15)
print(f"\nmerges to perform: {len(work)}")
if not EXECUTE:
    print("DRY RUN - add --execute"); sys.exit(0)

done=[]
for label,keep,dup,nc,nd,why in work:
    k,_=canonical(keep)          # re-resolve: the previous merge may have shifted it
    m=req("POST","/crm/v3/objects/companies/merge",
          {"primaryObjectId":k,"objectIdToMerge":dup})
    if m.get('_err'):
        print(f"  FAIL {label} [{dup}]: {m.get('_err')} {m.get('_b','')[:130]}")
    else:
        done.append((label,k,dup,nc,nd))
        print(f"  merged {label:18} [{dup}] -> [{k}]  (carried {nc} contacts, {nd} deals)")
    time.sleep(0.8)

print(f"\nmerged {len(done)} of {len(work)}")
print("\nREAD-BACK - survivor, its contacts, and the retained domains")
seen=set()
for label,keep,dup,nc,nd in done:
    k,kp=canonical(keep)
    if k in seen: continue
    seen.add(k)
    g=req("GET",f"/crm/v3/objects/companies/{k}?properties=name,domain,hs_additional_domains,"
                 "numberofemployees,copier_company")
    p=g.get('properties',{})
    a=req("GET",f"/crm/v4/objects/companies/{k}/associations/contacts")
    d=req("GET",f"/crm/v4/objects/companies/{k}/associations/deals")
    print(f"  [{k}] {str(p.get('name'))[:32]:34} dom={str(p.get('domain'))[:22]:24} "
          f"contacts={len(a.get('results') or []):3} deals={len(d.get('results') or []):2}")
    print(f"        additional domains: {p.get('hs_additional_domains')}")
    time.sleep(0.2)
json.dump([{'label':l,'keep':k,'merged':d,'contacts':c,'deals':dl} for l,k,d,c,dl in done],
          open(S+'/approved_merges_done.json','w'), indent=1)
