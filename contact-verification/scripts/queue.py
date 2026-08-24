#!/usr/bin/env python3
"""queue.py <listId> [N] - print the next N unverified contacts on a HubSpot list.
Reads membership live from the list (never a stale local queue), skips anything already
carrying ai__li_still_at_company, and prints: id | First Last | company | jobtitle | li-identifier
Env: TOKEN (HubSpot private-app). Writes an intake snapshot mem_<listId>.txt on first run."""
import json,subprocess,os,sys,re,urllib.parse,tempfile,datetime
T=os.environ['TOKEN']
lid=sys.argv[1]; N=int(sys.argv[2]) if len(sys.argv)>2 else 6
STALE_DAYS=int(os.environ.get('STALE_DAYS','90'))   # re-verify a verdict older than this
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
def call(m,url,body=None):
    """Fail-fast: any non-2xx exits. An auth/rate-limit failure must NEVER read as 'no data' -
    an empty result here satisfies the run's stop condition and reports a dirty list as clean."""
    c=['curl','-s','--max-time','30','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open(TMP,'w').write(json.dumps(body)); c+=['-d','@'+TMP]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    body_txt,_,code=o.rpartition('\n')
    if not code.strip().isdigit() or not code.strip().startswith('2'):
        sys.stderr.write('HTTP '+code.strip()+' on '+m+' '+url.split('?')[0]+' :: '+body_txt[:200]+'\n')
        sys.exit(2)
    try: return json.loads(body_txt) if body_txt.strip() else {}
    except Exception:
        sys.stderr.write('unparseable response from '+url.split('?')[0]+'\n'); sys.exit(2)
# live membership + immutable intake snapshot
ids=[];after=None
while True:
    u="https://api.hubapi.com/crm/v3/lists/"+lid+"/memberships?limit=250"+(("&after="+after) if after else "")
    q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
    after=(q.get('paging') or {}).get('next',{}).get('after')
    if not after: break
if not ids:
    sys.stderr.write('list '+lid+' returned ZERO members - refusing to proceed or to write an '
                     'intake snapshot. An empty list is not a normal state for this process.\n')
    sys.exit(2)
snap="mem_"+lid+".txt"
if not os.path.exists(snap): open(snap,'w').write("\n".join(ids))
SNAP=set(open(snap).read().split()) if os.path.exists(snap) else set()
def ident(u):
    if not u: return None
    m=re.search(r'/in/([^/?#]+)',u)
    return urllib.parse.quote(m.group(1)) if m else None
def stale(datestr):
    """True when a verdict is old enough to re-verify (or its date is missing/unparseable)."""
    if not datestr: return True
    try: d=datetime.date.fromisoformat(str(datestr)[:10])
    except Exception: return True
    return (datetime.date.today()-d).days > STALE_DAYS
out=[];unver=0;stale_n=0;unread_flag=0;seen=set()
for i in range(0,len(ids),100):
    chunk=ids[i:i+100]
    b={"inputs":[{"id":x} for x in chunk],
       "properties":["firstname","lastname","company","jobtitle","ai__li_still_at_company",
                     "ai__contact_verified_date",
                     "hs_linkedin_url","linkedin_profile_url__unique_value"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']; seen.add(x['id'])
        v=p.get('ai__li_still_at_company')
        if v:
            if v=='unreadable': unread_flag+=1
            if not stale(p.get('ai__contact_verified_date')): continue
            stale_n+=1                      # verdict has aged past STALE_DAYS -> re-verify
        unver+=1
        if len(out)<N:
            idn=ident(p.get('hs_linkedin_url')) or ident(p.get('linkedin_profile_url__unique_value'))
            out.append((x['id'],p.get('firstname'),p.get('lastname'),p.get('company'),p.get('jobtitle'),idn))
unread_snapshot=len(SNAP-seen)
print("LIST "+lid+" | members "+str(len(ids))+" | unverified "+str(unver)
      +" (of which stale>"+str(STALE_DAYS)+"d: "+str(stale_n)+")"
      +" | unreadable-still-on-list "+str(unread_flag)
      +" | in intake snapshot but no longer members: "+str(unread_snapshot))
for cid,f,l,co,jt,idn in out:
    print(cid+" | "+str(f)+" "+str(l)+" | "+str(co)+" | "+str(jt)[:34]+" | "+str(idn))
