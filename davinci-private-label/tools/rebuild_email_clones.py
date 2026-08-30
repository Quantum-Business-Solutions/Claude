"""Rebuild every clone's content from its untouched source, correctly this time.

The first pass ran a brand regex over the whole HTML string. That destroyed
every href containing davincilabs.com -- the domain was eaten and replaced with
highlight markup, so the URL is not recoverable by patching the clone. The
sources were never modified, so the honest repair is to derive the content again
from source rather than try to reconstruct what was lost.

Four transforms, each scoped to where it belongs:

  text nodes   brand swap + highlight, between tags only, never in an attribute
  href         mapped to the Praxera equivalent, or to the home page as a
               holding position -- the same rule already applied to the blog
  img src      DaVinci logos to the Praxera mark; assets with no equivalent
               flagged rather than guessed
  alt          swapped separately, since it is read aloud and indexed
"""
import json,os,re,sys,time,urllib.request,urllib.error,collections
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
                return {"_err":e.code,"_msg":e.read().decode()[:250]}
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

# The words are not always separated by a plain space: the signature block uses
# DaVinci&nbsp;Laboratories, which a literal " " never matches, so the two-word
# form fell through to the one-word form and left "Laboratories" stranded.
SEP=r"(?:\s|&nbsp;|&#160;|\u00a0)+"
BRAND=re.compile(
    "DaVinci"+SEP+"Laboratories"+SEP+"of"+SEP+"Vermont"
    "|DaVinci"+SEP+"Laboratories"
    "|DaVinci"+SEP+"Labs"
    "|DaVinci"+SEP+"for"+SEP+"Healthcare"+SEP+"Professionals"
    "|DaVinci", re.I)
CLAIM=re.compile(
    r"(handles?\s+(?:the\s+)?(?:formulation|manufactur\w*|bottling|quality)"
    r"|we\s+(?:manufacture|produce|make|formulate|bottle|blend|handle)\w*"
    r"|\bour\s+(?:manufactur\w*|facilit(?:y|ies)|plant|production|labs?\b|formulators?)"
    r"|manufactured\s+(?:in|at|by)\s+our|family[- ]owned\s+company"
    r"|in[- ]house\s+(?:manufactur\w*|production|formulation)"
    r"|from\s+(?:formulation|concept)\s+(?:through|to)\s+delivery"
    r"|doable\s+within\s+DSHEA|c?GMP[- ]certified\s+facilit\w*"
    r"|not\s+just\s+manufacturers?|we(?:'re| are)\s+manufacturers?"
    r"|\bour\s+products?\s+(?:contain|are\s+made|are\s+manufactured)"
    r"|we\s+guarantee)",re.I)
ADDR=re.compile(r"929 Harvest Lane[^<]*",re.I)
DV_HOST=re.compile(r"^https?://(?:www\.|blog\.|info\.)?davincilabs\.com",re.I)
LOGOS=("Immune%20Bundle%20Blast/DaVinci-Logo.png","hubfs/4087538/Logo.png",
       "hubfs/4087538/New%20Logo.png","Newsletters/January%2026/DV-logo-header.jpg")
PX="https://www.pettechlabs.com/hubfs/Praxera/email/"
# Only four of the thirteen flagged assets actually carried DaVinci branding.
# The rest have DaVinci in the filename and nothing DaVinci in the pixels, which
# is the same trap the page imagery set: a calendar icon, a text banner, a plain
# white bottle. Replacing those would be churn, so they are left alone.
ASSET_MAP={
 "DV_Footer-1.jpg":            PX+"praxera-email-footer.png",
 "Group-Product-Shot.jpg":     PX+"praxera-group-product-shot.png",
 "DaVinci-PL_22.jpg":          PX+"praxera-two-bottle-yourname.png",
}
# genuinely has no replacement yet -> reported, never guessed
NO_EQUIV=re.compile(r"(DaVinci-Churn|schedule-a-time-headline)",re.I)

MARK='<span style="background:#FFF3CD;border-bottom:2px solid #8A6300;" data-praxera-review="brand">'
CMARK='<span style="background:#F8DDD9;border-bottom:2px solid #9B3B31;" data-praxera-review="claim">'
CLOSE='</span>'
TOKEN=re.compile(r"(<[^>]*>)")
# a stranded descriptor left behind when the brand name was swapped across markup
ORPHAN=re.compile(r"^\s*(?:Laboratories|Labs|Laboratories of Vermont)\b",re.I)
ATTR=re.compile(r'(\b(?:href|src|alt)\s*=\s*")([^"]*)(")',re.I)

def load_maps():
    b=json.load(open("reference/blog_namespace_split.json"))
    def slug(u):
        u=(u or "").split("?")[0].split("#")[0].rstrip("/")
        return u.split("/private-label/")[-1] if "/private-label/" in u else u.split("/")[-1]
    px={slug(p["url"]):p["url"] for p in b["pl_group"] if "praxerasupplements.com" in (p["url"] or "")}
    um={}
    for r in json.load(open("reference/url_map.json")):
        if r.get("new"): um[r["old"].split("?")[0]]=r["new"]
    return px,um,slug

def map_link(u,px,um,slug):
    base=u.split("?")[0].split("#")[0]
    if base in um: return um[base],"mapped"
    s=slug(base)
    if s in px: return px[s],"mapped"
    return HOME,"home"

def transform(h,px,um,slug,stats):
    """Rewrite one HTML fragment. Attributes and text are handled separately."""
    if not isinstance(h,str) or not h: return h
    h=ADDR.sub("[PLACEHOLDER: Praxera registered address &mdash; confirm before sending]",h)
    out=[]
    for part in TOKEN.split(h):
        if part.startswith("<"):
            def attr(m):
                key,val,q=m.group(1),m.group(2),m.group(3)
                k=key.lower()
                if k.startswith("href"):
                    if DV_HOST.match(val):
                        new,how=map_link(val,px,um,slug)
                        stats["link_"+how]+=1
                        return key+new+q
                elif k.startswith("src"):
                    for frag in LOGOS:
                        if frag in val:
                            stats["logo"]+=1; return key+PX_LOGO+q
                    for frag,rep in ASSET_MAP.items():
                        if frag in val:
                            stats["asset"]+=1; return key+rep+q
                    if NO_EQUIV.search(val): stats["flagged"].add(val)
                elif k.startswith("alt"):
                    if BRAND.search(val):
                        stats["alt"]+=1; return key+BRAND.sub("Praxera",val)+q
                return m.group(0)
            out.append(ATTR.sub(attr,part)); continue
        # text node
        def cs(m):
            stats["claim"]+=1; return CMARK+m.group(0)+CLOSE
        part=CLAIM.sub(cs,part)
        def bs(m):
            stats["brand"]+=1; return MARK+"Praxera"+CLOSE
        part=BRAND.sub(bs,part)
        # "DaVinci</strong> Laboratories" leaves Laboratories stranded once the
        # first half is swapped, and "Praxera Laboratories" is not the brand.
        part=ORPHAN.sub(lambda m: (stats.__setitem__("orphan",stats["orphan"]+1) or ""),part)
        out.append(part)
    return "".join(out)

def main():
    go="--go" in sys.argv
    px,um,slug=load_maps()
    clones=json.load(open("reference/praxera_email_clones.json"))
    print(f"rebuilding {len(clones)} clones from source   mode: {'APPLY' if go else 'DRY RUN'}\n")

    def one(c):
        src=call("GET",f"/marketing/v3/emails/{c['source_id']}?includeStats=false")
        if not src or "_err" in (src or {}): return {"err":c["clone_id"],"why":"source read"}
        cc=json.loads(json.dumps(src.get("content") or {}))
        st=collections.Counter(); st["flagged"]=set()
        for k,v in (cc.get("widgets") or {}).items():
            b=v.get("body")
            if not isinstance(b,dict): continue
            if isinstance(b.get("img"),dict):
                s=b["img"].get("src") or ""
                for frag in LOGOS:
                    if frag in s:
                        b["img"]["src"]=PX_LOGO; b["img"]["alt"]="Praxera"; st["logo"]+=1
                for frag,rep in ASSET_MAP.items():
                    if frag in (b["img"].get("src") or ""):
                        b["img"]["src"]=rep; st["asset"]+=1
                if NO_EQUIV.search(b["img"].get("src") or ""): st["flagged"].add(b["img"]["src"])
                if isinstance(b["img"].get("alt"),str) and BRAND.search(b["img"]["alt"]):
                    b["img"]["alt"]=BRAND.sub("Praxera",b["img"]["alt"]); st["alt"]+=1
            for f in ("html","value"):
                if isinstance(b.get(f),str) and b[f]:
                    b[f]=transform(b[f],px,um,slug,st)
        r={"clone_id":c["clone_id"],"name":c["clone_name"],
           "brand":st["brand"],"claim":st["claim"],"logo":st["logo"],"alt":st["alt"],
           "link_mapped":st["link_mapped"],"link_home":st["link_home"],"asset":st["asset"],
           "flagged":sorted(st["flagged"])}
        if go:
            res=call("PATCH",f"/marketing/v3/emails/{c['clone_id']}",{"content":cc})
            if not res or "_err" in (res or {}): r["err"]=(res or {}).get("_msg","")
            elif res.get("state")!="DRAFT": r["err"]="state left DRAFT"
        return r

    out=[]
    with cf.ThreadPoolExecutor(5) as ex:
        for n,r in enumerate(ex.map(one,clones),1):
            out.append(r)
            if r.get("err"): print(f"  !! {r.get('name','?')[:46]} {r['err'][:80]}")
            if n%25==0: print(f"  {n}/{len(clones)}")
    json.dump(out,open("reference/email_rebuild.json","w"),indent=1)
    tot=lambda k: sum(r.get(k,0) for r in out)
    print(f"\nbrand marks     : {tot('brand')}")
    print(f"claim flags     : {tot('claim')}")
    print(f"logos swapped   : {tot('logo')}")
    print(f"alt text fixed  : {tot('alt')}")
    print(f"graphics swapped: {tot('asset')}")
    print(f"links -> Praxera page : {tot('link_mapped')}")
    print(f"links -> home holding : {tot('link_home')}")
    fl=collections.Counter(u for r in out for u in r.get("flagged",[]))
    print(f"\nassets with no Praxera equivalent: {len(fl)}")
    for u,n in fl.most_common(8): print(f"   {n:>2}x {u[:94]}")
    print(f"errors: {sum(1 for r in out if r.get('err'))}")

if __name__=="__main__": main()
