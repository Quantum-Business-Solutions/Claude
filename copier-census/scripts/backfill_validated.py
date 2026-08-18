"""Backfill 'Validated - LinkedIn or Manually' = Yes, but ONLY where the evidence is a real
employment check.

The field is only worth what it asserts. Setting it on everything touched would include people
whose sole proof is a directory entry that goes stale for years - and this project has already
found dead principals still listed on BBB. So:

  YES  <- a LinkedIn profile or company page showing a CURRENT role naming the dealer
       <- the dealer's own website naming them
       <- a Secretary of State officer filing (filed under legal obligation)
  LEFT BLANK <- BBB, ZoomInfo, trade press, chamber, dealer locator, pattern-inferred anything

An existing value is never overwritten - Retired / Needs Updated / Delete were set deliberately.
"""
import os, sys, json, re, time, urllib.request, urllib.error
S='/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
H={"Authorization":"Bearer "+os.environ['TOKEN'],"Content-Type":"application/json"}
EXECUTE='--execute' in sys.argv
def req(m,p,b=None):
    for a in range(5):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+p,
                data=json.dumps(b).encode() if b else None,headers=H,method=m)
            return json.loads(urllib.request.urlopen(r,timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503): time.sleep(2*(a+1)); continue
            return {'_err':e.code,'_b':e.read().decode()[:250]}
        except Exception: time.sleep(2*(a+1))
    return {}

touched=json.load(open(S+'/touched_cycle.json'))
ids=[t['id'] for t in touched]
print(f"contacts verified this cycle: {len(ids)}")

# pull the evidence text so the source can be judged
ev={}
for i in range(0,len(ids),100):
    r=req("POST","/crm/v3/objects/contacts/batch/read",
      {"properties":["firstname","lastname","jobtitle","ai__contact_evidence",
                     "validated__linkedin_or_manually","ai__li_still_at_company"],
       "inputs":[{"id":x} for x in ids[i:i+100]]})
    for x in r.get('results',[]): ev[x['id']]=x['properties']
    time.sleep(0.15)
print(f"read back with evidence: {len(ev)}")

STRONG = re.compile(
  r'LinkedIn company-to-people sweep|RE-CONFIRMED ON LINKEDIN|'
  r'Source:\s*linkedin|Source:\s*company_site|Source:\s*sos_filing|'
  r'Matched LinkedIn company', re.I)
WEAK = re.compile(r'Source:\s*(bbb|zoominfo|trade_press|chamber|dealer_locator|pattern)', re.I)

ups=[]; why={'strong':0,'weak':0,'already set':0,'no evidence':0,'inferred only':0}
samples={'strong':[],'weak':[]}
for cid,p in ev.items():
    cur=(p.get('validated__linkedin_or_manually') or '').strip()
    if cur: why['already set']+=1; continue
    e=p.get('ai__contact_evidence') or ''
    if not e.strip(): why['no evidence']+=1; continue
    if 'INFERRED' in e and 'not been verified' in e:
        why['inferred only']+=1; continue
    if STRONG.search(e):
        why['strong']+=1
        if len(samples['strong'])<6:
            samples['strong'].append((cid,f"{p.get('firstname')} {p.get('lastname')}",p.get('jobtitle')))
        ups.append({'id':cid,'properties':{'validated__linkedin_or_manually':'Yes'}})
    elif WEAK.search(e):
        why['weak']+=1
        if len(samples['weak'])<6:
            samples['weak'].append((cid,f"{p.get('firstname')} {p.get('lastname')}",
                                    (WEAK.search(e).group(1) if WEAK.search(e) else '?')))
    else:
        why['no evidence']+=1

print("\nclassification of this cycle's contacts:")
print(f"  STRONG - LinkedIn / company site / SoS filing -> set Yes : {why['strong']}")
print(f"  WEAK   - BBB / ZoomInfo / trade press -> LEFT BLANK      : {why['weak']}")
print(f"  pattern-inferred only -> LEFT BLANK                      : {why['inferred only']}")
print(f"  no usable source marker -> LEFT BLANK                    : {why['no evidence']}")
print(f"  already carried a value (Retired/Needs Updated/etc)      : {why['already set']}")
print("\nsample being set to Yes:")
for cid,n,t in samples['strong']: print(f"   [{cid}] {n:24} {str(t)[:34]}")
print("\nsample deliberately LEFT BLANK (weaker source):")
for cid,n,s in samples['weak']: print(f"   [{cid}] {n:24} source={s}")

if not EXECUTE:
    print("\nDRY RUN - add --execute"); sys.exit(0)

ok=0
for i in range(0,len(ups),100):
    chunk=ups[i:i+100]
    r=req("POST","/crm/v3/objects/contacts/batch/update",{"inputs":chunk})
    if r.get('results'): ok+=len(r['results']); time.sleep(0.35); continue
    for one in chunk:
        rr=req("PATCH",f"/crm/v3/objects/contacts/{one['id']}",{"properties":one['properties']})
        if not rr.get('_err'): ok+=1
        time.sleep(0.1)
print(f"\nset to Yes: {ok} of {len(ups)}")

print("\nREAD-BACK")
chk=[u['id'] for u in ups]; got={}
for i in range(0,len(chk),100):
    r=req("POST","/crm/v3/objects/contacts/batch/read",
      {"properties":["validated__linkedin_or_manually","firstname","lastname"],
       "inputs":[{"id":x} for x in chk[i:i+100]]})
    for x in r.get('results',[]): got[x['id']]=x['properties']
held=sum(1 for p in got.values() if (p.get('validated__linkedin_or_manually') or '')=='Yes')
print(f"  reading 'Yes': {held} of {len(chk)}")
