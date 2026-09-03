#!/usr/bin/env python3
"""unipile.py - reach LinkedIn through Unipile by whatever path is actually available, and
refuse to let a run proceed when none is.

TRANSPORTS, best first. They fail independently, so the ladder tries each and reports which
one carried the run:

  v2   https://api.unipile.com/v2/{acc}/users/{slug}?with_sections=linkedin_experience
       Plain HTTPS on 443. Needs no relay and no MCP connector, so it is the ONLY path that
       works in a Routine-fired session - those get no connector tools at all. Also returns
       LinkedIn company IDs, which resolve movers far better than a company name string.
       Key: UNIPILE_V2_KEY. Account ids look like acc_...

  v1   https://<relay>/api/v1/users/{slug}?linkedin_sections=experience&account_id=...
       Kept as a fallback while v2 is in beta. Unipile serves v1 on port 16072 and cloud
       egress reaches 443 only, so v1 goes through the Supabase relay in ../relay/.
       Keys: UNIPILE_API_KEY + UNIPILE_RELAY_TOKEN. Account ids are opaque strings.

ALWAYS ASK FOR THE FULL HISTORY. Measured 2026-08-30, rows returned per profile:

    profile          experience_preview   experience   v2 linkedin_experience
    williamhgates             3                3               3
    sherylsandberg            5               15              15
    jeffweiner08              7               24              24

The preview truncates; the full section does not, on EITHER version. This matters because the
judge decides "still there?" by looking for a row matching the CRM company - if that row falls
outside a truncated preview it reads as departed, and a real contact gets ejected as "No Longer
with Company". SKILL.md used to defend against this with a conditional re-pull the model had to
remember on every contact. Requesting the full section unconditionally makes the failure
impossible instead of defended-against, so never reintroduce the preview to save a little time.

ACCOUNT RESTRICTION, enforced not trusted: only Shawn's own account. Every other account on this
tenant is a CLIENT identity, and reading from one spends a client's LinkedIn seat.

Env: UNIPILE_V2_KEY and/or (UNIPILE_API_KEY + UNIPILE_RELAY_TOKEN). At least one complete set is
     required. Optional: UNIPILE_V2_ACCOUNT_ID, UNIPILE_ACCOUNT_ID, UNIPILE_DSN, SELFTEST_SLUG.
Exit: 0 a path works | 2 no path reachable | 3 reachable but returned nothing usable."""
import json,subprocess,os,sys,re,socket,time,tempfile

# ---- v2 ---------------------------------------------------------------------------------
V2_KEY=os.environ.get('UNIPILE_V2_KEY')
V2_BASE=(os.environ.get('UNIPILE_V2_BASE') or 'https://api.unipile.com').rstrip('/')
V2_OK={'acc_01m19mb99wfzvsb68etkn5n87x'}                      # Shawn Peterson, and only him
V2_ACC=os.environ.get('UNIPILE_V2_ACCOUNT_ID') or 'acc_01m19mb99wfzvsb68etkn5n87x'

# ---- v1 ---------------------------------------------------------------------------------
KEY=os.environ.get('UNIPILE_API_KEY')
V1_OK={'S6ua4SfUT4SMRFZFOmyUzQ','7lBoyXuETqKdiJYLj5HBGA'}
ACC=os.environ.get('UNIPILE_ACCOUNT_ID') or 'S6ua4SfUT4SMRFZFOmyUzQ'
RELAY=(os.environ.get('UNIPILE_RELAY_URL') or
       'https://ladhdgwedwynmdmeeena.supabase.co/functions/v1/unipile-relay').rstrip('/')
RELAY_TOKEN=os.environ.get('UNIPILE_RELAY_TOKEN')

if not V2_KEY and not KEY:
    sys.stderr.write("HALT: neither UNIPILE_V2_KEY nor UNIPILE_API_KEY is set - no REST path can\n"
                     "      even be tried. That is NOT the same as 'nobody could be verified'.\n")
    sys.exit(2)
if V2_KEY and V2_ACC not in V2_OK:
    sys.stderr.write("HALT: v2 account_id "+V2_ACC+" is not Shawn's authorized account.\n"); sys.exit(2)
if KEY and ACC not in V1_OK:
    sys.stderr.write("HALT: v1 account_id "+ACC+" is not one of Shawn's authorized accounts.\n"); sys.exit(2)

def candidates():
    """Every transport worth trying, best first, each tagged with the API version that shapes
    its requests. v2 leads because it is the only one that works unattended."""
    out=[]
    if V2_KEY:
        out.append({'ver':2,'base':V2_BASE,'key':V2_KEY,'acc':V2_ACC,'label':V2_BASE+'/v2'})
    if KEY and RELAY_TOKEN:
        out.append({'ver':1,'base':RELAY,'key':KEY,'acc':ACC,'label':RELAY+'  (v1 via relay)'})
    if KEY:
        raw=(os.environ.get('UNIPILE_DSN') or '').strip().rstrip('/')
        seen={c['base'] for c in out}
        for u in ([raw if '://' in raw else 'https://'+raw] if raw else []) + \
                 ['https://api.unipile.com','https://api1.unipile.com']:
            m=re.match(r'^(https?://)([^/:]+)(?::(\d+))?$',u)
            for v in ([u]+([m.group(1)+m.group(2)] if m and m.group(3) not in (None,'443') else [])):
                if v not in seen:
                    seen.add(v); out.append({'ver':1,'base':v,'key':KEY,'acc':ACC,'label':v+'  (v1 direct)'})
    return out

def reachable(base):
    """TCP reachability, independent of auth - separates 'firewall' from 'bad key'."""
    m=re.match(r'^https?://([^/:]+)(?::(\d+))?',base)
    host=m.group(1); port=int(m.group(2) or 443)
    try: ip=socket.gethostbyname(host)
    except Exception as e: return False,"DNS failed: "+type(e).__name__
    s=socket.socket(); s.settimeout(10)
    try:
        s.connect((ip,port)); return True,"tcp open "+ip+":"+str(port)
    except Exception as e:
        return False,"tcp "+ip+":"+str(port)+" "+type(e).__name__+" (egress here reaches 443 only)"
    finally: s.close()

# Unipile publishes its budget in response headers, and states it plainly in a 429 body:
#   x-ratelimit-limit: 100   x-ratelimit-remaining: N   retry-after: <seconds>
# Measured 2026-08-31: 100 requests per ~16-minute rolling window, i.e. ~375/hour, ~9,000/day.
# That is far more headroom than a fixed sleep suggests - but a fixed sleep gets it wrong in BOTH
# directions: 3.5s spends the whole budget in six minutes and then stalls, while a "safe" 10s
# throttles a run that could have gone faster. Read the headers and pace to the actual budget.
RATE={'limit':None,'remaining':None,'reset':None}
# The rate budget has to survive the PROCESS, not just the function. Callers invoke this script once
# per contact - `unipile.py profile <slug>` - so RATE was re-initialised to None on every single
# read and pace() was never reached at all. The documented behaviour ("spreads the remaining budget
# across the remaining window") was therefore not happening in the way the script is actually used:
# nothing paced anything, and throttling was handled only reactively, once the wall was already hit.
# That is why v2 exhausted itself mid-run on 2026-09-03. A tiny state file makes the pacing real.
RATE_STATE=os.environ.get('UNIPILE_RATE_STATE') or '/tmp/.unipile_rate.json'
def _load_rate(ver):
    # RESET FIRST. RATE is module-level and the ladder walks several rungs in one process, so
    # without this the next rung inherits the previous rung's budget - observed live: v2 came back
    # spent, and v1 was then demoted "per the last read's headers" using v2's numbers, taking the
    # whole ladder down over a limit that did not apply to it.
    RATE['limit']=RATE['remaining']=RATE['reset']=None
    try:
        d=json.load(open(RATE_STATE)).get(str(ver))
        if not d: return
        # A stale record is worse than none: it would pace against a window that has already
        # reopened. Anything older than its own reset window is discarded.
        if time.time()-d.get('at',0) > max(d.get('reset') or 0,60)+30: return
        elapsed=time.time()-d['at']
        RATE['limit']=d.get('limit'); RATE['remaining']=d.get('remaining')
        RATE['reset']=None if d.get('reset') is None else max(0,int(d['reset']-elapsed))
    except Exception:
        pass          # no state, unreadable state, or a concurrent write: pace from scratch
def _save_rate(ver):
    try:
        try: all_=json.load(open(RATE_STATE))
        except Exception: all_={}
        all_[str(ver)]={'limit':RATE['limit'],'remaining':RATE['remaining'],
                        'reset':RATE['reset'],'at':time.time()}
        tmp=RATE_STATE+'.tmp'
        json.dump(all_,open(tmp,'w')); os.replace(tmp,RATE_STATE)
    except Exception:
        pass          # pacing is an optimisation; never fail a read because state could not persist
def fetch(c,url):
    hdr=tempfile.NamedTemporaryFile('w',suffix='.hdr',delete=False).name
    cmd=['curl','-s','--max-time','40','-D',hdr,'-w','\n%{http_code}',
         '-H','X-API-KEY: '+c['key'],'-H','accept: application/json']
    # The relay is a Supabase Edge Function with JWT verification left ON, so it needs a bearer
    # of its own. It never stores a credential - the Unipile key above is forwarded through.
    if c['base']==RELAY and RELAY_TOKEN: cmd+=['-H','Authorization: Bearer '+RELAY_TOKEN]
    o=subprocess.run(cmd+[url],capture_output=True,text=True).stdout
    try:
        for line in open(hdr,errors='replace'):
            k,_,v=line.partition(':'); k=k.strip().lower(); v=v.strip()
            if k=='x-ratelimit-limit':     RATE['limit']=int(v) if v.isdigit() else None
            elif k=='x-ratelimit-remaining':RATE['remaining']=int(v) if v.isdigit() else None
            elif k in ('retry-after','x-ratelimit-reset'): RATE['reset']=int(v) if v.isdigit() else None
    except Exception: pass
    finally:
        try: os.unlink(hdr)
        except Exception: pass
    body,_,code=o.rpartition('\n'); return body,code.strip()

# A single sleep must never be able to swallow a whole run. Measured 2026-09-03: v2 reported its
# budget spent and the run's evidence recorded "exhausted for ~23h" - and pace() slept the server's
# reset value with NO upper bound, so a 23-hour reset meant a 23-hour sleep inside a scheduled job
# with a three-hour budget. That is not a pause, it is a silent stall, and a silent stall is the
# failure this whole process is built to prevent.
PACE_CAP=90          # the longest any single pacing sleep may take
RUNG_SPENT_AFTER=300 # a reset longer than this means the rung is done for now, not "wait"
def pace():
    """Sleep only as long as the remaining budget actually requires, and never longer than
    PACE_CAP. Returns (seconds_waited, rung_spent). `rung_spent` is True when the server's own
    reset says the window will not reopen soon enough to be worth waiting for - the caller should
    demote to the next rung on the ladder rather than sit there, which is the entire point of
    having a ladder."""
    rem,rst=RATE['remaining'],RATE['reset']
    if rem is None or rst is None: return 0,False
    if rem<=0:
        if rst>RUNG_SPENT_AFTER: return 0,True     # do NOT sleep it off - demote instead
        w=min(rst+2,PACE_CAP); time.sleep(w); return w,False
    # spread what is left evenly across the window that remains, with a small floor
    w=min(max(1.0,float(rst)/max(rem,1)),PACE_CAP)
    time.sleep(w); return w,False

def accounts_url(c):
    return c['base']+('/v2/accounts' if c['ver']==2 else '/api/v1/accounts?account_id='+c['acc'])

def profile_url(c,slug):
    if c['ver']==2:
        return c['base']+'/v2/'+c['acc']+'/users/'+slug+'?with_sections=linkedin_experience'
    return c['base']+'/api/v1/users/'+slug+'?linkedin_sections=experience&account_id='+c['acc']

RATE_LIMIT_CODES={'429','503'}
def rows(c,slug):
    """Dated employment rows, normalised across both API versions.

    v2 nests them under specifics.experience as {company:{id,name}, job_title, started_on,
    ended_on} and OMITS ended_on for a current role. v1 returns work_experience as
    {company, position, start, end} with end=None for a current role. Both collapse to the
    same shape here, with company_id carried through when the version supplies it."""
    # A 429 means "slow down", NOT "this transport is broken". Falling straight through on one
    # would silently demote every run to the fallback rung the moment we were merely throttled -
    # and on this ladder that means quietly using v1, whose history the caller may then judge on.
    # Back off and retry before giving up on the rung.
    _load_rate(c['ver'])
    waited,spent=pace()
    if spent:
        sys.stderr.write("  v%d budget is already spent per the last read's headers "
                         "(reset %ss); demoting without spending a request\n"
                         %(c['ver'],RATE['reset']))
        return None,'RUNG-SPENT (from cached headers, reset %ss)'%RATE['reset']
    if waited: sys.stderr.write("  paced %.1fs on v%d (remaining %s, reset %ss)\n"
                                %(waited,c['ver'],RATE['remaining'],RATE['reset']))
    for attempt in range(4):
        body,code=fetch(c,profile_url(c,slug))
        _save_rate(c['ver'])
        if code not in RATE_LIMIT_CODES: break
        wait=RATE['reset'] if RATE['reset'] else 6*(attempt+1)
        if wait>RUNG_SPENT_AFTER:
            # The window will not reopen inside this run. Waiting it out used to be capped at 1200s
            # per attempt - up to 80 minutes across four attempts, against a run that has three
            # hours in total. Demote now and let the next rung carry the read.
            sys.stderr.write("  v%d is SPENT (HTTP %s, server says %ds - beyond the %ds worth "
                             "waiting for); demoting to the next rung\n"
                             %(c['ver'],code,wait,RUNG_SPENT_AFTER))
            return None,'RUNG-SPENT (HTTP %s, reset %ds)'%(code,wait)
        if attempt<3:
            # Honour the server's own retry-after rather than an invented backoff. Guessing short
            # burns retries against a window that has not reset; guessing long wastes the run.
            sys.stderr.write("  rate-limited on v%d (HTTP %s), server says retry in %ds "
                             "(limit %s/window)\n"%(c['ver'],code,wait,RATE['limit']))
            time.sleep(min(wait+2,RUNG_SPENT_AFTER))
    if code in RATE_LIMIT_CODES: return None,'RATE-LIMITED (HTTP '+code+') - not a transport failure'
    if not code.startswith('2'): return None,code
    try: d=json.loads(body)
    except Exception: return None,'unparseable'
    out=[]
    if c['ver']==2:
        for e in ((d.get('specifics') or {}).get('experience') or d.get('experience') or []):
            if not e.get('started_on'): continue
            co=e.get('company') or {}
            out.append({'company':co.get('name'),'company_id':co.get('id'),
                        'position':e.get('job_title'),
                        'start':e.get('started_on'),'end':e.get('ended_on'),
                        'location':e.get('location')})
    else:
        for e in (d.get('work_experience') or d.get('experience') or []):
            if not (e.get('start') or e.get('start_date') or e.get('date_range')): continue
            out.append({'company':e.get('company'),'company_id':None,
                        'position':e.get('position') or e.get('title'),
                        'start':e.get('start') or e.get('start_date'),
                        'end':e.get('end') or e.get('end_date'),
                        'location':e.get('location')})
    return out,code

cmd=sys.argv[1] if len(sys.argv)>1 else 'selftest'
SLUG=(sys.argv[2] if cmd=='profile' and len(sys.argv)>2 else
      os.environ.get('SELFTEST_SLUG') or 'williamhgates')

if cmd=='probe':
    print("v2 account "+(V2_ACC if V2_KEY else "(no UNIPILE_V2_KEY)")+
          "   |   v1 account "+(ACC if KEY else "(no UNIPILE_API_KEY)"))
    for c in candidates():
        ok,why=reachable(c['base'])
        line="  "+("REACHABLE  " if ok else "unreachable")+"  v"+str(c['ver'])+"  "+c['label']+"   "+why
        if ok:
            body,code=fetch(c,accounts_url(c))
            line+="   | GET accounts -> HTTP "+code+("  (auth ok)" if code.startswith('2')
                   else "  (reachable but rejected - check the key for this version)")
        print(line)
    sys.exit(0)

tried=[]
for c in candidates():
    ok,why=reachable(c['base'])
    if not ok: tried.append((c['label'],why)); continue
    r,code=rows(c,SLUG)
    if r is None: tried.append((c['label'],"HTTP "+str(code))); continue
    if not r:    tried.append((c['label'],"2xx but ZERO dated rows")); continue
    if cmd=='profile':
        print(json.dumps({'api_version':c['ver'],'rows':r},indent=1)); sys.exit(0)
    print("SELF-TEST PASSED via Unipile v"+str(c['ver'])+": "+c['label'])
    print("  "+SLUG+" returned "+str(len(r))+" dated row(s) on account "+c['acc'])
    for e in r[:4]:
        print("   "+str(e.get('company'))+" | "+str(e.get('position'))+" | "
              +str(e.get('start'))+" -> "+str(e.get('end'))
              +("   [li company "+str(e['company_id'])+"]" if e.get('company_id') else ""))
    sys.exit(0)

print("SELF-TEST FAILED on every REST candidate:")
for lbl,why in tried: print("  "+lbl+"  ->  "+why)
print("\nNo REST path is available. If this session HAS the Unipile MCP connector, try that before")
print("halting - it routes via Anthropic's mcp-proxy and ignores this environment's egress limits.")
print("A Routine-fired session has no connector tools, so for those this failure IS the end of the")
print("run. Halt and say which paths failed. A LinkedIn outage is not a finding about the contacts,")
print("and must never be written as unreadable verdicts.")
sys.exit(2 if all('tcp' in w or 'DNS' in w for _,w in tried) else 3)
