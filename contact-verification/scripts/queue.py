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
RETRY_DAYS=int(os.environ.get('RETRY_DAYS','14'))         # 'unreadable' = transient, retry soon
NOPROFILE_DAYS=int(os.environ.get('NOPROFILE_DAYS','180'))# 'no_profile' = permanent by this method
def age(datestr):
    if not datestr: return None
    try: return (datetime.date.today()-datetime.date.fromisoformat(str(datestr)[:10])).days
    except Exception: return None
def stale(datestr):
    a=age(datestr); return True if a is None else a>STALE_DAYS
def due(verdict,verified,attempt):
    """Should this record go back in the queue, and why?

    Splitting the retry interval by verdict class is the point of separating
    ai__contact_verified_date (confirmed verdicts only) from ai__li_last_attempt_date (every
    touch). Without it a record with no LinkedIn profile has no verified date, reads as 'never
    verified', and is re-read at full cost on every run forever - buying nothing."""
    if not verdict:            return True,'never verified'
    if verdict in ('yes','no'):
        return (True,'verdict stale') if stale(verified) else (False,None)
    if verdict=='unreadable':
        a=age(attempt); return (True,'unreadable retry due') if (a is None or a>RETRY_DAYS) else (False,None)
    if verdict=='no_profile':
        a=age(attempt); return (True,'no_profile recheck due') if (a is None or a>NOPROFILE_DAYS) else (False,None)
    if verdict=='moved':
        # A valid portal option no script writes - it is set by hand. Treat it like a confirmed
        # verdict so a human's answer is not re-litigated on every single run.
        return (True,'moved, verdict stale') if stale(verified) else (False,None)
    return True,'unknown verdict '+str(verdict)
out=[];unver=0;stale_n=0;unread_flag=0;noprof=0;seen=set();reasons={}
for i in range(0,len(ids),100):
    chunk=ids[i:i+100]
    b={"inputs":[{"id":x} for x in chunk],
       "properties":["firstname","lastname","company","jobtitle","ai__li_still_at_company",
                     "ai__contact_verified_date","ai__li_last_attempt_date",
                     "hs_linkedin_url","linkedin_profile_url__unique_value"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']; seen.add(x['id'])
        v=p.get('ai__li_still_at_company')
        if v=='unreadable': unread_flag+=1
        if v=='no_profile': noprof+=1
        want,why=due(v,p.get('ai__contact_verified_date'),p.get('ai__li_last_attempt_date'))
        if not want: continue
        reasons[why]=reasons.get(why,0)+1
        if v: stale_n+=1                    # already carries a verdict, but it is due again
        unver+=1
        if len(out)<N:
            idn=ident(p.get('hs_linkedin_url')) or ident(p.get('linkedin_profile_url__unique_value'))
            out.append((x['id'],p.get('firstname'),p.get('lastname'),p.get('company'),p.get('jobtitle'),idn))
unread_snapshot=len(SNAP-seen)
print("LIST "+lid+" | members "+str(len(ids))+" | unverified "+str(unver)
      +" (of which re-due: "+str(stale_n)+")"
      +" | unreadable "+str(unread_flag)+" | no_profile "+str(noprof)
      +" | in intake snapshot but no longer members: "+str(unread_snapshot))
if reasons: print("  why queued: "+" | ".join(k+" "+str(v) for k,v in sorted(reasons.items(),key=lambda x:-x[1])))
for cid,f,l,co,jt,idn in out:
    print(cid+" | "+str(f)+" "+str(l)+" | "+str(co)+" | "+str(jt)[:34]+" | "+str(idn))
