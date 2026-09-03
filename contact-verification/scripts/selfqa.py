#!/usr/bin/env python3
"""selfqa.py - what did today's run actually do, and is any of it drifting?

Run it as the LAST step of every fire:

    TOKEN=... python3 selfqa.py [--days 14] [--json report.json]

It reads only HubSpot, because HubSpot is the one thing that survives the container. Everything it
reports is a count it computed, not a claim the run made about itself - the whole point is that a
run cannot grade its own homework from its own log. Three kinds of output:

  METRIC   today's number next to the trailing baseline, so drift is visible
  DRIFT    today is materially out of band against that baseline - worth a human's attention
  BACKLOG  work that exists and is not being drained, with the number and the days it has sat

Exit codes: 0 nothing out of band - 1 at least one DRIFT or BACKLOG worth reading. Never non-zero
for "today was quiet"; a routine that halts on its own QA step has turned a report into an outage.

WHAT THIS DELIBERATELY DOES NOT DO
It does not change its own rules, thresholds, prompts or code, and it must not be given the
ability to. An unattended process that edits the definition of its own success can drift a long
way while reporting that everything is fine, and the failure is unrecoverable because the
yardstick moved with it. Improvement proposals come out as text for a person to accept or reject.
The one thing worse than a rule a model has to remember is a rule a model can rewrite."""
import os,sys,json,subprocess,tempfile,datetime
T=os.environ['TOKEN']
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
DAYS=14; OUTJ=None
a=sys.argv[1:]
while a:
    k=a.pop(0)
    if k=='--days': DAYS=int(a.pop(0))
    elif k=='--json': OUTJ=a.pop(0)
    else: sys.exit("unknown argument "+k)
D=os.environ.get('DATE') or subprocess.run(['date','-u','+%Y-%m-%d'],capture_output=True,text=True).stdout.strip()
def ms(datestr):
    y,m,d=(int(x) for x in datestr.split('-'))
    return int(datetime.datetime(y,m,d).timestamp()*1000)
TODAY=ms(D)
def call(m,url,body=None):
    c=['curl','-s','--max-time','30','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open(TMP,'w').write(json.dumps(body)); c+=['-d','@'+TMP]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    txt,_,code=o.rpartition('\n'); code=code.strip()
    if not code.isdigit() or not code.startswith('2'):
        # A failed count is not a zero. Reporting "0 unreadable today" because the query 400'd is
        # precisely the shape of lie this whole file exists to prevent.
        sys.stderr.write("QA QUERY FAILED HTTP "+code+" :: "+txt[:160]+"\n"); return None
    try: return json.loads(txt)
    except Exception: return None
def total(filters):
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',
           {"filterGroups":[{"filters":filters}],"properties":["hs_object_id"],"limit":1})
    return None if r is None else r.get('total',0)
# Date properties compare as EPOCH MILLISECONDS in the search API; an ISO string is HTTP 400, and a
# 400 swallowed into a fallback is how an earlier guardrail became silently inert.
ATT=lambda op,v: {"propertyName":"ai__li_last_attempt_date","operator":op,"value":str(v)}
V=lambda v: {"propertyName":"ai__li_still_at_company","operator":"EQ","value":v}
HAS=lambda p: {"propertyName":p,"operator":"HAS_PROPERTY"}
NOT=lambda p: {"propertyName":p,"operator":"NOT_HAS_PROPERTY"}
metrics={};drift=[];backlog=[];notes=[]
def pct(n,d): return None if not d else 100.0*n/d
today_n=total([ATT('EQ',TODAY)])
if today_n is None: print("HALT: cannot read today's counts - QA is inconclusive, not clean."); sys.exit(1)
metrics['verdicts_today']=today_n
mix={}
for v in ('yes','no','unreadable','no_profile'):
    mix[v]=total([ATT('EQ',TODAY),V(v)])
metrics['mix_today']=mix
base_from=ms(D)-DAYS*86400000
basen=total([ATT('GTE',base_from),ATT('LT',TODAY)])
bmix={v:total([ATT('GTE',base_from),ATT('LT',TODAY),V(v)]) for v in ('yes','no','unreadable','no_profile')}
metrics['baseline_days']=DAYS; metrics['baseline_n']=basen; metrics['baseline_mix']=bmix
print("== today %s: %d verdicts | trailing %d days: %d"%(D,today_n,DAYS,basen or 0))
for v in ('yes','no','unreadable','no_profile'):
    tp,bp=pct(mix[v] or 0,today_n),pct(bmix[v] or 0,basen or 0)
    print("   METRIC %-11s today %4d (%5s%%)  baseline (%5s%%)"%(
        v,mix[v] or 0,'%.1f'%tp if tp is not None else '  n/a','%.1f'%bp if bp is not None else '  n/a'))
    # Drift, not correctness. A verdict mix moving a long way in a day is usually a platform
    # change or a queue change, and it is the earliest visible symptom of both.
    if tp is not None and bp is not None and today_n>=25 and abs(tp-bp)>=15:
        drift.append("%s share moved %.1f pts (today %.1f%% vs %.1f%% over %d days) on %d records"
                     %(v,tp-bp,tp,bp,DAYS,today_n))
# Absolute ceilings, independent of any baseline: a bad baseline must not legitimise a bad day.
if today_n>=25:
    for v,ceil in (('unreadable',30.0),('no_profile',25.0)):
        p=pct(mix[v] or 0,today_n)
        if p is not None and p>ceil:
            drift.append("%s at %.1f%% of today's run exceeds the %.0f%% ceiling - suspect the "
                         "transport or the queue, not the people"%(v,p,ceil))
# Backlogs: work that exists, is known, and is not being drained.
b_pending=total([HAS('ai__pending_mover_to')])
b_nodest=total([V('no'),NOT('ai__pending_mover_to'),NOT('ai__reassociated_on')])
# Split it: a `no` with no destination is only STRANDED while it still carries a verified date,
# because queue.py returns a `no` for re-reading once that date goes stale. Clearing the date is
# how a suspect verdict is sent back for another look, so counting those as stranded overstates
# the backlog and - worse - describes work that IS scheduled as work that will never happen.
b_requeue=total([V('no'),NOT('ai__pending_mover_to'),NOT('ai__reassociated_on'),
                 NOT('ai__contact_verified_date')])
b_stranded=None if (b_nodest is None or b_requeue is None) else b_nodest-b_requeue
b_issue=total([HAS('ai__verification_issue')])
b_wrong=total([{"propertyName":"ai__verification_issue","operator":"EQ","value":"wrong_link_suspected"}])
b_stale=total([V('yes'),{"propertyName":"validated__linkedin_or_manually","operator":"EQ","value":"Needs Updated"}])
metrics.update(pending_movers=b_pending,no_destination=b_nodest,
               no_destination_requeued=b_requeue,no_destination_stranded=b_stranded,open_issues=b_issue,
               wrong_link=b_wrong,stale_validated_flag=b_stale)
print("   METRIC movers queued but not re-associated  %s"%b_pending)
print("   METRIC `no` verdicts with nowhere to go     %s  (of which %s already re-queued for a "
      "re-read, %s stranded)"%(b_nodest,b_requeue,b_stranded))
print("   METRIC records flagged for a human          %s (wrong_link_suspected %s)"%(b_issue,b_wrong))
print("   METRIC verified `yes` still flagged stale   %s"%b_stale)
if b_pending: backlog.append("%s mover(s) carry a destination and were never re-associated - run "
                             "moverqueue.py then movepipe.py IN THIS FIRE, not tomorrow"%b_pending)
if b_stranded: backlog.append("%s contact(s) verified as departed with no destination and a "
                              "verified date still set - queue.py will not return them for %s days, "
                              "so they will NOT resurface on their own. Recover the destination from "
                              "their evidence (recoverdest.py) or clear the verified date to re-read "
                              "them."%(b_stranded,os.environ.get('STALE_DAYS','90')))
if b_requeue: notes.append("%s departed contact(s) have no destination but have had their verified "
                           "date cleared, so the next pass will re-read them. That is the intended "
                           "state for a verdict under suspicion - not a backlog."%b_requeue)
if b_stale: backlog.append("%s contact(s) verified present but still flagged 'Needs Updated' - the "
                           "flag is lying about work that is finished"%b_stale)
if b_wrong and b_wrong>=5: backlog.append("%s contact(s) carry wrong_link_suspected - each is a "
                                          "LinkedIn URL pointing at somebody else"%b_wrong)
# Coverage: is the pace actually going to finish, or is this theatre?
never=total([NOT('ai__li_still_at_company'),
             {"propertyName":"hs_lead_status","operator":"EQ","value":"ConnectandSell Prospect"}])
metrics['dialable_never_verified']=never
if never and today_n:
    days=never/max(today_n,1)
    print("   METRIC dialable never verified              %d  =>  %.0f days (%.1f months) at "
          "today's pace of %d"%(never,days,days/30.4,today_n))
    metrics['months_to_finish']=round(days/30.4,1)
    if days/30.4>12: notes.append("At today's pace this takes %.1f months. If the goal is months "
                                  "rather than years the daily cap is the thing to change - the "
                                  "Unipile budget is ~9,000 reads/day and today used %d."
                                  %(days/30.4,today_n))
print()
for d in drift:   print("DRIFT   "+d)
for b in backlog: print("BACKLOG "+b)
for n in notes:   print("NOTE    "+n)
if not (drift or backlog):
    print("No drift and no backlog. Today's numbers sit inside the trailing %d-day band."%DAYS)
print("\nIMPROVEMENTS ARE PROPOSALS, NOT CHANGES. If this run suggests the process should work")
print("differently, say so in the run summary and leave the code alone. A scheduled job that")
print("edits its own rules can drift a long way while reporting that all is well.")
if OUTJ:
    json.dump({"date":D,"metrics":metrics,"drift":drift,"backlog":backlog,"notes":notes},
              open(OUTJ,'w'),indent=1)
    print("\nwrote "+OUTJ)
sys.exit(1 if (drift or backlog) else 0)
