#!/usr/bin/env python3
"""movepipe.py <listId> <movers.json> - re-associate confirmed movers to their new employer,
one HubSpot transaction per contact, with the qbs-list-verification conventions.

movers.json = [{"id","newco",
                "domain"(optional - verified company domain; find-or-create by it),
                "dm"(optional bool - is the person a decision-maker at newco?),
                "ls"(optional lead status override; default: ConnectandSell Prospect. This
                     process does NOT write "Not Decision Maker" - see the note at the
                     lead-status assignment for why),
                "title"(optional - current title -> ai__job_title),
                "title_conf"(optional float 0-1 - >=0.90 AND a resolved domain ALSO writes native
                             `jobtitle`. Absent = no native write, ever),
                "li_url"(optional - corrected LinkedIn URL -> BOTH url fields),
                "ev"(evidence string; the mechanism, dates, sources)}]

Per contact: find-or-create company (by domain if given, else by exact name), DELETE stale company
associations, PUT the new one with BOTH associationTypeId 1 AND 279, reconcile the flag to `yes`,
set `company`, set `ai__job_title` (+ native `jobtitle` only when title_conf >= 0.90 and the new
employer's domain resolved) + `validated__linkedin_or_manually`, stamp evidence as
`Verified - <date> - <ev> - Changed: RE-ASSOCIATED to <newco> ...` (must contain RE-ASSOCIATED so the
Moved-Companies list picks it up), and set lead status. The phone is
left untouched so a personal/mobile number carries; the evidence flags "verify phone before dialing".
A corrected LinkedIn URL is written to hs_linkedin_url AND (per-record) linkedin_profile_url__unique_value;
a unique-value collision means a duplicate/wrong-linked contact -> logged, not forced.
Env: TOKEN. DATE=YYYY-MM-DD optional. Appends to reassoc_<listId>_log.json; clears pending_movers_<listId>.json."""
import json,subprocess,os,sys,re,tempfile
T=os.environ['TOKEN']; D=os.environ.get('DATE') or subprocess.run(['date','-u','+%Y-%m-%d'],capture_output=True,text=True).stdout.strip()
lid=sys.argv[1]
FROM_HS=(len(sys.argv)>2 and sys.argv[2]=='--from-hubspot')
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
MARKER="RE-"+"ASSOCIATED"   # built at runtime so the source file cannot seed the filter token
# HubSpot has no URL property type - every URL field in this portal (hs_linkedin_url, website,
# previous__company_domain_name) is plain string/text, and the UI renders any http value as a
# link. So a text property holding this prefix + a record id IS the clickable link.
PORTAL=os.environ.get("HS_PORTAL_ID","20682069")
PORTAL_RECORD_URL="https://app.hubspot.com/contacts/"+PORTAL+"/company/"
def call(m,url,body=None,fatal=True):
    """Returns (data, ok). A timeout or 4xx must never look like an empty result set - that is how
    a failed associations read turns into 'there was nothing stale to remove'."""
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
        return {"__http":code}
    try: return json.loads(body_txt) if body_txt.strip() else {}
    except Exception: return {}
if FROM_HS:
    # Rebuild the queue from the CRM instead of a local file. pending_movers_<lid>.json does not
    # survive a scheduled container, and a lost queue leaves real people ejected at the employer
    # they left with no record of where they went. ai__pending_mover_to does survive.
    M=[]; after=None
    while True:
        body={"filterGroups":[{"filters":[{"propertyName":"ai__pending_mover_to","operator":"HAS_PROPERTY"}]}],
              "properties":["ai__pending_mover_to","ai__contact_evidence"],"limit":100}
        if after: body["after"]=after
        r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',body)
        for x in r.get('results',[]):
            dest=(x['properties'] or {}).get('ai__pending_mover_to')
            if dest: M.append({"id":x['id'],"newco":dest,
                               "ev":"Queue rebuilt from ai__pending_mover_to (the local queue file "
                                    "did not survive the container that wrote the verdict)."})
        after=((r.get('paging') or {}).get('next') or {}).get('after')
        if not after: break
    print("rebuilt "+str(len(M))+" pending mover(s) from HubSpot")
    if not M: sys.exit(0)
else:
    M=json.load(open(sys.argv[2]))
TITLE_CONF_MIN=0.95   # Shawn's number, raised from 0.90 on 2026-09-03. The native `jobtitle`
                      # field is what reps see in the sidebar, the screen-pop and every export, so
                      # the bar is "I am reading this title off a dated, end-null row for THIS
                      # employer", not "I am fairly sure". `ai__job_title` still gets every
                      # verified title regardless - nothing else writes that field, so it is the
                      # lossless record and the native write is the opinionated one.
AMBIG=("caution","ambig","uncertain","unclear","probably","possibly","perhaps","assumed","appears to",
       "may be","might be","succession","dormant","not updated","stale profile","conflict","unsure","?")
def title_ok(m,dom):
    """Native `jobtitle` needs an explicit >=0.90 flag AND a resolved domain - an unresolved domain
    means we are not certain WHICH employer the title belongs to. Fails closed."""
    if not m.get('title'): return (False,"no title supplied")
    if not dom: return (False,"employer domain unresolved - title employer not certain")
    c=m.get('title_conf')
    if isinstance(c,bool) or not isinstance(c,(int,float)): return (False,"no numeric title_conf - failing closed")
    if c<TITLE_CONF_MIN: return (False,"title_conf %.2f below %.2f"%(c,TITLE_CONF_MIN))
    hit=[t for t in AMBIG if t in str(m.get('ev','')).lower()]
    if hit: return (False,"ambiguity marker in evidence: "+", ".join(hit[:3]))
    return (True,None)
def dest_status(coid,default):
    """What lead status is honest for a mover landing at THIS company?

    A confirmed mover is a prospect at their new employer - unless the new employer is already
    somebody in the pipeline, in which case calling them a fresh ConnectandSell Prospect is wrong
    twice over: it mislabels an existing relationship, and it drops the contact into cold-calling
    lists that gate on that status. Shawn's rule, and it is the right one: the only reasons NOT to
    write prospect are that the destination is a current client, a former client, or has a meeting
    or an open deal in flight.

    Returns (lead_status, reason). Reads only the destination company, so it costs at most three
    calls per mover and cannot be skipped by forgetting - it is on the write path.

    Every status returned here is an EXISTING value in this portal's hs_lead_status vocabulary; a
    guard that invents an option writes nothing and returns HTTP 400 mid-pass."""
    c=call('GET',"https://api.hubapi.com/crm/v3/objects/companies/"+str(coid)
                 +"?properties=name,lifecyclestage,type,num_associated_deals",fatal=False)
    p=(c.get('properties') or {})
    life=(p.get('lifecyclestage') or '').lower(); typ=(p.get('type') or '')
    if life=='customer' or typ=='Current Client':
        return ("Current Client","destination %r is a CURRENT CLIENT (lifecyclestage=%s type=%s)"
                %((p.get('name') or coid)[:40],life or '-',typ or '-'))
    if life=='evangelist':
        return ("Current Client","destination %r is marked evangelist - an existing advocate, not a "
                "cold prospect"%(p.get('name') or coid)[:40])
    # open deal beats a stale lifecycle stage: lifecyclestage is edited by hand and goes stale,
    # a deal in an open stage is somebody actively working the account right now.
    try: nd=int(float(p.get('num_associated_deals') or 0))
    except Exception: nd=0
    if nd>0:
        da=call('GET',"https://api.hubapi.com/crm/v4/objects/companies/"+str(coid)+"/associations/deals",fatal=False)
        dids=[str(a['toObjectId']) for a in (da.get('results') or [])][:100]
        if dids:
            dr=call('POST','https://api.hubapi.com/crm/v3/objects/deals/batch/read',
                    {"inputs":[{"id":i} for i in dids],
                     "properties":["dealname","dealstage","hs_is_closed","hs_is_closed_won"]},fatal=False)
            res=dr.get('results') or []
            openx=[x for x in res if (x['properties'].get('hs_is_closed') or 'false')=='false']
            won  =[x for x in res if (x['properties'].get('hs_is_closed_won') or 'false')=='true']
            if openx:
                return ("Open Opportunity","destination %r has %d OPEN deal(s) - e.g. %r"
                        %((p.get('name') or coid)[:40],len(openx),
                          (openx[0]['properties'].get('dealname') or '')[:40]))
            if won:
                return ("Current Client","destination %r has a closed-won deal - existing client"
                        %(p.get('name') or coid)[:40])
            if res:
                return ("Former Client","destination %r has %d closed-lost deal(s) and none open"
                        %((p.get('name') or coid)[:40],len(res)))
    # a meeting already on the calendar outranks any status derived from stage or deal
    ma=call('GET',"https://api.hubapi.com/crm/v4/objects/companies/"+str(coid)+"/associations/meetings",fatal=False)
    mids=[str(a['toObjectId']) for a in (ma.get('results') or [])][-100:]
    if mids:
        mr=call('POST','https://api.hubapi.com/crm/v3/objects/meetings/batch/read',
                {"inputs":[{"id":i} for i in mids],
                 "properties":["hs_meeting_title","hs_meeting_start_time"]},fatal=False)
        now=subprocess.run(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],capture_output=True,text=True).stdout.strip()
        up=[x for x in (mr.get('results') or [])
            if (x['properties'].get('hs_meeting_start_time') or '')>now]
        if up:
            up.sort(key=lambda x:x['properties']['hs_meeting_start_time'])
            return ("ConnectandSell Meeting Set","destination %r has an UPCOMING meeting %s %r"
                    %((p.get('name') or coid)[:40],up[0]['properties']['hs_meeting_start_time'][:16],
                      (up[0]['properties'].get('hs_meeting_title') or '')[:30]))
    return (default,None)
logf='reassoc_'+lid+'_log.json'
log=json.load(open(logf)) if os.path.exists(logf) else []
done={x['id'] for x in log if x.get('ok')}
for m in M:
    cid=str(m['id'])
    if cid in done: continue
    newco=m['newco']; dom=m.get('domain')
    # `dm` is now OPTIONAL and drives no write. It used to be mandatory because an absent value
    # fell through to "Not Decision Maker", silently ejecting a verified executive - so refusing to
    # run was the right call then. This process no longer writes that status at all, so the
    # requirement only blocked queues rebuilt from HubSpot (which carry no dm) from processing at
    # all. It is still recorded in the log when supplied.
    dm=m.get('dm')
    if MARKER in (m.get('ev') or ''):
        log.append({"id":cid,"newco":newco,"ok":False,"err":"ev contains the filter token"})
        print("SKIP  "+cid+" evidence contains the mover filter token"); continue
    # 1. find-or-create company
    coid=None; created=False
    if dom:
        r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
          {"filterGroups":[{"filters":[{"propertyName":"domain","operator":"EQ","value":dom}]}],"properties":["name"],"limit":1})
        res=r.get('results',[])
        if res: coid=res[0]['id']
        else:
            c=call('POST','https://api.hubapi.com/crm/v3/objects/companies',{"properties":{"name":newco,"domain":dom}}); coid=c.get('id'); created=True
    else:
        r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
          {"filterGroups":[{"filters":[{"propertyName":"name","operator":"EQ","value":newco}]}],"properties":["name","domain"],"limit":10})
        res=r.get('results',[])
        if len(res)>1:
            # two companies can share a name. Queue, never guess - picking results[0] silently
            # attaches the contact to whichever record sorted first.
            dr='dedupe_review_'+lid+'.json'
            d=json.load(open(dr)) if os.path.exists(dr) else []
            d.append({"contact":cid,"newco":newco,"candidates":[{"id":x['id'],"name":x['properties'].get('name'),"domain":x['properties'].get('domain')} for x in res]})
            tmp=dr+'.tmp'; json.dump(d,open(tmp,'w'),indent=1); os.replace(tmp,dr)
            log.append({"id":cid,"newco":newco,"ok":False,"err":str(len(res))+" companies share this name - queued to "+dr})
            # also raise it IN HubSpot - the scratch file dies with the container
            call('PATCH','https://api.hubapi.com/crm/v3/objects/contacts/'+cid,
                 {"properties":{"ai__verification_issue":"company_ambiguous",
                                "ai__verification_issue_on":D,
                                "ai__verification_issue_note":("%d HubSpot companies are named %r - "
                                  "pick the right one before re-associating."%(len(res),newco[:60]))}},
                 fatal=False)
            print("QUEUE "+cid+" "+str(len(res))+" companies named '"+newco[:30]+"' -> "+dr); continue
        if res: coid=res[0]['id']
        else:
            c=call('POST','https://api.hubapi.com/crm/v3/objects/companies',{"properties":{"name":newco}}); coid=c.get('id'); created=True
    if not coid:
        log.append({"id":cid,"newco":newco,"ok":False,"err":"no company id"}); json.dump(log,open(logf,'w'),indent=1); print("FAIL company",cid); continue
    # 2. swap associations
    prev=call('GET',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}?properties=company,ai__contact_evidence,jobtitle")
    prev_company=(prev.get('properties') or {}).get('company')
    prev_title=(prev.get('properties') or {}).get('jobtitle') or ''
    prev_ev=(prev.get('properties') or {}).get('ai__contact_evidence') or ''
    assoc=call('GET',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies",fatal=False)
    if 'results' not in assoc:
        # a timeout here used to yield old=[] - indistinguishable from "nothing stale to remove" -
        # leaving the contact associated to BOTH employers with the log reading unassoc:0.
        log.append({"id":cid,"newco":newco,"ok":False,"err":"associations read failed: "+str(assoc)[:80]})
        print("FAIL  "+cid+" associations read failed - contact left untouched"); continue
    old=[a['toObjectId'] for a in assoc.get('results',[]) if str(a['toObjectId'])!=str(coid)]
    # Capture the company we are about to detach BEFORE detaching it. Re-association used to
    # destroy this outright: the association was deleted and the only trace left was a company
    # NAME written into previous__company_domain_name (a domain field), so nobody could get back
    # to the record. Keep the id, the name and the real domain.
    prev_co_id=prev_co_name=prev_co_domain=None
    recovered=False
    src=old[0] if old else None
    if src is None:
        # There may be nothing left to detach, and that is NOT the same as "never had an employer".
        # A portal workflow enrolls on hs_lead_status = 'No Longer with Company' and, ~20 seconds
        # later, REMOVES THE COMPANY ASSOCIATION and blanks native `jobtitle`. Measured on contact
        # 12002674829: status written 14:41:32 by INTEGRATION, associatedcompanyid -> '' at
        # 14:41:52 (CALCULATED), jobtitle -> '' at 14:41:52 (AUTOMATION_PLATFORM). So by the time a
        # mover reaches this script - minutes or a day after the verdict - the employer they left is
        # already gone from the record, and reading only live associations loses the one fact this
        # whole property exists to preserve. The value survives in property HISTORY; take it from
        # there so the previous-employer link is written for movers processed after the ejection.
        h=call('GET',"https://api.hubapi.com/crm/v3/objects/contacts/"+cid
                     +"?propertiesWithHistory=associatedcompanyid",fatal=False)
        for e in ((h.get('propertiesWithHistory') or {}).get('associatedcompanyid') or []):
            if (e.get('value') or '').strip():
                src=e['value'].strip(); recovered=True; break
    if src:
        oc=call('GET',f"https://api.hubapi.com/crm/v3/objects/companies/{src}?properties=name,domain",
                fatal=False)
        if 'id' in oc:
            prev_co_id=str(oc['id'])
            prev_co_name=(oc.get('properties') or {}).get('name')
            prev_co_domain=(oc.get('properties') or {}).get('domain')
            if recovered: print("      previous employer recovered from history: "+prev_co_id+" "+str(prev_co_name))
    for o in old: call('DELETE',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies/{o}")
    call('PUT',f"https://api.hubapi.com/crm/v4/objects/contacts/{cid}/associations/companies/{coid}",
      [{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":1},{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":279}])
    # 3. reconcile contact
    # THIS PROCESS NO LONGER WRITES "Not Decision Maker". It reads dated employment history, which
    # can establish WHERE somebody works and cannot establish whether they can authorise a purchase.
    # That judgement was being derived from title strings - "Chairman", "Founder", "Advisor" - and
    # it ejected a Founder-CEO, an Executive Chairman, a VP of Sales and a Regional Sales Manager
    # who were all still in seat. Worse, it was written alongside verdict `no`, which asserts the
    # person has LEFT: two different questions collapsed into one field, corrupting the one the
    # retry and staleness logic keys on. A re-associated mover is a valid prospect at their new
    # employer; buyability is a human's call.
    ls=m.get('ls') or "ConnectandSell Prospect"
    ls_reason=None
    if not m.get('ls'):
        ls,ls_reason=dest_status(coid,ls)
        if ls_reason: print("      destination check: "+ls_reason+" -> lead status '"+ls+"'")
    wt,wt_why=title_ok(m,dom)
    if m.get('title') and not wt: print("      no-jobtitle "+cid+": "+wt_why+" (ai__job_title still written)")
    tnote=""
    if wt:
        tnote=("jobtitle was '"+prev_title+"' -> " if prev_title else "jobtitle set -> ")+\
              "'"+m['title']+"' (conf %.2f); "%m['title_conf']
    domnote=dom if dom else "UNRESOLVED (verify/enrich)"
    tail=(f" - Changed: {MARKER} to {newco} ({domnote}); was '{prev_company}' (assoc {old}); flag->yes; "
          f"lead status='{ls}'"+(f" NOT prospect because {ls_reason}" if ls_reason else "")+f"; "
          f"phone carried (verify before dialing); "
          f"{'ai__job_title set; ' if m.get('title') else ''}"
          f"{tnote}"
          f"{'LinkedIn URL corrected; ' if m.get('li_url') else ''}"
          f"previous employer record {prev_co_id or 'unknown'} preserved"
          f"{' (recovered from property history - the ejection workflow had already detached it)' if recovered else ''}.")
    head=f"Verified - {D} - "
    ev=head+str(m.get('ev',''))[:max(0,900-len(head)-len(tail))]+tail
    if prev_ev: ev=(ev+" || "+prev_ev)[:990]
    p={"company":newco,"ai__li_still_at_company":"yes","ai__contact_verified_date":D,
       "ai__li_last_attempt_date":D,
       # A DATE, not a substring inside a 990-char field that truncates. The evidence marker
       # survived only 69% of movers on a measured pass; a date cannot be truncated away.
       "ai__reassociated_on":D,
       "ai__sources_confirming":m.get('sources',1),
       "ai__contact_evidence":ev,"hs_lead_status":ls,
       # the contact has now BEEN moved: clear the pending marker so a later run does not
       # re-process them, and so the outstanding-mover count means what it says.
       "ai__pending_mover_to":"",
       "validated__linkedin_or_manually":"Yes"}
    if m.get('title'): p["ai__job_title"]=m['title']
    if wt: p["jobtitle"]=m['title']
    if ls_reason:
        # The status is now a claim about the RELATIONSHIP, not about employment, and this process
        # is not entitled to make that claim silently. Surface it.
        p["ai__verification_issue"]="destination_is_account"; p["ai__verification_issue_on"]=D
        p["ai__verification_issue_note"]=("Re-associated, but NOT set to prospect: "+ls_reason
                                          +". Lead status set to '"+ls+"' - confirm with whoever "
                                          "owns the account.")[:900]
    if not dom:
        # re-associated without a proven domain: the company record has no ICP fields and the
        # contact silently leaves every gated list. Surface it rather than let it vanish.
        p["ai__verification_issue"]="ambiguous_destination"; p["ai__verification_issue_on"]=D
        # one property, two possible findings: keep both rather than letting the later write erase
        # the earlier one - a relationship warning silently replaced by a domain warning is how a
        # contact ends up mislabelled with nobody able to see why.
        _n=("Re-associated to %r with no verified domain - confirm the employer and fill the ICP "
            "fields."%newco[:60])
        if ls_reason: _n+=" ALSO: not set to prospect - "+ls_reason+" (status '"+ls+"')."
        p["ai__verification_issue_note"]=_n[:900]
    if isinstance(m.get('tenure'),(int,float)) and not isinstance(m.get('tenure'),bool):
        p["ai__li_tenure_years"]=m['tenure']
    # Deliberately NOT hardcoded to "yes". Nothing in this process ever writes it back to "no",
    # so an unconditional write means every contact ever re-associated reads "recent role change"
    # forever - and `ai__reassociated_on` (above) already records the same fact WITH a date that
    # can be aged. Write it only when the caller actually judged recency.
    if m.get('role_change') in ('yes','no'): p["ai__li_recent_role_change"]=m['role_change']
    if m.get('li_url'): p["hs_linkedin_url"]=m['li_url']
    # previous__company_domain_name is a DOMAIN field; it was being given a company NAME.
    # It ALSO enforces URL validation despite reporting fieldType 'text' in
    # /crm/v3/properties/contacts - a bare domain returns HTTP 400 INVALID_URL ("No protocol
    # found"), which is fatal here and halted a whole mover pass on its first contact. Send a
    # protocol. Measured 2026-09-03 on 1316587 with 'fictiv.com'.
    if prev_co_domain:
        d=prev_co_domain.strip()
        p["previous__company_domain_name"]=d if d.lower().startswith(('http://','https://')) else 'https://'+d
    if prev_co_id:
        p["ai__previously_associated_company_id"]=prev_co_id
        # Rich text (fieldType html), so this renders as a real anchor with the company NAME as the
        # link text rather than a bare URL. Escape the name - a company called "Smith & Jones <Co>"
        # would otherwise break the markup or, worse, inject it.
        import html as _html
        _label=_html.escape(prev_co_name or ("company "+prev_co_id))
        p["ai__previously_associated_company"]=(
            '<a href="'+PORTAL_RECORD_URL+prev_co_id+'">'+_label+'</a>')
    if prev_co_name or prev_company:
        p["ai__previously_associated_company_name"]=prev_co_name or prev_company
    # The previous employer must not BE the destination. Measured 2026-09-03: 5 of 86
    # re-associations recorded the new company as the one they left, because a failed earlier
    # attempt had already written the destination into associatedcompanyid history and the
    # history-recovery path then read it back. That destroys the single field that would let a
    # human notice a wrong re-association - so refuse to write it rather than write it wrong.
    _pn=(p.get("ai__previously_associated_company_name") or '').strip().lower()
    if _pn and _pn==str(newco).strip().lower():
        for _k in ("ai__previously_associated_company","ai__previously_associated_company_id",
                   "ai__previously_associated_company_name","previous__company_domain_name"):
            p.pop(_k,None)
        p["ai__verification_issue"]="ambiguous_destination"; p["ai__verification_issue_on"]=D
        p["ai__verification_issue_note"]=("The recovered previous employer was the SAME company as "
            "the destination (%r), which means the history had already been written by an earlier "
            "attempt. Left blank rather than recorded wrongly - the employer they left is not "
            "known from this run."%str(newco)[:60])[:900]
        print("      previous employer == destination on "+cid+" - left blank, issue raised")
    u=call('PATCH',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}",{"properties":p}); ok='id' in u
    t_held=None
    if ok and wt:
        # measure, do not assume: 3 integrations compete for jobtitle and it has been seen reverting.
        tb=call('GET',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}?properties=jobtitle",fatal=False)
        t_held=((tb.get('properties') or {}).get('jobtitle') or '')==m['title']
        if t_held is False: print("      jobtitle REVERTED on "+cid+" (competing integration; ai__job_title holds the truth)")
    ucol=False
    if ok and m.get('li_url'):
        ur=call('PATCH',f"https://api.hubapi.com/crm/v3/objects/contacts/{cid}",{"properties":{"linkedin_profile_url__unique_value":m['li_url']}})
        ucol=not ur.get('id')
    log.append({"id":cid,"newco":newco,"companyId":coid,"created":created,"dm":dm,"title":m.get('title'),
                "title_conf":m.get('title_conf'),"jobtitle_written":bool(wt),"jobtitle_held":t_held,"prev_title":prev_title,
                "unassoc":len(old),"unassoc_ids":old,"prev_company":prev_company,"lead_status":ls,"url_unique_collision":ucol,"ok":ok,"err":None if ok else str(u)[:150]})
    print(f"{'OK ' if ok else 'ERR'} {cid} -> {newco[:26]:26} co={coid}{' NEW' if created else ''} ls={ls}"+(" UNIQUE-COLLISION(dup?)" if ucol else ""))
    json.dump(log,open(logf,'w'),indent=1)
okc=sum(1 for x in log if x.get('ok'))
print(f"\nreassoc_{lid}_log: {len(log)} | ok {okc} | companies created {sum(1 for x in log if x.get('created'))}"
      f" | unique-URL collisions (dedupe review) {sum(1 for x in log if x.get('url_unique_collision'))}")
jt=[x for x in log if x.get('jobtitle_written')]
if jt: print(f"jobtitle written {len(jt)} (conf>={TITLE_CONF_MIN}) | held on read-back {sum(1 for x in jt if x.get('jobtitle_held'))}/{len(jt)}")
# remove ONLY the movers this run actually completed - blanking the file used to discard every
# mover that was queued but not in this batch, and they are already flagged so nothing resurfaces them.
pf='pending_movers_'+lid+'.json'
if os.path.exists(pf):
    okids={x['id'] for x in log if x.get('ok')}
    rest=[x for x in json.load(open(pf)) if str(x['id']) not in okids]
    tmp=pf+'.tmp'; json.dump(rest,open(tmp,'w'),indent=1); os.replace(tmp,pf)
    print(f"pending_movers: {len(rest)} still queued")
