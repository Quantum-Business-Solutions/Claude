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
ISSUE_OK={"wrong_link_suspected","identity_unresolved","no_identifier","ambiguous_destination",
          "company_ambiguous","succession_conflict","duplicate_contact","division_scope_unclear",
          "persona_review","title_conflict","phone_unverified","email_unprovable","retired_headline"}
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
    try: return json.loads(body_txt) if body_txt.strip() else {}
    except Exception:
        if fatal: sys.stderr.write('unparseable response\n'); sys.exit(2)
        return {}
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
    return (True,None)
inputs=[];refused=[];urlfix=[];accepted=[];titlewrite=[];title_skip=[]
# Read prior evidence AND prior jobtitle before building anything: the evidence string records the
# native title we are about to overwrite, so the overwrite stays reversible with no new field.
prior={}
for i in range(0,len(V),100):
    pr=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
            {"inputs":[{"id":str(x['id'])} for x in V[i:i+100]],
             "properties":["ai__contact_evidence","jobtitle"]})
    for x in pr.get('results',[]): prior[str(x['id'])]=x['properties'] or {}
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
    if r.get('issue'):
        if r['issue'] not in ISSUE_OK:
            refused.append((r['id'],"unknown issue '"+str(r['issue'])+"' - RECORD DROPPED")); continue
        p["ai__verification_issue"]=r['issue']; p["ai__verification_issue_on"]=D
        if r.get('issue_note'): p["ai__verification_issue_note"]=str(r['issue_note'])[:900]
    if ls: p["hs_lead_status"]=ls
    if r.get('title'): p["ai__job_title"]=r['title']            # AI-owned title, always safe to write
    if wt: p["jobtitle"]=r['title']; titlewrite.append((str(r['id']),r['title'],old_title))
    if r.get('li_url'): p["hs_linkedin_url"]=r['li_url']; urlfix.append((str(r['id']),r['li_url']))
    inputs.append({"id":str(r['id']),"properties":p}); accepted.append(r)
for cid,why in refused: print("REFUSED",cid,why)
for cid,why in title_skip: print("NO-JOBTITLE",cid,why,"(ai__job_title still written)")
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
c=Counter(x['verdict'] for x in log); n=len(log)
if n>=50:
    no_share=c.get('no',0)/n; un_share=c.get('unreadable',0)/n; np_share=c.get('no_profile',0)/n
    if MODE=='refresh' and no_share<0.05:
        print("note: 'no' share %.1f%% - floor not applied in MODE=refresh (re-confirming known-good records)"%(no_share*100))
        no_share=0.10
    if no_share>0.60 or no_share<0.05:
        print("GUARDRAIL: 'no' share %.0f%% over %d verdicts - outside 5-60%%. HALT and report."%(no_share*100,n)); sys.exit(3)
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
