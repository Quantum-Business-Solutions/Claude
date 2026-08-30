"""Find images on the Praxera pages that still show DaVinci branding.

A DaVinci-labelled bottle on a Praxera page is worse than a stray text mention:
copy gets proofread, product photography does not, and a client will spot it
instantly. Filenames are the first filter but they lie in both directions -- a
file called shutterstock_1565452774.jpg can still be a shot of DaVinci bottles,
and a file called davinci-banner.jpg might be a background with no product in it.

So this reports every distinct image with the pages it appears on, sorted by
reach, and flags the ones whose name or path implicates the old brand. The visual
check on the flagged set is a human step -- or a follow-up render.
"""
import json,os,re,time,urllib.request,urllib.error,collections
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

IMG=re.compile(r'https?://[^"\\\s)]+?\.(?:png|jpe?g|webp|gif|svg)',re.I)
# names that implicate the old brand, or product shots that probably carry a label
SUSPECT=re.compile(r"(davinci|da-vinci|dv[-_]|dvl|bottle|label|product|packag|jar|capsule|"
                   r"softgel|tablet|powder|supplement|prexera|praxera)",re.I)
BRAND=re.compile(r"(davinci|da-vinci|\bdv\b|dvl)",re.I)

def main():
    idx=json.load(open("reference/page_index.json"))
    pages=idx["production"]
    where=collections.defaultdict(set)
    def scan(p):
        d=get(f"/cms/v3/pages/site-pages/{p['id']}/draft")
        if not d: return p["slug"],set()
        return p["slug"], set(IMG.findall(json.dumps(d)))
    with cf.ThreadPoolExecutor(6) as ex:
        for slug,urls in ex.map(scan,pages):
            for u in urls: where[u].add(slug)

    rows=[]
    for u,slugs in where.items():
        name=u.split("/")[-1].split("?")[0]
        rows.append({"url":u,"name":name,"pages":sorted(slugs),"n":len(slugs),
                     "brand_in_name":bool(BRAND.search(u)),
                     "suspect":bool(SUSPECT.search(u))})
    rows.sort(key=lambda r:(-r["n"],r["name"]))
    json.dump(rows,open("reference/image_audit.json","w"),indent=1)

    icons=[r for r in rows if "/Praxera/" in r["url"] and r["url"].endswith(".png")]
    photos=[r for r in rows if r not in icons]
    print(f"distinct images across {len(pages)} pages : {len(rows)}")
    print(f"  Praxera icon set                       : {len(icons)}")
    print(f"  everything else (photos, logos, art)   : {len(photos)}")
    brand=[r for r in photos if r["brand_in_name"]]
    print(f"  DaVinci named in the file path         : {len(brand)}")
    print("\n=== DAVINCI IN THE PATH ===")
    for r in brand:
        print(f"  {r['n']:2} page(s)  {r['url'][:104]}")
        print(f"              {', '.join(r['pages'][:4])}{' …' if r['n']>4 else ''}")
    print("\n=== OTHER PHOTOGRAPHY / ART, most-used first ===")
    for r in photos:
        if r["brand_in_name"]: continue
        flag="?" if r["suspect"] else " "
        print(f" {flag}{r['n']:2} page(s)  {r['url'][:100]}")

if __name__=="__main__": main()
