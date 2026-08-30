#!/usr/bin/env python3
"""repair.py <fix> [--apply] - repair damage this process wrote into the CRM.

Dry-run by DEFAULT. Every fix prints what it would change and a sample before touching anything;
add --apply to write. Every fix reads back what it wrote and reports the confirmed count, because
a repair that reports success it cannot prove is the same failure as the bug it is repairing.

FIXES
  dates      A verified date was stamped on `unreadable` and `no_profile` records, which the
             writers are supposed to set only on a CONFIRMED verdict. Those records read as
             freshly verified to a human and to queue.py, which then will not re-check them until
             the date ages out. The attempt DID happen, so the date is MOVED to
             ai__li_last_attempt_date rather than deleted - that keeps the fact, stops the false
             claim, and lets the 14-day / 180-day retry intervals work for the first time.

  movers     230 records say RE-ASSOCIATED in their evidence but only 38 carry
             ai__reassociated_on, which is the property the Moved-Companies list filters on - so
             ~192 movers are invisible to it. Recovers the date from the evidence text where it is
             stated, and reports the ones it cannot derive rather than guessing.

  contradict Contacts carrying verdict `yes` - verified still employed - while ALSO carrying an
             ejection lead status, which removes them from every calling list. The skill's rule is
             "NEVER write hs_lead_status on a yes". Classified rather than bulk-reverted, because
             one subset is defensible: a record with no email on file is arguably a real
             `Need Updated Info`.

  dialable   Contacts carrying verdict `no` while still sitting on an ACTIVE lead status: proven
             departed and still in the dialer. Ejects them to No Longer with Company.

Env: TOKEN, EXPECT_PORTAL (refuses to run against a different portal - these are bulk writes and
     pointing them at the wrong CRM is not something a later pass can find or undo).
Usage: TOKEN=... EXPECT_PORTAL=20682069 python3 repair.py dates [--apply]"""
import json,os,sys,re,time,urllib.request,urllib.error

T=os.environ.get('TOKEN')
if not T: sys.stderr.write("HALT: TOKEN not set\n"); sys.exit(2)
FIX=sys.argv[1] if len(sys.argv)>1 else ''
import subprocess as _sp
D_TODAY=os.environ.get('DATE') or _sp.run(['date','-u','+%Y-%m-%d'],capture_output=True,text=True).stdout.strip()
APPLY='--apply' in sys.argv

def api(m,path,body=None):
    r=urllib.request.Request("https://api.hubapi.com"+path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"},method=m)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(r,timeout=60) as f:
                raw=f.read(); return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503) and attempt<3: time.sleep(2*(attempt+1)); continue
            sys.stderr.write("HTTP %d on %s :: %s\n"%(e.code,path,e.read(300).decode('utf-8','replace')))
            sys.exit(2)
    sys.exit(2)

want=(os.environ.get('EXPECT_PORTAL') or '').strip()
hub=str(api('GET','/account-info/v3/details').get('portalId') or '')
if not want:
    sys.stderr.write("HALT: set EXPECT_PORTAL. This writes to many records at once and there is no\n"
                     "      undo; naming the portal you mean is the cheapest possible safeguard.\n"
                     "      This token belongs to portal "+hub+".\n"); sys.exit(2)
if hub!=want:
    sys.stderr.write("HALT: token is for portal "+hub+", EXPECT_PORTAL="+want+".\n"); sys.exit(2)
print("portal "+hub+" confirmed | mode: "+("APPLY" if APPLY else "DRY RUN (add --apply to write)"))

def search(filters,props,limit=100):
    out=[];after=None
    while True:
        b={"filterGroups":[{"filters":filters}],"properties":props,"limit":limit}
        if after: b["after"]=after
        r=api('POST','/crm/v3/objects/contacts/search',b)
        out+=r.get('results',[])
        after=((r.get('paging') or {}).get('next') or {}).get('after')
        if not after: break
    return out

def write(updates,label):
    """updates: {id: {prop: value}}. Chunked at 100, read back, reports CONFIRMED not requested."""
    if not updates: print("  nothing to change"); return 0
    if not APPLY:
        print("  DRY RUN - would update %d contact(s). Re-run with --apply."%len(updates)); return 0
    ids=list(updates); applied=0
    for i in range(0,len(ids),100):
        ch=ids[i:i+100]
        api('POST','/crm/v3/objects/contacts/batch/update',
            {"inputs":[{"id":c,"properties":updates[c]} for c in ch]})
        applied+=len(ch)
    # read back: a bulk write that reports its own request count has proved nothing
    checked=0;bad=[]
    for i in range(0,len(ids),100):
        ch=ids[i:i+100]
        prop=sorted({k for c in ch for k in updates[c]})
        r=api('POST','/crm/v3/objects/contacts/batch/read',{"inputs":[{"id":c} for c in ch],"properties":prop})
        for x in r.get('results',[]):
            checked+=1
            for k,v in updates[str(x['id'])].items():
                if (x['properties'] or {}).get(k,'') != v: bad.append((x['id'],k))
    print("  applied %d | read-back confirmed %d | mismatches %d"%(applied,checked-len(bad),len(bad)))
    for b in bad[:10]: print("     MISMATCH",b)
    return applied

# ---------------------------------------------------------------------------------------------
if FIX=='dates':
    rows=[]
    for v in ('unreadable','no_profile'):
        rows+=search([{"propertyName":"ai__li_still_at_company","operator":"EQ","value":v},
                      {"propertyName":"ai__contact_verified_date","operator":"HAS_PROPERTY"}],
                     ["ai__li_still_at_company","ai__contact_verified_date","ai__li_last_attempt_date"])
    print("\n%d record(s) carry a verified date they never earned"%len(rows))
    upd={}
    for x in rows:
        p=x['properties']; vd=(p.get('ai__contact_verified_date') or '')[:10]
        u={"ai__contact_verified_date":""}
        # keep the fact that an attempt happened; only the "verified" claim was false
        if vd and not p.get('ai__li_last_attempt_date'): u["ai__li_last_attempt_date"]=vd
        upd[x['id']]=u
    moved=sum(1 for u in upd.values() if 'ai__li_last_attempt_date' in u)
    print("  clearing the verified date on %d, and moving it to the attempt date on %d"%(len(upd),moved))
    for x in rows[:3]:
        print("   e.g. %s  verdict=%s  verified=%s -> attempt"%(x['id'],
              x['properties'].get('ai__li_still_at_company'),
              (x['properties'].get('ai__contact_verified_date') or '')[:10]))
    write(upd,'dates')

elif FIX=='movers':
    rows=search([{"propertyName":"ai__contact_evidence","operator":"CONTAINS_TOKEN","value":"RE-ASSOCIATED"},
                 {"propertyName":"ai__reassociated_on","operator":"NOT_HAS_PROPERTY"}],
                ["ai__contact_evidence","ai__contact_verified_date"])
    print("\n%d mover(s) say RE-ASSOCIATED in evidence but carry no ai__reassociated_on"%len(rows))
    upd={};nodate=[]
    for x in rows:
        ev=x['properties'].get('ai__contact_evidence') or ''
        # the writers stamp "Verified - YYYY-MM-DD - ..."; the legacy form is "RE-ASSOCIATED <date>:"
        m=(re.search(r'RE-ASSOCIATED\s+(\d{4}-\d{2}-\d{2})',ev) or
           re.search(r'Verified\s*-\s*(\d{4}-\d{2}-\d{2})',ev))
        d=m.group(1) if m else (x['properties'].get('ai__contact_verified_date') or '')[:10]
        if d: upd[x['id']]={"ai__reassociated_on":d}
        else: nodate.append(x['id'])
    print("  date recovered for %d | cannot derive for %d (left alone, not guessed)"%(len(upd),len(nodate)))
    if nodate: print("   undated e.g.: "+", ".join(nodate[:8]))
    write(upd,'movers')

elif FIX=='contradict':
    LSX=("No Longer with Company","Need Updated Info","Retired - Remove from All Lists","Not Decision Maker")
    rows=[];after=None
    while True:
        b={"filterGroups":[{"filters":[{"propertyName":"ai__li_still_at_company","operator":"EQ","value":"yes"},
                                       {"propertyName":"hs_lead_status","operator":"EQ","value":ls}]} for ls in LSX],
           "properties":["hs_lead_status","ai__contact_evidence","email","phone","company",
                         "ai__reassociated_on","ai__verification_issue"],"limit":100}
        if after: b["after"]=after
        r=api('POST','/crm/v3/objects/contacts/search',b)
        rows+=r.get('results',[]); after=((r.get('paging') or {}).get('next') or {}).get('after')
        if not after: break
    print("\n%d contact(s) verified employed AND ejected"%len(rows))
    restore={};persona={};keep=0
    for x in rows:
        cid=x['id']; p=x['properties']; ls=p.get('hs_lead_status'); ev=(p.get('ai__contact_evidence') or '')
        if p.get('ai__reassociated_on') or ls in ("No Longer with Company","Retired - Remove from All Lists"):
            # A mover reconciled to `yes` is employed at the NEW company; the ejection belonged to
            # the `no` stage and was never cleared. And "departed"/"retired" on a `yes` verdict is
            # a straight contradiction under any reading.
            restore[cid]={"hs_lead_status":"ConnectandSell Prospect"}
        elif ls=="Not Decision Maker":
            # This process should never have made a buyability call. Restore the person to the
            # list and flag it, so a human can re-eject on a real judgement rather than a title
            # string - reversible in both directions, which the silent ejection was not.
            persona[cid]={"hs_lead_status":"ConnectandSell Prospect",
                          "ai__verification_issue":"persona_review",
                          "ai__verification_issue_on":D_TODAY,
                          "ai__verification_issue_note":("Was 'Not Decision Maker' on a verified-employed "
                            "record. This process no longer makes buying-authority calls; confirm the "
                            "persona and re-eject by hand if it genuinely does not fit.")[:900]}
        elif not p.get('email'):
            keep+=1                     # genuinely needs an address; the status is doing its job
        else:
            restore[cid]={"hs_lead_status":"ConnectandSell Prospect"}
    print("  restore to prospect          %d  (movers never reconciled, plus straight contradictions)"%len(restore))
    print("  restore + flag persona_review %d  (was 'Not Decision Maker' on a verified-employed record)"%len(persona))
    print("  leave alone                   %d  (no email on file - 'Need Updated Info' is accurate)"%keep)
    upd=dict(restore); upd.update(persona)
    write(upd,'contradict')

elif FIX=='ejections':
    # Re-read every banked `no` against the FULL LinkedIn history and restore anyone who is still
    # in the job we ejected them from. The verdicts were written from `experience_preview`, which
    # truncates - a current employer outside the cut reads as departed. A 57-record sample found
    # 19% wrong. Reads are expensive and rate-limited, so this runs ONCE and writes a proposal to
    # /tmp/ejection_proposal.json; --apply reads that file and does not re-read LinkedIn.
    import html as _h
    PROP='/tmp/ejection_proposal.json'
    if APPLY:
        if not os.path.exists(PROP):
            sys.stderr.write("HALT: no proposal at "+PROP+". Run without --apply first.\n"); sys.exit(2)
        prop=json.load(open(PROP))
        print("\napplying %d restoration(s) from %s"%(len(prop),PROP))
        upd={}
        for r in prop:
            note=("CORRECTION %s: this contact was marked departed on a TRUNCATED LinkedIn history "
                  "(experience_preview returns only the most recent rows). A full read shows %s as a "
                  "CURRENT role - %s since %s, no end date. Verdict and lead status restored."
                  %(D_TODAY,r['company'],r['title'],r['start']))
            upd[r['id']]={"ai__li_still_at_company":"yes",
                          "hs_lead_status":"ConnectandSell Prospect",
                          "ai__contact_verified_date":D_TODAY,
                          "ai__li_last_attempt_date":D_TODAY,
                          "ai__contact_evidence":(note+" || "+r.get('old_ev',''))[:990]}
        write(upd,'ejections'); sys.exit(0)

    K=os.environ.get('UNIPILE_V2_KEY')
    if not K: sys.stderr.write("HALT: UNIPILE_V2_KEY not set - cannot re-read LinkedIn.\n"); sys.exit(2)
    ACC=os.environ.get('UNIPILE_V2_ACCOUNT_ID','acc_01m19mb99wfzvsb68etkn5n87x')
    SUF=r'\b(inc|incorporated|llc|ltd|limited|corp|corporation|co|company|group|holdings|plc|the)\b'
    def norm(x):
        x=re.sub(SUF,' ',re.sub(r'[^a-z0-9 ]',' ',(x or '').lower())); return re.sub(r'\s+',' ',x).strip()
    def same(a,b):
        a,b=norm(a),norm(b)
        if not a or not b: return False
        if a==b: return True
        sh,lo=(a,b) if len(a)<=len(b) else (b,a)
        return len(sh)>=5 and sh in lo
    def prof(slug):
        u=("https://api.unipile.com/v2/"+ACC+"/users/"+slug+"?with_sections=linkedin_experience")
        rq=urllib.request.Request(u,headers={"X-API-KEY":K,"accept":"application/json"})
        for a in range(5):
            try:
                with urllib.request.urlopen(rq,timeout=45) as f: d=json.loads(f.read())
            except urllib.error.HTTPError as e:
                if e.code==429: time.sleep(8*(a+1)); continue
                return None,"HTTP %d"%e.code
            except Exception as e: return None,type(e).__name__
            return ((d.get('specifics') or {}).get('experience') or d.get('experience') or []),None
        return None,"429 after 5 retries"
    rows=search([{"propertyName":"ai__li_still_at_company","operator":"EQ","value":"no"}],
                ["firstname","lastname","company","hs_lead_status","hs_linkedin_url",
                 "linkedin_profile_url__unique_value","ai__contact_evidence"])
    print("\nre-reading %d banked 'no' verdict(s) against FULL history..."%len(rows))
    out=[];checked=0;skipped=0
    for i,x in enumerate(rows):
        p=x['properties']
        m=re.search(r'/in/([^/?#]+)',(p.get('hs_linkedin_url') or p.get('linkedin_profile_url__unique_value') or ''))
        if not m or not p.get('company'): skipped+=1; continue
        exp,err=prof(m.group(1))
        if err: skipped+=1; time.sleep(3.5); continue
        checked+=1
        cur=[e for e in exp if not e.get('ended_on')]
        hit=[e for e in cur if same((e.get('company') or {}).get('name'),p['company'])]
        if hit:
            e=hit[0]
            out.append({"id":x['id'],"who":"%s %s"%(p.get('firstname') or '',p.get('lastname') or ''),
                        "company":p['company'],"title":e.get('job_title'),"start":e.get('started_on'),
                        "was":p.get('hs_lead_status'),"rows":len(exp),
                        "old_ev":(p.get('ai__contact_evidence') or '')[:600]})
            print("   WRONG  %s  %s still at %s as %s since %s  [was %s]"
                  %(x['id'],out[-1]['who'],p['company'],e.get('job_title'),e.get('started_on'),p.get('hs_lead_status')))
        if (i+1)%50==0: print("   ...%d/%d read, %d wrong so far"%(i+1,len(rows),len(out)))
        time.sleep(3.5)
    json.dump(out,open(PROP,'w'),indent=1)
    print("\nchecked %d | could not check %d | WRONGLY EJECTED %d  (%.0f%%)"
          %(checked,skipped,len(out),100.0*len(out)/max(checked,1)))
    print("proposal written to "+PROP+" - review it, then re-run with --apply")

elif FIX=='dialable':
    # A contact carrying verdict `no` while still on an active status is either a missed ejection
    # or a verdict that was never really about employment. Ejecting the whole set on the strength
    # of the verdict alone is exactly the mistake this repair exists to clean up, so each record
    # is classified on its EVIDENCE and its attached pipeline, and only one class is ejected.
    rows=[]
    for ls in ("ConnectandSell Prospect","Deal Follow up"):
        rows+=search([{"propertyName":"ai__li_still_at_company","operator":"EQ","value":"no"},
                      {"propertyName":"hs_lead_status","operator":"EQ","value":ls}],
                     ["hs_lead_status","ai__contact_evidence","firstname","lastname","company"])
    print("\n%d contact(s) carry verdict 'no' on an active status"%len(rows))
    DEPARTED=("departed","left ","no longer","resigned","retired","former")
    eject={};park={};mismatch={}
    for x in rows:
        cid=x['id']; p=x['properties']; ev=(p.get('ai__contact_evidence') or '')
        who="%s %s @ %s"%(p.get('firstname') or '',p.get('lastname') or '',p.get('company') or '')
        deals=len(api('GET','/crm/v4/objects/contacts/%s/associations/deals'%cid).get('results',[]))
        mtgs=len(api('GET','/crm/v4/objects/contacts/%s/associations/meetings'%cid).get('results',[]))
        asserts_departure=any(t in ev.lower() for t in DEPARTED)
        if not asserts_departure:
            # the verdict says 'no' but the evidence never claims they left - e.g. a persona
            # correction filed under the employment field. Ejecting on this would be a guess.
            mismatch[cid]={"ai__verification_issue":"verdict_not_employment",
                           "ai__verification_issue_on":D_TODAY,
                           "ai__verification_issue_note":("Verdict 'no' but the evidence does not "
                             "assert a departure. Confirm employment before ejecting.")[:900]}
            print("   MISMATCH %s  %s  (evidence is not a departure finding)"%(cid,who))
        elif deals or mtgs:
            # real pipeline attached. Ejecting removes a warm re-target - the most expensive
            # mistake available here - so park it for a human and say why.
            park[cid]={"ai__verification_issue":"departed_with_pipeline",
                       "ai__verification_issue_on":D_TODAY,
                       "ai__verification_issue_note":("Departed, but carries %d deal(s) and %d "
                         "meeting(s). Re-target at the new employer rather than ejecting."
                         %(deals,mtgs))[:900]}
            print("   PARK     %s  %s  deals=%d meetings=%d"%(cid,who,deals,mtgs))
        else:
            eject[cid]={"hs_lead_status":"No Longer with Company"}
            print("   EJECT    %s  %s"%(cid,who))
    print("\n  eject %d | park with an issue %d | verdict/evidence mismatch %d"%(len(eject),len(park),len(mismatch)))
    upd=dict(eject); upd.update(park); upd.update(mismatch)
    write(upd,'dialable')

else:
    print(__doc__); sys.exit(2)
