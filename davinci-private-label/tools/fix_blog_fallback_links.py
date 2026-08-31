"""Repoint blog links that were parked on the Praxera home page.

When the blog was relinked there was no page-level pairing yet, so anything
that could not be resolved was sent to praxerasupplements.com/ as a holding
position. The pairing now exists, so some of those are recoverable: if the
DaVinci original linked to something that HAS a Praxera equivalent, the clone
should link to that equivalent, not to the home page.

Reads and writes the DRAFT only. Both body shapes are handled: the DaVinci
originals keep their body in postBody, the Praxera clones in
widgets.article_body -- reading the wrong one reports a post as clean.
"""
import json,re,collections,sys
exec(open('/tmp/hs.py').read())
APPLY="--apply" in sys.argv

def page(path):
    out=[];q={"limit":100};after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

pairs=json.load(open("reference/pairs.json"))
MAP={}
for p in pairs["pages"]:
    if p["source_url"]: MAP[p["source_url"].rstrip("/")]=p["url"]
for b in pairs["blog"]:
    if b["source_url"]:
        MAP[b["source_url"].rstrip("/")]="https://www.praxerasupplements.com/"+(b["slug"] or "")

posts=page("/cms/v3/blogs/posts")
px=[b for b in posts if "praxera" in ((b.get("url") or "")+(b.get("slug") or "")).lower()]
dvby={b.get("url","").rstrip("/"):b for b in posts}
srcof={b["slug"]:b["source_url"] for b in pairs["blog"] if b["source_url"]}
HREF=re.compile(r'href="([^"]+)"',re.I)
HOME=re.compile(r"^https?://(www\.)?praxerasupplements\.com/?$",re.I)

def links(rec):
    s=json.dumps({"w":rec.get("widgets"),"l":rec.get("layoutSections"),
                  "p":rec.get("postBody")}).replace('\\"','"')
    return [u for u in HREF.findall(s) if u.startswith("http")]

unres=collections.Counter(); plan=[]
for b in px:
    src=srcof.get(b.get("slug"))
    if not src or src.rstrip("/") not in dvby: continue
    d=call("GET",f"/cms/v3/blogs/posts/{b['id']}/draft")
    if not any(HOME.match(u) for u in links(d)): continue
    od=call("GET",f"/cms/v3/blogs/posts/{dvby[src.rstrip('/')]['id']}/draft")
    targets=[]
    for u in links(od):
        if "praxerasupplements" in u.lower(): continue
        k=u.rstrip("/")
        if k in MAP: targets.append(MAP[k])
        else:
            h=re.sub(r"^https?://","",u)
            unres["/".join(h.split("/")[:3])]+=1
    if targets: plan.append({"id":b["id"],"slug":b.get("slug"),"targets":targets})

nfix=sum(len(p["targets"]) for p in plan)
print(f"posts with a recoverable home-page link : {len(plan)}")
print(f"link targets recoverable                : {nfix}")
print("\nunresolvable targets the originals used (no Praxera equivalent):")
for k,v in unres.most_common(14): print(f"  x{v:<3} {k}")

if not APPLY:
    print("\n(dry run — pass --apply to write)"); sys.exit()

# Replace ONE home-page href per recoverable target, in document order, so a
# post with five parked links and two recoverable targets fixes two and leaves
# the rest parked rather than pointing all five at the first target.
done=0
for p in plan:
    d=call("GET",f"/cms/v3/blogs/posts/{p['id']}/draft")
    w=json.dumps(d.get("widgets") or {})
    before=w
    for t in p["targets"]:
        m=re.search(r'href=\\"https?://(?:www\.)?praxerasupplements\.com/?\\"',w)
        if not m: break
        w=w[:m.start()]+'href=\\"'+t+'\\"'+w[m.end():]
        done+=1
    if w==before: continue
    call("PATCH",f"/cms/v3/blogs/posts/{p['id']}/draft",{"widgets":json.loads(w)})
    print(f"  {p['slug'][:60]}  {len(p['targets'])} link(s) repointed")
print(f"\nrepointed {done} links across {len(plan)} posts (drafts only)")
