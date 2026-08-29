"""Harvest the ELAPSED-term class: notes that say how far INTO a lease a prospect is,
rather than how much is left. Same windowing as the main harvest - the 10k search cap
silently truncates without it."""
import json, os, sys, time, urllib.request, urllib.error, datetime, socket
socket.setdefaulttimeout(60)
PAT = os.environ['PAT']
OBJ, PROPS = sys.argv[1], sys.argv[2].split(",")
POOL, DONE = "el_%s_pool.json" % OBJ, "el_%s_done.json" % OBJ
pool = json.load(open(POOL)) if os.path.exists(POOL) else {}
done = set(json.load(open(DONE))) if os.path.exists(DONE) else set()

def srch(b):
    for i in range(8):
        try:
            r = urllib.request.Request("https://api.hubapi.com/crm/v3/objects/%s/search" % OBJ,
                data=json.dumps(b).encode(),
                headers={'Authorization':'Bearer '+PAT,'Content-Type':'application/json'}, method='POST')
            return json.load(urllib.request.urlopen(r))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            return None
        except Exception: time.sleep(2*(i+1))
    return None

def ms(d): return str(int(datetime.datetime(d.year,d.month,d.day).timestamp()*1000))
def F(p,t,lo,hi): return [{"propertyName":p,"operator":"CONTAINS_TOKEN","value":t},
                          {"propertyName":"hs_timestamp","operator":"GTE","value":ms(lo)},
                          {"propertyName":"hs_timestamp","operator":"LT","value":ms(hi)}]
def count(p,t,lo,hi): return (srch({"limit":1,"filterGroups":[{"filters":F(p,t,lo,hi)}]}) or {}).get("total",0)
def page(p,t,lo,hi):
    after=None; n=0
    while True:
        b={"limit":200,"properties":PROPS,"filterGroups":[{"filters":F(p,t,lo,hi)}]}
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
def windows(p,t,lo,hi,depth=0):
    c=count(p,t,lo,hi)
    if c==0: return 0
    if c<9000 or depth>=8: return page(p,t,lo,hi)
    m=lo+(hi-lo)/2; m=datetime.date(m.year,m.month,1)
    if m<=lo or m>=hi: return page(p,t,lo,hi)
    return windows(p,t,lo,m,depth+1)+windows(p,t,m,hi,depth+1)

TERMS=json.load(open("elapsed_terms.json"))
LO,HI=datetime.date(2010,1,1),datetime.date(2027,1,1)
for prop in PROPS:
    if prop=="hs_timestamp" or prop=="hs_email_direction": continue
    for t in TERMS:
        k="%s|%s"%(prop,t)
        if k in done: continue
        got=windows(prop,t,LO,HI)
        done.add(k)
        if got: print("  %-22s %-24s +%-6d pool=%d"%(prop,t.strip('*')[:24],got,len(pool)),flush=True)
        json.dump(pool,open(POOL,"w")); json.dump(sorted(done),open(DONE,"w"))
print("%s POOL: %s"%(OBJ.upper(),format(len(pool),",")),flush=True)
