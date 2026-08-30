"""Put the Praxera brand into the 83 clones properly, and undo the damage the
first pass did.

The first rewrite ran a regex over the whole HTML string. That is wrong for two
reasons and both showed up: it injected highlight markup INSIDE src attributes,
corrupting two image URLs, and it could never have caught the actual problem,
because the DaVinci brand in these emails is mostly a LOGO -- an image on 77
placements -- not a word.

So this pass works on the document, not the string:

  text nodes only   the brand swap and its highlight touch text between tags,
                    never inside an attribute, so a URL cannot be rewritten
  images by URL     each DaVinci asset is mapped to a Praxera one explicitly,
                    or flagged when no equivalent exists rather than guessed
  alt text          swapped separately, because it is read aloud and indexed
"""
import json,os,re,sys,time,urllib.request,urllib.error,collections
import concurrent.futures as cf

T=os.environ["TOKEN"]
PX_LOGO="https://info.davincilabs.com/hs-fs/hubfs/Praxera/Praxera%20Logo.png"

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

# every DaVinci logo variant in the set -> the Praxera mark
LOGOS=[
 "Immune%20Bundle%20Blast/DaVinci-Logo.png",
 "hubfs/4087538/Logo.png",
 "hubfs/4087538/New%20Logo.png",
]
# assets with no Praxera equivalent: flagged, never silently swapped
NO_EQUIV=re.compile(r"(DV_Footer|DaVinci-Churn|schedule-a-time-headline|"
                    r"Download%20Offers/DaVinci)",re.I)

BRAND=re.compile(r"DaVinci Laboratories of Vermont|DaVinci Laboratories|DaVinci Labs|"
                 r"DaVinci for Healthcare Professionals|DaVinci",re.I)
MARK=('<span style="background:#FFF3CD;border-bottom:2px solid #8A6300;" '
      'data-praxera-review="brand">')
CLOSE='</span>'
# a tag, or the text between tags -- so we can treat them differently
TOKEN=re.compile(r"(<[^>]*>)")
SPAN_IN_ATTR=re.compile(r'(src\s*=\s*"[^"]*?)<span[^>]*>(?:</span>)?',re.I)

def fix_corruption(h):
    """Undo highlight markup that landed inside an attribute."""
    before=h
    h=SPAN_IN_ATTR.sub(r"\1",h)
    h=re.sub(r'(src\s*=\s*"[^"]*?)</span>',r"\1",h,flags=re.I)
    return h, h!=before

def swap_images(h):
    n=0; flagged=[]
    for frag in LOGOS:
        if frag in h:
            h=re.sub(r'(<img[^>]*?src\s*=\s*")[^"]*?'+re.escape(frag)+r'[^"]*(")',
                     lambda m: m.group(1)+PX_LOGO+m.group(2), h, flags=re.I)
            n+=1
    for m in re.finditer(r'<img[^>]*?src\s*=\s*"([^"]+)"',h,re.I):
        if NO_EQUIV.search(m.group(1)): flagged.append(m.group(1))
    # alt text is read aloud; swap it too
    h=re.sub(r'(alt\s*=\s*")([^"]*)(")',
             lambda m: m.group(1)+BRAND.sub("Praxera",m.group(2))+m.group(3), h, flags=re.I)
    return h,n,flagged

def swap_text(h):
    """Brand swap in text nodes only. Tags pass through untouched."""
    out=[];n=0
    for part in TOKEN.split(h):
        if part.startswith("<"): out.append(part); continue
        if BRAND.search(part):
            def sub(m):
                nonlocal n; n+=1
                return MARK+"Praxera"+CLOSE
            part=BRAND.sub(sub,part)
        out.append(part)
    return "".join(out),n

def main():
    go="--go" in sys.argv
    clones=json.load(open("reference/praxera_email_clones.json"))
    print(f"repairing {len(clones)} clones   mode: {'APPLY' if go else 'DRY RUN'}\n")

    def one(c):
        d=call("GET",f"/marketing/v3/emails/{c['clone_id']}?includeStats=false")
        if not d or "_err" in (d or {}): return {"err":c["clone_id"]}
        cc=json.loads(json.dumps(d.get("content") or {}))
        fixed=logo=txt=0; flags=[]
        for k,v in (cc.get("widgets") or {}).items():
            b=v.get("body")
            if not isinstance(b,dict): continue
            if isinstance(b.get("img"),dict):
                src=b["img"].get("src") or ""
                for frag in LOGOS:
                    if frag in src: b["img"]["src"]=PX_LOGO; b["img"]["alt"]="Praxera"; logo+=1
                if NO_EQUIV.search(b["img"].get("src") or ""): flags.append(b["img"]["src"])
            for f in ("html","value"):
                if not isinstance(b.get(f),str) or not b[f]: continue
                h=b[f]
                h,did=fix_corruption(h);  fixed+=1 if did else 0
                h,l,fl=swap_images(h);    logo+=l; flags+=fl
                h,t=swap_text(h);         txt+=t
                b[f]=h
        r={"clone_id":c["clone_id"],"name":c["clone_name"],"corrupt_fixed":fixed,
           "logos_swapped":logo,"text_marks":txt,"flagged":sorted(set(flags))}
        if go:
            res=call("PATCH",f"/marketing/v3/emails/{c['clone_id']}",{"content":cc})
            if not res or "_err" in (res or {}):
                r["err"]=(res or {}).get("_msg",""); return r
            back=call("GET",f"/marketing/v3/emails/{c['clone_id']}?includeStats=false")
            if back.get("state")!="DRAFT": r["err"]="state left DRAFT"
        return r

    out=[]
    with cf.ThreadPoolExecutor(5) as ex:
        for n,r in enumerate(ex.map(one,clones),1):
            out.append(r)
            if r.get("err"): print(f"  !! {r.get('name','?')[:50]}  {r['err'][:90]}")
            elif r["logos_swapped"] or r["corrupt_fixed"] or r["flagged"]:
                print(f"  logo={r['logos_swapped']:>2} fixed={r['corrupt_fixed']} "
                      f"marks={r['text_marks']:>2} flags={len(r['flagged'])}  {r['name'][:52]}")
    json.dump(out,open("reference/email_repair.json","w"),indent=1)
    print(f"\nlogos swapped to Praxera : {sum(r.get('logos_swapped',0) for r in out)}")
    print(f"corrupted URLs repaired  : {sum(r.get('corrupt_fixed',0) for r in out)}")
    print(f"text brand marks         : {sum(r.get('text_marks',0) for r in out)}")
    fl=collections.Counter(u for r in out for u in r.get("flagged",[]))
    print(f"\nDAVINCI ASSETS WITH NO PRAXERA EQUIVALENT ({len(fl)}):")
    for u,n in fl.most_common(): print(f"   {n:>2}x  {u[:100]}")
    errs=[r for r in out if r.get("err")]
    print(f"\nerrors: {len(errs)}")

if __name__=="__main__": main()
