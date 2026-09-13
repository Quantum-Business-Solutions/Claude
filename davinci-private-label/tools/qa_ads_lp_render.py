#!/usr/bin/env python3
"""Render the three ad landing-page DRAFTS and screenshot them.

Mirrors each draft preview locally with its stylesheets and fonts (headless
Chromium cannot reach the live site through the proxy), then drives one browser
over the lot at desktop and phone width. Reports broken images, sideways
scroll, script errors and any DaVinci text a reader would see.

usage: TOKEN=... qa_ads_lp_render.py
"""
import hashlib, http.server, json, os, re, socketserver, sys, threading, time
import urllib.parse, urllib.request

T = os.environ["TOKEN"]
OUT = "/tmp/adslp"
PAGES = [("216192983652", "alp/ads-mfg-usa"),
         ("216192983654", "alp/ads-contract-mfg"),
         ("216194811734", "alp/ads-pl-mfg")]


def api(u, tr=5):
    for i in range(tr):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(
                "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))
        except Exception:
            if i == tr - 1:
                raise
            time.sleep(2 * (i + 1))


def fetch(u, tr=3):
    for i in range(tr):
        try:
            return urllib.request.urlopen(urllib.request.Request(
                u, headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read()
        except Exception:
            if i == tr - 1:
                raise
            time.sleep(1.5 * (i + 1))


os.makedirs(OUT + "/a", exist_ok=True)
seen = {}


def local(u, base, depth=0):
    u = urllib.parse.urljoin(base, u.strip())
    if not u.startswith("http"):
        return None
    if u in seen:
        return seen[u]
    ext = os.path.splitext(urllib.parse.urlparse(u).path)[1][:6] or ".bin"
    name = "a/" + hashlib.md5(u.encode()).hexdigest()[:12] + ext
    try:
        b = fetch(u)
    except Exception:
        return None
    if ext == ".css" and depth < 2:
        t = b.decode("utf8", "replace")
        for m in set(re.findall(r"url\(([^)]+)\)", t)):
            p = local(m.strip("'\""), u, depth + 1)
            if p:
                t = t.replace(m, "../" + p)
        b = t.encode()
    open(OUT + "/" + name, "wb").write(b)
    seen[u] = name
    return name


mirrored = []
for pid, slug in PAGES:
    d = api(f"/cms/v3/pages/site-pages/{pid}/draft")
    v2 = api(f"/content/api/v2/pages/{pid}")
    url = f"{d['url']}?hs_preview={v2['preview_key']}-{pid}"
    html = fetch(url).decode("utf8", "replace")
    base = "https://" + urllib.parse.urlparse(d["url"]).netloc
    html = re.sub(r'\bsrcset="[^"]*"', "", html)

    def rew(m):
        loc = local(m.group(2), base)
        return f'{m.group(1)}="{loc}"' if loc else ""
    html = re.sub(r'\b(href|src)="([^"]+\.(?:css|png|jpg|jpeg|svg|webp|gif|woff2?|ico)(?:\?[^"]*)?)"',
                  rew, html)
    fn = slug.replace("/", "_") + ".html"
    open(OUT + "/" + fn, "w").write(html)
    mirrored.append((slug, fn))
    print(f"mirrored {slug}  ({len(html)} chars)")
print(f"assets cached: {len(seen)}")


class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=OUT, **k)

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", 0), Q)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

PROBE = """() => {
  const out = {broken:[], overflow:false, h:document.body.scrollHeight, empty:0};
  document.querySelectorAll('img').forEach(i => {
    if (i.naturalWidth === 0) out.broken.push((i.currentSrc||i.src).split('/').pop());
  });
  out.overflow = document.documentElement.scrollWidth > window.innerWidth + 2;
  out.sw = document.documentElement.scrollWidth;
  document.querySelectorAll('section, .dnd-section').forEach(s => {
    if (s.getBoundingClientRect().height < 4) out.empty++;
  });
  const t = document.body.innerText;
  out.davinci = (t.match(/da\\s?vinci/gi)||[]).length;
  out.placeholder = (t.match(/PLACEHOLDER/gi)||[]).length;
  out.customform = (t.match(/custom formulation/gi)||[]).length;
  out.h1 = [...document.querySelectorAll('h1')].map(h=>h.innerText.trim());
  out.ctas = [...document.querySelectorAll('a')].filter(a=>/schedule/i.test(a.innerText))
              .map(a=>a.innerText.trim()+' -> '+a.getAttribute('href'));
  return out;
}"""

from playwright.sync_api import sync_playwright
glob = sorted(os.listdir("/opt/pw-browsers"))
chrome = next((f"/opt/pw-browsers/{g}/chrome-linux/chrome" for g in glob
               if g.startswith("chromium")), None)
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
    for w, h, tag in ((1440, 1000, "desktop"), (900, 1000, "tablet"), (390, 844, "phone")):
        pg = b.new_page(viewport={"width": w, "height": h})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:90]))
        for slug, fn in mirrored:
            errs.clear()
            pg.goto(f"http://127.0.0.1:{port}/{fn}", wait_until="load", timeout=45000)
            pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
            pg.evaluate("""async()=>{for(let y=0;y<document.body.scrollHeight;y+=900){
                window.scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}window.scrollTo(0,0);}""")
            pg.wait_for_timeout(400)
            r = pg.evaluate(PROBE)
            shot = f"{OUT}/{slug.replace('/','_')}.{tag}.png"
            pg.screenshot(path=shot, full_page=(tag == "desktop"))
            flag = []
            if r["broken"]:
                flag.append(f"broken images: {r['broken'][:4]}")
            if r["overflow"]:
                flag.append(f"sideways scroll ({r['sw']}px > {w}px)")
            if r["davinci"]:
                flag.append(f"DaVinci text x{r['davinci']}")
            if r["placeholder"]:
                flag.append("PLACEHOLDER still visible")
            if r["customform"]:
                flag.append('"custom formulation" visible')
            if len(r["h1"]) != 1:
                flag.append(f"h1 count = {len(r['h1'])}")
            if errs:
                flag.append(f"js errors: {errs[:2]}")
            print(f"{tag:8} {slug:22} {r['h']:>6}px  " +
                  ("; ".join(flag) if flag else "clean"))
            if tag == "desktop":
                print(f"         h1: {r['h1']}")
                for c in r["ctas"]:
                    print(f"         cta: {c}")
        pg.close()
    b.close()
print(f"\nscreenshots in {OUT}")
