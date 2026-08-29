"""
Stage 1+2 funnel: find every call in the portal whose note contains genuine
authority language. Output is the READING queue, not a finding.
"""
import json, os, re, time, urllib.request, socket, datetime
socket.setdefaulttimeout(60)
PAT = os.environ['PAT']
H = {'Authorization': 'Bearer ' + PAT, 'Content-Type': 'application/json'}
POOL, DONE = "dm_funnel_pool.json", "dm_funnel_done.json"
pool = json.load(open(POOL)) if os.path.exists(POOL) else {}
done = set(json.load(open(DONE))) if os.path.exists(DONE) else set()

def srch(b):
    for i in range(8):
        try:
            r = urllib.request.Request("https://api.hubapi.com/crm/v3/objects/calls/search",
                                       data=json.dumps(b).encode(), headers=H, method='POST')
            return json.load(urllib.request.urlopen(r))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            return None
        except Exception: time.sleep(2*(i+1))
    return None

def ms(d): return str(int(datetime.datetime(d.year,d.month,d.day).timestamp()*1000))

# terms that only appear when someone discusses who decides
AUTHORITY = ["*decision maker*","*decision-maker*","*decides*","*signs off*","*sign off*",
             "*in charge of*","*handles the*","*responsible for*","*not my area*",
             "*need to speak*","*need to talk*","*have to go through*","*go through*",
             "*referred me to*","*refer you to*","*transferred me to*","*put me through*",
             "*is the owner*","*is the president*","*is the CFO*","*is the director*",
             "*not the right person*","*not in charge*","*wrong person*","*who handles*"]

PROPS = ["hs_call_body","hs_call_summary","hs_call_title","hs_timestamp"]
LO, HI = datetime.date(2010,1,1), datetime.date(2027,1,1)

def page(prop, term, lo, hi):
    f = [{"propertyName":prop,"operator":"CONTAINS_TOKEN","value":term},
         {"propertyName":"hs_timestamp","operator":"GTE","value":ms(lo)},
         {"propertyName":"hs_timestamp","operator":"LT","value":ms(hi)}]
    after=None; n=0
    while True:
        b={"limit":200,"properties":PROPS,"filterGroups":[{"filters":f}]}
        if after: b["after"]=after
        d=srch(b)
        if not d: break
        rs=d.get("results",[])
        if not rs: break
        for r in rs: pool.setdefault(r["id"], r)
        n+=len(rs)
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after or n>=9800: break
        time.sleep(0.03)
    return n

def count(prop, term, lo, hi):
    f = [{"propertyName":prop,"operator":"CONTAINS_TOKEN","value":term},
         {"propertyName":"hs_timestamp","operator":"GTE","value":ms(lo)},
         {"propertyName":"hs_timestamp","operator":"LT","value":ms(hi)}]
    d = srch({"limit":1,"filterGroups":[{"filters":f}]})
    return (d or {}).get("total",0)

def windows(prop, term, lo, hi, depth=0):
    c = count(prop, term, lo, hi)
    if c == 0: return 0
    if c < 9000 or depth >= 8: return page(prop, term, lo, hi)
    m = lo + (hi-lo)/2; m = datetime.date(m.year, m.month, 1)
    if m <= lo or m >= hi: return page(prop, term, lo, hi)
    return windows(prop,term,lo,m,depth+1) + windows(prop,term,m,hi,depth+1)

for prop in ["hs_call_body","hs_call_summary"]:
    for t in AUTHORITY:
        k = "%s|%s" % (prop, t)
        if k in done: continue
        got = windows(prop, t, LO, HI)
        done.add(k)
        print("  %-9s %-24s +%-6d pool=%d" % (prop.split('_')[-1], t.strip('*')[:24], got, len(pool)), flush=True)
        json.dump(pool, open(POOL,"w")); json.dump(sorted(done), open(DONE,"w"))

print("\nAUTHORITY-LANGUAGE POOL: %s" % format(len(pool), ","), flush=True)

# ── now apply the conversation filter ────────────────────────────────
def clean(t): return re.sub(r'\s+',' ', re.sub('<[^>]+>',' ', t or '')).strip()
DEAD = ["no live person","speaker 1","automated greeting","welcome message","left a message",
        "left a voicemail","leave a message","standard greeting","not in service","mailbox is full",
        "office was closed","office is closed","unable to answer","attempted to reach",
        "attempted to contact","could not be completed","unsuccessful","insufficient information",
        "no further details","enter some information","directing callers","press 1","did not answer",
        "no answer","call failure"]
SPOKE = re.compile(r"spoke (?:with|to)|s/w\b|talked to|\btt\b|\bsaid\b|advised|mentioned|"
                   r"informed me|told me|\bPOC\b|connected w", re.I)
AUTH = re.compile(r"decision.?maker|decides|signs? off|in charge of|handles the|responsible for|"
                  r"need to (?:speak|talk)|have to go through|referred? (?:me )?to|transferred (?:me )?to|"
                  r"put me through|is the (?:owner|president|CFO|director)|not the right person|"
                  r"not in charge|not my area|wrong person|who handles", re.I)

queue = []
for cid, r in pool.items():
    p = r["properties"]
    body, summ = clean(p.get("hs_call_body")), clean(p.get("hs_call_summary"))
    txt = (body + " || " + summ).strip(" |") if summ else body
    low = txt.lower()
    if len(txt) < 120: continue
    if any(k in low for k in DEAD): continue
    if not SPOKE.search(txt): continue
    if not AUTH.search(txt): continue
    queue.append({"call": cid, "ts": (p.get("hs_timestamp") or "")[:10], "text": txt[:900]})

queue.sort(key=lambda x: x["ts"], reverse=True)
json.dump(queue, open("dm_reading_queue.json","w"))
print("\n" + "="*60)
print("READING QUEUE: %s calls" % format(len(queue), ","))
print("  (authority language + confirmed conversation + not a dial attempt)")
print("="*60)
