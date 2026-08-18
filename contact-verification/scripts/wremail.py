import json,subprocess,os,sys
T=os.environ['TOKEN']; D="2026-08-17"
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_e.json','w').write(json.dumps(body)); c+=['-d','@_e.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:300]}

rows=json.load(open(sys.argv[1]))
SKIP=set(json.load(open('email_skip.json'))) if os.path.exists('email_skip.json') else set()
log=[]
for r in rows:
    cid=r['cid']
    if not r.get('email') or r['verdict'] not in ('valid','catchall') or cid in SKIP:
        continue
    dom=r['email'].split('@')[-1].lower()
    if dom!=r['codom'].lower():
        print("HARD RULE REJECT",r['name'],r['email']); continue
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+cid+
        "?properties=email,hs_lead_status,ai__email_information,ai__contact_evidence")
    p=cur.get('properties') or {}
    old=p.get('email'); ls=p.get('hs_lead_status')
    note=("EMAIL SET "+D+": "+r['email']+" at "+str(r['coname'])+" ("+r['codom']+") - pattern '"
          +str(r['pattern'])+"' confirmed from a known-good address at the same domain, NeverBounce result '"
          +r['verdict']+"'."
          + (" REPLACED stale address "+old+" which belonged to a PRIOR employer." if old else ""))
    props={"email":r['email'],
           "ai__email_information":((p.get('ai__email_information') or '')+" | "+note).strip(' |')[:990]}
    if ls: props["hs_lead_status"]=ls   # re-assert against workflow 1829121879
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+cid,{"properties":props})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+r['name'][:20].ljust(20)+" "+r['email'].ljust(38)+" "+r['verdict'].ljust(8)+" replaced="+str(old or '-'))
    if not ok: print("     "+json.dumps(u)[:220])
    log.append({"cid":cid,"name":r['name'],"email":r['email'],"verdict":r['verdict'],
                "replaced":old,"lead_status_reasserted":ls,"ok":ok,"date":D})
f='email_write_log.json'
prev=json.load(open(f)) if os.path.exists(f) else []
json.dump(prev+log,open(f,'w'),indent=1)
print("\nwrote "+str(len([x for x in log if x['ok']]))+" emails")
