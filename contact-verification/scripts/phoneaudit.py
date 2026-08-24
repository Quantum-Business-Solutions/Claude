import json,subprocess,os,sys,re
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_ph.json','w').write(json.dumps(body)); c+=['-d','@_ph.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}

def dig(s):
    d=re.sub(r"\D","",s or "")
    if len(d)==11 and d.startswith("1"): d=d[1:]
    return d

lid=sys.argv[1] if len(sys.argv)>1 else os.environ.get('LIST_ID')
if not lid: sys.stderr.write('usage: %s <listId>\n'%__file__); sys.exit(2)
LOGF='reassoc_'+str(lid)+'_log.json'
if not os.path.exists(LOGF): sys.stderr.write('no '+LOGF+' - run movepipe.py first\n'); sys.exit(2)
L=json.load(open(LOGF))
rows={}
for r in L:
    cid=str(r.get('id') or r.get('cid'))
    rows[cid]={"cid":cid,"newco":r.get('newco'),"name":r.get('name'),
               "coid_logged":r.get('companyId') or r.get('company_id'),
               "unassociated":r.get('unassoc') or []}
ids=list(rows)
PH=["phone","mobilephone","business_phone","hs_calculated_phone_number","company_phone"]
for i in range(0,len(ids),100):
    b={"inputs":[{"id":x} for x in ids[i:i+100]],
       "properties":PH+["firstname","lastname","company","associatedcompanyid","hs_lead_status"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']; rows[x['id']].update(p)
        if not rows[x['id']]['name']:
            rows[x['id']]['name']=str(p.get('firstname'))+" "+str(p.get('lastname'))

# new company phone
coids=sorted({v.get('associatedcompanyid') or v.get('coid_logged') for v in rows.values()
              if (v.get('associatedcompanyid') or v.get('coid_logged'))})
co={}
for i in range(0,len(coids),100):
    b={"inputs":[{"id":x} for x in coids[i:i+100]],"properties":["name","domain","phone"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/batch/read',b)
    for x in r.get('results',[]): co[x['id']]=x['properties']

out=[]
for v in rows.values():
    c=co.get(v.get('associatedcompanyid') or v.get('coid_logged')) or {}
    newph=dig(c.get('phone'))
    rec={"cid":v['cid'],"name":v['name'],"newco":c.get('name') or v.get('newco'),
         "newco_phone":c.get('phone'),"newco_dig":newph}
    for k in PH: rec[k]=v.get(k)
    # which business-ish numbers do NOT match the new company's switchboard?
    suspect=[]
    for k in ("phone","business_phone","company_phone"):
        val=v.get(k)
        if not val: continue
        d=dig(val)
        if newph and d==newph: continue          # correct company switchboard
        suspect.append((k,val,d))
    rec["suspect"]=suspect
    rec["has_mobile"]=bool(v.get('mobilephone'))
    out.append(rec)

json.dump(out,open('phone_audit.json','w'),indent=1)
n_sus=len([r for r in out if r['suspect']])
print("movers audited:",len(out))
print("with a business/company number that does NOT match their new employer's switchboard:",n_sus)
print("with a mobile on file (follows the person, safe):",len([r for r in out if r['has_mobile']]))
print()
print("name                 | new employer          | new co switchboard | number on the contact")
for r in out:
    if not r['suspect']: continue
    for k,val,d in r['suspect']:
        print(str(r['name'])[:20].ljust(20)+" | "+str(r['newco'])[:21].ljust(21)+" | "
              +str(r['newco_phone'] or '-')[:18].ljust(18)+" | "+k+"="+str(val))
