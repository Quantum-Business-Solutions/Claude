import json,subprocess,os,re
T=os.environ['TOKEN']; D="2026-08-17"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_fp.json','w').write(json.dumps(body)); c+=['-d','@_fp.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:300]}
def dig(s):
    d=re.sub(r"\D","",s or "")
    if len(d)==11 and d.startswith("1"): d=d[1:]
    return d

aud={r['cid']:r for r in json.load(open('phone_audit.json'))}
owners={}
for x in json.load(open('phone_owners.json')):
    named=[str(n) for n,_ in (x.get('owners') or []) if n]
    if named: owners[(x['cid'],x['field'])]=named[0]

log=[]
for cid,a in aud.items():
    newph=a.get('newco_phone'); newdig=a.get('newco_dig')
    acts=[]; props={}; notes=[]
    for k,val,d in a['suspect']:
        own=owners.get((cid,k))
        if k=="business_phone":
            # business_phone must be the CURRENT employer's business line. It predates the
            # discovered move, so it describes the old job whether or not we can name the owner.
            if newph and newdig and d!=newdig:
                props[k]=newph; acts.append("business_phone -> new employer's line")
            elif not newph:
                props[k]=""; acts.append("business_phone CLEARED (new employer has no number on file)")
            notes.append("business_phone was "+str(val)+(" = "+own+"'s number" if own else " (owner not identified)"))
        elif k=="phone" and own and (a.get('newco') or '').lower()[:12] not in own.lower():
            # only touch `phone` when we PROVED it belongs to a former employer
            props[k]=newph if newph else ""
            acts.append("phone "+("-> new employer's line" if newph else "CLEARED")+" (proved to be "+own+"'s)")
            notes.append("phone was "+str(val)+" = "+own+"'s number")
    if not props: continue
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+cid+"?properties=ai__contact_evidence,mobilephone")
    p=cur.get('properties') or {}
    mob=p.get('mobilephone')
    note=("PHONE CORRECTED "+D+": "+"; ".join(notes)+". A number belonging to a previous employer "
          "would have connected a rep to the wrong company. "
          +("Replaced with "+str(newph)+", the switchboard on the current employer's record. " if newph else
            "No number is on file for the current employer, so the field was cleared rather than left wrong. ")
          +("Mobile "+str(mob)+" is unchanged - a mobile follows the person." if mob else
            "NOTE: no mobile on file, so this contact may now have no dialable number."))
    props["ai__contact_evidence"]=((p.get('ai__contact_evidence') or '')+" || "+note).strip(' |')[:990]
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+cid,{"properties":props})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+str(a['name'])[:20].ljust(20)+" | "+"; ".join(acts))
    if not ok: print("     "+json.dumps(u)[:220])
    log.append({"cid":cid,"name":a['name'],"newco":a['newco'],"acts":acts,"notes":notes,
                "new_phone":newph,"had_mobile":bool(mob),"ok":ok,"date":D})
f='phone_fix_log.json'
prev=json.load(open(f)) if os.path.exists(f) else []
json.dump(prev+log,open(f,'w'),indent=1)
print()
print("records corrected: "+str(len([x for x in log if x['ok']])))
print("of those, left with NO mobile as a fallback: "+str(len([x for x in log if x['ok'] and not x['had_mobile']])))
