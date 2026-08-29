#!/usr/bin/env python3
"""preflight.py <listId> - prove this checkout and this environment can safely run an
UNATTENDED verification pass, BEFORE any contact record is touched.

Exists because a routine fires into a fresh session with nobody watching. Every failure
mode this catches previously presented as a clean, confident "nothing needed refreshing":
  1. the checkout predates the QA fixes  -> queue.py finds 0 stale, reports a clean list
  2. the token is missing/expired        -> reads return nothing, which IS the stop condition
  3. the list is empty or gone           -> zero members reads as "fully verified"
  4. a written property was renamed      -> every write silently lands nowhere
  5. hs_lead_status lost a literal       -> movers cannot be ejected, write 400s mid-run

Exit codes (match the rest of the pipeline):
  0 safe to proceed | 2 environment/auth/data failure | 3 wrong code version or schema drift
Env: TOKEN. Usage: TOKEN=... python3 preflight.py 3675"""
import json,subprocess,os,sys,re

lid=sys.argv[1] if len(sys.argv)>1 else os.environ.get('LIST_ID')
if not lid: sys.stderr.write("usage: preflight.py <listId>\n"); sys.exit(2)
HERE=os.path.dirname(os.path.abspath(__file__))
fail=[]; warn=[]

# ---------- 1. code version guard --------------------------------------------------------
# A routine clones the default branch. If that branch predates the QA fixes, the run will
# look successful and do nothing. Refuse rather than emit a false clean bill of health.
REQUIRED={
 'queue.py':        [('STALE_DAYS',              'staleness window'),
                     ('sys.exit(2)',             'fail-fast on non-2xx'),
                     ('def due(',                'per-verdict-class retry intervals'),
                     ('NOPROFILE_DAYS',          'no_profile long recheck')],
 'writeverdicts.py':[('sys.exit(2)',             'fail-fast on non-2xx'),
                     ('title_conf',              'jobtitle confidence gate'),
                     ('RECORD DROPPED',          'rule refusals'),
                     ('VERDICT_OK',              'verdict vocabulary enforcement'),
                     ('ai__li_last_attempt_date','attempt vs confirmed date split')],
 'movepipe.py':     [('dm not supplied',         'no silent Not-Decision-Maker default'),
                     ('associations read failed','associations guard'),
                     ('ai__reassociated_on',     'mover marker as a date, not a substring')],
 'twolists.py':     [('ai__reassociated_on',     'Moved-Companies filters the date')],
 'phoneaudit.py':   [("reassoc_'+str(lid)",     'per-list log filename')],
 'verifyphone.py':  [("reassoc_'+str(lid)",     'per-list log filename')],
}
for fn,checks in REQUIRED.items():
    p=os.path.join(HERE,fn)
    if not os.path.exists(p): fail.append("CODE  missing script "+fn); continue
    src=open(p).read()
    for token,why in checks:
        if token not in src: fail.append("CODE  "+fn+" lacks "+repr(token)+" - "+why)
if any(f.startswith("CODE") for f in fail):
    print("\n".join(fail))
    print("\nHALT: this checkout predates the verification QA fixes. A run from here would")
    print("report a clean list without reading anything. Merge the fixes to the default")
    print("branch before letting a routine run against live records.")
    sys.exit(3)
print("ok   code version: all QA fixes present")

# ---------- 2. auth + reachability -------------------------------------------------------
T=os.environ.get('TOKEN')
if not T:
    print("HALT: TOKEN is not set. Load the HubSpot PAT before running."); sys.exit(2)
def call(m,url,body=None):
    c=['curl','-s','--max-time','30','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        c+=['-d',json.dumps(body)]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    txt,_,code=o.rpartition('\n')
    return txt,code.strip()
txt,code=call('GET','https://api.hubapi.com/crm/v3/objects/contacts?limit=1')
if not code.startswith('2'):
    print("HALT: HubSpot auth/reachability failed - HTTP "+code+" :: "+txt[:160])
    print("An expired token reads as 'no data', which is indistinguishable from a clean list.")
    sys.exit(2)
print("ok   hubspot auth: HTTP "+code)

# ---------- 3. the self-test rule: prove a query returns a KNOWN answer -------------------
# Never trust a null from a query that has not been shown to return something.
txt,code=call('GET','https://api.hubapi.com/crm/v3/lists/'+lid)
if not code.startswith('2'):
    print("HALT: cannot read list "+lid+" - HTTP "+code+" :: "+txt[:160]); sys.exit(2)
meta=(json.loads(txt) or {}).get('list',{})
name=meta.get('name'); size=meta.get('additionalProperties',{}).get('hs_list_size')
otype=meta.get('objectTypeId'); ptype=meta.get('processingType')
print("ok   list "+lid+": "+repr(name)+" objectType="+str(otype)+" processing="+str(ptype)+" size="+str(size))
if otype!='0-1': fail.append("LIST  objectTypeId "+str(otype)+" is not contacts (0-1)")
if ptype and ptype!='DYNAMIC':
    fail.append("LIST  processingType "+str(ptype)+" is not DYNAMIC - a static list does not "
                "recalculate, so coverage and the output lists are meaningless")
txt,code=call('GET','https://api.hubapi.com/crm/v3/lists/'+lid+'/memberships?limit=2')
ids=[x.get('recordId') for x in (json.loads(txt) if code.startswith('2') else {}).get('results',[])]
if not ids:
    print("HALT: list "+lid+" returned zero members. That is the stop condition, so a run")
    print("from here would report success having done nothing. Verify the list by hand.")
    sys.exit(2)
print("ok   membership probe: "+str(len(ids))+" member(s) readable, e.g. "+str(ids[0]))

# ---------- 4. every property this process writes must still exist ------------------------
WRITES=['ai__li_still_at_company','ai__contact_evidence','ai__contact_verified_date',
        'ai__li_last_attempt_date','ai__reassociated_on','ai__li_tenure_years',
        'ai__li_recent_role_change','ai__sources_confirming','ai__job_title',
        'validated__linkedin_or_manually','hs_linkedin_url','linkedin_profile_url__unique_value',
        'previous__company_domain_name','jobtitle','hs_lead_status','company','phone',
        'business_phone','email']
txt,code=call('GET','https://api.hubapi.com/crm/v3/properties/contacts')
if not code.startswith('2'):
    print("HALT: cannot read the contact property schema - HTTP "+code); sys.exit(2)
props={p['name']:p for p in json.loads(txt).get('results',[])}
missing=[w for w in WRITES if w not in props]
if missing: fail.append("SCHEMA missing written properties: "+", ".join(missing))
else: print("ok   schema: all "+str(len(WRITES))+" written properties exist")

# the four lead-status literals are the only way a departed contact leaves a calling list.
LS_OK={"No Longer with Company","Need Updated Info","Retired - Remove from All Lists","Not Decision Maker"}
opts={o['value'] for o in (props.get('hs_lead_status') or {}).get('options',[])}
lost=sorted(LS_OK-opts)
if lost: fail.append("SCHEMA hs_lead_status lost literal(s): "+", ".join(lost)+" - movers cannot be ejected")
else: print("ok   lead-status vocabulary: all 4 literals present")
# The verdict field is an enumeration. Writing a value it does not define 400s mid-pass, AFTER
# movers have been queued - so check the options, not just that the property exists.
VERDICTS_NEEDED={'yes','no','unreadable','no_profile'}
vopts={o['value'] for o in (props.get('ai__li_still_at_company') or {}).get('options',[])}
vlost=sorted(VERDICTS_NEEDED-vopts)
if vlost: fail.append("SCHEMA ai__li_still_at_company lost option(s): "+", ".join(vlost))
else: print("ok   verdict vocabulary: "+", ".join(sorted(VERDICTS_NEEDED))+" all present")
if 'ai__contact_evidence' in props:
    ml=(props['ai__contact_evidence'] or {}).get('maxLength')
    if ml and int(ml)<990: warn.append("ai__contact_evidence maxLength "+str(ml)+" < the 990 the writers assume")

# ---------- verdict -----------------------------------------------------------------------
for w in warn: print("WARN "+w)
if fail:
    print("\n".join("FAIL "+f for f in fail))
    print("\nHALT: preflight failed. Do NOT run the pass; report this instead.")
    sys.exit(3)
print("\nPREFLIGHT PASSED for list "+lid+" - safe to run.")
print("Still required before writing, and NOT checkable from here:")
print("  - a Unipile read of a known-good profile that returns dated experience rows")
print("    (only Shawn's accounts S6ua4SfUT4SMRFZFOmyUzQ / 7lBoyXuETqKdiJYLj5HBGA)")
print("  - listanatomy.py "+lid+" to map which gating properties this run will move")
