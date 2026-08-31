"""Prove no PetTechLabs or VetriScience asset was modified by this project.

Claiming "we didn't touch it" is worth nothing without the timestamps. Every
change in this migration was made after the project started, so anything on
another brand whose updatedAt predates that date cannot have been touched by
us -- and anything that does not is listed by name for inspection.
"""
import json,collections,datetime
exec(open('/tmp/hs.py').read())

START="2026-08-07"   # first day any tool in this project wrote to the portal
OTHER=("pettechlabs","vetriscience")

def page(path):
    out=[];q={"limit":100};after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

def brand(rec):
    hay=((rec.get("url") or "")+" "+(rec.get("name") or "")+" "
         +(rec.get("slug") or "")).lower()
    for b in OTHER:
        if b in hay: return b
    return None

report={}
for label,path,stamp in [
    ("site pages","/cms/v3/pages/site-pages","updatedAt"),
    ("landing pages","/cms/v3/pages/landing-pages","updatedAt"),
    ("blog posts","/cms/v3/blogs/posts","updated"),
    ("emails","/marketing/v3/emails/","updatedAt"),
    ("forms","/marketing/v3/forms/","updatedAt"),
]:
    recs=page(path)
    mine=[r for r in recs if brand(r)]
    touched=[r for r in mine if (r.get(stamp) or r.get("updatedAt") or "")[:10]>=START]
    report[label]={"total":len(recs),"other_brand":len(mine),
        "modified_since_"+START:[{"name":r.get("name"),"brand":brand(r),
            "at":(r.get(stamp) or r.get("updatedAt"))} for r in touched]}
    print(f"{label:15s} {len(recs):>5} total | {len(mine):>4} PetTech/VetriScience "
          f"| {len(touched)} modified since {START}")
    for t in touched[:10]:
        print(f"    !! {t.get('name')}  {(t.get(stamp) or t.get('updatedAt'))}")

# workflows carry no brand in the name reliably; check by updatedAt across all
flows=page("/automation/v4/flows")
recent=[f for f in flows if (f.get("updatedAt") or "")[:10]>=START]
report["workflows"]={"total":len(flows),
    "modified_since_"+START:[{"name":f.get("name"),"at":f.get("updatedAt"),
        "enabled":f.get("isEnabled")} for f in recent]}
print(f"{'workflows':15s} {len(flows):>5} total | {len(recent)} modified since {START}")
for f in recent:
    tag="PRAXERA" if (f.get("name") or "").lower().startswith("praxera") else "!! NOT OURS"
    print(f"    {tag:12s} {f.get('name')[:62]}  enabled={f.get('isEnabled')}")

json.dump(report,open("reference/untouched.json","w"),indent=1)
