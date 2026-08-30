"""Put the Praxera forms on the Praxera pages.

Only the form GUID changes. A form embed is a 36-character id sitting in a module
property, so the swap is a string replacement of one id for another and nothing
else in the page can move -- which is what makes it verifiable: read the page
back and assert that every field except the ids is byte-identical.

Two forms are deliberately left alone. "Private Label (Praxera) - Schedule a
Consultation" on 23 pages is already the Praxera form and predates this work; its
clone is a redundant duplicate that should not displace the one in use. And any
form without a clone is reported, never guessed at.
"""
import json,os,re,sys,time,urllib.request,urllib.error,collections
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
                return {"_err":e.code,"_msg":e.read().decode()[:250]}
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

# the form already in use on 23 pages -- Praxera-named, not ours to replace
KEEP={"d8dfdd90-98f1-4cba-bedf-181dd9286ca1"}

def differences(a,b,path=""):
    if type(a)!=type(b): yield path,a,b; return
    if isinstance(a,dict):
        for k in set(a)|set(b):
            yield from differences(a.get(k),b.get(k),f"{path}/{k}")
    elif isinstance(a,list):
        if len(a)!=len(b): yield path,f"len {len(a)}",f"len {len(b)}"; return
        for i,(x,y) in enumerate(zip(a,b)): yield from differences(x,y,f"{path}[{i}]")
    elif a!=b: yield path,a,b

# HubSpot rewrites these on any save; they are not content
STAMPS={"updated","updatedAt","updatedById","authorName","publishDate","currentState"}

def main():
    go="--go" in sys.argv
    clones=json.load(open("reference/praxera_form_clones.json"))
    m={c["source_id"]:c for c in clones}
    idx=json.load(open("reference/page_index.json"))
    snapdir=f"snapshots/form-swap-{time.strftime('%Y%m%dT%H%M%S')}"
    if go: os.makedirs(snapdir,exist_ok=True)
    print(f"{len(idx['production'])} pages   mode: {'APPLY' if go else 'DRY RUN'}")
    if go: print(f"snapshot -> {snapdir}\n")

    swaps=collections.Counter(); skipped=collections.Counter()

    def one(p):
        live=call("GET",f"/cms/v3/pages/site-pages/{p['id']}/draft")
        if not live or "_err" in (live or {}): return {"err":p["slug"]}
        blob=json.dumps(live)
        hits=[sid for sid in m if sid in blob and sid not in KEEP]
        for k in KEEP:
            if k in blob: skipped[k]+=1
        if not hits: return {"n":0}
        new=blob
        for sid in hits:
            cid=m[sid]["clone_id"]
            n=new.count(sid)
            new=new.replace(sid,cid)
            swaps[f"{m[sid]['source_name'][:40]} -> {m[sid]['clone_name'][:40]}"]+=n
        after=json.loads(new)
        if go:
            open(f"{snapdir}/{p['id']}.json","w").write(blob)
            r=call("PATCH",f"/cms/v3/pages/site-pages/{p['id']}/draft",after)
            if not r or "_err" in (r or {}):
                return {"err":p["slug"],"why":(r or {}).get("_msg","")}
            back=call("GET",f"/cms/v3/pages/site-pages/{p['id']}/draft")
            # nothing but the ids (and HubSpot's own stamps) may differ
            stray=[d for d in differences(after,back)
                   if d[0].rsplit("/",1)[-1] not in STAMPS]
            if stray:
                return {"err":p["slug"],"why":f"unexpected change {stray[:2]}"}
            if back.get("slug")!=live.get("slug"):
                return {"err":p["slug"],"why":"SLUG CHANGED"}
        return {"n":sum(blob.count(s) for s in hits),"slug":p["slug"],
                "forms":[m[s]["clone_name"] for s in hits]}

    out=[]
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(one,idx["production"]):
            out.append(r)
            if r.get("err"): print(f"  !! {r['err']} {r.get('why','')[:110]}")
            elif r.get("n"): print(f"  {r['slug'][:38]:40} {', '.join(x[:38] for x in r['forms'])}")
    print(f"\nembeds swapped : {sum(r.get('n',0) for r in out)}")
    print(f"pages changed  : {sum(1 for r in out if r.get('n'))}")
    print(f"errors         : {sum(1 for r in out if r.get('err'))}")
    print("\nBY FORM:")
    for k,v in swaps.most_common(): print(f"   {v:>3}x  {k}")
    print("\nLEFT ALONE (already Praxera, in use):")
    for k,v in skipped.most_common(): print(f"   {v:>3} pages  {k}")

if __name__=="__main__": main()
