import json,subprocess,os
T=os.environ['TOKEN']; D="2026-08-18"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_f9.json','w').write(json.dumps(body)); c+=['-d','@_f9.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:250]}

pairs=json.load(open('pairs9.json'))
log=[]
for p in pairs:
    cid=p.get('cid')
    if not cid:
        # look the contact up by name + company
        nm=p['name'].split()
        r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',
          {"filterGroups":[{"filters":[
            {"propertyName":"firstname","operator":"EQ","value":nm[0]},
            {"propertyName":"lastname","operator":"EQ","value":nm[-1]}]}],
           "properties":["firstname","lastname","company","business_phone","ai__contact_evidence"],"limit":3})
        hits=[x for x in r.get('results',[]) if (x['properties'].get('company') or '')==p['employer']]
        if not hits:
            print("SKIP could not locate "+p['name']); continue
        c0=hits[0]; cid=c0['id']; props0=c0['properties']
    else:
        props0=(call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+cid+
                     "?properties=ai__contact_evidence,business_phone").get('properties') or {})
    ev=props0.get('ai__contact_evidence') or ''
    note=("PHONE CONFLICT FLAGGED "+D+": business_phone "+str(p['number'])+" is registered to "
          +str(p['owner'])+" ("+str(p['owner_domain'])+"), not to "+str(p['employer'])+" ("
          +str(p['employer_domain'])+"). This contact is CONFIRMED CURRENT at "+str(p['employer'])+
          ", so the number was NOT overwritten - it may be a predecessor or acquired-company line "
          "that still reaches them, and replacing a working direct line with a toll-free menu would "
          "be worse. VERIFY BEFORE DIALING. Note the vendor alias test cannot settle this: it keeps "
          "predecessor names as separate company records with separate ids.")
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+cid,
           {"properties":{"ai__contact_evidence":((ev+" || "+note).strip(' |'))[:990]}})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+str(p['name'])[:20].ljust(20)+str(p['employer'])[:20].ljust(20)
          +"flagged: number belongs to "+str(p['owner']))
    if not ok: print("     "+json.dumps(u)[:200])
    log.append({"cid":cid,"name":p['name'],"employer":p['employer'],"number":p['number'],
                "owner":p['owner'],"action":"flagged, not overwritten","ok":ok,"date":D})
json.dump(log,open('phone_flag9_log.json','w'),indent=1)
print("\nflagged "+str(len([x for x in log if x['ok']]))+" of "+str(len(pairs)))
