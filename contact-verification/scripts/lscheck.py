import json,subprocess,os
T=os.environ['TOKEN']
log=json.load(open('email_write_log.json'))
ids=[x['cid'] for x in log if x['ok']]
body={"inputs":[{"id":i} for i in ids],"properties":["email","hs_lead_status","firstname","lastname","ai__li_still_at_company"]}
open('_q.json','w').write(json.dumps(body))
o=subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+T,'-H','Content-Type: application/json',
 '-d','@_q.json','https://api.hubapi.com/crm/v3/objects/contacts/batch/read'],capture_output=True,text=True).stdout
r=json.loads(o)
want={x['cid']:x['lead_status_reasserted'] for x in log}
for x in r.get('results',[]):
    p=x['properties']; w=want.get(x['id'])
    got=p.get('hs_lead_status')
    flag='OK ' if got==w else 'DRIFT'
    print(f"{flag} {str(p.get('firstname'))+' '+str(p.get('lastname')):24s} email={p.get('email'):38s} lead={got} (wanted {w})")
