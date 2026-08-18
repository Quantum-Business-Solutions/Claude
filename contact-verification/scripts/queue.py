#!/usr/bin/env python3
"""queue.py <listId> [N] - print the next N unverified contacts on a HubSpot list.
Reads membership live from the list (never a stale local queue), skips anything already
carrying ai__li_still_at_company, and prints: id | First Last | company | jobtitle | li-identifier
Env: TOKEN (HubSpot private-app). Writes an intake snapshot mem_<listId>.txt on first run."""
import json,subprocess,os,sys,re,urllib.parse
T=os.environ['TOKEN']
lid=sys.argv[1]; N=int(sys.argv[2]) if len(sys.argv)>2 else 6
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_q.json','w').write(json.dumps(body)); c+=['-d','@_q.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
# live membership + immutable intake snapshot
ids=[];after=None
while True:
    u="https://api.hubapi.com/crm/v3/lists/"+lid+"/memberships?limit=250"+(("&after="+after) if after else "")
    q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
    after=(q.get('paging') or {}).get('next',{}).get('after')
    if not after: break
snap="mem_"+lid+".txt"
if not os.path.exists(snap): open(snap,'w').write("\n".join(ids))
def ident(u):
    if not u: return None
    m=re.search(r'/in/([^/?#]+)',u)
    return urllib.parse.quote(m.group(1)) if m else None
out=[];unver=0
for i in range(0,len(ids),100):
    chunk=ids[i:i+100]
    b={"inputs":[{"id":x} for x in chunk],
       "properties":["firstname","lastname","company","jobtitle","ai__li_still_at_company",
                     "hs_linkedin_url","linkedin_profile_url__unique_value"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']
        if p.get('ai__li_still_at_company'): continue
        unver+=1
        if len(out)<N:
            idn=ident(p.get('hs_linkedin_url')) or ident(p.get('linkedin_profile_url__unique_value'))
            out.append((x['id'],p.get('firstname'),p.get('lastname'),p.get('company'),p.get('jobtitle'),idn))
print("LIST "+lid+" | members "+str(len(ids))+" | unverified "+str(unver))
for cid,f,l,co,jt,idn in out:
    print(cid+" | "+str(f)+" "+str(l)+" | "+str(co)+" | "+str(jt)[:34]+" | "+str(idn))
