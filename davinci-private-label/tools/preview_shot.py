#!/usr/bin/env python3
"""Screenshot a Private Label page as HubSpot actually renders it.

The pages are unpublished drafts, so there is no public URL -- but the v2 API
carries a preview_key, and <page url>?hs_preview=<key>-<id> serves the real
rendered draft. The agent proxy resets browser navigation to the outside while
urllib passes through it, so the page and its assets are fetched here, rewritten
to local paths and served from 127.0.0.1 for the browser to load.

Reports each icon's rendered size against its natural size, and any broken
image, which is the check a JSON diff cannot make.

usage: TOKEN=... preview_shot.py <slug> [--out DIR]
"""
import hashlib, http.server, json, os, re, socketserver, sys, threading
import urllib.parse, urllib.request

T    = os.environ["TOKEN"]
S    = os.path.dirname(os.path.abspath(__file__)) + "/"
SLUG = sys.argv[1]
OUT  = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/tmp/preview_shot"
# A fixed port breaks the second page in a row: the first server is still
# holding it. Let the OS pick a free one.
PORT = 0

def api(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))

def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(
        u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read()

idx  = json.load(open(S + "../reference/page_index.json"))
page = next(p for b, v in idx.items() if isinstance(v, list)
            for p in v if p["slug"] == SLUG)
v2   = api(f"/content/api/v2/pages/{page['id']}")
live = api(f"/cms/v3/pages/site-pages/{page['id']}/draft")["url"]
url  = f"{live}?hs_preview={v2['preview_key']}-{page['id']}"
print("preview:", url)

os.makedirs(OUT + "/a", exist_ok=True)
os.chdir(OUT)
html = fetch(url).decode("utf8", "replace")
seen = {}
def local(u, depth=0):
    u = urllib.parse.urljoin("https://" + urllib.parse.urlparse(url).netloc, u.strip())
    if not u.startswith("http"): return None
    if u in seen: return seen[u]
    ext = os.path.splitext(urllib.parse.urlparse(u).path)[1][:6] or ".bin"
    name = "a/" + hashlib.md5(u.encode()).hexdigest()[:12] + ext
    try: b = fetch(u)
    except Exception: return None
    if ext == ".css" and depth < 2:
        t = b.decode("utf8", "replace")
        for m in set(re.findall(r"url\(([^)]+)\)", t)):
            p = local(m.strip("'\""), depth + 1)
            if p: t = t.replace(m, "../" + p)
        b = t.encode()
    open(name, "wb").write(b); seen[u] = name
    return name

# srcset too: leaving it absolute makes the browser fetch through the blocked proxy
# and report a broken image that is fine on the real site.
def rew(m):
    p = local(m.group(2).split("?")[0] if m.group(1) != "srcset" else m.group(2))
    return f'{m.group(1)}="{p}"' if p else ""
html = re.sub(r'\b(href|src)="([^"]+\.(?:css|png|jpg|jpeg|svg|webp|gif|woff2?|ico)(?:\?[^"]*)?)"', rew, html)
html = re.sub(r'\bsrcset="[^"]*"', "", html)
open("index.html", "w").write(html)
print(f"mirrored {len(seen)} assets")

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", PORT), Q)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                           args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    pg.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=45000)
    pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
    pg.evaluate("""async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){
        window.scrollTo(0,y);await new Promise(r=>setTimeout(r,120));}window.scrollTo(0,0);}""")
    pg.wait_for_timeout(1500)
    icons = pg.eval_on_selector_all(".pl-cg__icon img, .pl-stat__icon img",
        "e=>e.map(i=>({f:i.currentSrc.split('/').pop(),nw:i.naturalWidth,nh:i.naturalHeight,"
        "rw:Math.round(i.getBoundingClientRect().width),rh:Math.round(i.getBoundingClientRect().height)}))")
    print(f"\n{'rendered':>10} {'natural':>9}  file")
    for i in icons:
        print(f"{i['rw']}x{i['rh']:<6} {i['nw']}x{i['nh']:<5}  "
              f"{'BROKEN ' if i['nw']==0 else ''}{i['f']}")
    broken = pg.eval_on_selector_all("img", "e=>e.filter(i=>i.naturalWidth===0).length")
    print(f"\nicons: {len(icons)}   broken images on page: {broken}")
    pg.screenshot(path="full.png", full_page=True)
    b.close()
srv.shutdown()
print("wrote", OUT + "/full.png")
