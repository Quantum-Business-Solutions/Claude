"""Correct the Praxera page paths already written into the blog drafts.

The links were generated from reference/page_index.json, which was stale: 41 of
the 65 pages carry an `en/` slug prefix the index did not record. So links like
/pl-demo-guides were written pointing at a page that does not exist and would
still 404 the day the site publishes -- the worst kind of broken link, because
it looks right.

This repairs only the path segment. Any link already correct is left alone, and
a link whose target does not exist under either form is reported rather than
guessed at.
"""
import json,os,re,sys,time,urllib.request,urllib.error,collections
import concurrent.futures as cf

T=os.environ["TOKEN"]
BASE="https://www.praxerasupplements.com/"

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
                return {"_err":e.code,"_msg":e.read().decode()[:200]}
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

def main():
    go="--go" in sys.argv
    idx=json.load(open("reference/page_index.json"))
    slugs={p["slug"] for p in idx["production"]}
    posts=[];u="/cms/v3/blogs/posts?limit=100&archived=false"
    while u:
        r=call("GET",u); posts+=r["results"]
        u=r.get("paging",{}).get("next",{}).get("link")
    px=[p for p in posts if "praxerasupplements.com" in (p.get("url") or "")
        and p.get("state")=="DRAFT"]
    print(f"{len(px)} drafts   mode: {'APPLY' if go else 'DRY RUN'}\n")

    LINK=re.compile(re.escape(BASE)+r"((?:en/)?pl-demo-[a-z0-9\-]+)")
    fixedc=collections.Counter(); missing=collections.Counter()

    def one(p):
        d=call("GET",f"/cms/v3/blogs/posts/{p['id']}/draft")
        if not d or "_err" in (d or {}): return {"err":p["id"]}
        body={}; n=0
        for field in ("widgets","layoutSections"):
            v=d.get(field)
            if v in (None,{},[],""): continue
            blob=json.dumps(v); new=blob
            for tail in sorted(set(LINK.findall(blob)),key=len,reverse=True):
                if tail in slugs: continue
                alt=("en/"+tail) if not tail.startswith("en/") else tail[3:]
                if alt in slugs:
                    cnt=new.count(BASE+tail)
                    new=new.replace(BASE+tail,BASE+alt)
                    fixedc[f"{tail} -> {alt}"]+=cnt; n+=cnt
                else:
                    missing[tail]+=1
            if new!=blob: body[field]=json.loads(new)
        if not body: return {"n":0}
        if go:
            r=call("PATCH",f"/cms/v3/blogs/posts/{p['id']}/draft",body)
            if not r or "_err" in (r or {}): return {"err":p["id"],"why":(r or {}).get("_msg","")}
            back=call("GET",f"/cms/v3/blogs/posts/{p['id']}/draft")
            if back.get("state")!="DRAFT": return {"err":p["id"],"why":"state left DRAFT"}
        return {"n":n,"slug":p.get("slug")}

    out=[]
    with cf.ThreadPoolExecutor(5) as ex:
        for r in ex.map(one,px):
            out.append(r)
            if r.get("err"): print(f"  !! {r['err']} {r.get('why','')[:80]}")
    print(f"links corrected : {sum(r.get('n',0) for r in out)}")
    print(f"posts touched   : {sum(1 for r in out if r.get('n'))}")
    print("\nBY TARGET:")
    for k,v in fixedc.most_common(): print(f"   {v:>3}x  {k}")
    if missing:
        print("\nTARGET EXISTS UNDER NEITHER FORM (left alone):")
        for k,v in missing.most_common(): print(f"   {v:>3}x  {k}")

if __name__=="__main__": main()
