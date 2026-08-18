import json,subprocess,os
T=os.environ['TOKEN']; D="2026-08-17"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_r2.json','w').write(json.dumps(body)); c+=['-d','@_r2.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:300]}

# DERIVE: pattern confirmed by an in-house sample at the exact domain, but the mail
# server refuses SMTP verification so NeverBounce returns 'unknown'. Write + flag.
DERIVE=[
 {"cid":"213005271434","name":"Kelli Negro","email":"kelli.negro@workday.com","dom":"workday.com",
  "why":"pattern first.last confirmed by sara.williamson@workday.com already in the portal"},
 {"cid":"1295967","name":"Nancy Elsner","email":"nelsner@artsquest.org","dom":"artsquest.org",
  "why":"pattern flast confirmed by khilgert@artsquest.org already in the portal, AND her own prior "
        "address used the identical local part (nelsner@touchtunes.com)"},
]
# FLAG ONLY: cannot derive a defensible address. Leave the field alone, warn in evidence.
FLAG=[
 {"cid":"136488761141","name":"Kristin Melville","dom":"celigo.com",
  "why":"celigo.com DOES answer verification and returned INVALID for all four standard patterns, "
        "so her real address is non-standard. A guess would be wrong, not just unproven."},
 {"cid":"213196247380","name":"Stacy Malyil","dom":"aidoc.com",
  "why":"aidoc.com uses two different formats in the portal (elad@ and parkero@) so the pattern is "
        "ambiguous, and the server will not confirm a mailbox."},
 {"cid":"224274393164","name":"Juliann Irwin","dom":"sandkindustrial.com",
  "why":"only in-house sample is a.preston@sandkindustrial.com whose name order is itself unclear, "
        "so no reliable pattern; server will not confirm a mailbox."},
 {"cid":"214602982813","name":"Mariana Cogan","dom":"hexagonmi.com",
  "why":"no known-good address at hexagonmi.com anywhere in the portal and the server will not "
        "confirm a mailbox, so there is no evidence to build on."},
]
log=[]
for r in DERIVE:
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+r['cid']+
        "?properties=email,hs_lead_status,ai__email_information")
    p=cur.get('properties') or {}; old=p.get('email'); ls=p.get('hs_lead_status')
    note=("EMAIL SET "+D+" (UNVERIFIED - PATTERN DERIVED): "+r['email']+" - "+r['why']+
          ". NeverBounce could not confirm the mailbox because "+r['dom']+" does not respond to "
          "SMTP verification (result 'unknown'), so treat this as probable, not proven."
          + (" REPLACED stale address "+old+" belonging to a PRIOR employer." if old else ""))
    props={"email":r['email'],
           "ai__email_information":((p.get('ai__email_information') or '')+" | "+note).strip(' |')[:990]}
    if ls: props["hs_lead_status"]=ls
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+r['cid'],{"properties":props})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+"DERIVED  "+r['name'][:20].ljust(20)+" "+r['email'].ljust(34)+" replaced="+str(old or '-'))
    if not ok: print("     "+json.dumps(u)[:200])
    log.append({"cid":r['cid'],"name":r['name'],"email":r['email'],"verdict":"unverified-derived",
                "replaced":old,"ok":ok,"date":D})

for r in FLAG:
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+r['cid']+
        "?properties=email,ai__email_information")
    p=cur.get('properties') or {}; old=p.get('email')
    note=("EMAIL NOT REPAIRED "+D+": the address on this record ("+str(old)+") belongs to a PRIOR "
          "employer and is almost certainly dead. I could not derive a defensible address at "
          +r['dom']+": "+r['why']+" DO NOT EMAIL this address - phone only until someone confirms it.")
    props={"ai__email_information":((p.get('ai__email_information') or '')+" | "+note).strip(' |')[:990]}
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+r['cid'],{"properties":props})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+"FLAGGED  "+r['name'][:20].ljust(20)+" keeps "+str(old))
    log.append({"cid":r['cid'],"name":r['name'],"email":None,"verdict":"flagged-stale-kept",
                "replaced":None,"stale_left_in_place":old,"ok":ok,"date":D})

f='email_write_log.json'
prev=json.load(open(f)) if os.path.exists(f) else []
json.dump(prev+log,open(f,'w'),indent=1)
print("\nderived "+str(len(DERIVE))+", flagged "+str(len(FLAG)))
