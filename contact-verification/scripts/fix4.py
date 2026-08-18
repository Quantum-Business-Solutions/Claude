import json,subprocess,os
T=os.environ['TOKEN']; D="2026-08-17"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_x.json','w').write(json.dumps(body)); c+=['-d','@_x.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:400]}

JOBS=[
 {"cid":"213196247380","name":"Stacy Malyil","new":"stacys@aidoc.com","codom":"aidoc.com",
  "clear_additional":True,
  "why":"stacys@aidoc.com was ALREADY sitting in this record's hs_additional_emails - the current-"
        "employer address was in the CRM the whole time, just not in the primary Email field. "
        "NeverBounce 'valid'. Promoted to primary."},
 {"cid":"214602982813","name":"Mariana Cogan","new":"mariana.cogan@hexagon.com","codom":"hexagon.com",
  "clear_additional":True,
  "why":"mariana.cogan@hexagon.com was already in this record's hs_additional_emails. NeverBounce "
        "'valid'. hexagon.com is the PARENT group domain (ZoomInfo id 17662709) of Hexagon "
        "Manufacturing Intelligence (id 396535383), the division LinkedIn confirms she leads "
        "marketing for - a group that size runs one corporate mail domain. Promoted to primary."},
 {"cid":"136488761141","name":"Kristin Melville","new":"kris.melville@celigo.com","codom":"celigo.com",
  "clear_additional":True,
  "why":"she goes by KRIS, not Kristin. celigo.com rejected kristin.melville, kmelville, "
        "kristinmelville, kristin, kris and melville as INVALID but accepts kris.melville - the "
        "server discriminates, so this is a genuine positive and not a catch-all."},
]
CLEAR=[
 {"cid":"224274393164","name":"Juliann Irwin","codom":"sandkindustrial.com",
  "why":"no address at sandkindustrial.com could be established - the only in-house sample "
        "(a.preston@) has an ambiguous name order and the server answers 'unknown' to every "
        "candidate, so nothing is provable. Her kasasa.com address is dead."},
]
log=[]
for j in JOBS:
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+j['cid']+
        "?properties=email,hs_additional_emails,previous__email,previous__company_domain_name,ai__email_information,hs_lead_status")
    p=cur.get('properties') or {}
    old=p.get('email'); addl=p.get('hs_additional_emails')
    note=("EMAIL REPAIRED "+D+": primary set to "+j['new']+". "+j['why']
          + (" Prior primary "+old+" (former employer) filed to Previous - Email." if old else "")
          + (" Former-employer address also seen in secondary field: "+addl+"." if addl else ""))
    props={"email":j['new'],
           "ai__email_information":((p.get('ai__email_information') or '')+" | "+note).strip(' |')[:990]}
    if old and not p.get('previous__email'): props['previous__email']=old
    if old and not p.get('previous__company_domain_name'):
        props['previous__company_domain_name']="https://"+old.split('@')[-1].lower()
    if j.get('clear_additional') and addl: props['hs_additional_emails']=''
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+j['cid'],{"properties":props})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+j['name'][:20].ljust(20)+" -> "+j['new'].ljust(34)+" (was "+str(old)+")")
    if not ok: print("     "+json.dumps(u)[:300])
    log.append({"cid":j['cid'],"name":j['name'],"email":j['new'],"replaced":old,"ok":ok,
                "verdict":"valid","date":D})

for j in CLEAR:
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+j['cid']+
        "?properties=email,hs_additional_emails,previous__email,previous__company_domain_name,ai__email_information")
    p=cur.get('properties') or {}
    old=p.get('email'); addl=p.get('hs_additional_emails')
    note=("EMAIL CLEARED "+D+": "+str(old)+" belonged to a PRIOR employer and has been moved to "
          "Previous - Email. "+j['why']+" No address at "+j['codom']+" is on file - phone only.")
    props={"ai__email_information":((p.get('ai__email_information') or '')+" | "+note).strip(' |')[:990]}
    if old and not p.get('previous__email'): props['previous__email']=old
    if old and not p.get('previous__company_domain_name'):
        props['previous__company_domain_name']="https://"+old.split('@')[-1].lower()
    if addl: props['hs_additional_emails']=''
    # must clear secondaries before the primary; do it in two writes
    u1=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+j['cid'],{"properties":props})
    u2=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+j['cid'],{"properties":{"email":""}})
    ok=('id' in u1) and ('id' in u2)
    print(("OK  " if ok else "ERR ")+j['name'][:20].ljust(20)+" -> EMAIL CLEARED (was "+str(old)+")")
    if 'id' not in u2: print("     clear step: "+json.dumps(u2)[:300])
    log.append({"cid":j['cid'],"name":j['name'],"email":None,"replaced":old,"ok":ok,
                "verdict":"cleared-no-address-obtainable","date":D})

f='email_write_log.json'
prev=json.load(open(f)) if os.path.exists(f) else []
json.dump(prev+log,open(f,'w'),indent=1)
print("\ndone")
