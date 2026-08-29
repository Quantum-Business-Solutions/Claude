#!/usr/bin/env python3
"""unipile.py - LinkedIn reads over the Unipile REST API, as a deterministic fallback for when
the MCP connector is unavailable, and as the self-test an unattended run is required to pass.

WHY THIS EXISTS. LinkedIn reads normally go through the Unipile MCP tool. That connector drops
and reconnects; a scheduled run that lands during a dropout scores every contact `unreadable`
and reports an instrument outage as a finding about the data. This gives the run a second path
and, more importantly, a way to PROVE the path works before it writes anything.

  selftest            read a profile known to carry dated rows; exit 3 if it does not
  profile <slug>      print the dated experience rows for one profile

ACCOUNT RESTRICTION, enforced here rather than trusted: only Shawn's two authorized accounts.
The other accounts connected to this Unipile tenant are CLIENT identities and reading from them
would be using a client's LinkedIn seat for our own prospecting.

Env: UNIPILE_DSN, UNIPILE_API_KEY, optionally UNIPILE_ACCOUNT_ID and SELFTEST_SLUG.
Exit: 0 ok | 2 environment/transport | 3 reachable but returned nothing usable."""
import json,subprocess,os,sys

DSN=(os.environ.get('UNIPILE_DSN') or '').rstrip('/')
KEY=os.environ.get('UNIPILE_API_KEY')
OK_ACCOUNTS={'S6ua4SfUT4SMRFZFOmyUzQ','7lBoyXuETqKdiJYLj5HBGA'}
ACC=os.environ.get('UNIPILE_ACCOUNT_ID') or 'S6ua4SfUT4SMRFZFOmyUzQ'
if not DSN or not KEY:
    sys.stderr.write("HALT: UNIPILE_DSN and UNIPILE_API_KEY must both be set.\n"
                     "      Without them this run has no LinkedIn path at all - which is not the\n"
                     "      same as 'nobody could be verified', and must not be reported as such.\n")
    sys.exit(2)
if ACC not in OK_ACCOUNTS:
    sys.stderr.write("HALT: account_id "+ACC+" is not one of Shawn's authorized accounts.\n"
                     "      The other accounts on this tenant are CLIENT identities.\n")
    sys.exit(2)

def get(path):
    url=DSN+path+('&' if '?' in path else '?')+'account_id='+ACC
    o=subprocess.run(['curl','-s','--max-time','45','-w','\n%{http_code}',
                      '-H','X-API-KEY: '+KEY,'-H','accept: application/json',url],
                     capture_output=True,text=True).stdout
    body,_,code=o.rpartition('\n')
    return body, code.strip()

def rows(slug):
    """Return (dated_rows, http_code, raw). A row is dated when it carries a start date."""
    body,code=get('/api/v1/users/'+slug+'?linkedin_sections=experience_preview')
    if not code.startswith('2'): return None,code,body
    try: d=json.loads(body)
    except Exception: return None,code,body
    out=[]
    for e in (d.get('work_experience') or d.get('experience') or []):
        if e.get('start') or e.get('start_date') or e.get('date_range'):
            out.append({'company':e.get('company'),'position':e.get('position') or e.get('title'),
                        'start':e.get('start') or e.get('start_date'),
                        'end':e.get('end') or e.get('end_date')})
    return out,code,d

cmd=sys.argv[1] if len(sys.argv)>1 else 'selftest'

if cmd=='profile':
    slug=sys.argv[2]
    r,code,raw=rows(slug)
    if r is None:
        print("HTTP "+code+" reading "+slug+" :: "+str(raw)[:200]); sys.exit(2)
    print(json.dumps(r,indent=1)); sys.exit(0)

# ---- selftest -------------------------------------------------------------------------------
# The rule this implements: never trust a null from a query you have not shown returns something.
# A profile read that comes back empty is indistinguishable from "this person has no history",
# and that is how an outage becomes 800 `unreadable` verdicts.
SLUG=os.environ.get('SELFTEST_SLUG') or 'williamhgates'
r,code,raw=rows(SLUG)
if r is None:
    print("SELF-TEST FAILED: HTTP "+code+" for "+SLUG)
    print("  Unipile is not answering. HALT the pass - do NOT interpret unreadable profiles as")
    print("  a finding about the contacts.")
    sys.exit(2)
if not r:
    print("SELF-TEST FAILED: "+SLUG+" returned 2xx but ZERO dated experience rows.")
    print("  The transport works and the payload is empty, which is the more dangerous failure:")
    print("  every contact would score unreadable and look like data rot. HALT.")
    sys.exit(3)
print("SELF-TEST PASSED: "+SLUG+" returned "+str(len(r))+" dated row(s) via account "+ACC)
for e in r[:3]:
    print("   "+str(e.get('company'))+" | "+str(e.get('position'))+" | "+str(e.get('start'))+" -> "+str(e.get('end')))
