"""Pair each Praxera asset with the DaVinci asset it replaces.

The ledger's whole job is the before/after column, so the pairing has to come
from the portal rather than from a naming convention alone -- a clone whose
original was renamed or deleted has to show up as unpaired, not as a silent gap.
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

pairs={}

# --- pages: praxera slug <-> the pl-demo page with the same tail -----------
sp=page("/cms/v3/pages/site-pages")
px={p["slug"]:p for p in sp if "praxera" in (p.get("url") or "").lower()}
dv={p["slug"]:p for p in sp if "praxera" not in (p.get("url") or "").lower()}
def tail(s):
    """Reduce a slug to the part both sides share.

    The DaVinci originals are the pl-demo-*-v3 set: language and section
    prefixes on one side, a pl-demo- prefix and a -v3 suffix on the other.
    Strip all four and 'en/pl-demo-heart-health-v3' meets 'heart-health'.
    """
    s=(s or "").strip("/")
    s=re.sub(r"^(en|alp|learning)/","",s)
    s=re.sub(r"^pl-demo-","",s)
    s=re.sub(r"-v3$","",s)
    return s
dv_by_tail=collections.defaultdict(list)
for s,p in dv.items():
    t=tail(s)
    dv_by_tail[t].append(p)
rows=[]
for s,p in sorted(px.items()):
    cand=dv_by_tail.get(tail(s),[])
    cand=sorted(cand,key=lambda x:"info.davincilabs" not in (x.get("url") or ""))
    src=cand[0] if cand else None
    rows.append({"slug":s,"name":p.get("name"),"url":p.get("url"),
        "source_name":src.get("name") if src else None,
        "source_url":src.get("url") if src else None,
        "source_state":src.get("currentState") if src else None})
pairs["pages"]=rows
print("pages paired:",sum(1 for r in rows if r["source_name"]),"of",len(rows))

# --- blog ------------------------------------------------------------------
bp=page("/cms/v3/blogs/posts")
pxb=[b for b in bp if "praxera" in ((b.get("url") or "")+(b.get("slug") or "")).lower()]
# Praxera posts sit under blog/ or blog/dev-blog/, the originals under
# private-label/ or en/. Only the final path segment is common to both.
leaf=lambda s:(s or "").rstrip("/").split("/")[-1]
dvb={}
for b in bp:
    if b in pxb: continue
    dvb.setdefault(leaf(b.get("slug")),b)
rows=[]
for b in sorted(pxb,key=lambda x:x.get("slug") or ""):
    src=dvb.get(leaf(b.get("slug")))
    rows.append({"slug":b.get("slug"),"name":b.get("name"),
        "source_name":src.get("name") if src else None,
        "source_url":src.get("url") if src else None,
        "source_state":src.get("currentState") if src else None,
        "publishDate":b.get("publishDate"),"tags":len(b.get("tagIds") or [])})
pairs["blog"]=rows
print("blog paired:",sum(1 for r in rows if r["source_name"]),"of",len(rows))

# --- emails ----------------------------------------------------------------
# The clone name is not just the original with a prefix: the rename swapped the
# brand inside the name too, so "DV WF: ...With_DaVinci" became
# "Praxera - WF: ...With_Praxera". Match on a key with the brand and every
# house prefix removed from both sides.
em=page("/marketing/v3/emails/")
def key(n):
    n=re.sub(r"^(Praxera|DV|DaVinci)\s*[-:]?\s*","",n.strip(),flags=re.I)
    n=re.sub(r"^(WF|LP)\s*:\s*","",n,flags=re.I)
    n=re.sub(r"da\s*vinci|davinci|praxera","",n,flags=re.I)
    return re.sub(r"[^a-z0-9]+","",n.lower())
originals={}
for e in em:
    if e["name"].strip().lower().startswith("praxera"): continue
    originals.setdefault(key(e["name"]),e)
rows=[]
for e in em:
    n=e["name"].strip()
    if not n.lower().startswith("praxera"): continue
    src=originals.get(key(n))
    rows.append({"id":e["id"],"name":n,
                 "source_name":src["name"].strip() if src else None,
                 "source_id":src["id"] if src else None,
                 "source_state":src.get("state") if src else None})
pairs["emails"]=rows
print("emails paired:",sum(1 for r in rows if r["source_name"]),"of",len(rows))

# --- workflows -------------------------------------------------------------
fl=page("/automation/v4/flows")
fbyname={}
for f in fl:
    if (f.get("name") or "").strip().lower().startswith("praxera"): continue
    fbyname.setdefault(key(f.get("name") or ""),f)
rows=[]
for f in fl:
    n=(f.get("name") or "").strip()
    if not n.lower().startswith("praxera"): continue
    src=fbyname.get(key(n))
    rows.append({"id":f["id"],"name":n,"enabled":f.get("isEnabled"),
        "source_name":(src or {}).get("name"),"source_id":(src or {}).get("id"),
        "source_enabled":(src or {}).get("isEnabled")})
pairs["workflows"]=rows
print("workflows paired:",sum(1 for r in rows if r["source_name"]),"of",len(rows))

json.dump(pairs,open("reference/pairs.json","w"),indent=1)
