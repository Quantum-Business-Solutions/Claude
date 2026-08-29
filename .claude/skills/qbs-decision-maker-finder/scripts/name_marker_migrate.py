"""Migrate hand-written markers out of contact NAME fields into real properties.

Reps had nowhere to record "this person decides", so they typed it into the name:
    firstname "Tomiko (DM)"        lastname "Leitner (DM)"
    firstname "(Retired) Nancy"    lastname "Lasky (DM) (GONE)"

NAMES ARE NEVER MODIFIED. This only reads them and writes the AI fields, so
nothing downstream breaks and the migration is repeatable.
"""
import json, os, re, time, urllib.request, collections
H={'Authorization':'Bearer '+os.environ['PAT'],'Content-Type':'application/json'}
def post(u,b):
    for i in range(6):
        try:
            r=urllib.request.Request(u,data=json.dumps(b).encode(),headers=H,method='POST')
            return json.load(urllib.request.urlopen(r))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            print("  ERR",e.code,e.read().decode()[:160]); return {}
        except Exception: time.sleep(2*(i+1))
    return {}

PROPS=["firstname","lastname","hs_buying_role","email","lifecyclestage",
       "ai__decision_maker_verdict","ai__contact_status_flag","ai__decision_maker"]
TOKENS=["*(DM)*","*(GONE)*","*(RETIRED)*","*retired*","*no longer*","*(DO NOT CALL)*",
        "*(DO NOT EMAIL)*","*DONOTCALL*","*(NO LOCAL DM)*","*(POC)*","*(left)*","*(replaced*"]

pool={}
for term in TOKENS:
    for f in ["firstname","lastname"]:
        after=None; n=0
        while True:
            b={"limit":100,"properties":PROPS,
               "filterGroups":[{"filters":[{"propertyName":f,"operator":"CONTAINS_TOKEN","value":term}]}]}
            if after: b["after"]=after
            d=post("https://api.hubapi.com/crm/v3/objects/contacts/search",b)
            rs=d.get("results",[])
            if not rs: break
            for r in rs: pool[r["id"]]=r["properties"]
            n+=len(rs)
            after=(d.get("paging") or {}).get("next",{}).get("after")
            if not after or n>=9800: break
    print("  after %-18s pool=%s"%(term.strip('*'),format(len(pool),",")),flush=True)

# verify literally - the token search matches "Do Nguyen" for "DO NOT CALL"
DM      = re.compile(r'\((?:DM|D\.M\.)\)|\bDM\s*[/)]|\(DM[ /]', re.I)
NODM    = re.compile(r'\(NO LOCAL DM\)|\(NOT DM\)|\(NOT THE DM\)', re.I)
GONE    = re.compile(r'\(GONE\)|\bno longer\b|\(left\)|\(replaced', re.I)
RETIRED = re.compile(r'\(retired\)|\bretired\b', re.I)
DNC     = re.compile(r'DO NOT CALL|DO NOT EMAIL|DONOTCALL|DO NOT CONTACT', re.I)

writes={}; skipped_existing=0
tally=collections.Counter()
for cid,p in pool.items():
    full=("%s %s"%(p.get("firstname") or "", p.get("lastname") or "")).strip()
    if not full: continue
    isdm   = bool(DM.search(full)) and not NODM.search(full)
    gone   = bool(GONE.search(full))
    ret    = bool(RETIRED.search(full))
    dnc    = bool(DNC.search(full))
    if not (isdm or gone or ret or dnc or NODM.search(full)): continue
    w={}
    # a verdict already written from READING an engagement is better evidence - never overwrite it
    if (isdm or NODM.search(full)) and not p.get("ai__decision_maker_verdict"):
        verdict = "Not the Decision Maker" if NODM.search(full) else "Decision Maker"
        w["ai__decision_maker_verdict"]=verdict
        w["ai__decision_maker_confidence"]="STATED"
        w["ai__decision_maker"]=(
            "%s [STATED] - recovered from a marker a rep hand-typed into this contact's NAME field, "
            "where nothing could filter on it. Name as stored: \"%s\". "
            "** No conversation was read for this verdict - it reflects what a rep concluded at the time "
            "and recorded the only way they could. Treat as a strong lead, not a confirmed fact."
            % (verdict, full))[:65000]
        tally[verdict]+=1
    flag=None
    if dnc:      flag="Opt-Out Requested"
    elif ret:    flag="Retired"
    elif gone:   flag="No Longer At Company"
    if flag and not p.get("ai__contact_status_flag"):
        w["ai__contact_status_flag"]=flag
        w["ai__contact_status_evidence"]=(
            "Recovered from the contact's NAME field, as stored: \"%s\". "
            "The name itself has NOT been modified." % full)[:65000]
        tally["FLAG "+flag]+=1
    if w: writes[cid]=w
    elif p.get("ai__decision_maker_verdict") or p.get("ai__contact_status_flag"): skipped_existing+=1

print()
print("pool searched            : %s"%format(len(pool),","))
print("verified markers         : %s contacts"%format(len(writes),","))
print("already had a read-based verdict, left alone: %d"%skipped_existing)
for k,v in tally.most_common(): print("   %-30s %s"%(k,format(v,",")))
json.dump(writes,open("name_marker_writes.json","w"))

items=[{"id":k,"properties":v} for k,v in writes.items()]
ok=0
for i in range(0,len(items),100):
    d=post("https://api.hubapi.com/crm/v3/objects/contacts/batch/update",{"inputs":items[i:i+100]})
    ok+=len(d.get("results",[]))
    time.sleep(0.2)
print()
print("WRITTEN TO %s CONTACT RECORDS (names untouched)"%format(ok,","))
