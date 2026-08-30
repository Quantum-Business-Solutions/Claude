"""Repoint the blog drafts' internal links at their Praxera equivalents.

Only rewrites a link when a Praxera page or post actually exists to receive it.
The 57 DaVinci retail product URLs are deliberately left alone: Praxera does not
sell branded SKUs, so there is no page for /collagen-bright-153.html to become,
and silently pointing it at a category page would invent a claim nobody approved.
Those come back as a report instead.

Writes go to the draft buffer of posts that are already drafts on the Praxera
domain. Nothing published is touched. Every post is re-read after the write and
compared field by field, and the run aborts if anything but the body changed.
"""
import json,os,re,sys,time,urllib.request,urllib.error,collections

T=os.environ["TOKEN"]
def call(m,u,body=None,tr=4):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    d=json.dumps(body).encode() if body is not None else None
    for i in range(tr):
        try:
            r=urllib.request.Request(u,data=d,method=m,
                headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"})
            return json.load(urllib.request.urlopen(r,timeout=60))
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            if e.code not in (429,502,503,504) or i==tr-1:
                print("   HTTP",e.code,e.read().decode()[:300]); return None
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

def slug(u):
    u=(u or "").split("?")[0].split("#")[0].rstrip("/")
    return u.split("/private-label/")[-1] if "/private-label/" in u else u.split("/")[-1]

def build_map():
    b=json.load(open("reference/blog_namespace_split.json"))
    px={slug(p["url"]):p["url"] for p in b["pl_group"]
        if "praxerasupplements.com" in (p["url"] or "")}
    um=json.load(open("reference/url_map.json"))
    m={}
    for r in um:
        if r.get("new"): m[r["old"].split("?")[0]]=r["new"]
    return px,m

# The body does NOT live in postBody. HubSpot's newer blog editor keeps it in
# widgets.article_body.body.content and mirrors it into layoutSections, so a
# rewrite keyed on postBody finds nothing and reports a clean run -- which is
# exactly what the first version of this did.
FIELDS=("widgets","layoutSections","postBody","postSummary","metaDescription")
DV=re.compile(r"https?://(?:www\.|blog\.|info\.)?davincilabs\.com[^\"'<>\s\\)]*",re.I)

def target(url,px,um):
    base=url.split("?")[0].split("#")[0]
    if base in um: return um[base]
    s=slug(base)
    if s in px: return px[s]
    return None

def main():
    go="--go" in sys.argv
    px,um=build_map()
    posts=[];u="/cms/v3/blogs/posts?limit=100&archived=false"
    while u:
        r=call("GET",u); posts+=r["results"]
        u=r.get("paging",{}).get("next",{}).get("link")
    drafts=[p for p in posts if "praxerasupplements.com" in (p.get("url") or "")
            and p.get("state")=="DRAFT"]
    print(f"Praxera blog drafts: {len(drafts)}   mode: {'APPLY' if go else 'DRY RUN'}\n")

    changed=skipped=0
    left=collections.Counter()
    for p in drafts:
        body={}
        hits=0
        for f in FIELDS:
            v=p.get(f)
            if v in (None,"",{},[]): continue
            blob=json.dumps(v)
            new=blob
            for url in sorted(set(DV.findall(blob)),key=len,reverse=True):
                t=target(url,px,um)
                if t:
                    n=new.count(url); new=new.replace(url,t); hits+=n
                else: left[url.split("?")[0]]+=1
            if new!=blob: body[f]=json.loads(new)
        if not body:
            skipped+=1; continue
        changed+=1
        print(f"  {p['name'][:58]:60} {hits} link(s) in {len(body)} field(s)")
        if not go: continue
        before={k:v for k,v in p.items() if k not in ("updated","updatedById","publishDate")}
        r=call("PATCH",f"/cms/v3/blogs/posts/{p['id']}/draft",body)
        if r is None: print("     WRITE FAILED"); continue
        back=call("GET",f"/cms/v3/blogs/posts/{p['id']}/draft")
        stray=[k for k in before
               if k in back and k not in body and k not in
               ("updated","updatedById","publishDate","currentState","widgets")
               and json.dumps(back[k])!=json.dumps(before[k])]
        if stray:
            print(f"     !! UNEXPECTED FIELD CHANGE: {stray} -- stopping"); sys.exit(1)
        if back.get("state")!="DRAFT":
            print("     !! state left DRAFT -- stopping"); sys.exit(1)

    print(f"\nposts rewritten : {changed}")
    print(f"posts untouched : {skipped}")
    print(f"\nLINKS LEFT ALONE (no Praxera equivalent): "
          f"{len(left)} targets, {sum(left.values())} links")
    for u_,n in left.most_common(20): print(f"   {n:>3}x  {u_[:88]}")
    json.dump({k:v for k,v in left.items()},
              open("reference/blog_links_unresolved.json","w"),indent=1)

if __name__=="__main__": main()
