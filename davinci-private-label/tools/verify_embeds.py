"""Which Praxera form sits on which Praxera page.

The base record is the published one and every change in this migration was
made to the draft, so reading the list endpoint shows the site as it was
before any of this work. Only the /draft record answers the question.
"""
import json,re,collections
exec(open('/tmp/hs.py').read())

st=json.load(open("reference/current_state.json"))
pxids={f["id"]:f["name"] for f in st["praxera_forms"]}

def page(path):
    out=[];q={"limit":100};after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

pages=[x for x in page("/cms/v3/pages/site-pages")
       if "praxera" in (x.get("url") or "").lower()]

GUID=re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
rows=[];byform=collections.defaultdict(list);noform=[];foreign=[]
for p in pages:
    d=call("GET",f"/cms/v3/pages/site-pages/{p['id']}/draft")
    blob=json.dumps(d)
    mine=sorted({g for g in GUID.findall(blob) if g in pxids})
    # a form guid that is not one of ours, sitting in a form module
    others=sorted({m.group(1) for m in re.finditer(r'"form_id"\s*:\s*"([0-9a-f-]{36})"',blob)
                   if m.group(1) not in pxids}
                | {m.group(1) for m in re.finditer(r'"formId"\s*:\s*"([0-9a-f-]{36})"',blob)
                   if m.group(1) not in pxids})
    rows.append({"slug":p.get("slug"),"url":p.get("url"),
                 "state":d.get("currentState"),"praxera_forms":mine,"other_forms":others})
    for g in mine: byform[g].append(p.get("slug"))
    if not mine and not others: noform.append(p.get("slug"))
    if others: foreign.append({"slug":p.get("slug"),"ids":others})

out={"pages":rows,
     "by_form":{pxids[k]:sorted(v) for k,v in byform.items()},
     "pages_with_no_form":sorted(noform),
     "pages_with_non_praxera_form":foreign,
     "n_pages":len(pages),
     "n_pages_with_praxera_form":sum(1 for r in rows if r["praxera_forms"]),
     "n_published":sum(1 for r in rows if r["state"]=="PUBLISHED")}
json.dump(out,open("reference/form_embeds.json","w"),indent=1)
print("pages",out["n_pages"],"| with praxera form",out["n_pages_with_praxera_form"],
      "| no form at all",len(noform),"| non-praxera form",len(foreign),
      "| published",out["n_published"])
for k,v in sorted(out["by_form"].items(),key=lambda x:-len(x[1])):
    print(f"  {len(v):>3}  {k}")
if foreign:
    print("NON-PRAXERA FORMS STILL EMBEDDED:")
    for f in foreign: print("   ",f["slug"],f["ids"])
