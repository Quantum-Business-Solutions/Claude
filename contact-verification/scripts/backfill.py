#!/usr/bin/env python3
"""backfill.py <listId> [--apply] - bring records verified by the OLD code up to the current
standard, WITHOUT inventing anything.

Two migrations, both derivable from data already in the record:
  1. ai__reassociated_on  <- the date parsed out of the `Verified - <date> - ... RE-ASSOCIATED`
     evidence string, for movers written before that property existed. The Moved-Companies list
     filters on this date; the substring it used to filter on truncates out of the evidence.
  2. ai__contact_verified_date CLEARED on records whose verdict is `unreadable` or `no_profile`.
     The old code stamped a verified date on every touch, so records that were never verified
     look freshly verified - and because the new queue logic reads only the ATTEMPT date for
     those verdicts, the false date would otherwise survive every future pass forever.

Deliberately NOT backfilled: ai__li_tenure_years and ai__li_recent_role_change. Those require
reading the dated rows again. Deriving them from anything else would be the guessing this
process exists to refuse.

Dry-run by default - prints exactly what it would change. Pass --apply to write.
Env: TOKEN. Usage: TOKEN=... python3 backfill.py 3675 [--apply]"""
import json,subprocess,os,sys,re
T=os.environ['TOKEN']; lid=sys.argv[1]
APPLY='--apply' in sys.argv
def call(m,url,body=None):
    c=['curl','-s','--max-time','40','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None: c+=['-d',json.dumps(body)]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    txt,_,code=o.rpartition('\n'); code=code.strip()
    if not code.startswith('2'):
        sys.stderr.write('HTTP '+code+' on '+m+' '+url.split('?')[0]+' :: '+txt[:200]+'\n'); sys.exit(2)
    return json.loads(txt) if txt.strip() else {}
ids=[];after=None
while True:
    u="https://api.hubapi.com/crm/v3/lists/"+lid+"/memberships?limit=250"+(("&after="+after) if after else "")
    q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
    after=(q.get('paging') or {}).get('next',{}).get('after')
    if not after: break
if not ids: sys.stderr.write("list "+lid+" returned zero members - refusing\n"); sys.exit(2)
MARK="RE-"+"ASSOCIATED"
PROPS=["ai__li_still_at_company","ai__contact_verified_date","ai__li_last_attempt_date",
       "ai__reassociated_on","ai__contact_evidence"]
fix_date=[];fix_clear=[];skipped_nodate=0
for i in range(0,len(ids),100):
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
           {"inputs":[{"id":x} for x in ids[i:i+100]],"properties":PROPS})
    for x in r.get('results',[]):
        p=x['properties']; cid=str(x['id'])
        ev=p.get('ai__contact_evidence') or ''
        if MARK in ev and not p.get('ai__reassociated_on'):
            # take the FIRST `Verified - YYYY-MM-DD` that precedes the marker: evidence is
            # appended newest-first, so the segment carrying the marker owns that date.
            seg=ev.split(MARK)[0]
            ds=re.findall(r'Verified\s*-\s*(\d{4}-\d{2}-\d{2})',seg)
            if ds: fix_date.append((cid,ds[-1]))
            else:  skipped_nodate+=1
        v=p.get('ai__li_still_at_company')
        if v in ('unreadable','no_profile') and p.get('ai__contact_verified_date'):
            fix_clear.append((cid,p['ai__contact_verified_date'],v))
print("members %d" % len(ids))
print("  ai__reassociated_on to set      : %d  %s" % (len(fix_date), fix_date[:3]))
print("  movers whose evidence lost its date (cannot derive, left alone): %d" % skipped_nodate)
print("  false verified dates to clear   : %d  %s" % (len(fix_clear), fix_clear[:3]))
if not APPLY:
    print("\nDRY RUN - nothing written. Re-run with --apply to write."); sys.exit(0)
def batch(pairs,build):
    done=0
    for i in range(0,len(pairs),100):
        ch=pairs[i:i+100]
        res=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/update',
                 {"inputs":[{"id":c,"properties":build(t)} for c,*t in ch]})
        done+=len(res.get('results',[]))
    return done
n1=batch(fix_date, lambda t:{"ai__reassociated_on":t[0]}) if fix_date else 0
n2=batch(fix_clear,lambda t:{"ai__contact_verified_date":""}) if fix_clear else 0
print("applied: reassociated_on %d/%d | verified_date cleared %d/%d" %
      (n1,len(fix_date),n2,len(fix_clear)))
# read-back: never report a write we did not confirm
if fix_clear:
    chk=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
             {"inputs":[{"id":c} for c,_,_ in fix_clear[:100]],"properties":["ai__contact_verified_date"]})
    still=[str(x['id']) for x in chk.get('results',[]) if x['properties'].get('ai__contact_verified_date')]
    print("read-back: %d of the first %d still carry a verified date%s" %
          (len(still),min(100,len(fix_clear))," -> "+str(still[:5]) if still else ""))
