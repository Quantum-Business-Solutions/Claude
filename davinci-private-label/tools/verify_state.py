"""Re-read the live portal and write the numbers the ledger quotes.

The ledger has three copies in three systems; the only way they stay honest is
if every number in them comes from one pass over the live portal rather than
from whichever copy was edited last.
"""
import json,re,collections
exec(open('/tmp/hs.py').read())

def page(path,q=None,key="results"):
    out=[];q=dict(q or {});q["limit"]=100;after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get(key,[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

st={}
# --- forms -------------------------------------------------------------
forms=page("/marketing/v3/forms/")
px_forms=[f for f in forms if "praxera" in f["name"].lower()]
st["forms_total"]=len(forms)
st["praxera_forms"]=[{"id":f["id"],"name":f["name"].strip()} for f in px_forms]
pxids={f["id"] for f in px_forms}

# --- site pages --------------------------------------------------------
pages=page("/cms/v3/pages/site-pages")
def is_px(p):
    u=(p.get("url") or "")+" "+(p.get("slug") or "")
    return "praxera" in u.lower()
pxp=[p for p in pages if is_px(p)]
st["site_pages_total"]=len(pages)
st["praxera_pages"]=len(pxp)
st["praxera_pages_published"]=sum(1 for p in pxp if (p.get("currentState") or p.get("state"))=="PUBLISHED")

# which Praxera form sits on which Praxera page -------------------------
embeds=collections.defaultdict(list)
noform=[]
for p in pxp:
    blob=json.dumps(p)
    hit=[fid for fid in pxids if fid in blob]
    if hit:
        for fid in hit: embeds[fid].append(p.get("slug"))
    else:
        # a page with any form at all, just not a Praxera one
        other=re.findall(r'"formId"\s*:\s*"([0-9a-f-]{36})"',blob)
        noform.append({"slug":p.get("slug"),"other_form_ids":sorted(set(other))})
st["form_embeds"]={k:sorted(v) for k,v in embeds.items()}
st["praxera_pages_without_praxera_form"]=noform

# --- blog --------------------------------------------------------------
posts=page("/cms/v3/blogs/posts")
pxb=[b for b in posts if "praxera" in ((b.get("url") or "")+(b.get("slug") or "")).lower()]
st["blog_total"]=len(posts)
st["praxera_blog"]=len(pxb)
st["praxera_blog_published"]=sum(1 for b in pxb if (b.get("currentState") or b.get("state"))=="PUBLISHED")

# --- emails ------------------------------------------------------------
emails=page("/marketing/v3/emails/",{"includeStats":"false"})
pxe=[e for e in emails if e["name"].lower().startswith("praxera") or "praxera" in e["name"].lower()]
st["emails_total"]=len(emails)
st["praxera_emails"]=len(pxe)
st["praxera_emails_not_draft"]=[e["name"] for e in pxe if e.get("state") not in ("DRAFT",None)]

# --- workflows ---------------------------------------------------------
flows=page("/automation/v4/flows")
pxw=[f for f in flows if "praxera" in (f.get("name") or "").lower()]
st["workflows_total"]=len(flows)
st["praxera_workflows"]=[{"id":f["id"],"name":f["name"],"enabled":f.get("isEnabled")} for f in pxw]
st["praxera_workflows_enabled"]=sum(1 for f in pxw if f.get("isEnabled"))

json.dump(st,open("reference/current_state.json","w"),indent=1)
for k,v in st.items():
    print(f"{k}: {v if not isinstance(v,(list,dict)) else ('%d items'%len(v))}")
