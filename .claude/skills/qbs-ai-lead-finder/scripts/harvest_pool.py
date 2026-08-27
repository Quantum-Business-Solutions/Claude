#!/usr/bin/env python3
"""
Date-windowed, resumable harvester.

HubSpot search HARD-CAPS AT 10,000 RESULTS and returns a 400 at result 10,001
with no warning. Any term above that is silently truncated. This recursively
halves the timestamp range until each slice is under the cap.

Measured impact: identical term set, 3,997 records flat vs 142,909 windowed.

Also: resumable (persists after every term), catches every exception not just
HTTPError, and prints per-term progress. All three learned the hard way.

  OBJ=tasks FIELDS=hs_task_body,hs_task_subject TERMS=master_terms.json \
  PAT=... python3 harvest_pool.py

Writes per_term_counts.json for the harvest QA gate.
"""
import json,os,time,urllib.request,urllib.error,datetime,socket
PAT=os.environ['PAT']
# ── configure per object ────────────────────────────────────────────
OBJ      = os.environ.get("OBJ","calls")
POOLF    = os.environ.get("POOL","%s_pool.json"%OBJ)
DONEF    = os.environ.get("DONE","%s_done.json"%OBJ)
FIELDS   = os.environ.get("FIELDS","hs_call_body,hs_call_summary,hs_call_title").split(",")
TERMFILE = os.environ.get("TERMS","master_terms.json")
socket.setdefaulttimeout(60)
POOL=POOLF; DONE=DONEF
pool=json.load(open(POOL)) if os.path.exists(POOL) else {}
per_term={}
done=set(json.load(open(DONE))) if os.path.exists(DONE) else set()
def srch(b,tries=8):
    for i in range(tries):
        try:
            r=urllib.request.Request("https://api.hubapi.com/crm/v3/objects/%s/search"%OBJ,data=json.dumps(b).encode(),
              headers={'Authorization':'Bearer '+PAT,'Content-Type':'application/json'},method='POST')
            return json.load(urllib.request.urlopen(r))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            return None
        except Exception: time.sleep(2*(i+1)); continue
    return None
def ms(d): return str(int(datetime.datetime(d.year,d.month,d.day).timestamp()*1000))
def F(prop,term,lo,hi):
    return [{"propertyName":prop,"operator":"CONTAINS_TOKEN","value":term},
            {"propertyName":"hs_timestamp","operator":"GTE","value":ms(lo)},
            {"propertyName":"hs_timestamp","operator":"LT","value":ms(hi)}]
def count(prop,term,lo,hi):
    d=srch({"limit":1,"filterGroups":[{"filters":F(prop,term,lo,hi)}]}); return (d or {}).get("total",0)
def page(prop,term,lo,hi,props):
    after=None;n=0
    while True:
        b={"limit":200,"properties":props,"filterGroups":[{"filters":F(prop,term,lo,hi)}]}
        if after: b["after"]=after
        d=srch(b)
        if not d: break
        rs=d.get("results",[])
        if not rs: break
        for r in rs: pool.setdefault(r["id"],r)
        n+=len(rs)
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after or n>=9800: break
        time.sleep(0.03)
    return n
def windows(prop,term,lo,hi,props,depth=0):
    c=count(prop,term,lo,hi)
    if c==0: return 0
    if c<9000 or depth>=8: return page(prop,term,lo,hi,props)
    m=lo+(hi-lo)/2; m=datetime.date(m.year,m.month,1)
    if m<=lo or m>=hi: return page(prop,term,lo,hi,props)
    return windows(prop,term,lo,m,props,depth+1)+windows(prop,term,m,hi,props,depth+1)
PROPS=FIELDS+["hs_timestamp"]
TERMS=json.load(open(TERMFILE))
LO=datetime.date(2010,1,1); HI=datetime.date(2027,1,1)
for prop in FIELDS:
    for t in TERMS:
        k="%s|%s"%(prop,t)
        if k in done: continue
        got=windows(prop,t,LO,HI,PROPS)
        per_term[k]=got
        done.add(k)
        print("  %-9s %-20s +%-6d pool=%d"%(prop.split('_')[-1],t.strip('*')[:20],got,len(pool)),flush=True)
        json.dump(pool,open(POOL,"w")); json.dump(sorted(done),open(DONE,"w"))
print("FULL POOL (%s):"%OBJ,len(pool),flush=True)

# per-term counts for the harvest QA gate (cap-truncation detection)
json.dump(per_term,open("per_term_counts.json","w"))
