"""Where do the Praxera blog posts actually link?

An earlier pass repointed what it could and sent the rest to the Praxera home
page as a holding position. Now that the full pairing exists, a home-page link
can be checked against what the DaVinci original linked to: if that target has
a Praxera equivalent, the link is recoverable and should point at it.
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
# DaVinci URL -> Praxera URL, from the redirect table
MAP={}
for p in pairs["pages"]:
    if p["source_url"]: MAP[p["source_url"].rstrip("/")]=p["url"]
for b in pairs["blog"]:
    if b["source_url"]:
        MAP[b["source_url"].rstrip("/")]="https://www.praxerasupplements.com/"+(b["slug"] or "")

posts=page("/cms/v3/blogs/posts")
px=[b for b in posts if "praxera" in ((b.get("url") or "")+(b.get("slug") or "")).lower()]
dv={b["id"]:b for b in posts}
srcof={b["slug"]:b["source_url"] for b in pairs["blog"] if b["source_url"]}
dvby={b.get("url","").rstrip("/"):b for b in posts}

HREF=re.compile(r'href="([^"]+)"',re.I)
def links(rec):
    """postBody is EMPTY on these records -- the body lives in
    widgets.article_body.body.content and is mirrored into layoutSections.
    Reading postBody is how an audit reports a post as clean that is not."""
    body=json.dumps({"w":rec.get("widgets"),"l":rec.get("layoutSections"),
                     "p":rec.get("postBody")})
    body=body.replace('\\"','"')
    return [u for u in HREF.findall(body) if u.startswith("http")]

HOME=re.compile(r"^https?://(www\.)?praxerasupplements\.com/?$",re.I)
buckets=collections.Counter(); recoverable=[]; still_dv=[]
per=[]
for b in px:
    d=call("GET",f"/cms/v3/blogs/posts/{b['id']}/draft")
    ls=links(d)
    home=[u for u in ls if HOME.match(u)]
    dvl=[u for u in ls if "davincilabs" in u.lower()]
    spec=[u for u in ls if "praxerasupplements" in u.lower() and not HOME.match(u)]
    ext=[u for u in ls if "praxerasupplements" not in u.lower()
         and "davincilabs" not in u.lower()]
    buckets["home fallback"]+=len(home); buckets["davinci"]+=len(dvl)
    buckets["specific praxera"]+=len(spec); buckets["external"]+=len(ext)
    if dvl: still_dv.append({"slug":b.get("slug"),"links":dvl})
    # what did the DaVinci original link to?
    src=srcof.get(b.get("slug"))
    fixable=[]
    if home and src and src.rstrip("/") in dvby:
        o=dvby[src.rstrip("/")]
        od=call("GET",f"/cms/v3/blogs/posts/{o['id']}/draft")
        for u in links(od):
            key=u.rstrip("/")
            if key in MAP: fixable.append({"was":u,"should_be":MAP[key]})
    if fixable:
        recoverable.append({"slug":b.get("slug"),"home_links":len(home),
                            "resolvable":fixable[:6],"n_resolvable":len(fixable)})
    per.append({"slug":b.get("slug"),"home":len(home),"davinci":len(dvl),
                "specific":len(spec),"external":len(ext)})

out={"buckets":dict(buckets),"posts_with_davinci_links":still_dv,
     "recoverable":recoverable,"per_post":per}
json.dump(out,open("reference/blog_links.json","w"),indent=1)
print("LINKS ACROSS THE 75 PRAXERA POSTS")
for k,v in buckets.most_common(): print(f"  {k:20s} {v}")
print(f"\nposts still linking to davincilabs.com : {len(still_dv)}")
for s in still_dv[:6]: print("   ",s["slug"],s["links"][:2])
print(f"\nposts whose home-page links are RECOVERABLE to a specific Praxera page: {len(recoverable)}")
tot=sum(r["n_resolvable"] for r in recoverable)
print(f"  resolvable link targets found: {tot}")
for r in recoverable[:6]:
    print(f"   {r['slug'][:56]}  home:{r['home_links']}  resolvable:{r['n_resolvable']}")
    for f in r["resolvable"][:2]:
        print(f"      {f['was'][:66]}\n        -> {f['should_be'][:66]}")
