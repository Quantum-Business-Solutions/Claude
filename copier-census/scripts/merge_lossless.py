"""Merge ONLY the acquirer duplicates that are genuinely lossless.

A HubSpot merge cannot be undone. So the bar here is absolute: the losing record must hold no
contacts, no deals, and no field the survivor lacks. Each is RE-CHECKED live immediately before
the merge - the earlier pre-check is minutes old and this is irreversible.

Everything else - 12 records holding contacts, deals, or unique data - is left for Shawn.
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
PROPS=["name","domain","city","state","phone","numberofemployees","annualrevenue",
       "copier_company","ai__dealer_verdict","ai__company_type","hs_additional_domains"]

plan=json.load(open(S+'/acquirer_merge_plan.json'))
safe=plan['safe']
print(f"candidates marked lossless earlier: {len(safe)}\n")

go=[]
for r in safe:
    dup, keep = r['dup'], r['keep']
    a=req("GET",f"/crm/v4/objects/companies/{dup}/associations/contacts")
    b=req("GET",f"/crm/v4/objects/companies/{dup}/associations/deals")
    nc,nd=len(a.get('results') or []),len(b.get('results') or [])
    rr=req("POST","/crm/v3/objects/companies/batch/read",
           {"properties":PROPS,"inputs":[{"id":dup},{"id":keep}]})
    got={x['id']:x['properties'] for x in rr.get('results',[])}
    dp,kp=got.get(dup,{}),got.get(keep,{})
    uniq=[f for f in PROPS if (dp.get(f) or '') and not (kp.get(f) or '')]
    if nc or nd or uniq:
        print(f"  WITHDRAWN [{dup}] {str(r['name'])[:32]:34} contacts={nc} deals={nd} "
              f"unique={','.join(uniq) or '-'}  <- no longer lossless, holding back")
        continue
    go.append(r)
    print(f"  confirmed [{dup}] {str(r['name'])[:32]:34} -> merge into [{keep}] "
          f"{str(kp.get('name'))[:26]}")
print(f"\nre-verified lossless: {len(go)} of {len(safe)}")
if not EXECUTE:
    print("\nDRY RUN - add --execute"); sys.exit(0)

done=[]; failed=[]
for r in go:
    # capture the losing record's domain first - it should survive as an additional domain
    pre=req("GET",f"/crm/v3/objects/companies/{r['dup']}?properties=name,domain")
    lostdom=(pre.get('properties',{}) or {}).get('domain') or ''
    m=req("POST","/crm/v3/objects/companies/merge",
          {"primaryObjectId":r['keep'],"objectIdToMerge":r['dup']})
    if m.get('_err'):
        failed.append((r['dup'],m.get('_err'),m.get('_b','')[:140]))
        print(f"  FAIL  [{r['dup']}] {m.get('_err')} {m.get('_b','')[:110]}")
    else:
        done.append((r['dup'],r['keep'],r['name'],lostdom))
        print(f"  merged [{r['dup']}] -> [{r['keep']}]   {r['name']}")
    time.sleep(0.6)
print(f"\nmerged {len(done)}, failed {len(failed)}")

print("\nREAD-BACK - does the survivor exist, and did the domain carry over?")
survivors=sorted({k for _,k,_,_ in done})
rr=req("POST","/crm/v3/objects/companies/batch/read",
   {"properties":["name","domain","hs_additional_domains","numberofemployees"],
    "inputs":[{"id":x} for x in survivors]})
sv={x['id']:x['properties'] for x in rr.get('results',[])}
for cid,p in sv.items():
    print(f"  [{cid}] {str(p.get('name'))[:34]:36} dom={str(p.get('domain'))[:24]:26} "
          f"additional={str(p.get('hs_additional_domains'))[:44]}")
gone=0
for dup,keep,name,lostdom in done:
    g=req("GET",f"/crm/v3/objects/companies/{dup}?properties=name")
    if g.get('_err')==404: gone+=1
    else: print(f"  NOTE [{dup}] still resolves (HubSpot redirects a merged id) - expected")
print(f"\nlosing ids returning 404: {gone} of {len(done)} (a merged id often redirects, so this is informational)")
json.dump({'merged':[{'dup':d,'keep':k,'name':n,'domain_lost':dm} for d,k,n,dm in done],
           'failed':failed}, open(S+'/acquirer_merges_done.json','w'), indent=1)
