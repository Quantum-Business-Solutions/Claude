import json,subprocess,os
T=os.environ['TOKEN']; D="2026-08-17"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_sm.json','w').write(json.dumps(body)); c+=['-d','@_sm.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
L=json.load(open('reassoc_log.json'))
ids=sorted({str(r.get('id') or r.get('cid')) for r in L if (r.get('id') or r.get('cid'))})
print("movers we re-associated:",len(ids))
missing=[]
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],"properties":["ai__contact_evidence","firstname","lastname","company"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        ev=x['properties'].get('ai__contact_evidence') or ''
        if 'RE-ASSOCIATED' not in ev:
            missing.append((x['id'],ev,str(x['properties'].get('firstname'))+' '+str(x['properties'].get('lastname')),x['properties'].get('company')))
print("missing the RE-ASSOCIATED marker:",len(missing))
for cid,ev,nm,co in missing: print("   "+nm[:22].ljust(22)+str(co)[:22])
if missing:
    inputs=[]
    for cid,ev,nm,co in missing:
        note=("RE-ASSOCIATED "+D+": primary associated company was changed to "+str(co)+
              " after LinkedIn confirmed they no longer work at the company previously on file.")
        inputs.append({"id":cid,"properties":{"ai__contact_evidence":((ev+" || "+note).strip(' |'))[:990]}})
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/update',{"inputs":inputs})
    print("stamped:",len(r.get('results',[])),"status",r.get('status'))
