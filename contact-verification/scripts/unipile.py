#!/usr/bin/env python3
"""unipile.py - reach LinkedIn through Unipile by whatever path is actually available, and
refuse to let a run proceed when none is.

THE PROBLEM THIS SOLVES. There are two transports to Unipile and they fail independently:
  MCP connector  - travels via Anthropic's mcp-proxy, so it ignores the egress firewall. It is
                   the only path measured working from a cloud session. It also drops and
                   reconnects on its own schedule.
  REST API       - direct HTTPS to the tenant DSN. Measured from a cloud session: the agent proxy
                   ESTABLISHES the tunnel (CONNECT -> 200) and the TLS handshake is then reset,
                   and a direct socket to the same IP times out on :16072 while :443 is open.
                   So outbound egress here reaches standard ports only. That is a property of the
                   environment, not of the DSN or the key.
A run must not stop because one of them is down, and must never treat "no path" as "nobody could
be verified" - an outage rendered as 800 unreadable verdicts is a lie about the data.

This script owns the REST half and probes rather than assumes. The MCP half is a model-level tool
call, so the two-path rule lives in SKILL.md / ROUTINE.md: try MCP, then this, halt only if BOTH
fail - and say which one failed and how.

  probe       try every candidate endpoint, report which are reachable and why the others are not
  selftest    first candidate that returns dated rows wins; exit 0 if ANY path works
  profile <slug>   dated experience rows for one profile, over the first working candidate

ACCOUNT RESTRICTION, enforced not trusted: only Shawn's two authorized account_ids. Every other
account on this tenant is a CLIENT identity; reading from one spends a client's LinkedIn seat.

Env: UNIPILE_API_KEY (required), UNIPILE_DSN (optional - candidates are derived when absent),
     UNIPILE_ACCOUNT_ID, SELFTEST_SLUG.
Exit: 0 a path works | 2 no path reachable | 3 reachable but returned nothing usable."""
import json,subprocess,os,sys,re,socket

KEY=os.environ.get('UNIPILE_API_KEY')
OK_ACCOUNTS={'S6ua4SfUT4SMRFZFOmyUzQ','7lBoyXuETqKdiJYLj5HBGA'}
ACC=os.environ.get('UNIPILE_ACCOUNT_ID') or 'S6ua4SfUT4SMRFZFOmyUzQ'
if not KEY:
    sys.stderr.write("HALT: UNIPILE_API_KEY is not set - the REST path cannot be tried at all.\n"
                     "      That is NOT the same as 'nobody could be verified'.\n"); sys.exit(2)
if ACC not in OK_ACCOUNTS:
    sys.stderr.write("HALT: account_id "+ACC+" is not one of Shawn's authorized accounts.\n"); sys.exit(2)

RELAY=(os.environ.get('UNIPILE_RELAY_URL') or
       'https://ladhdgwedwynmdmeeena.supabase.co/functions/v1/unipile-relay').rstrip('/')
RELAY_TOKEN=os.environ.get('UNIPILE_RELAY_TOKEN')

def candidates():
    """Every endpoint worth trying, best first. A tenant DSN often carries a non-standard port
    that this environment cannot reach, so the same host on 443 is always tried as well.

    The relay comes FIRST because it is the only REST path that works from a cloud session: it
    sits on 443 and forwards to the tenant's :16072. It needs UNIPILE_RELAY_TOKEN (the Supabase
    publishable key) in the environment - deliberately not committed, since this repo is public."""
    out=[]
    if RELAY_TOKEN: out.append(RELAY)
    raw=(os.environ.get('UNIPILE_DSN') or '').strip().rstrip('/')
    if raw:
        u=raw if '://' in raw else 'https://'+raw
        out.append(u)
        m=re.match(r'^(https?://)([^/:]+)(?::(\d+))?$',u)
        if m and m.group(3) not in (None,'443'):
            out.append(m.group(1)+m.group(2))              # same host, standard port
    for extra in ('https://api.unipile.com','https://api1.unipile.com'):
        if extra not in out: out.append(extra)
    return out

def reachable(url):
    """TCP reachability, independent of auth - separates 'firewall' from 'bad key'."""
    m=re.match(r'^https?://([^/:]+)(?::(\d+))?',url)
    host=m.group(1); port=int(m.group(2) or 443)
    try: ip=socket.gethostbyname(host)
    except Exception as e: return False,"DNS failed: "+type(e).__name__
    s=socket.socket(); s.settimeout(10)
    try:
        s.connect((ip,port)); return True,"tcp open "+ip+":"+str(port)
    except Exception as e:
        return False,"tcp "+ip+":"+str(port)+" "+type(e).__name__+" (egress here reaches 443 only)"
    finally: s.close()

def get(base,path):
    url=base+path+('&' if '?' in path else '?')+'account_id='+ACC
    cmd=['curl','-s','--max-time','40','-w','\n%{http_code}',
         '-H','X-API-KEY: '+KEY,'-H','accept: application/json']
    # The relay is a Supabase Edge Function with JWT verification left ON, so it needs a bearer
    # of its own. It never sees a stored credential - the Unipile key above is forwarded through.
    if base==RELAY and RELAY_TOKEN: cmd+=['-H','Authorization: Bearer '+RELAY_TOKEN]
    o=subprocess.run(cmd+[url],capture_output=True,text=True).stdout
    body,_,code=o.rpartition('\n'); return body,code.strip()

def rows(base,slug):
    body,code=get(base,'/api/v1/users/'+slug+'?linkedin_sections=experience_preview')
    if not code.startswith('2'): return None,code
    try: d=json.loads(body)
    except Exception: return None,'unparseable'
    out=[]
    for e in (d.get('work_experience') or d.get('experience') or []):
        if e.get('start') or e.get('start_date') or e.get('date_range'):
            out.append({'company':e.get('company'),
                        'position':e.get('position') or e.get('title'),
                        'start':e.get('start') or e.get('start_date'),
                        'end':e.get('end') or e.get('end_date')})
    return out,code

cmd=sys.argv[1] if len(sys.argv)>1 else 'selftest'
SLUG=(sys.argv[2] if cmd=='profile' and len(sys.argv)>2 else
      os.environ.get('SELFTEST_SLUG') or 'williamhgates')

if cmd=='probe':
    print("account "+ACC)
    for c in candidates():
        ok,why=reachable(c)
        line="  "+("REACHABLE  " if ok else "unreachable")+"  "+c+"   "+why
        if ok:
            body,code=get(c,'/api/v1/accounts')
            line+="   | GET /accounts -> HTTP "+code+("  (auth ok)" if code.startswith('2')
                   else "  (reachable but rejected - check UNIPILE_API_KEY)")
        print(line)
    sys.exit(0)

tried=[]
for c in candidates():
    ok,why=reachable(c)
    if not ok: tried.append((c,why)); continue
    r,code=rows(c,SLUG)
    if r is None: tried.append((c,"HTTP "+str(code))); continue
    if not r:    tried.append((c,"2xx but ZERO dated rows")); continue
    if cmd=='profile': print(json.dumps(r,indent=1)); sys.exit(0)
    print("SELF-TEST PASSED via REST: "+c)
    print("  "+SLUG+" returned "+str(len(r))+" dated row(s) on account "+ACC)
    for e in r[:3]:
        print("   "+str(e.get('company'))+" | "+str(e.get('position'))+" | "
              +str(e.get('start'))+" -> "+str(e.get('end')))
    sys.exit(0)

print("SELF-TEST FAILED on every REST candidate:")
for c,why in tried: print("  "+c+"  ->  "+why)
print("\nThe REST path is unavailable. Before halting the run, TRY THE MCP CONNECTOR - it routes")
print("via Anthropic's mcp-proxy and is unaffected by this environment's egress limits. Halt only")
print("if BOTH paths fail, and report WHICH failed. A LinkedIn outage is not a finding about the")
print("contacts, and must never be written as unreadable verdicts.")
sys.exit(2 if all('tcp' in w or 'DNS' in w for _,w in tried) else 3)
