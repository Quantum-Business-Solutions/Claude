"""The cutover redirect plan: which DaVinci URL points at which Praxera URL.

Every DaVinci private-label page the Praxera set replaces becomes a redirect to
its replacement at cutover, so the pairing is not just provenance -- it is the
redirect table. That makes two gaps worth as much as the matches:

  orphan target  a Praxera page with no DaVinci original. Nothing redirects to
                 it, so it only gets traffic from new links.
  orphan source  a DaVinci private-label page with no Praxera equivalent. It
                 has nowhere to redirect to, and at cutover it either keeps
                 serving DaVinci content or 404s. These need a decision.
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

pairs=json.load(open("reference/pairs.json"))

# --- what the Praxera set covers ------------------------------------------
rows=[]
for p in pairs["pages"]:
    if p["source_url"]:
        rows.append({"kind":"page","from":p["source_url"],"to":p["url"],
                     "from_state":p["source_state"]})
for b in pairs["blog"]:
    if b["source_url"]:
        rows.append({"kind":"blog","from":b["source_url"],
                     "to":"https://www.praxerasupplements.com/"+(b["slug"] or ""),
                     "from_state":b["source_state"]})
covered={r["from"] for r in rows}

# --- every DaVinci private-label asset, so the uncovered ones show up ------
# Namespace, not topic: the same rule the whole audit uses.
PL=re.compile(r"(davincilabs\.com/(en/)?pl-demo|davincilabs\.com/private-label"
              r"|davincilabs\.com/private-labeling"
              r"|blog\.davincilabs\.com/private-label/)",re.I)
# -v3 is Barb's working set and -v1ref the V1 reference replicas: both are
# unpublished working copies, not URLs anyone can follow to a dead end.
IGNORE=re.compile(r"-v3$|-v1ref$|pl-module-library|pl-global-blocks|private-label-test",re.I)

src=[]
for p in page("/cms/v3/pages/site-pages"):
    u=p.get("url") or ""
    if PL.search(u): src.append({"kind":"page","url":u,"name":p.get("name"),
        "slug":p.get("slug"),"state":p.get("currentState")})
for p in page("/cms/v3/pages/landing-pages"):
    u=p.get("url") or ""
    if PL.search(u): src.append({"kind":"landing page","url":u,"name":p.get("name"),
        "slug":p.get("slug"),"state":p.get("currentState")})
for b in page("/cms/v3/blogs/posts"):
    u=b.get("url") or ""
    if PL.search(u): src.append({"kind":"blog","url":u,"name":b.get("name"),
        "slug":b.get("slug"),"state":b.get("currentState")})

orphan_src=[s for s in src if s["url"] not in covered]
# a -v3 page is Barb's working copy, not a public URL anyone would follow
orphan_src_real=[s for s in orphan_src if not IGNORE.search(s["slug"] or s["url"])]
orphan_tgt=([{"kind":"page","to":p["url"],"slug":p["slug"]}
             for p in pairs["pages"] if not p["source_url"]]
          + [{"kind":"blog","to":b["slug"],"slug":b["slug"]}
             for b in pairs["blog"] if not b["source_url"]])

out={"redirects":rows,"orphan_sources":orphan_src_real,
     "orphan_sources_ignored":[s["slug"] for s in orphan_src if s not in orphan_src_real],
     "orphan_targets":orphan_tgt,
     "counts":{"redirects":len(rows),
               "by_kind":dict(collections.Counter(r["kind"] for r in rows)),
               "davinci_pl_assets_found":len(src),
               "orphan_sources":len(orphan_src_real),
               "orphan_targets":len(orphan_tgt)}}
json.dump(out,open("reference/redirects.json","w"),indent=1)

print(f"redirect pairs      : {len(rows)}  {out['counts']['by_kind']}")
print(f"DaVinci PL assets   : {len(src)} found in the private-label namespace")
print(f"  no Praxera target : {len(orphan_src_real)}  <- need a decision")
print(f"  working copies    : {len(orphan_src)-len(orphan_src_real)} (-v3 / module library, ignored)")
print(f"Praxera, nothing redirects to it: {len(orphan_tgt)}")
print()
by=collections.Counter(s["kind"] for s in orphan_src_real)
print("orphan sources by kind:",dict(by))
for s in orphan_src_real[:25]:
    print(f"   {s['kind']:12s} {s['state']:>9}  {s['url']}")
if len(orphan_src_real)>25: print(f"   … {len(orphan_src_real)-25} more")
print()
print("orphan targets:")
for t in orphan_tgt: print("   ",t["kind"],t["slug"] or "(home)")
