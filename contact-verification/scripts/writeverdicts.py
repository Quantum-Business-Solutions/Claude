#!/usr/bin/env python3
"""writeverdicts.py <listId> <batch.json> - write a batch of verdicts, verify by read-back,
append to per-list log li_verdicts_<listId>.json, and queue movers to pending_movers_<listId>.json.

batch.json = [{"id","verdict"(yes|no|unreadable|no_profile),"ev",
               "ls"(optional lead status),"newco"(optional),"sources"(optional),
               "issue"(optional - machine-readable reason a human is needed -> ai__verification_issue),
               "issue_note"(optional - one line a human can act on in seconds),
               "tenure"(optional number - years in the current role -> ai__li_tenure_years),
               "role_change"(optional 'yes'/'no' -> ai__li_recent_role_change),
               "title"(optional - current LinkedIn title -> ai__job_title),
               "title_conf"(optional float 0-1 - confidence the title is accurate; >=0.90 ALSO
                            writes the native `jobtitle`. Absent = no native write, ever),
               "li_url"(optional - corrected LinkedIn URL, written to BOTH url fields),
               "changed"(optional - explicit 'what changed in HubSpot' text)}]

RULES enforced here so no caller can bypass them:
  - verdict 'yes'  -> NEVER writes hs_lead_status (must stay ConnectandSell Prospect or the
                      contact drops off the calling list). An 'ls' on a yes is refused.
  - lead status    -> only these literals allowed: No Longer with Company / Need Updated Info /
                      Retired - Remove from All Lists   (NOT 'Not Decision Maker')
  - ai__job_title  -> always written when `title` is given (AI-owned, uncontested).
  - jobtitle       -> the NATIVE title field is written only when title_conf >= 0.90 AND the
                      verdict is `yes` AND the evidence carries no ambiguity marker. Fails CLOSED:
                      no title_conf means no native write. 3 integrations compete for this field
                      (~38% oscillation), so the write is read back and the prior value is recorded
                      in ai__contact_evidence, making a bad write reversible without a schema change.
  - validated__linkedin_or_manually -> set from the verdict: yes->Yes, retired->Retired, else->Needs Updated
  - evidence       -> ai__contact_evidence, formatted "Verified - <date> - <evidence> - Changed: <what changed>"
                      (<=990 chars). Appended-safe; the verified date is also stamped structurally.
  - LinkedIn URL   -> when li_url is given it is written to hs_linkedin_url AND
                      linkedin_profile_url__unique_value (the unique field is set per-record so a
                      duplicate-contact collision is flagged, not allowed to block the batch).
Env: TOKEN. Pass DATE=YYYY-MM-DD to override the stamp (else uses `date -u`)."""
import json,subprocess,os,sys,re,tempfile
T=os.environ['TOKEN']
D=os.environ.get('DATE') or subprocess.run(['date','-u','+%Y-%m-%d'],capture_output=True,text=True).stdout.strip()
lid=sys.argv[1]; V=json.load(open(sys.argv[2]))
# "Not Decision Maker" is deliberately NOT here. This process reads dated employment history,
# which establishes WHERE somebody works and cannot establish whether they can authorise a
# purchase. That judgement was being inferred from title strings and it ejected people who were
# demonstrably still in seat - a Founder-CEO, an Executive Chairman, a VP of Sales. It was also
# written alongside verdict `no`, which asserts the person has LEFT, collapsing two different
# questions into the one field the retry and staleness logic keys on. Buyability is a human call.
LS_OK={"No Longer with Company","Need Updated Info","Retired - Remove from All Lists"}
LS_RETIRED={"Not Decision Maker"}   # recognised only so it can be refused with a real reason
# The portal defines five values. `moved` is reserved for the mover pipeline (movepipe reconciles to
# `yes`), so a batch may write four. Splitting `no_profile` out of `unreadable` matters: a person with
# no LinkedIn profile is PERMANENTLY unverifiable by this method and re-reading them forever is waste,
# while `unreadable` is a transient failure worth retrying. Collapsing them hid both facts.
VERDICT_OK={"yes","no","unreadable","no_profile"}
# Must match the portal's ai__verification_issue options EXACTLY. An unknown value passes the
# local check, reaches batch/update, and HubSpot 400s - which is fatal here and loses the whole
# 100-record chunk AFTER the movers were queued. preflight now compares the two sets.
ISSUE_OK={"wrong_link_suspected","identity_unresolved","no_identifier","ambiguous_destination",
          "company_ambiguous","succession_conflict","duplicate_contact","division_scope_unclear",
          "persona_review","title_conflict","phone_unverified","email_unprovable","retired_headline",
          # departed but carrying live pipeline - eject and you delete a warm re-target
          "departed_with_pipeline",
          # the verdict does not match its own evidence (e.g. a persona call filed as employment)
          "verdict_not_employment"}
CONFIRMED={"yes","no"}      # only these two justify stamping a "verified" date
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
def call(m,url,body=None,fatal=True):
    """Fail-fast on any non-2xx. An auth failure must never read as 'no data' and stamp live records."""
    c=['curl','-s','--max-time','30','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open(TMP,'w').write(json.dumps(body)); c+=['-d','@'+TMP]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    body_txt,_,code=o.rpartition('\n'); code=code.strip()
    if not code.isdigit() or not code.startswith('2'):
        if fatal:
            sys.stderr.write('HTTP '+code+' on '+m+' '+url.split('?')[0]+' :: '+body_txt[:200]+'\n')
            sys.exit(2)
        return {"__http":code,"__body":body_txt[:200]}
    try: d=json.loads(body_txt) if body_txt.strip() else {}
    except Exception:
        if fatal: sys.stderr.write('unparseable response\n'); sys.exit(2)
        return {}
    # HubSpot answers a PARTIALLY failed batch with 207 and an errors[] array. 207 starts with a
    # 2, so the check above waves it through and every caller here used to read the short results
    # list as if it were the whole answer. On the prior-evidence read that is destructive: a
    # contact missing from the response looks like "no prior evidence", and the write then
    # REPLACES its history instead of appending to it. Surface it; never let it pass as complete.
    if isinstance(d,dict) and d.get('numErrors'):
        d['__partial']=True
        sys.stderr.write("PARTIAL BATCH: HTTP "+code+", numErrors="+str(d.get('numErrors'))
                         +" on "+url.split('?')[0]+" :: "+json.dumps(d.get('errors'))[:300]+"\n")
    return d
MARKER="RE-"+"ASSOCIATED"    # built at runtime: a filter token is a control character, not prose
def slug(u):
    if not u: return None
    m=re.search(r'/in/([^/?#]+)',u); return m.group(1).lower() if m else None
def validated_of(verdict,ls):
    if verdict=='yes': return "Yes"
    if verdict=='no' and ls=='Retired - Remove from All Lists': return "Retired"
    return "Needs Updated"   # any other 'no' (moved / need info) or 'unreadable' -> a human should look
TITLE_CONF_MIN=0.90
# Hedge words in the evidence mean the title is not a 90% call, whatever number the caller passed.
AMBIG=("caution","ambig","uncertain","unclear","probably","possibly","perhaps","assumed","appears to",
       "may be","might be","succession","dormant","not updated","stale profile","conflict","unsure","?",
       # Added from evidence strings found in the live portal that hedged and were acted on anyway.
       # Deliberately phrase-matched, not word-matched: bare "confirm"/"verify" would collide with
       # "CONFIRMED" and "Verified -", which open most GOOD evidence strings.
       "cannot confirm","confirm before","confirm on","verify before","second check","needs a second",
       "review persona","human review","wrong-link","unresolved","suspect","only moderate",
       "not conclusive","suggestive")
def title_ok(r):
    """Native `jobtitle` is written ONLY on an explicit >=0.90 flag. ai__sources_confirming is NOT a
    proxy for confidence - it is populated liberally and would wave nearly everything through."""
    if not r.get('title'): return (False,"no title supplied")
    if r['verdict']!='yes': return (False,"verdict is '"+str(r['verdict'])+"', not yes")
    c=r.get('title_conf')
    if isinstance(c,bool) or not isinstance(c,(int,float)): return (False,"no numeric title_conf - failing closed")
    if c<TITLE_CONF_MIN: return (False,"title_conf %.2f below %.2f"%(c,TITLE_CONF_MIN))
    blob=((r.get('ev') or '')+' '+(r.get('changed') or '')).lower()
    hit=[t for t in AMBIG if t in blob]
    if hit: return (False,"ambiguity marker in evidence: "+", ".join(hit[:3]))
    if identity_doubt(r): return (False,"slug does not carry this contact's name - whose title is it")
    return (True,None)
def identity_doubt(r):
    """Does the LinkedIn slug we read carry this contact's name at all?

    A wrong-linked profile produces a verdict that is perfectly reasoned about the WRONG HUMAN.
    Found on the first validation pass: CRM 'Matt Eberhart / matt@query.ai' carried the slug
    `manthony`, which resolves to Matt Anthony - a real Query advisor, so every dated row checked
    out and the run banked a confident `yes` plus a title write about someone else entirely.
    SKILL.md has documented this failure mode ("1.3% of contacts carry URLs pointing at different
    people") and named an issue value for it since the beginning, but nothing ever CHECKED - it was
    prose, and prose does not run.

    Deliberately advisory, not fatal. Custom vanity slugs, maiden names and initials are all
    legitimate, and 63 of 66 slugs matched on the measured run - so a mismatch is rare but is not
    proof of anything. It raises the issue for a human and blocks the native title write, because
    the 0.90 gate should fail closed on doubt about WHOSE title it is."""
    pr=prior.get(str(r['id'])) or {}
    # the URL this verdict was actually read from: a corrected one if supplied, else what is stored
    sl=(slug(r.get('li_url')) or slug(pr.get('hs_linkedin_url'))
        or slug(pr.get('linkedin_profile_url__unique_value')))
    if not sl: return None
    body=re.sub(r'[^a-z]','',sl)
    fn=re.sub(r'[^a-z]','',(pr.get('firstname') or '').lower())
    ln=re.sub(r'[^a-z]','',(pr.get('lastname') or '').lower())
    if not (fn or ln): return None            # nothing to compare against
    if ln and len(ln)>=4 and ln in body: return None
    if fn and len(fn)>=3 and fn in body: return None
    return ("slug %r carries neither the first nor the last name on this record - the profile may "
            "belong to a different person, which would make every dated row correct and the "
            "verdict about the wrong human"%sl)

inputs=[];refused=[];urlfix=[];accepted=[];titlewrite=[];title_skip=[];idflag=[]
# Read prior evidence AND prior jobtitle before building anything: the evidence string records the
# native title we are about to overwrite, so the overwrite stays reversible with no new field.
prior={}
for i in range(0,len(V),100):
    pr=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
            {"inputs":[{"id":str(x['id'])} for x in V[i:i+100]],
             "properties":["ai__contact_evidence","jobtitle","firstname","lastname",
                           "hs_linkedin_url","linkedin_profile_url__unique_value"]})
    for x in pr.get('results',[]): prior[str(x['id'])]=x['properties'] or {}
# Fail CLOSED on anything the prior read could not return. Writing a contact whose prior evidence
# we never saw would replace that history rather than append to it - silently, and unrecoverably.
unread=[str(x['id']) for x in V if str(x['id']) not in prior]
if unread:
    print("PRIOR READ INCOMPLETE for "+str(len(unread))+" contact(s): "+", ".join(unread[:10])
          +("" if len(unread)<=10 else " ..."))
    print("  These are DROPPED from this batch. Their prior evidence could not be read, so writing")
    print("  them would overwrite history instead of appending to it. Usually a contact deleted or")
    print("  merged since the queue was built, or a HubSpot partial-batch (207) failure.")
    _before=len(V); V=[x for x in V if str(x['id']) in prior]
    if not V:
        print("HALT: nothing left in this batch after dropping unreadable records."); sys.exit(2)
for r in V:
    verdict=r['verdict']; ls=r.get('ls')
    if verdict not in VERDICT_OK:
        refused.append((r['id'],"unknown verdict '"+str(verdict)+"' - RECORD DROPPED")); continue
    if ls and verdict=='yes':
        refused.append((r['id'],"ls on a yes verdict - RECORD DROPPED")); continue
    if ls in LS_RETIRED:
        refused.append((r['id'],"'"+str(ls)+"' is no longer written by this process - RECORD DROPPED. "
                        "Employment dates cannot establish buying authority; leave the lead status "
                        "alone and raise an issue for a human if the persona looks wrong.")); continue
    if ls and ls not in LS_OK:
        refused.append((r['id'],"bad ls '"+str(ls)+"' - RECORD DROPPED")); continue
    # EJECTION GATE. Every literal in LS_OK removes a human being from every calling list, and this
    # write used to carry NO confidence requirement at all - while the reversible, cosmetic
    # `jobtitle` write was gated behind title_conf >= 0.90 AND this same hedge scan. The asymmetry
    # was exactly backwards: the consequential write was the unguarded one.
    # Observed in production (contact 1286948): evidence hedged three separate ways - "PROBABLY
    # MOVED ... suggestive, not conclusive ... needs a second check" - ejected the contact exactly
    # as hard as a certainty would have. A caveat in prose must not fire a hard action.
    # Refuse the whole record rather than write the verdict without the ejection: a `no` with no
    # lead status is the dialable-but-departed state the check below already refuses, and it would
    # also bank a verdict that stops queue.py ever surfacing the contact again.
    if ls:
        blob=((r.get('ev') or '')+' '+(r.get('changed') or '')).lower()
        hedge=[t for t in AMBIG if t in blob]
        if hedge:
            refused.append((r['id'],"ejecting ls '"+ls+"' on hedged evidence ("+", ".join(hedge[:3])
                            +") - RECORD DROPPED. Firm up the evidence or file an issue for a human."))
            continue
    if verdict=='no' and not ls:
        # a `no` with no lead status never ejects the contact, and queue.py will never surface it
        # again because it now carries a verdict -> a dialable record proven to have left. Refuse.
        refused.append((r['id'],"verdict 'no' with no lead status - RECORD DROPPED")); continue
    if MARKER in (r.get('ev') or '') or MARKER in (r.get('changed') or ''):
        refused.append((r['id'],"evidence contains the mover filter token - RECORD DROPPED")); continue
    wt,wt_why=title_ok(r)
    old_title=(prior.get(str(r['id'])) or {}).get('jobtitle') or ''
    if r.get('title') and not wt: title_skip.append((str(r['id']),wt_why))
    # build the "what changed in HubSpot" clause (explicit if given, else auto)
    if r.get('changed'):
        changed=r['changed']
    else:
        bits=["flag="+verdict]
        if ls: bits.append("lead status='"+ls+"'")
        if r.get('title'): bits.append("ai__job_title='"+r['title']+"'")
        if wt: bits.append("jobtitle "+(("was '"+old_title+"' ->") if old_title else "set ->")
                           +" '"+r['title']+"' (conf %.2f)"%r['title_conf'])
        if r.get('li_url'): bits.append("LinkedIn URL corrected")
        if r.get('newco'): bits.append("re-associate queued -> "+r['newco'])
        changed=", ".join(bits)
    tail=" - Changed: "+changed
    head="Verified - "+D+" - "
    ev=head+r['ev'][:max(0,900-len(head)-len(tail))]+tail    # budget so `Changed:` always survives
    p={"ai__li_still_at_company":verdict,"ai__contact_evidence":ev,
       "ai__li_last_attempt_date":D,          # every touch, including a failed read
       "ai__sources_confirming":r.get('sources',1),
       "validated__linkedin_or_manually":validated_of(verdict,ls)}
    # Only a CONFIRMED verdict earns a verified date. Stamping it on an unreadable made a record
    # that had never been verified look freshly verified for the whole staleness window, and the
    # 90-day freshness query returned those records as if they were good.
    if verdict in CONFIRMED: p["ai__contact_verified_date"]=D
    # Free to record, already read off the same dated rows, and the only way tenure-stratified
    # decay is ever computable: a 10-year incumbent and a 4-month hire are not the same risk.
    if isinstance(r.get('tenure'),(int,float)) and not isinstance(r.get('tenure'),bool):
        p["ai__li_tenure_years"]=r['tenure']
    if r.get('role_change') in ('yes','no'): p["ai__li_recent_role_change"]=r['role_change']
    # The durable exception register. Session scratch files do not survive a scheduled run, so a
    # queued judgement call that lives only in a local JSON is a queued judgement call nobody sees.
    _doubt=identity_doubt(r)
    if _doubt and not r.get('issue'):
        r=dict(r); r['issue']='wrong_link_suspected'; r['issue_note']=_doubt[:900]
        idflag.append((str(r['id']),_doubt[:80]))
    if r.get('issue'):
        if r['issue'] not in ISSUE_OK:
            refused.append((r['id'],"unknown issue '"+str(r['issue'])+"' - RECORD DROPPED")); continue
        p["ai__verification_issue"]=r['issue']; p["ai__verification_issue_on"]=D
        if r.get('issue_note'): p["ai__verification_issue_note"]=str(r['issue_note'])[:900]
    if ls: p["hs_lead_status"]=ls
    # A mover's destination goes on the CONTACT, not only into pending_movers_<lid>.json. That
    # file dies with a scheduled container, and once the verdict is banked queue.py never surfaces
    # the contact again - so a lost queue leaves a real person ejected at the employer they left,
    # with nothing anywhere recording where they went. movepipe clears this when it re-associates.
    if r['verdict']=='no' and r.get('newco'): p["ai__pending_mover_to"]=str(r['newco'])[:200]
    if r.get('title'): p["ai__job_title"]=r['title']            # AI-owned title, always safe to write
    if wt: p["jobtitle"]=r['title']; titlewrite.append((str(r['id']),r['title'],old_title))
    if r.get('li_url'): p["hs_linkedin_url"]=r['li_url']; urlfix.append((str(r['id']),r['li_url']))
    inputs.append({"id":str(r['id']),"properties":p}); accepted.append(r)
for cid,why in refused: print("REFUSED",cid,why)
for cid,why in title_skip: print("NO-JOBTITLE",cid,why,"(ai__job_title still written)")
for cid,why in idflag: print("IDENTITY",cid,why,"-> wrong_link_suspected raised")
# append, never overwrite: prior entries carry the mover marker, phone-correction notes and
# human flags that two production lists filter on.
for it in inputs:
    old=(prior.get(it['id']) or {}).get('ai__contact_evidence') or ''
    if old: it['properties']['ai__contact_evidence']=(it['properties']['ai__contact_evidence']+" || "+old)[:990]
# queue movers FIRST: once a contact is flagged in the CRM, queue.py never surfaces it again,
# so a crash between the write and the queue loses the mover permanently.
mv=[{"id":str(r['id']),"newco":r['newco']} for r in accepted if r['verdict']=='no' and r.get('newco')]
if mv:
    pf="pending_movers_"+lid+".json"
    pend=json.load(open(pf)) if os.path.exists(pf) else []
    have={x['id'] for x in pend}
    pend+=[x for x in mv if x['id'] not in have]
    tmp=pf+'.tmp'; json.dump(pend,open(tmp,'w'),indent=1); os.replace(tmp,pf)
    print("queued "+str(len(mv))+" movers -> "+pf+" (total "+str(len(pend))+")")
    print("      also stamped ai__pending_mover_to on each, so the queue survives this container")
# ---------- PRE-WRITE GUARDRAILS -------------------------------------------------------
# These used to live at the BOTTOM of this file, after batch/update had already committed, and
# they only evaluated once the accumulated log passed n>=50. That log is a local file that does
# not survive a routine container, so at 15-60 verdicts a run `n` never reached 50 and the
# guardrails NEVER EXECUTED - not once - while SKILL.md advertised them as ENFORCED.
# This block runs BEFORE the write and measures THIS batch, so a bad batch is refused rather
# than reported. The lifetime check further down still runs, but it is now the second line of
# defence rather than the only one.
# A ceiling breach here almost always means the INSTRUMENT failed, not that the data is bad:
# LinkedIn rate-limiting or an auth failure turns every read into an `unreadable`.
from collections import Counter as _C
_bc=_C(r['verdict'] for r in accepted); _bn=len(accepted)
if _bn>=8:      # below this a single record swings the share; too noisy to act on
    for _v,_ceil,_why in (('unreadable',0.50,'a transport or rate-limit failure, not a finding about these people'),
                          ('no_profile',0.60,'a statement about the SOURCE of this data, not about individuals'),
                          ('no',0.80,'a judge ejecting nearly everyone, or a list pointed at the wrong cohort')):
        _sh=_bc.get(_v,0)/_bn
        if _sh>_ceil:
            print("GUARDRAIL (pre-write): '%s' is %.0f%% of this batch of %d - above %.0f%%."
                  %(_v,_sh*100,_bn,_ceil*100))
            print("  Refusing to write. That share usually means "+_why+".")
            print("  NOTHING was written. Fix the cause and re-run this batch.")
            sys.exit(3)
    print("ok   pre-write guardrails: batch of %d %s"%(_bn,dict(_bc)))

# chunk at 100 (HubSpot batch cap), diff requested vs returned
applied=0
for i in range(0,len(inputs),100):
    ch=inputs[i:i+100]
    res=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/update',{"inputs":ch})
    got={str(x['id']) for x in res.get('results',[])}
    applied+=len(got)
    missing=[x['id'] for x in ch if x['id'] not in got]
    if missing: print("WARNING not returned by batch:",missing, json.dumps(res)[:200])
# sync the unique LinkedIn field per-record (unique constraint -> collision means a duplicate contact)
usync=0;ucollide=[]
for cid,url in urlfix:
    res=call('PATCH','https://api.hubapi.com/crm/v3/objects/contacts/'+cid,
        {"properties":{"linkedin_profile_url__unique_value":url}})
    if res.get('id'): usync+=1
    else: ucollide.append(cid)
if urlfix: print("LinkedIn unique-value synced "+str(usync)+"/"+str(len(urlfix))+
                 (" | collisions (duplicate contacts) -> "+str(ucollide) if ucollide else ""))
# read-back verification
ids=[str(r['id']) for r in V]
rb=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
   {"inputs":[{"id":i} for i in ids],"properties":["ai__li_still_at_company","jobtitle"]})
want={str(r['id']):r['verdict'] for r in accepted}
back={str(x['id']):x['properties'].get('ai__li_still_at_company') for x in rb.get('results',[])}
confirmed=[i for i,v in want.items() if back.get(i)==v]
bad=[(i,v,back.get(i)) for i,v in want.items() if back.get(i)!=v]
print("applied "+str(applied)+"/"+str(len(inputs))+" | read-back confirms "+str(len(confirmed))+"/"+str(len(want))+" | date "+D)
if titlewrite:
    # measure, do not assume: this field has competing writers and has been observed reverting.
    tb={str(x['id']):(x['properties'].get('jobtitle') or '') for x in rb.get('results',[])}
    lost=[(c,t,tb.get(c)) for c,t,_ in titlewrite if tb.get(c)!=t]
    print("jobtitle written "+str(len(titlewrite))+" (conf>="+str(TITLE_CONF_MIN)+
          ") | held on read-back "+str(len(titlewrite)-len(lost))+"/"+str(len(titlewrite)))
    for c,t,g in lost[:10]: print("   REVERTED",c,repr(t),"->",repr(g))
    if lost: print("   NOTE: a reverted jobtitle is a competing integration, not a failed write. "
                   "ai__job_title is unaffected and the prior value is in ai__contact_evidence. "
                   "A durable fix is a HubSpot-admin change to the integration field mappings.")
if bad:
    print("READ-BACK MISMATCH (requested -> found):")
    for i,v,g in bad[:20]: print("  ",i,v,"->",g)
# per-list verdict log
f="li_verdicts_"+lid+".json"
log=json.load(open(f)) if os.path.exists(f) else []
cset=set(confirmed)
for r in accepted:
    if str(r['id']) not in cset: continue      # never log a write we could not confirm
    log.append({"id":str(r['id']),"verdict":r['verdict'],"newco":r.get('newco'),
                "lead_status":r.get('ls'),"title":r.get('title'),"title_conf":r.get('title_conf'),
                "jobtitle_written":str(r['id']) in {c for c,_,_ in titlewrite},
                "tenure":r.get('tenure'),"role_change":r.get('role_change'),"date":D})
tmp=f+'.tmp'; json.dump(log,open(tmp,'w'),indent=1); os.replace(tmp,f)
from collections import Counter
print("li_verdicts_"+lid+" total "+str(len(log))+" "+str(dict(Counter(x['verdict'] for x in log))))
# running guardrails over the accumulated log (the model cannot hold these across context windows)
# MODE matters. A refresh pass deliberately selects records that were confirmed before, so most
# re-confirm and the `no` share is legitimately near zero - the floor exists to catch a judge
# rubber-stamping `yes` on a FIRST pass, and on a refresh it fires on correct behaviour. Ceilings
# still apply in both modes: they detect the instrument failing, which mode does not excuse.
MODE=os.environ.get('MODE','first_pass')
# Count from HUBSPOT, not from the local log. The log is a file in the working directory and a
# routine-fired container is destroyed after every run, so `n` restarted from zero on every fire
# and never reached the 50 this block requires - which is why these checks had never once run.
# Scope: everything this run has touched TODAY (ai__li_last_attempt_date == D), which survives a
# container restart, spans however many batches the run took, and is exactly the population these
# ratios are meant to describe.
def _today_counts():
    # HubSpot search compares DATE properties as epoch MILLISECONDS at UTC midnight. Passing the
    # ISO string returns HTTP 400, which this function would have swallowed into a fallback - so
    # the guardrail would have quietly gone on using the dead local log on every single run.
    import datetime as _dt
    try:
        ms=int(_dt.datetime.strptime(D,"%Y-%m-%d").replace(tzinfo=_dt.timezone.utc).timestamp()*1000)
    except Exception:
        return None
    out={}
    for v in ('yes','no','unreadable','no_profile'):
        r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',
               {"filterGroups":[{"filters":[
                   {"propertyName":"ai__li_last_attempt_date","operator":"EQ","value":ms},
                   {"propertyName":"ai__li_still_at_company","operator":"EQ","value":v}]}],
                "limit":1},fatal=False)
        if not isinstance(r,dict) or '__http' in r or 'total' not in r: return None
        out[v]=r.get('total',0)
    return out
_hs=_today_counts()
if _hs is None:
    print("WARN could not read today's verdict counts from HubSpot - falling back to the local log,")
    print("     which does NOT survive a routine container and may understate the run.")
    c=Counter(x['verdict'] for x in log); n=len(log)
else:
    # HubSpot's search index is EVENTUALLY consistent - measured ~1-3 minutes behind a write. The
    # batch we just committed is therefore invisible to the query above, which reported 0 verdicts
    # seconds after six were written. Add this batch's own counts, which we know locally, so the
    # guardrail sees the run it is supposed to be supervising instead of trailing it by a batch.
    _mine=Counter(r['verdict'] for r in accepted if str(r['id']) in cset)
    for _v,_k in _mine.items(): _hs[_v]=_hs.get(_v,0)+_k
    c=Counter(_hs); n=sum(_hs.values())
    print("run-to-date (attempt date "+D+"): "+str(n)+" "+str(dict(_hs))
          +"  [HubSpot search + this batch; the index lags a write by 1-3 min]")
if n>=50:
    no_share=c.get('no',0)/n; un_share=c.get('unreadable',0)/n; np_share=c.get('no_profile',0)/n
    if MODE=='refresh' and no_share<0.05:
        print("note: 'no' share %.1f%% - floor not applied in MODE=refresh (re-confirming known-good records)"%(no_share*100))
        no_share=0.10
    if no_share>0.60 or no_share<0.05:
        print("GUARDRAIL: 'no' share %.0f%% over %d verdicts today - outside 5-60%%. HALT and report."%(no_share*100,n)); sys.exit(3)
    if un_share>0.20:
        print("GUARDRAIL: 'unreadable' share %.1f%% over %d verdicts - above 20%%. HALT and report."%(un_share*100,n))
        print("  'unreadable' is a TRANSIENT read failure. A high share means the instrument is")
        print("  failing, not that the data is bad - check the Unipile account before continuing.")
        print("  Records with no profile at all belong in 'no_profile' and are excluded from this")
        print("  ratio; if they were being written as 'unreadable' that alone can trip it.")
        sys.exit(3)
    if np_share>0.35:
        print("GUARDRAIL: 'no_profile' share %.1f%% over %d verdicts - above 35%%. HALT and report."%(np_share*100,n))
        print("  That many contacts absent from LinkedIn is a statement about the SOURCE of this")
        print("  data or about a sector this method cannot see - not a per-contact finding.")
        sys.exit(3)
# A batch where everything was refused writes nothing and would otherwise exit 0 - which an
# unattended runner reads as a clean success. Refusal is a finding, not a no-op.
if refused and not inputs:
    print("HALT: every record in this batch was refused - nothing was written."); sys.exit(3)
if bad: sys.exit(1)
