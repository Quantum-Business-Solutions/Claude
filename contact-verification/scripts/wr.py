import json,subprocess,os,sys
D="2026-08-17"
V=json.load(open(sys.argv[1]))
inputs=[]
for r in V:
    p={"ai__li_still_at_company":r['verdict'],"ai__contact_evidence":r['ev'][:990],"ai__contact_verified_date":D,"ai__sources_confirming":1}
    if r.get('ls'): p["hs_lead_status"]=r['ls']
    inputs.append({"id":r['id'],"properties":p})
open('_wb.json','w').write(json.dumps({"inputs":inputs}))
res=json.loads(subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+os.environ['TOKEN'],'-H','Content-Type: application/json','-d','@_wb.json','https://api.hubapi.com/crm/v3/objects/contacts/batch/update'],capture_output=True,text=True).stdout)
print('status',res.get('status'),'updated',len(res.get('results',[])))
if res.get('message'): print(json.dumps(res)[:400])
log=json.load(open('li_verdicts.json'))
for r in V: log.append({"id":r['id'],"verdict":r['verdict'],"new_company":r.get('newco'),"lead_status":r.get('ls'),"date":D})
json.dump(log,open('li_verdicts.json','w'),indent=1)
from collections import Counter
print('TOTAL',len(log),Counter(x['verdict'] for x in log))
