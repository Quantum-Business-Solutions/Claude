"""Look for this project's fingerprints inside PetTechLabs and VetriScience.

The author id on a record proves nothing here -- the PAT is bound to Marko, so
every write from this project and every write Marko or another QBS automation
makes carry the same id. What DOES separate them is content: if this migration
had reached another brand, the word Praxera would be in it.
"""
import json,re,collections
exec(open('/tmp/hs.py').read())

def page(path):
    out=[];q={"limit":100};after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

MINE=re.compile(r"praxera",re.I)
OTHER=re.compile(r"pettechlabs|vetriscience|petnaturals|^PTL[: ]|^VS[: ]",re.I)
def other(r):
    return bool(OTHER.search((r.get("url") or "")+" "+(r.get("name") or "")
                             +" "+(r.get("slug") or "")))

hits=[];counts={}
for label,path,draft in [
    ("site pages","/cms/v3/pages/site-pages","/cms/v3/pages/site-pages/{id}/draft"),
    ("landing pages","/cms/v3/pages/landing-pages","/cms/v3/pages/landing-pages/{id}/draft"),
    ("blog posts","/cms/v3/blogs/posts","/cms/v3/blogs/posts/{id}/draft"),
    ("emails","/marketing/v3/emails/",None),
    ("forms","/marketing/v3/forms/",None),
]:
    recs=[r for r in page(path) if other(r)]
    n=0
    for r in recs:
        blob=json.dumps(r)
        # the draft can differ from the published record, so check both
        if draft:
            try: blob+=json.dumps(call("GET",draft.format(id=r["id"])))
            except Exception: pass
        if MINE.search(blob):
            hits.append({"kind":label,"name":r.get("name"),"url":r.get("url")}); n+=1
    counts[label]={"checked":len(recs),"containing_praxera":n}
    print(f"{label:15s} {len(recs):>4} PetTech/VetriScience/PetNaturals records checked "
          f"(published + draft) | {n} mentioning Praxera")

flows=[f for f in page("/automation/v4/flows")
       if other({"name":f.get("name")})]
n=0
for f in flows:
    d=call("GET",f"/automation/v4/flows/{f['id']}")
    if MINE.search(json.dumps(d)):
        hits.append({"kind":"workflow","name":f.get("name")}); n+=1
counts["workflows"]={"checked":len(flows),"containing_praxera":n}
print(f"{'workflows':15s} {len(flows):>4} PetTech/VetriScience records checked | "
      f"{n} mentioning Praxera")

json.dump({"counts":counts,"hits":hits},open("reference/pettech_clean.json","w"),indent=1)
print()
print("TOTAL other-brand assets containing 'Praxera':",len(hits))
for h in hits[:20]: print("  !!",h)
