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
                     ('ai__li_last_attempt_date','attempt vs confirmed date split'),
                     ('GUARDRAIL (pre-write)',  'guardrails evaluated BEFORE the batch write'),
                     ('ai__pending_mover_to',   'mover destination stamped on the contact')],
 'movepipe.py':     [('associations read failed','associations guard'),
                     ('ai__reassociated_on',     'mover marker as a date, not a substring'),
                     ('ai__pending_mover_to',    'mover queue survives the container'),
                     ('ai__previously_associated_company','previous employer preserved on re-association')],
 'twolists.py':     [('ai__reassociated_on',     'Moved-Companies filters the date')],
 'phoneaudit.py':   [("reassoc_'+str(lid)",     'per-list log filename')],
 'verifyphone.py':  [("reassoc_'+str(lid)",     'per-list log filename')],
 'unipile.py':      [('with_sections=linkedin_experience','v2 full-history read'),
                     ("'ver':2",                'v2-first transport ladder')],
}

# Tokens whose PRESENCE is the bug. A positive check cannot catch this one:
# 'linkedin_sections=experience' is a substring of 'linkedin_sections=experience_preview',
# so a checkout still asking for the preview would satisfy the positive marker while
# quietly truncating employment history.
# Matched as a REGEX against the request form, not as a bare word - unipile.py's docstring
# documents the preview and its measured row counts on purpose, and that prose must not trip the
# guard. The first version of this check matched the literal 'sections=experience_preview', which
# caught only the v1 spelling and let the v2 form ('with_sections=linkedin_experience_preview')
# straight through - i.e. it defended the deprecated fallback while the primary transport, which
# carries every run, stayed wide open.
FORBIDDEN={
 'writeverdicts.py':[(r'LS_OK\s*=\s*\{[^}]*Not Decision Maker',
                      'the "Not Decision Maker" literal back in the WRITABLE lead-status set. '
                      'Employment dates cannot establish buying authority; inferring it from title '
                      'strings ejected a Founder-CEO, an Executive Chairman and a VP of Sales who '
                      'were all still in seat')],
 'movepipe.py':     [(r'or\s*["\']Not Decision Maker',
                      'the "Not Decision Maker" fallback restored as a mover default')],
 'unipile.py':      [(r'sections\s*=\s*[\'"]?[a-z_]*experience_preview',
                      'the truncating preview section. It returned 5 rows where the full '
                      'section returns 15, so a current employer can fall outside it, read '
                      'as departed, and eject a real contact as "No Longer with Company"')],
}
for fn,checks in REQUIRED.items():
    p=os.path.join(HERE,fn)
    if not os.path.exists(p): fail.append("CODE  missing script "+fn); continue
    src=open(p).read()
    for token,why in checks:
        if token not in src: fail.append("CODE  "+fn+" lacks "+repr(token)+" - "+why)
for fn,checks in FORBIDDEN.items():
    p=os.path.join(HERE,fn)
    if not os.path.exists(p): continue
    src=open(p).read()
    for pat,why in checks:
        m=re.search(pat,src)
        if m: fail.append("CODE  "+fn+" still requests "+repr(m.group(0))+" - "+why)
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

# ---------- 2b. WHICH portal is this token for? ------------------------------------------
# Nothing here used to assert it. The scripts take a list id as an argument and are otherwise
# portal-agnostic, so pointing TOKEN at a different portal and passing a list id that exists in
# both writes to the WRONG CRM - silently, and with no way to tell from the output. That is a
# footnote internally and unrecoverable on a client portal.
# Set EXPECT_PORTAL to the hub id you intend to write to. Refusing to run without it would break
# every existing caller, so an absent value WARNS and names the portal it found.
txt,code=call('GET','https://api.hubapi.com/account-info/v3/details')
hub=str((json.loads(txt) if code.startswith('2') else {}).get('portalId') or '')
want=(os.environ.get('EXPECT_PORTAL') or '').strip()
if not hub:
    warn.append("could not read the portal id from this token - cannot confirm WHICH CRM this "
                "run would write to")
elif not want:
    warn.append("this token belongs to portal "+hub+" and EXPECT_PORTAL is not set. Set "
                "EXPECT_PORTAL="+hub+" to make a wrong-portal run impossible.")
    print("ok   portal: "+hub+" (unasserted - see WARN)")
elif hub!=want:
    print("HALT: this token belongs to portal "+hub+", but EXPECT_PORTAL="+want+".")
    print("      Refusing to run. Writing verification verdicts into the wrong CRM is not")
    print("      something a later pass can find or undo.")
    sys.exit(2)
else:
    print("ok   portal: "+hub+" matches EXPECT_PORTAL")

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
WRITES=['ai__pending_mover_to','ai__previously_associated_company',
        'ai__previously_associated_company_id','ai__previously_associated_company_name',
        'ai__li_still_at_company','ai__contact_evidence','ai__contact_verified_date',
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
# Only the literals this process actually writes. "Not Decision Maker" was removed from the
# writable set - it still exists in the portal for human use, but a missing option there can no
# longer break a run, so requiring it would fail the preflight for no reason.
LS_OK={"No Longer with Company","Need Updated Info","Retired - Remove from All Lists"}
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

# ---------- 6. LinkedIn transport: RUN it, do not print prose at the model ----------------
# This used to be a sentence at the end telling the model to run the self-test itself. Preflight
# exited 0 regardless, so a routine whose Unipile key had rotated - or which simply had no key on
# the environment - passed, reached the batch loop, failed every read, and recorded an environment
# misconfiguration as dozens of findings about people. The one dependency an unattended run
# actually lacks was the one thing preflight did not verify.
# SKIP_TRANSPORT=1 exists for schema-only checks; it warns loudly and never passes silently.
if os.environ.get('SKIP_TRANSPORT'):
    warn.append("transport check SKIPPED by SKIP_TRANSPORT - this preflight does NOT prove that "
                "LinkedIn is reachable, so it cannot clear an unattended run")
else:
    try:
        r=subprocess.run([sys.executable,os.path.join(HERE,'unipile.py'),'selftest'],
                         capture_output=True,text=True,timeout=300)
        rc=r.returncode; head=((r.stdout or '')+(r.stderr or '')).strip().split('\n')[0][:150]
    except Exception as e:
        rc=2; head='selftest could not be launched: '+type(e).__name__
    if rc==0:
        print("ok   linkedin transport: "+head)
    else:
        print("HALT: no LinkedIn transport (unipile.py selftest exit "+str(rc)+")")
        print("      "+head)
        print("      exit 2 = no reachable path | exit 3 = reachable but returned nothing usable.")
        print("      Run `python3 unipile.py probe` for the per-endpoint reason. Do NOT proceed:")
        print("      an outage written as `unreadable` verdicts is a durable lie about the data.")
        sys.exit(2)

# ---------- verdict -----------------------------------------------------------------------
for w in warn: print("WARN "+w)
if fail:
    print("\n".join("FAIL "+f for f in fail))
    print("\nHALT: preflight failed. Do NOT run the pass; report this instead.")
    sys.exit(3)
print("\nPREFLIGHT PASSED for list "+lid+" - safe to run.")
print("Still required before writing:")
print("  - listanatomy.py "+lid+" to map which gating properties this run will move")
