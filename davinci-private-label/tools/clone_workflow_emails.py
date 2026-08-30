"""Clone every private-label workflow email into a Praxera draft, with the
sentences that need a human marked in place.

Two rules shape this.

Nothing existing is touched. Each clone is a POST of a new email; the originals
keep their ids, their stats and their workflow bindings, which is what makes it
safe to run while the old nurtures are still sending.

And a brand swap is not a rewrite. "DaVinci handles the formulation, sourcing and
compliance" becomes true of nobody just because the noun changes -- it is also a
manufacturer claim we are not allowed to make. So the swap is applied AND the
sentence is highlighted where it sits, so whoever edits it sees the claim rather
than a clean-looking sentence that now says something false.
"""
import json,os,re,sys,time,html,urllib.request,urllib.error,collections
import concurrent.futures as cf

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
                return {"_err":e.code,"_msg":e.read().decode()[:300]}
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

BRAND=re.compile(r"DaVinci Laboratories of Vermont|DaVinci Laboratories|DaVinci Labs|"
                 r"DaVinci for Healthcare Professionals|DaVinci",re.I)
# claims we are not allowed to make in the first person, whatever the brand name is
# First-person manufacturing is the claim we are not allowed to make, however it
# is phrased. Kept deliberately broad: a false positive costs a highlight nobody
# needed, a false negative ships a claim.
CLAIM=re.compile(
    r"(handles?\s+(?:the\s+)?(?:formulation|manufactur\w*|bottling|quality)"
    r"|we\s+(?:manufacture|produce|make|formulate|bottle|blend|handle)\w*"
    r"|our\s+(?:manufactur\w*|facility|facilities|plant|production|lab|labs|"
    r"formulators?|chemists?|manufacturing\s+team)"
    r"|manufactured\s+(?:in|at|by)\s+our"
    r"|family[- ]owned\s+company"
    r"|in[- ]house\s+(?:manufactur\w*|production|formulation)"
    r"|from\s+(?:formulation|concept)\s+(?:through|to)\s+delivery"
    r"|doable\s+within\s+DSHEA"
    r"|GMP[- ]certified\s+facilit\w*"
    r"|cGMP\s+facilit\w*)",re.I)
ADDR=re.compile(r"929 Harvest Lane[^<]*",re.I)

MARK_OPEN=('<span style="background:#FFF3CD;border-bottom:2px solid #8A6300;" '
           'data-praxera-review="brand">')
CLAIM_OPEN=('<span style="background:#F8DDD9;border-bottom:2px solid #9B3B31;" '
            'data-praxera-review="claim">')
CLOSE='</span>'

def rewrite(h):
    """Swap the brand, highlight what changed, and flag claims separately.

    Works on the HTML string, not the rendered text, so the marker survives into
    the editor where somebody will actually see it."""
    if not isinstance(h,str) or not h: return h,0,0
    brand=claims=0
    # address block -> placeholder, it is a legal footer and must not be guessed
    def addr(m):
        return "[PLACEHOLDER: Praxera registered address &mdash; confirm before sending]"
    h=ADDR.sub(addr,h)
    # claims first: mark the phrase, then let the brand swap run inside it
    def claim_sub(m):
        nonlocal claims; claims+=1
        return CLAIM_OPEN+m.group(0)+CLOSE
    h=CLAIM.sub(claim_sub,h)
    def brand_sub(m):
        nonlocal brand; brand+=1
        return MARK_OPEN+"Praxera"+CLOSE
    h=BRAND.sub(brand_sub,h)
    return h,brand,claims

def walk_widgets(c):
    """Every editable string in the content tree, with a setter."""
    for k,v in (c.get("widgets") or {}).items():
        b=v.get("body")
        if not isinstance(b,dict): continue
        for f in ("html","value"):
            if isinstance(b.get(f),str) and b[f]:
                yield b,f

# subcategory carries automated_ab_master on the ten A/B parents, and HubSpot
# refuses to create a new email holding it -- the clone is not part of anyone's
# test, so the field has no business travelling with it.
STRIP=("id","createdAt","updatedAt","createdById","updatedById","publishedAt",
       "publishDate","isPublished","previewKey","archived","state","statistics",
       "isAb","abStatus","abTestId","abVariation","abSampleSizeDefault",
       "abSamplingDefault","abSuccessMetric","abTestPercentage","abHoursToWait",
       "subcategory","rssData","teamsWithAccess")

def main():
    go="--go" in sys.argv
    M=json.load(open("reference/merged_audit.json"))
    ids={}
    for w in M["workflows"]:
        for eid,nm in w["verified_emails"]:
            ids.setdefault(eid,{"live":False,"wfs":set()})
            ids[eid]["wfs"].add(w["name"])
            if w["live"]: ids[eid]["live"]=True
    print(f"emails to clone: {len(ids)}   mode: {'APPLY' if go else 'DRY RUN'}\n")

    done=[]
    if os.path.exists("reference/praxera_email_clones.json"):
        done=json.load(open("reference/praxera_email_clones.json"))
    already={d["source_id"] for d in done}

    def one(item):
        eid,meta=item
        if eid in already: return {"skip":eid}
        src=call("GET",f"/marketing/v3/emails/{eid}?includeStats=false")
        if not src or "_err" in (src or {}): return {"err":eid,"why":(src or {}).get("_msg","")}
        c=json.loads(json.dumps(src.get("content") or {}))
        brand=claims=0
        for holder,field in walk_widgets(c):
            new,b,cl=rewrite(holder[field])
            holder[field]=new; brand+=b; claims+=cl
        name=src.get("name","")
        clean=re.sub(r"^(DV:?\s*|DVL\s*//\s*)","",name).strip()
        clean=BRAND.sub("Praxera",clean)
        newname=f"Praxera - {clean}"[:190]
        body={k:v for k,v in src.items() if k not in STRIP}
        body["content"]=c
        body["name"]=newname
        body["state"]="DRAFT"
        body["subject"]=BRAND.sub("Praxera",src.get("subject") or "")
        body["from"]={"fromName":"Praxera",
                      "replyTo":(src.get("from") or {}).get("replyTo") or "enews@davincilabs.com"}
        body["to"]={"contactIds":{"exclude":[],"include":[]},
                    "contactIlsLists":{"exclude":[],"include":[]},
                    "contactLists":{"exclude":[],"include":[]},"suppressGraymail":True}
        if not go:
            return {"dry":True,"name":newname,"brand":brand,"claims":claims,
                    "live":meta["live"],"source_id":eid}
        new=call("POST","/marketing/v3/emails",body)
        if not new or "_err" in (new or {}):
            return {"err":eid,"why":(new or {}).get("_msg","")}
        return {"source_id":eid,"source_name":name,"clone_id":new["id"],
                "clone_name":new["name"],"state":new.get("state"),
                "brand_marks":brand,"claim_marks":claims,"live_source":meta["live"],
                "workflows":sorted(meta["wfs"])}

    out=[];errs=[];skipped=0
    with cf.ThreadPoolExecutor(4) as ex:
        for n,r in enumerate(ex.map(one,ids.items()),1):
            if not r: continue
            if r.get("skip"): skipped+=1; continue
            if r.get("err"): errs.append(r); print(f"  !! {r['err']}  {r.get('why','')[:120]}"); continue
            out.append(r)
            tag="LIVE" if r.get("live") or r.get("live_source") else "off "
            print(f"  [{n:>2}/{len(ids)}] {tag} brand={r.get('brand',r.get('brand_marks',0)):>2} "
                  f"claim={r.get('claims',r.get('claim_marks',0)):>2}  {r.get('name',r.get('clone_name',''))[:66]}")

    print(f"\ncloned : {len(out)}   skipped(existing) : {skipped}   errors : {len(errs)}")
    tb=sum(r.get("brand",r.get("brand_marks",0)) for r in out)
    tc=sum(r.get("claims",r.get("claim_marks",0)) for r in out)
    print(f"brand mentions marked : {tb}")
    print(f"claim phrases flagged : {tc}")
    if go and out:
        json.dump(done+out,open("reference/praxera_email_clones.json","w"),indent=1)
        print("-> reference/praxera_email_clones.json")

if __name__=="__main__": main()
