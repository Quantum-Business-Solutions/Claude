"""Fix what the HTML-only rewrite could never see.

A drag-and-drop email keeps a button's URL in body.destination and a module's
link in body.link -- structured properties, not markup. The earlier pass walked
body.html and body.value, so every one of those survived: 152 links and 81
button destinations still pointing at davincilabs.com behind Praxera-branded
buttons.

Three more repairs ride along, all caused by rewriting strings without knowing
what they were:
  Praxeralabs.com   "DaVinci" was replaced inside the host davincilabs.com,
                    inventing a domain that does not resolve
  preview_text      the review-highlight span leaked into plain-text preview,
                    so 15 inboxes would display raw markup
  croud logo        a DaVinci wordmark under a filename the logo list missed
"""
import json,os,re,sys,time,html,urllib.request,urllib.error,collections
import concurrent.futures as cf

T=os.environ["TOKEN"]
PX_LOGO="https://info.davincilabs.com/hs-fs/hubfs/Praxera/Praxera%20Logo.png"
HOME="https://www.praxerasupplements.com/"

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

DV_URL=re.compile(r"^https?://(?:www\.|blog\.|info\.)?(?:davincilabs|foodsciencecorp)\.com",re.I)
CROUD=re.compile(r"croud_davinci[-_a-z]*\.png",re.I)
TAGS=re.compile(r"<[^>]+>")

def load_maps():
    b=json.load(open("reference/blog_namespace_split.json"))
    def slug(u):
        u=(u or "").split("?")[0].split("#")[0].rstrip("/")
        return u.split("/private-label/")[-1] if "/private-label/" in u else u.split("/")[-1]
    px={slug(p["url"]):p["url"] for p in b["pl_group"] if "praxerasupplements.com" in (p["url"] or "")}
    um={r["old"].split("?")[0]:r["new"] for r in json.load(open("reference/url_map.json")) if r.get("new")}
    return px,um,slug

def target(u,px,um,slug):
    base=u.split("?")[0].split("#")[0]
    if base in um: return um[base]
    s=slug(base)
    if s in px: return px[s]
    return HOME

def main():
    go="--go" in sys.argv
    px,um,slug=load_maps()
    clones=json.load(open("reference/praxera_email_clones.json"))
    print(f"{len(clones)} clones   mode: {'APPLY' if go else 'DRY RUN'}\n")
    agg=collections.Counter()

    def fix(node,st):
        """Walk the content tree and repair by KEY, not by pattern."""
        if isinstance(node,dict):
            for k,v in list(node.items()):
                if k in ("link","destination","url","href") and isinstance(v,str) and v:
                    if DV_URL.match(v):
                        node[k]=target(v,px,um,slug); st["dest"]+=1; continue
                    if "Praxeralabs.com" in v:
                        node[k]=v.replace("https://www.Praxeralabs.com","https://www.praxerasupplements.com")\
                                 .replace("Praxeralabs.com","praxerasupplements.com"); st["praxlabs"]+=1; continue
                if k=="src" and isinstance(v,str) and CROUD.search(v):
                    node[k]=PX_LOGO; st["croud"]+=1; continue
                if isinstance(v,str) and "Praxeralabs" in v:
                    node[k]=v.replace("Praxeralabs.com","praxerasupplements.com"); st["praxlabs"]+=1
                    v=node[k]
                if isinstance(v,str) and CROUD.search(v):
                    node[k]=CROUD.sub("",v); st["croud"]+=1
                fix(v,st)
        elif isinstance(node,list):
            for v in node: fix(v,st)

    def one(c):
        d=call("GET",f"/marketing/v3/emails/{c['clone_id']}?includeStats=false")
        if not d or "_err" in (d or {}): return {"err":c["clone_id"]}
        cc=json.loads(json.dumps(d.get("content") or {}))
        st=collections.Counter()
        # raw-HTML croud modules need the img src swapped inside markup too
        for k,v in (cc.get("widgets") or {}).items():
            b=v.get("body")
            if isinstance(b,dict):
                for f in ("html","value"):
                    if isinstance(b.get(f),str) and CROUD.search(b[f]):
                        b[f]=CROUD.sub("Praxera%20Logo.png",b[f]); st["croud"]+=1
        fix(cc,st)
        # preview text is plain text: strip any markup that leaked in
        pt=(cc.get("widgets") or {}).get("preview_text")
        if isinstance(pt,dict) and isinstance((pt.get("body") or {}).get("value"),str):
            v=pt["body"]["value"]
            if "<" in v:
                pt["body"]["value"]=re.sub(r"\s+"," ",html.unescape(TAGS.sub("",v))).strip()
                st["preview"]+=1
        if go and sum(st.values()):
            r=call("PATCH",f"/marketing/v3/emails/{c['clone_id']}",{"content":cc})
            if not r or "_err" in (r or {}): return {"err":c["clone_id"],"why":(r or {}).get("_msg","")}
            if r.get("state")!="DRAFT": return {"err":c["clone_id"],"why":"state left DRAFT"}
        return {"st":st,"name":c["clone_name"]}

    with cf.ThreadPoolExecutor(5) as ex:
        for r in ex.map(one,clones):
            if r.get("err"): print(f"  !! {r['err']} {r.get('why','')[:70]}"); continue
            agg+=r["st"]
    print(f"button/module destinations repointed : {agg['dest']}")
    print(f"Praxeralabs.com occurrences fixed    : {agg['praxlabs']}")
    print(f"preview_text markup stripped         : {agg['preview']}")
    print(f"croud DaVinci logo refs replaced     : {agg['croud']}")

if __name__=="__main__": main()
