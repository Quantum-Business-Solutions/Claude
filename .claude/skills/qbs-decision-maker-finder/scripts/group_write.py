"""Write one hand-read determination to every record that shares it.

The legacy system stamped an account-level header onto every task for that
account, so the same sentence - "Linda POC and Trish the final decision maker" -
appears on 11 records. Read once, write to all 11.
"""
import json, os, sys, time, urllib.request
from resolver import resolve, candidates, H

PORTAL="516382"
GROUPS=json.load(open(sys.argv[1]))
lookup={g["key"]: g for g in json.load(open("noncall_dedup.json"))}
written=0; nearmiss=[]
for c in GROUPS:
    g=lookup.get(c["key"])
    if not g: print("  !! no group for key", c["key"][:50]); continue
    ids=[tuple(x) for x in g["ids"]]
    obj0, id0 = ids[0]
    cands, direct = candidates(id0, obj0)
    cid, role_state, crm_name, strength = resolve(c.get("dm"), id0, cands, obj0)
    in_hs = "Yes" if cid else ("No" if c.get("dm") else None)
    assoc=None
    for x in cands:
        if x["id"] in direct:
            p=x["properties"]; assoc=("%s %s"%(p.get("firstname") or "",p.get("lastname") or "")).strip(); break
    if c.get("dm"):
        shown=c["dm"]
        if crm_name and crm_name.lower()!=c["dm"].lower(): shown="%s (CRM: %s)"%(c["dm"],crm_name)
        head="%s [%s]"%(shown,c["conf"])
        if c.get("role"): head+=" - "+c["role"]
        head+=" - "+("IN HUBSPOT" if cid else "NOT IN HUBSPOT")
    else:
        head="No decision maker established [UNRESOLVED]"
    props={"ai__decision_maker":("%s - %s [source: a header stamped on %d engagement records at this account, "
            "most recent %s, logged against: %s] ** %s"
            %(head,c["ev"],len(ids),g["ts"],assoc or "no contact",c["why"]))[:65000],
           "ai__associated_contact_is_dm": ("Yes" if (cid and cid in direct) else
                                            ("None" if not direct else ("No" if c.get("dm") else "Unclear")))}
    if c.get("dm"):
        props["ai__decision_maker_name"]=crm_name or c["dm"]
        props["ai__decision_maker_in_hubspot"]=in_hs
        props["ai__decision_maker_buying_role"]=role_state
        if cid: props["ai__decision_maker_contact_id"]="https://app.hubspot.com/contacts/%s/contact/%s"%(PORTAL,cid)
    byobj={}
    for o,i in ids: byobj.setdefault(o,[]).append(i)
    n=0
    for o,lst in byobj.items():
        for k in range(0,len(lst),100):
            r=urllib.request.Request("https://api.hubapi.com/crm/v3/objects/%s/batch/update"%o,
                data=json.dumps({"inputs":[{"id":x,"properties":props} for x in lst[k:k+100]]}).encode(),
                headers=H,method='POST')
            try: n+=len(json.load(urllib.request.urlopen(r)).get("results",[]))
            except urllib.error.HTTPError as e: print("   ERR",o,e.read().decode()[:130])
            time.sleep(0.15)
    written+=n
    tag=("-> %s"%crm_name) if cid else ("NOT IN HUBSPOT" if c.get("dm") else "")
    print("  x%-4d %-22s %s"%(n, c.get("dm") or "(none)", tag))
    if c.get("dm") and not cid and strength==1: nearmiss.append((c["dm"], ids[0]))
print("\nengagement records written: %d"%written)
for dm,i in nearmiss: print("  NEAR MISS - check by hand: %s (%s %s)"%(dm,i[0],i[1]))
