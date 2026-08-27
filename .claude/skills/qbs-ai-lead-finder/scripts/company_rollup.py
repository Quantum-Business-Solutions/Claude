#!/usr/bin/env python3
"""
Company rollup. Ranks competing signals per account and applies both gates.

GATE 1  lifecycle != customer (plus dealer-specific stages - ASK, don't assume)
GATE 2  never downgrade: a value with no [source:] tag is human-authored and is
        never touched; machine values are replaced only by a higher rank.

Writes customer_engagement_ids.json - feed it to clear_customers so the customer
gate is applied at the ENGAGEMENT level too. Gating only here leaves the
dealer's own leases visible to reps browsing activity.
"""
import json,os,re,time,datetime,urllib.request,collections,socket
socket.setdefaulttimeout(60)
PAT=os.environ['PAT']

def post(u,b,t=6):
    for i in range(t):
        try:
            r=urllib.request.Request(u,data=json.dumps(b).encode(),
              headers={'Authorization':'Bearer '+PAT,'Content-Type':'application/json'},method='POST')
            return json.load(urllib.request.urlopen(r)),None
        except urllib.error.HTTPError as e:
            body=e.read().decode()[:180]
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            return None,"%s %s"%(e.code,body)
        except Exception:
            time.sleep(2*(i+1))
    return None,"retries"

# every signal from both objects, merged
sigs={}
for fn in ["call_clean_v10.json","task_clean_v10.json","email_clean_v10.json","meeting_clean_v10.json","note_clean_v10.json"]:
    for x in json.load(open(fn)): sigs[x['engagement_id']]=x
print("signals across all engagement types: %s"%format(len(sigs),','))

# associations
amap={}
for typ,obj in (("call","calls"),("task","tasks"),("email","emails"),("meeting","meetings"),("note","notes")):
    ids=[k for k,v in sigs.items() if v['engagement_type']==typ]
    for i in range(0,len(ids),100):
        d,e=post("https://api.hubapi.com/crm/v4/associations/%s/companies/batch/read"%obj,
                 {"inputs":[{"id":x} for x in ids[i:i+100]]})
        if e: continue
        for res in d.get("results",[]):
            f=res.get("from",{}).get("id"); tos=[t["toObjectId"] for t in res.get("to",[])]
            if f and tos: amap[f]=str(tos[0])
        time.sleep(0.12)
print("with company association   : %s"%format(len(amap),','))

comps=sorted(set(amap.values()))
info={}
for i in range(0,len(comps),100):
    d,e=post("https://api.hubapi.com/crm/v3/objects/companies/batch/read",
             {"properties":["name","lifecyclestage","ai_lease_information"],
              "inputs":[{"id":c} for c in comps[i:i+100]]})
    if e: continue
    for r in d.get("results",[]): info[r["id"]]=r["properties"]
    time.sleep(0.12)
print("distinct companies         : %s"%format(len(info),','))

EXCLUDE={"customer","96368288"}
RANK={"stated date":6,"stated year only (pinned 10/31)":5,"computed from remaining term":4,
      "computed from renewal term":4,"computed from term + start year":3,"computed from signed-year + term":3,
      "computed from just-signed":3,"month-to-month (no lease term)":3,
      "computed from remaining term (approx)":2,"projected next cycle (1 renewal)":1}
def rank(x): return (RANK.get(x['src'],0), 1 if x['oem'] else 0, x['ts'])

def excerpt(b,basis,w=140):
    b=re.sub(r'\s+',' ',b).strip()
    key=(basis or '').split(' term,')[0]
    i=b.lower().find(key.lower()) if key else -1
    if i>=0:
        s=max(0,i-w); e=min(len(b),i+len(key)+w)
        return ("..." if s>0 else "")+b[s:e].strip()+("..." if e<len(b) else "")
    return b[:280]

CONF={"stated date":"CONFIRMED","stated year only (pinned 10/31)":"CONFIRMED (year only - month assumed)",
      "computed from remaining term":"CALCULATED","computed from renewal term":"CALCULATED",
      "computed from remaining term (approx)":"CALCULATED (approx qty)","computed from just-signed":"CALCULATED",
      "computed from term + start year":"CALCULATED","computed from signed-year + term":"CALCULATED",
      "month-to-month (no lease term)":"MONTH-TO-MONTH - no lease, winnable now",
      "projected next cycle (1 renewal)":"PROJECTED - one renewal assumed, VERIFY"}

per=collections.defaultdict(list)
for eid,cid in amap.items():
    if eid in sigs: per[cid].append(sigs[eid])

writes={}; skip_cust=skip_human=0; new=upg=kept=0
for cid,rows in per.items():
    p=info.get(cid) or {}
    if (p.get("lifecyclestage") or "") in EXCLUDE: skip_cust+=1; continue
    ex=(p.get("ai_lease_information") or "").strip()
    if ex and "[source:" not in ex: skip_human+=1; continue
    best=max(rows,key=rank)
    if ex:
        m=re.search(r'logged (\d{2}/\d{2}/\d{4}), ([a-z0-9 ()/\-+]+):',ex)
        if m:
            cur=(RANK.get(m.group(2).strip(),0),
                 0 if re.search(r'- Provider unknown',ex) else 1,
                 datetime.datetime.strptime(m.group(1),"%m/%d/%Y").date().isoformat())
            if cur>=rank(best): kept+=1; continue
        upg+=1
    else: new+=1
    d=datetime.date(*map(int,best['end'].split('-')))
    prov=best['oem'][0] if best['oem'] else "Provider unknown"
    ev=excerpt(best['body'],best['basis']).replace('"',"'")
    logged=datetime.date(*map(int,best['ts'].split('-'))).strftime('%m/%d/%Y')
    others=len(rows)-1
    extra=" (+%d other engagement%s with lease signal)"%(others,'s' if others>1 else '') if others else ""
    f=(" ** "+",".join(best['flags'])) if best['flags'] else ""
    writes[cid]=("%s [%s] - %s - %s [source: %s id %s, logged %s, %s: \"%s\"]%s%s"%(
        d.strftime('%Y/%m'),CONF.get(best['src'],best['src']),prov,ev,best['engagement_type'],
        best['engagement_id'],logged,best['src'],best['basis'],extra,f))[:65000]

cust_eng=[eid for eid,cid in amap.items() if (info.get(cid) or {}).get("lifecyclestage")=="customer"]
json.dump(cust_eng,open("customer_engagement_ids.json","w"))
print("\nengagement records on CUSTOMER companies: %s"%format(len(cust_eng),','))
print("\nnet-new companies    : %s"%format(new,','))
print("upgraded             : %s"%format(upg,','))
print("kept existing        : %s"%format(kept,','))
print("skipped customer     : %s"%format(skip_cust,','))
print("skipped human-written: %s"%format(skip_human,','))

items=[{"id":k,"properties":{"ai_lease_information":v}} for k,v in writes.items()]
ok=0
for i in range(0,len(items),100):
    d,e=post("https://api.hubapi.com/crm/v3/objects/companies/batch/update",{"inputs":items[i:i+100]})
    if e: print("ERR",e)
    else: ok+=len(d.get("results",[]))
    time.sleep(0.25)
print("\nwritten to %s companies"%format(ok,','))
