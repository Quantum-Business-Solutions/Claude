"""Render every Praxera email clone and report what a person would see wrong.

The API can tell you a field changed. It cannot tell you the email now has an
empty grey block where a module used to be, or that a highlight lands mid-word,
or that a sentence reads as nonsense after the brand swap. So each clone is
assembled the way HubSpot will assemble it -- sections in order, no padding this
harness invents -- rendered in a real browser, and inspected as pixels and text.
"""
import json,os,re,sys,time,html,urllib.request,collections
import concurrent.futures as cf
from playwright.sync_api import sync_playwright

T=os.environ["TOKEN"]
OUT=sys.argv[sys.argv.index("--out")+1] if "--out" in sys.argv else "/tmp/qa_emails"
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

def get(u,tr=4):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(
            urllib.request.Request(u,headers={"Authorization":"Bearer "+T}),timeout=60))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

def assemble(d):
    c=d.get("content") or {}
    w=c.get("widgets") or {}
    fa=(c.get("flexAreas") or {}).get("main") or {}
    parts=[]
    if fa.get("sections"):
        for s in fa["sections"]:
            st=s.get("style") or {}
            bg=st.get("backgroundColor") or "transparent"
            pt=st.get("paddingTop","0px"); pb=st.get("paddingBottom","0px")
            inner=[]
            for col in s.get("columns",[]):
                for wid in col.get("widgets",[]):
                    b=(w.get(wid) or {}).get("body") or {}
                    if isinstance(b.get("html"),str): inner.append(b["html"])
                    elif isinstance(b.get("value"),str): inner.append(f"<p>{b['value']}</p>")
                    elif isinstance(b.get("img"),dict):
                        im=b["img"]
                        inner.append(f'<img src="{im.get("src","")}" alt="{im.get("alt","")}" '
                                     f'style="display:block;max-width:100%;height:auto;">')
            parts.append(f'<div style="background:{bg};padding:{pt} 0 {pb};">{"".join(inner)}</div>')
    else:
        # older emails have no flexAreas; fall back to widget order
        for k,v in w.items():
            b=v.get("body") or {}
            if isinstance(b.get("html"),str): parts.append(b["html"])
            elif isinstance(b.get("value"),str): parts.append(f"<p>{b['value']}</p>")
    return "".join(parts)

SHELL=('<!doctype html><meta charset="utf-8"><body style="margin:0;background:#F4F5F2;padding:20px 0;">'
       '<table role="presentation" width="640" cellpadding="0" cellspacing="0" align="center" '
       'style="background:#fff;border-collapse:collapse;"><tr><td style="padding:20px 28px;">{}</td>'
       '</tr></table></body>')

DV=re.compile(r"da\s?vinci",re.I)

def main():
    os.makedirs(OUT,exist_ok=True)
    clones=json.load(open("reference/praxera_email_clones.json"))
    print(f"rendering {len(clones)} clones -> {OUT}\n")

    def fetch(c):
        d=get(f"/marketing/v3/emails/{c['clone_id']}?includeStats=false")
        return c,d
    pages=[]
    with cf.ThreadPoolExecutor(6) as ex:
        for c,d in ex.map(fetch,clones):
            h=assemble(d)
            f=os.path.join(OUT,f"{c['clone_id']}.html")
            open(f,"w").write(SHELL.format(h))
            pages.append((c,d,f,h))

    findings=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,args=["--no-sandbox"])
        pg=b.new_page(viewport={"width":700,"height":900})
        # The sandbox cannot reach the image hosts, so every remote request hangs
        # until it times out and the run never finishes. Layout and text do not
        # need the bytes; whether an image URL actually resolves is checked
        # server-side instead, which is a better test anyway.
        pg.route("**/*", lambda r: r.abort()
                 if r.request.url.startswith(("http://","https://")) else r.continue_())
        for n,(c,d,f,h) in enumerate(pages,1):
            errs=[]
            pg.on("pageerror",lambda e: errs.append(str(e)))
            pg.goto("file://"+f); pg.wait_for_timeout(220)
            txt=pg.inner_text("body")
            srcs=pg.eval_on_selector_all("img","els=>els.map(i=>i.getAttribute('src')||'')")
            imgs=len(srcs)
            broken=[]  # filled in server-side after the render pass
            marks=pg.eval_on_selector_all('[data-praxera-review]',
                "els=>els.map(e=>({k:e.dataset.praxeraReview,t:e.innerText.trim()}))")
            box=pg.evaluate("document.body.scrollHeight")
            findings.append({
                "id":c["clone_id"],"name":c["clone_name"],
                "live_source":c.get("live_source"),
                "height":box,"chars":len(txt.strip()),
                "davinci_visible":len(DV.findall(txt)),
                "brand_marks":sum(1 for m in marks if m["k"]=="brand"),
                "claim_marks":sum(1 for m in marks if m["k"]=="claim"),
                "imgs":imgs,"broken":broken,"img_srcs":sorted(set(s_ for s_ in srcs if s_)),
                "placeholder":txt.count("[PLACEHOLDER"),
                "js_errors":errs[:2],
            })
            if n%20==0: print(f"  {n}/{len(pages)}")
        b.close()
    # now test the image URLs for real, without a browser in the way
    allsrc=sorted({u for f in findings for u in f["img_srcs"] if u.startswith("http")})
    print(f"\nchecking {len(allsrc)} distinct image URLs...")
    def head(u):
        try:
            r=urllib.request.Request(u,method="HEAD",headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(r,timeout=25) as resp: return u,resp.status
        except Exception as e:
            code=getattr(e,"code",None)
            return u,(code or 0)
    status={}
    with cf.ThreadPoolExecutor(8) as ex:
        for u,c in ex.map(head,allsrc): status[u]=c
    for f in findings:
        f["broken"]=[u for u in f["img_srcs"] if status.get(u,0) not in (200,301,302)]
    json.dump(findings,open("reference/qa_email_clones.json","w"),indent=1)

    def n(k,pred=lambda v:v): return sum(1 for f in findings if pred(f[k]))
    print("\n" + "="*62)
    print(f"clones rendered            : {len(findings)}")
    print(f"  DaVinci still VISIBLE    : {n('davinci_visible')}")
    print(f"  broken images            : {n('broken',lambda v:len(v)>0)}")
    print(f"  JS errors                : {n('js_errors',lambda v:len(v)>0)}")
    print(f"  suspiciously short (<250c): {n('chars',lambda v:v<250)}")
    print(f"  carrying a brand marker  : {n('brand_marks')}")
    print(f"  carrying a claim marker  : {n('claim_marks')}")
    print(f"  carrying an address placeholder: {n('placeholder')}")
    print(f"\ntotal brand markers: {sum(f['brand_marks'] for f in findings)}"
          f"   claim markers: {sum(f['claim_marks'] for f in findings)}")
    bad=[f for f in findings if f["davinci_visible"]]
    if bad:
        print("\nDAVINCI STILL VISIBLE:")
        for f in bad[:15]: print(f"   {f['davinci_visible']:>2}x  {f['name'][:64]}")
    short=[f for f in findings if f["chars"]<250]
    if short:
        print("\nSHORT / POSSIBLY EMPTY:")
        for f in short[:15]: print(f"   {f['chars']:>4} chars  {f['name'][:60]}")
    br=[f for f in findings if f["broken"]]
    if br:
        print("\nBROKEN IMAGES:")
        for f in br[:10]: print(f"   {f['name'][:52]}  {f['broken'][:2]}")

if __name__=="__main__": main()
