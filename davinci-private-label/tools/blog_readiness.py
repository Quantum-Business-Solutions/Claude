"""What the 75 cloned Praxera blog drafts still need before they can publish.

Cloning a post moves the words. It does not move anything the words point AT --
the images still load from the DaVinci file host, the CTAs still open DaVinci
forms, the internal links still resolve to blog.davincilabs.com, and the byline
still names a DaVinci author. Those are the parts a reader sees and a proofread
misses.

Reported per post so the work can be split, and per category so it can be
estimated.
"""
import json,os,re,time,urllib.request,urllib.error,collections,html
import concurrent.futures as cf

T=os.environ["TOKEN"]
def get(u,tr=4):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(
            urllib.request.Request(u,headers={"Authorization":"Bearer "+T}),timeout=60))
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            if e.code not in (429,502,503,504) or i==tr-1: raise
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

DV_WORD  = re.compile(r"da\s?vinci",re.I)
DV_LINK  = re.compile(r"https?://(?:www\.|blog\.|info\.)?davincilabs\.com[^\"'\\\s)]*",re.I)
DV_IMG   = re.compile(r"https?://[^\"'\\\s)]*davincilabs\.com[^\"'\\\s)]*?\.(?:png|jpe?g|webp|gif|svg)",re.I)
FSC      = re.compile(r"FoodScience",re.I)
MFG      = re.compile(r"\b(we manufacture|we make them|our manufacturing|we handle manufacturing|"
                      r"our facility|our plant|we produce)\b",re.I)
TM       = re.compile(r"[™®]")
CTA      = re.compile(r"hs-cta-|cta_button|hubspot\.com/cta",re.I)

def main():
    posts=[];u="/cms/v3/blogs/posts?limit=100&archived=false"
    while u:
        r=get(u); posts+=r["results"]; u=r.get("paging",{}).get("next",{}).get("link")
    px=[p for p in posts if "praxerasupplements.com" in (p.get("url") or "")]
    print(f"Praxera blog drafts: {len(px)}\n")

    rows=[]
    for p in px:
        blob=json.dumps(p)
        body=(p.get("postBody") or "")+(p.get("postSummary") or "")
        rows.append({
            "id":p["id"],"name":p.get("name",""),"slug":p.get("slug",""),
            "state":p.get("state"),
            "author":p.get("authorName") or "",
            "dv_words":len(DV_WORD.findall(body)),
            "dv_links":sorted(set(DV_LINK.findall(blob)))[:6],
            "dv_imgs":sorted(set(DV_IMG.findall(blob)))[:6],
            "fsc":len(FSC.findall(body)),
            "mfg":len(MFG.findall(body)),
            "tm":len(TM.findall(body)),
            "cta":len(CTA.findall(blob)),
            "meta":p.get("metaDescription") or "",
            "htmlTitle":p.get("htmlTitle") or "",
        })
    json.dump(rows,open("reference/blog_readiness.json","w"),indent=1)

    def n(k): return sum(1 for r in rows if (len(r[k]) if isinstance(r[k],list) else r[k]))
    print("POSTS AFFECTED, by issue")
    print(f"  images still served from davincilabs.com : {n('dv_imgs'):>3}")
    print(f"  links still pointing at davincilabs.com  : {n('dv_links'):>3}")
    print(f"  the words 'DaVinci' in the body          : {n('dv_words'):>3}")
    print(f"  HubSpot CTA modules embedded             : {n('cta'):>3}")
    print(f"  FoodScience mentioned                    : {n('fsc'):>3}")
    print(f"  first-person manufacturing claims        : {n('mfg'):>3}")
    print(f"  trademark symbols                        : {n('tm'):>3}")
    print(f"  missing meta description                 : {sum(1 for r in rows if not r['meta']):>3}")
    print(f"  missing html title                       : {sum(1 for r in rows if not r['htmlTitle']):>3}")
    au=collections.Counter(r["author"] for r in rows)
    print("\nBYLINES:")
    for a,c in au.most_common(): print(f"   {c:>3}  {a or '(none)'}")

    print("\nWORST POSTS (most DaVinci references)")
    for r in sorted(rows,key=lambda x:-(x['dv_words']+len(x['dv_links'])+len(x['dv_imgs'])))[:12]:
        print(f"   words={r['dv_words']:>2} links={len(r['dv_links'])} imgs={len(r['dv_imgs'])}  {r['name'][:62]}")

    hosts=collections.Counter()
    for r in rows:
        for i in r["dv_imgs"]: hosts[re.sub(r"^https?://([^/]+).*",r"\1",i)]+=1
        for l in r["dv_links"]: hosts[re.sub(r"^https?://([^/]+).*",r"\1",l)]+=1
    print("\nDAVINCI HOSTS REFERENCED:")
    for h,c in hosts.most_common(): print(f"   {c:>4}  {h}")

if __name__=="__main__": main()
