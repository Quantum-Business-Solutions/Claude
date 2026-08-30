"""Which workflow emails the two Praxera templates can actually carry.

"How many could be cloned" is the wrong count on its own. A nurture email written
as a plain note from a named rep does not fit a newsletter template, and forcing
it into one changes the voice that made it work. So this sorts the workflow
emails by the shape they already are -- how many images, how many links, whether
there is a hero, how long the body runs -- and matches each to the template that
fits, or reports that neither does.
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

TAG=re.compile(r"<[^>]+>")
IMG=re.compile(r"<img[^>]+>",re.I)
LINK=re.compile(r"<a\s[^>]*href",re.I)
BTN=re.compile(r"(background(-color)?\s*:\s*#|class=\"[^\"]*button|hs-cta)",re.I)
SIG=re.compile(r"\b(Danielle|Paul|Hannah|Luke|Patricia|Ronald)\b")

def shape(d):
    c=d.get("content") or {}
    blob=json.dumps(c)
    text=TAG.sub(" ",blob)
    words=len(re.findall(r"[A-Za-z']{3,}",text))
    return {"mode":d.get("emailTemplateMode"),
            "tpl":(c.get("templatePath") or "")[:52],
            "imgs":len(IMG.findall(blob)),
            "links":len(LINK.findall(blob)),
            "btns":len(BTN.findall(blob)),
            "words":words,
            "rep":bool(SIG.search(d.get("name","")))}

def fit(s):
    """Match the email to the template whose structure it already has."""
    if s["imgs"]>=3 and s["links"]>=5:      return "Pulse (newsletter)"
    if s["imgs"]>=1 and s["links"]<=4 and s["words"]>=60: return "Product / Category"
    if s["rep"] or (s["imgs"]<=1 and s["words"]<250):     return "needs a rep-note template"
    return "needs review"

def main():
    M=json.load(open("reference/merged_audit.json"))
    wf=M["workflows"]
    ids={}
    for w in wf:
        for eid,nm in w["verified_emails"]:
            ids.setdefault(eid,{"name":nm,"live":False,"wfs":set()})
            ids[eid]["wfs"].add(w["name"])
            if w["live"]: ids[eid]["live"]=True
    print(f"distinct emails sent by a PL workflow: {len(ids)}")
    print(f"  of those, sent by a LIVE workflow  : {sum(1 for v in ids.values() if v['live'])}\n")

    def one(item):
        eid,meta=item
        d=get(f"/marketing/v3/emails/{eid}?includeStats=false")
        if not d: return None
        s=shape(d)
        return {"id":eid,"name":d.get("name",""),"state":d.get("state",""),
                "live":meta["live"],"wfs":sorted(meta["wfs"])[:2],**s,"fit":fit(s)}
    with cf.ThreadPoolExecutor(8) as ex:
        rows=[r for r in ex.map(one,ids.items()) if r]
    json.dump(rows,open("reference/email_template_fit.json","w"),indent=1)

    live=[r for r in rows if r["live"]]
    print("TEMPLATE FIT  (emails sent by a LIVE workflow)")
    c=collections.Counter(r["fit"] for r in live)
    for k,n in c.most_common(): print(f"   {n:>3}  {k}")
    print("\nTEMPLATE FIT  (all workflow emails, live or off)")
    c2=collections.Counter(r["fit"] for r in rows)
    for k,n in c2.most_common(): print(f"   {n:>3}  {k}")
    print("\nBUILD MODE:",dict(collections.Counter(r["mode"] for r in rows)))
    print("\nSHAPE, live-workflow emails")
    for r in sorted(live,key=lambda x:-x["imgs"])[:14]:
        print(f"   img={r['imgs']:>2} link={r['links']:>2} words={r['words']:>4}  "
              f"{r['fit'][:22]:24} {r['name'][:46]}")

if __name__=="__main__": main()
