import json,subprocess,os
T=os.environ['TOKEN']; D="2026-08-17"
MARK="[NOT-"+"MKT]"          # built at runtime so THIS file never seeds the token into a note
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_u.json','w').write(json.dumps(body)); c+=['-d','@_u.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {"raw":o[:300]}

WHY={
 "Ann Boyd":"VP Communications at Checkmarx - owns comms/brand spend and sits in the marketing org.",
 "Rich Wenning":"Market Director North America at Consortium Networks - a senior revenue leader "
                "(ex-CyberArk SVP Sales NA, ex-SecurityScorecard SVP Sales Americas) who carries budget.",
 "Michele Bedford":"Director, Strategy Governance at Microsoft - a director-level budget holder.",
 "Aaron Russo":"Global VP Flagship Sales at Accruent - a VP-level revenue leader who can buy.",
 "William Clausen":"EVP of Partnerships at ECHO - an EVP who can buy, just not out of a marketing line.",
 "Judah Guber":"Chief Revenue Officer at Onetab - a C-level revenue owner, squarely a buyer.",
 "Lyndsi Stevens":"Director of Demand Generation at Defense Unicorns - demand gen IS marketing spend.",
}
rows=json.load(open('stale_marker.json'))
log=[]
for r in rows:
    nm=r['name']
    if nm not in WHY: print("skip",nm); continue
    cur=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+r['cid']+"?properties=ai__contact_evidence")
    ev=(cur.get('properties') or {}).get('ai__contact_evidence') or ''
    if MARK not in ev:
        print("already clean  "+nm); continue
    # strip every occurrence of the token, including the one my own correction note re-introduced
    new=ev.replace(MARK+" ","").replace(MARK,"")
    note=(" || PERSONA EXCLUSION LIFTED "+D+": per Shawn - not being a marketer does not mean they "
          "cannot be a decision maker; the test is whether this person can BUY. "+WHY[nm]+
          " Kept ON the calling list. (An earlier correction note accidentally repeated the "
          "exclusion token verbatim, which kept list 8260's filter matching this record and wrongly "
          "held them off the list - that token is now fully stripped.)")
    new=(new+note)[:990]
    u=call('PATCH',"https://api.hubapi.com/crm/v3/objects/contacts/"+r['cid'],
           {"properties":{"ai__contact_evidence":new}})
    ok='id' in u
    print(("OK  " if ok else "ERR ")+nm[:18].ljust(18)+" token stripped, still "+str(MARK in new))
    if not ok: print("     "+json.dumps(u)[:220])
    log.append({"cid":r['cid'],"name":nm,"ok":ok,"date":D})
f='unmark_log.json'
prev=json.load(open(f)) if os.path.exists(f) else []
json.dump(prev+log,open(f,'w'),indent=1)
print("\nunmarked "+str(len([x for x in log if x['ok']])))
