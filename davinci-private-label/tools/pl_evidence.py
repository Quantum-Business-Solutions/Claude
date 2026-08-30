"""Re-check every "this is private label" call, and record why.

The first pass matched a token anywhere in the email JSON, which found 394
emails against Patrick's 183. A token is not evidence: "private-label" also
appears in image filenames, CSS classes and campaign tags on emails that have
nothing to do with the brand. So this pass separates two very different claims:

  LINK   an <a href> actually points at a private-label URL. This is Patrick's
         definition, it is what breaks on migration, and it is quotable.
  TOKEN  the string appears somewhere else in the payload. Worth listing, never
         worth acting on without a human reading the context line.

Every row carries the matched string and where it was found, so any single
classification can be argued with.
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

TOKEN=re.compile(r"(private-label|private-labeling|privatelabel|private_label|praxera|pl-demo)",re.I)
# hrefs survive JSON-escaping, so allow the backslash form
HREF=re.compile(r'href=\\{0,2}"([^"\\]+)',re.I)
BARE=re.compile(r'https?://[^"\'\\ )]+')
# a PL destination is the page itself, not a mention of the phrase
PL_URL=re.compile(r"(blog\.davincilabs\.com/private-label/"
                  r"|info\.davincilabs\.com/[^\"']*(private-label|private-labeling|pl-demo)"
                  r"|www\.davincilabs\.com/private-label"
                  r"|praxerasupplements\.com"
                  r"|hs-sites\.com/[^\"']*private-label)",re.I)
# hubspot rewrites destinations behind click trackers; those hide the target
TRACKER=re.compile(r"(hs-sites|hubspotlinks|/e2t/|t\.hubspotemail|ct\.sendgrid)",re.I)

def classify(payload):
    """Return (link_hits, token_hits) for one asset's serialized payload."""
    urls=set(HREF.findall(payload))|set(BARE.findall(payload))
    links=sorted({u[:200] for u in urls if PL_URL.search(u)})
    tokens=[]
    if not links:
        for m in TOKEN.finditer(payload):
            a=max(0,m.start()-70); b=min(len(payload),m.end()+70)
            tokens.append(payload[a:b].replace("\\n"," ").replace("\\","")[:170])
            if len(tokens)>=3: break
    trackers=sorted({u[:120] for u in urls if TRACKER.search(u)})[:3]
    return links,tokens,trackers

def main():
    scan=json.load(open("reference/pl_dependency_scan.json"))
    ids=scan["pl_emails"]; names=scan["email_names"]
    print(f"re-checking {len(ids)} candidate emails\n",flush=True)
    def one(eid):
        try:
            d=get(f"/marketing/v3/emails/{eid}?includeStats=false")
        except Exception as e:
            return {"id":eid,"error":str(e)}
        s=json.dumps(d.get("content",{}))+json.dumps(d.get("webversion",{}))
        links,tokens,tr=classify(s)
        return {"id":eid,"name":names.get(eid,{}).get("name",""),
                "state":names.get(eid,{}).get("state",""),
                "verdict":"LINK" if links else ("TOKEN" if tokens else "NONE"),
                "pl_urls":links[:8],"token_context":tokens,"trackers":tr}
    out=[]
    with cf.ThreadPoolExecutor(8) as ex:
        for n,r in enumerate(ex.map(one,ids),1):
            out.append(r)
            if n%100==0: print(f"  {n}/{len(ids)}",flush=True)
    c=collections.Counter(r.get("verdict","ERR") for r in out)
    print("\nVERDICTS:",dict(c))
    json.dump(out,open("reference/email_evidence.json","w"),indent=1)
    link=[r for r in out if r.get("verdict")=="LINK"]
    tgt=collections.Counter(u for r in link for u in r["pl_urls"])
    print(f"\nEMAILS WITH A REAL LINK TO A PL PAGE: {len(link)}")
    print("\nMOST-LINKED PL DESTINATIONS:")
    for u,n in tgt.most_common(20): print(f"  {n:3}x  {u[:110]}")
    tok=[r for r in out if r.get("verdict")=="TOKEN"]
    print(f"\nTOKEN-ONLY (needs a human read, not a migration action): {len(tok)}")
    for r in tok[:12]:
        print(f"   {r['name'][:58]:60} :: {(r['token_context'] or [''])[0][:100]}")

if __name__=="__main__": main()
