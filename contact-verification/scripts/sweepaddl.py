import json,subprocess,os
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_s2.json','w').write(json.dumps(body)); c+=['-d','@_s2.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    return json.loads(o) if o.strip() else {}
L=json.load(open('reassoc_log.json'))
rows={}
for r in L:
    cid=r.get('id') or r.get('cid')
    rows[cid]={"cid":cid,"coid":r.get('companyId') or r.get('company_id'),"name":r.get('name')}
ids=list(rows)
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],
       "properties":["email","hs_additional_emails","email_2","email_other","work_email",
                     "linkedin__email","firstname","lastname","associatedcompanyid"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']; rows[x['id']].update(p)
        if not rows[x['id']]['name']: rows[x['id']]['name']=str(p.get('firstname'))+' '+str(p.get('lastname'))
coids=sorted({v.get('associatedcompanyid') or v.get('coid') for v in rows.values() if (v.get('associatedcompanyid') or v.get('coid'))})
dom={}
for i in range(0,len(coids),100):
    b={"inputs":[{"id":x} for x in coids[i:i+100]],"properties":["domain","name"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/batch/read',b)
    for x in r.get('results',[]): dom[x['id']]=(x['properties'].get('domain'),x['properties'].get('name'))
hits=[]
for v in rows.values():
    d,cn=dom.get(v.get('associatedcompanyid') or v.get('coid'),(None,None))
    if not d: continue
    prim=(v.get('email') or '').lower()
    if prim.endswith('@'+d.lower()): continue          # already correct
    pool=[]
    for k in ("hs_additional_emails","email_2","email_other","work_email","linkedin__email"):
        for e in (v.get(k) or '').replace(' ','').split(';'):
            if e: pool.append((k,e))
    cand=[(k,e) for k,e in pool if e.lower().endswith('@'+d.lower())]
    if cand:
        hits.append({"cid":v['cid'],"name":v['name'],"coname":cn,"codom":d,
                     "primary":v.get('email'),"found":cand[0][1],"src":cand[0][0]})
json.dump(hits,open('addl_hits.json','w'),indent=1)
print("movers whose CURRENT-employer address was already sitting in a secondary field:",len(hits))
for h in hits: print("  "+h['name'][:22].ljust(22)+" "+h['found'].ljust(36)+" from "+h['src']+"  (primary was "+str(h['primary'])+")")
