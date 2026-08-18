"""Consolidate the dealer-people sweep and write it, respecting the email-classification rule.

Shawn's rule, verbatim in effect:
  - a PERSONAL address never touches the primary `email` field
  - a populated business `email` is never overwritten
  - personal addresses go to `linkedin__email` only
  - a business address goes to `email` only when the record has none, otherwise `email_other`

This matters concretely: the President/CEO of ICC Business Products publishes
james.m.ray@gmail.com on LinkedIn, and Jeff Feller publishes jeff@gofeller.com - his own side
business, not the dealer's domain. Both would have landed in the primary field under the old
logic and poisoned a send list.
"""
import os, sys, json, glob, re, time, urllib.request, urllib.error
sys.path.insert(0,'/tmp')
from resolver import Companies, first_forms, last_forms, nmz, canon_li
from collections import defaultdict, Counter
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
            return {'_err':e.code,'_b':e.read().decode()[:300]}
        except Exception: time.sleep(2*(a+1))
    return {}

FREE={'gmail','googlemail','yahoo','ymail','rocketmail','hotmail','outlook','live','msn','aol',
      'icloud','me','mac','protonmail','proton','gmx','mail','zoho','yandex','comcast','verizon',
      'att','sbcglobal','bellsouth','cox','charter','spectrum','earthlink','juno','netzero',
      'roadrunner','rr','optonline','frontier','windstream','embarqmail','q','shaw','rogers',
      'sympatico','telus','bell','midco','cableone','centurylink','suddenlink','wowway','ptd',
      'hotmail','aim','btinternet','sky','virginmedia'}
def classify(email, dealer_domain):
    e=(email or '').strip().lower()
    if not e or '@' not in e: return (None,None,None)
    dom=e.split('@')[-1]
    root=dom.split('.')[0]
    dd=(dealer_domain or '').lower().replace('www.','')
    if root in FREE: return (e,'personal',dom)
    if dd and (dd in dom or dom in dd): return (e,'business',dom)
    # The CRM's dealer domain is null on many records. A corporate (non-free-mail) address is
    # then EVIDENCE of what the domain should be, not a mismatch - pflesch@gflesch.com told us
    # Gordon Flesch's domain, which the record was missing.
    if not dd: return (e,'business_domain_evidence',dom)
    return (e,'unknown',dom)

DM=re.compile(r'president|ceo|owner|chief|principal|founder|partner|vp\b|vice president|'
              r'director|general manager|coo|cro|cso|cmo|cfo|chairman|proprietor',re.I)
GONE=re.compile(r'\bformer\b|\bretired\b|\bex-\b|no longer|\bemeritus\b|role ended|departed',re.I)

comps=json.load(open(S+'/dealers_live.json'))
CO=Companies(comps)
hold=set(json.load(open(S+'/freeze_final.json'))['hard'])
D=json.load(open(S+'/xlsx_data.json'))
held=defaultdict(list)
for cid,lst in D['contacts'].items():
    held[CO.cluster(cid)] += lst

rows=[]
for f in sorted(glob.glob(S+'/gapwork/out/P*.jsonl')):
    for l in open(f):
        l=l.strip()
        if not l: continue
        try: rows.append(json.loads(l))
        except Exception: pass
print(f"dealers in the sweep output: {len(rows)}")

create=[]; fold=[]; skip=Counter(); ecls=Counter()
for o in rows:
    ids=[i for i in (o.get('company_ids') or '').split(';') if i]
    if not ids: skip['no company id']+=1; continue
    cl=CO.cluster(ids[0]); mem=CO.members.get(cl) or ids
    if any(m in hold for m in mem): skip['client hold']+=1; continue
    dd=o.get('domain')
    existing=held.get(cl,[])
    for p in (o.get('people') or []):
        nm=(p.get('name') or '').strip()
        parts=nm.replace(',',' ').split()
        if len(parts)<2: skip['unusable name']+=1; continue
        title=(p.get('title') or p.get('headline') or '').strip()
        if not DM.search(title): skip['below the DM bar']+=1; continue
        if GONE.search(title): skip['title says departed']+=1; continue
        em,cls,dom = classify(p.get('email'), dd)
        if cls: ecls[cls]+=1
        rec={'first':parts[0],'last':parts[-1],'title':title,'company':o.get('company'),
             'company_id':ids[0],'domain':dd,'li':p.get('profile_url'),
             'email':em,'email_class':cls,'email_domain':dom,
             'nd':p.get('network_distance'),'headline':p.get('headline'),
             'evidence':p.get('evidence_quote') or p.get('headline'),
             'li_company':o.get('li_company_name'),'li_company_id':o.get('li_company_id')}
        fa,la=first_forms(parts[0]), last_forms(parts[-1])
        match=None
        for q in existing:
            if (first_forms(q.get('firstname')) & fa) and (last_forms(q.get('lastname')) & la):
                match=q; break
        if match:
            rec['existing_id']=match['id']; rec['existing_title']=match.get('jobtitle')
            rec['existing_email']=match.get('email')
            fold.append(rec)
        else:
            create.append(rec)

print(f"\nCREATE (new to the portal) : {len(create)}")
print(f"FOLD   (already on dealer)  : {len(fold)}")
print("skipped:", dict(skip))
print("email classes seen:", dict(ecls))
prim=[c for c in create if c['email_class'] in ('business','business_domain_evidence')]
pers=[c for c in create+fold if c['email_class']=='personal']
unk=[c for c in create+fold if c['email_class']=='unknown']
print(f"\n  business emails -> primary field  : {len(prim)}")
print(f"  PERSONAL emails -> linkedin__email : {len(pers)}")
print(f"  unknown domain  -> linkedin__email : {len(unk)}")
if pers:
    print("\n  personal addresses correctly kept OUT of the primary field:")
    for c in pers[:8]:
        print(f"     {c['first']} {c['last']:16} {c['email']:34} ({c['title'][:26]}) @ {str(c['company'])[:22]}")
if unk:
    print("\n  unknown-domain addresses held for review:")
    for c in unk[:8]:
        print(f"     {c['first']} {c['last']:16} {c['email']:34} dealer domain={c['domain']}")
json.dump(create, open(S+'/dp_create.json','w'), indent=1)
json.dump(fold, open(S+'/dp_fold.json','w'), indent=1)
print("\nwrote dp_create.json / dp_fold.json")
if not EXECUTE:
    print("DRY RUN - add --execute")
    sys.exit(0)

# ---------------------------------------------------------------- WRITE
def route_email(rec):
    """Return (primary_email_or_None, extra_props). Shawn's rule enforced here."""
    em, cls = rec.get('email'), rec.get('email_class')
    extra = {}
    if not em: return None, extra
    extra['linkedin__email'] = em          # provenance, always
    if cls == 'personal':
        return None, extra                 # NEVER the primary field
    if cls == 'unknown':
        return None, extra                 # held for review
    return em, extra                       # business / domain-evidence

def taken(idprop, vals):
    hit={}
    vals=[v for v in dict.fromkeys(vals) if v]
    for k in range(0,len(vals),100):
        rq=req("POST","/crm/v3/objects/contacts/batch/read",
          {"idProperty":idprop,"properties":["firstname","lastname"],
           "inputs":[{"id":v} for v in vals[k:k+100]]})
        for x in rq.get('results',[]):
            key=x['properties'].get(idprop)
            if idprop=='email' and key: key=key.lower()
            hit[key]=x['id']
        time.sleep(0.25)
    return hit

# ---- build creates
ins=[]; seen=set()
for r in create:
    k=(nmz(r['first']), nmz(r['last']), r['company_id'])
    if k in seen: continue
    seen.add(k)
    prim, extra = route_email(r)
    q={'firstname':r['first'][:60],'lastname':r['last'][:60],
       'jobtitle':r['title'][:200],'associatedcompanyid':r['company_id'],
       'ai__contact_verified_date':'2026-08-17','ai__sources_confirming':1,
       'ai__li_still_at_company':'yes'}
    if prim: q['email']=prim
    else:    q['hs_lead_status']='Need Updated Info'
    q.update(extra)
    li=canon_li(r.get('li'))
    if li:
        q['linkedin_profile_url__unique_value']=li
        q['hs_linkedin_url']=li
    emnote=""
    if r.get('email'):
        if r['email_class']=='personal':
            emnote=(f"\n\nEMAIL FOUND BUT DELIBERATELY NOT SET AS THE BUSINESS EMAIL: "
                    f"{r['email']} is on {r['email_domain']}, a consumer mail provider. It is "
                    f"stored in 'LinkedIn - E-Mail' instead. A personal address must never "
                    f"occupy the business email field.")
        elif r['email_class']=='unknown':
            emnote=(f"\n\nEMAIL HELD FOR REVIEW: {r['email']} is on {r['email_domain']}, which "
                    f"is not this dealer's recorded domain ({r.get('domain')}). It may be a "
                    f"legitimate alias or a different company - stored in 'LinkedIn - E-Mail' "
                    f"only until someone confirms.")
        elif r['email_class']=='business_domain_evidence':
            emnote=(f"\n\nNOTE ON THE DOMAIN: this record had NO domain on the company. The "
                    f"address {r['email']} indicates the dealer's real mail domain is "
                    f"{r['email_domain']} - worth setting on the company record.")
    q['ai__contact_evidence']=(
      "CREATED 17 Aug 2026 - LinkedIn company-to-people sweep (dealer-people module)\n\n"
      f"Dealer: {r.get('company')} ({r.get('domain') or 'no domain on record'})\n"
      f"Matched LinkedIn company: {r.get('li_company')} [{r.get('li_company_id')}]\n"
      f"Profile: {r.get('li') or '(none)'}\n"
      f"Network distance: {r.get('nd')}\n"
      f"Headline (verbatim): \"{(r.get('evidence') or '')[:300]}\"\n\n"
      "METHOD: the dealer's own LinkedIn company page was located and verified by city/state or "
      "domain, then its people were listed and filtered to those whose headline names this "
      "dealer. The company filter is known to leak - unrelated people surfaced on genuine "
      "searches - so every person kept here was checked against the dealer by headline."
      + emnote)
    ins.append({'properties':q})

print(f"creates prepared: {len(ins)}")
if os.environ.get('FOLD_ONLY'):
    ins=[]
t_li=taken('linkedin_profile_url__unique_value',
           [i['properties'].get('linkedin_profile_url__unique_value') for i in ins])
t_em=taken('email',[i['properties'].get('email') for i in ins])
drop=0
for i in ins:
    q=i['properties']
    u=q.get('linkedin_profile_url__unique_value'); e=(q.get('email') or '').lower()
    if (u and u in t_li) or (e and e in t_em): q['_skip']=1; drop+=1
ins=[i for i in ins if not i['properties'].pop('_skip',None)]
print(f"live pre-check dropped {drop} already-present; creating {len(ins)}")

created=[]
for i in range(0,len(ins),50):
    chunk=ins[i:i+50]
    r=req("POST","/crm/v3/objects/contacts/batch/create",{"inputs":chunk})
    if r.get('results'): created+=[x['id'] for x in r['results']]; time.sleep(0.4); continue
    for one in chunk:
        rr=req("POST","/crm/v3/objects/contacts",one)
        if rr.get('id'): created.append(rr['id'])
        time.sleep(0.12)
print(f"created: {len(created)} of {len(ins)}")

# associatedcompanyid on create is silently ignored - associate explicitly
byname={(i['properties']['firstname'].lower(),i['properties']['lastname'].lower()):
        i['properties']['associatedcompanyid'] for i in ins}
att=0
for k in range(0,len(created),100):
    r=req("POST","/crm/v3/objects/contacts/batch/read",
      {"properties":["firstname","lastname","associatedcompanyid"],
       "inputs":[{"id":x} for x in created[k:k+100]]})
    for x in r.get('results',[]):
        pp=x['properties']
        if (pp.get('associatedcompanyid') or '').strip(): att+=1; continue
        co=byname.get(((pp.get('firstname') or '').lower(),(pp.get('lastname') or '').lower()))
        if not co: continue
        a=req("PUT",f"/crm/v4/objects/contacts/{x['id']}/associations/companies/{co}",
              [{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":1}])
        if not a.get('_err'): att+=1
        time.sleep(0.12)
print(f"attached to a dealer: {att} of {len(created)}")

# ---- folds: never overwrite a populated business email
ups={}
for r in fold:
    cid=str(r.get('existing_id') or '')
    if not cid.isdigit(): continue
    props={}; ev=[]
    t=r['title']
    if t and t.lower()!=str(r.get('existing_title') or '').lower():
        props['jobtitle']=t[:200]
        ev.append(f"title {r.get('existing_title')!r} -> {t!r} (LinkedIn is authoritative)")
    prim, extra = route_email(r)
    props.update(extra)
    if extra.get('linkedin__email'): ev.append(f"LinkedIn-published address recorded: {extra['linkedin__email']} ({r['email_class']})")
    if prim:
        if not (r.get('existing_email') or '').strip():
            props['email']=prim; ev.append(f"business email filled: {prim}")
        elif (r.get('existing_email') or '').lower()!=prim.lower():
            props['email_other']=prim
            ev.append(f"different business email found ({prim}) - stored in Email Other, "
                      f"primary {r.get('existing_email')} left untouched")
    li=canon_li(r.get('li'))
    if li: props['hs_linkedin_url']=li
    if not props: continue
    props['ai__contact_verified_date']='2026-08-17'
    props['ai__li_still_at_company']='yes'
    props['ai__contact_evidence']=(
      "RE-CONFIRMED ON LINKEDIN 17 Aug 2026 - dealer-people sweep\n\n"
      f"Found on {r.get('company')}'s own LinkedIn company page.\n"
      f"Headline (verbatim): \"{(r.get('evidence') or '')[:280]}\"\n"
      f"Network distance: {r.get('nd')}\n\n" + "\n".join('- '+e for e in ev) +
      "\n\nA populated business email is NEVER overwritten, and a personal address is NEVER "
      "written to the business email field.")
    if cid in ups: ups[cid]['properties'].update(props)
    else: ups[cid]={'id':cid,'properties':props}
# A batch update is all-or-nothing too: one unique-value conflict on `email` took an entire
# batch of folds down. Retry the batch per record, and when the conflict is the email itself,
# move that address to email_other rather than losing the whole update.
u=list(ups.values()); ok=0; conf=[]
for i in range(0,len(u),100):
    chunk=u[i:i+100]
    r=req("POST","/crm/v3/objects/contacts/batch/update",{"inputs":chunk})
    if r.get('results'):
        ok+=len(r['results']); time.sleep(0.35); continue
    print(f"  batch of {len(chunk)} rejected ({r.get('_err')}) - retrying individually")
    for one in chunk:
        rr=req("PATCH",f"/crm/v3/objects/contacts/{one['id']}",{"properties":one['properties']})
        if not rr.get('_err'): ok+=1; time.sleep(0.1); continue
        body=rr.get('_b','') or ''
        if 'propertyName=email' in body or 'already has that value' in body.lower():
            pr=dict(one['properties']); moved=pr.pop('email',None)
            if moved:
                pr['email_other']=moved
                pr['ai__contact_evidence']=(pr.get('ai__contact_evidence','')
                    + f"\n\nEMAIL NOT SET AS PRIMARY: {moved} is already held as the unique email "
                      f"on another contact in this portal. Stored in Email Other instead so the "
                      f"address is not lost and no existing record is disturbed. Worth checking "
                      f"whether the two records are the same person.")
            rr2=req("PATCH",f"/crm/v3/objects/contacts/{one['id']}",{"properties":pr})
            if not rr2.get('_err'): ok+=1; conf.append((one['id'],moved,'moved to email_other'))
            else: conf.append((one['id'],moved,f"still failed: {rr2.get('_err')}"))
        else:
            conf.append((one['id'],None,f"{rr.get('_err')} {body[:90]}"))
        time.sleep(0.12)
print(f"folded: {ok} of {len(u)}")
if conf:
    print(f"fold conflicts handled: {len(conf)}")
    for cid,em,w in conf[:12]: print(f"    [{cid}] {em or ''} -> {w}")

print("\nREAD-BACK")
chk=created[:]+[v['id'] for v in ups.values()]
got={}
for k in range(0,len(chk),100):
    r=req("POST","/crm/v3/objects/contacts/batch/read",
      {"properties":["firstname","lastname","jobtitle","email","linkedin__email",
                     "email_other","associatedcompanyid","ai__contact_evidence"],
       "inputs":[{"id":x} for x in chk[k:k+100]]})
    for x in r.get('results',[]): got[x['id']]=x['properties']
liem=sum(1 for p in got.values() if (p.get('linkedin__email') or '').strip())
withco=sum(1 for c in created if (got.get(c,{}).get('associatedcompanyid') or '').strip())
withev=sum(1 for c in chk if len(got.get(c,{}).get('ai__contact_evidence') or '')>100)
print(f"  records read back            : {len(got)} of {len(chk)}")
print(f"  creates attached to a dealer : {withco} of {len(created)}")
print(f"  carrying evidence            : {withev} of {len(chk)}")
print(f"  linkedin__email populated    : {liem}")
# prove no personal address reached the primary field
FREEC={e['email'].lower() for e in create+fold if e.get('email_class')=='personal' and e.get('email')}
bad=[c for c,p in got.items() if (p.get('email') or '').lower() in FREEC]
print(f"  personal addresses that leaked into the primary email field: {len(bad)}"
      + ("  <-- GOOD" if not bad else f"  <-- PROBLEM {bad[:5]}"))
json.dump(created, open(S+'/dp_created.json','w'))
