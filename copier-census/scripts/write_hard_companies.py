"""Record the hard-dealer company verdicts: 11 evidenced negatives plus 35 correction notes.

An evidenced negative is a real result. A dealer proven non-US, defunct, or not a copier dealer
should stop consuming effort every cycle - that is worth as much as a contact.
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
            return {'_err':e.code,'_b':e.read().decode()[:250]}
        except Exception: time.sleep(2*(a+1))
    return {}

rows=json.load(open(S+'/w_all.json'))
# outcome -> the verdict the enum can actually express. 'unresolved' is used for non-US and
# defunct because the enum has no value for either; the NOTE carries the real answer.
VERDICT={'not_a_dealer':'not_dealer','not_us':'unresolved','defunct':'unresolved',
         'found':None,'exhausted':None}
ups=[]; neg=0
for r in rows:
    cid=str(r.get('company_id') or '').strip()
    if not cid: continue
    out=r.get('outcome')
    parts=[f"HARD-DEALER SWEEP 17 Aug 2026 — outcome: {str(out).upper()}"]
    if r.get('legal_entity'): parts.append(f"LEGAL ENTITY: {r['legal_entity']}")
    if r.get('company_corrections'): parts.append("CORRECTIONS:\n"+str(r['company_corrections']))
    if r.get('why_not_found'): parts.append("EVIDENCE / REASONING:\n"+str(r['why_not_found']))
    if r.get('one_remaining_lead'): parts.append("BEST NEXT STEP FOR A HUMAN:\n"+str(r['one_remaining_lead']))
    st=r.get('sources_tried')
    if st: parts.append("SOURCES TRIED: "+(', '.join(st) if isinstance(st,list) else str(st)))
    holds=r.get('suspected_departed') or []
    if holds:
        parts.append("HOLDS — names that look like live owners but are NOT confirmed current "
                     "(prior-generation, retired, or obituary matches). NEVER treated as a "
                     "verdict; a human decides:\n" +
                     "\n".join(f"  - {h.get('name')}: {h.get('reason')} {h.get('evidence_url') or ''}"
                               for h in holds if isinstance(h,dict)))
    if out in ('not_us','defunct','not_a_dealer'):
        neg+=1
        parts.append("WHY THIS IS OFF THE TARGET LIST: this dealer was proven "
            + {'not_us':'NOT A US COMPANY','defunct':'DEFUNCT or no longer independent',
               'not_a_dealer':'NOT A COPIER/MFP DEALER'}[out]
            + ". It should stop consuming research effort each cycle. Note the enum on this "
              "property cannot express 'non-US' or 'defunct', so the verdict is set to "
              "'unresolved' where needed and the real answer lives in this note.")
    props={'ai__data_quality_notes':"\n\n".join(parts)[:60000],
           'ai__verification_date':'2026-08-17'}
    v=VERDICT.get(out)
    if v: props['ai__dealer_verdict']=v
    ups.append({'id':cid,'properties':props,'_name':r.get('company'),'_out':out})
print(f"company records to annotate: {len(ups)}   evidenced negatives: {neg}")
if not EXECUTE:
    for u in ups[:8]:
        print(f"   [{u['id']}] {str(u['_name'])[:34]:36} {u['_out']:14} "
              f"note={len(u['properties']['ai__data_quality_notes'])}c "
              f"verdict={u['properties'].get('ai__dealer_verdict','(unchanged)')}")
    print("\nDRY RUN - add --execute"); sys.exit(0)
ok=0
for u in ups:
    r=req("PATCH",f"/crm/v3/objects/companies/{u['id']}",{"properties":u['properties']})
    if r.get('_err'): print(f"  FAIL [{u['id']}] {u['_name']}: {r.get('_err')} {r.get('_b','')[:110]}")
    else: ok+=1
    time.sleep(0.2)
print(f"annotated {ok} of {len(ups)}")
print("\nREAD-BACK")
ids=[u['id'] for u in ups]; got={}
for i in range(0,len(ids),50):
    rr=req("POST","/crm/v3/objects/companies/batch/read",
      {"properties":["name","ai__dealer_verdict","ai__data_quality_notes"],
       "inputs":[{"id":x} for x in ids[i:i+50]]})
    for x in rr.get('results',[]): got[x['id']]=x['properties']
withnote=sum(1 for p in got.values() if len(p.get('ai__data_quality_notes') or '')>150)
print(f"  carrying the verdict note: {withnote} of {len(ids)}")
print("\n  the evidenced negatives, now recorded:")
for u in ups:
    if u['_out'] in ('not_us','defunct','not_a_dealer'):
        g=got.get(u['id'],{})
        print(f"    [{u['id']}] {str(g.get('name'))[:32]:34} {u['_out']:13} "
              f"verdict={g.get('ai__dealer_verdict')}")
