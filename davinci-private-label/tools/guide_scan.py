"""Find the downloadable guides the new Praxera pages offer.

A guide is not one asset. Each one is a chain -- the file, the landing page that
gates it, the form on that page, the thank-you page, and the fulfilment email --
and the chain breaks at whichever link still points at DaVinci. So this reports
the CTA and the destination it goes to, not just "there is a guide here".
"""
import json,os,re,sys,time,urllib.request,urllib.error,collections
import concurrent.futures as cf

T=os.environ["TOKEN"]
def get(u,tr=5):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(
            urllib.request.Request(u,headers={"Authorization":"Bearer "+T}),timeout=60))
        except urllib.error.HTTPError as e:
            if e.code not in (429,502,503,504) or i==tr-1: raise
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

# A guide shows itself three ways: the word in link text, a /guide LP slug, or a
# file that is literally a PDF sitting in the file manager.
GUIDE_WORD=re.compile(r"\b(guide|ebook|e-book|whitepaper|white paper|checklist|playbook|download)\b",re.I)
HREF=re.compile(r'href=\\?"([^"\\]+)\\?"',re.I)
PDF=re.compile(r'https?://[^"\'\\ ]+\.pdf',re.I)

idx=json.load(open("reference/page_index.json"))
pages=idx["production"]

def scan(p):
    d=get(f"/cms/v3/pages/site-pages/{p['id']}/draft")
    s=json.dumps(d)
    hrefs=set(HREF.findall(s))
    pdfs=set(PDF.findall(s))
    # keep only links that look like a gated asset, not nav
    guides={h for h in hrefs if GUIDE_WORD.search(h)}
    return p["slug"], sorted(guides), sorted(pdfs)

rows=[]
with cf.ThreadPoolExecutor(5) as ex:
    for slug,g,pdf in ex.map(scan,pages):
        if g or pdf: rows.append({"slug":slug,"guide_links":g,"pdfs":pdf})

dest=collections.Counter()
for r in rows:
    for h in r["guide_links"]: dest[h]+=1
    for h in r["pdfs"]: dest[h]+=1

print(f"pages offering a guide/download: {len(rows)} of {len(pages)}\n")
print("DESTINATIONS, most-linked first:")
for h,n in dest.most_common():
    host = "davincilabs" if "davincilabs" in h else ("praxera" if "praxera" in h else "other/relative")
    print(f"  {n:3}x  [{host:16}] {h[:120]}")
json.dump({"pages":rows,"destinations":dest.most_common()},
          open("reference/guide_assets.json","w"),indent=1)
