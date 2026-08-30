"""Separate DaVinci's private-label side from DaVinci's own brand.

Not-PetTechLabs is the easy half. The hard half is that DaVinci sells supplements
under its own name to practitioners AND runs a private-label business, in one
portal, with one email list, and the phrase "private label" appears on both sides.
A blog post about private labelling published in the main DaVinci blog is not a
private-label asset just because of its subject.

So classification is by NAMESPACE, not by topic:

  PL          the asset lives at a private-label address -- the /private-label/
              blog group, an info.davincilabs.com/private-label* slug, the
              /private-labeling* main-site paths, pl-demo-*, praxerasupplements.
  PL_TOPIC    it is about private label but sits in the brand namespace. Nobody
              can decide this from a string; it is surfaced for a human.
  BRAND_LINK  a DaVinci-brand asset that merely links to a PL page once. Needs
              its URL updated at cutover, and nothing else.
"""
import json,os,re,time,urllib.request,urllib.error,collections
import concurrent.futures as cf

T=os.environ["TOKEN"]
def get(u,tr=5):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(
            urllib.request.Request(u,headers={"Authorization":"Bearer "+T}),timeout=60))
        except urllib.error.HTTPError as ex:
            if ex.code==404: return None
            if ex.code not in (429,502,503,504) or i==tr-1: raise
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

PL_NS=re.compile(r"(blog\.davincilabs\.com/private-label/"
                 r"|/private-label/"
                 r"|info\.davincilabs\.com/[^\"' ]*private-label"
                 r"|www\.davincilabs\.com/private-label"
                 r"|/private-labeling"
                 r"|\bpl-demo-"
                 r"|praxerasupplements)",re.I)
PL_TOPIC=re.compile(r"private[ -]label",re.I)

def blog_sweep():
    """Every blog post, split by whether it lives in the private-label group."""
    posts=[];u="/cms/v3/blogs/posts?limit=100&archived=false"
    while u:
        r=get(u); posts+=r["results"]
        u=r.get("paging",{}).get("next",{}).get("link")
    pl,topic=[],[]
    for p in posts:
        url=p.get("url","") or ""
        slug=p.get("slug","") or ""
        title=p.get("name","") or ""
        if PL_NS.search(url) or PL_NS.search("/"+slug):
            pl.append(p)
        elif PL_TOPIC.search(title) or PL_TOPIC.search(slug):
            topic.append(p)
    return posts,pl,topic

def main():
    posts,pl,topic=blog_sweep()
    print(f"blog posts in portal      : {len(posts)}")
    print(f"  in the /private-label/ group (PL)        : {len(pl)}")
    print(f"  PL-topic but in the brand blog (PL_TOPIC): {len(topic)}")
    print("\nPL-TOPIC POSTS SITTING OUTSIDE THE PRIVATE-LABEL BLOG")
    print("(neither audit counts these; a human decides if they move)\n")
    for p in sorted(topic,key=lambda x:x.get("name","")):
        print(f"  [{p.get('state','?'):18}] {p.get('name','')[:62]:64}")
        print(f"      {p.get('url','')[:112]}")
    json.dump({"pl_group":[{"id":p["id"],"name":p.get("name"),"url":p.get("url"),
                            "state":p.get("state")} for p in pl],
               "pl_topic_brand_namespace":[{"id":p["id"],"name":p.get("name"),
                            "url":p.get("url"),"state":p.get("state")} for p in topic]},
              open("reference/blog_namespace_split.json","w"),indent=1)

if __name__=="__main__": main()
