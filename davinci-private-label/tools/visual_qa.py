#!/usr/bin/env python3
"""Render every Private Label page and report what a person would see wrong.

Mirrors all pages into one directory with a shared asset cache -- they run off
the same stylesheets and fonts, so fetching those once instead of 65 times turns
a 45-minute job into a few minutes -- then drives one browser over the lot.

Checks the things a JSON diff cannot: an image that does not load, an icon
rendering at the wrong size, a row where some cards have icons and others have
holes, script errors, and a page that scrolls sideways.

usage: TOKEN=... visual_qa.py [--out DIR] [--limit N]
"""
import hashlib, http.server, json, os, re, socketserver, sys, threading, time
import urllib.parse, urllib.request, urllib.error
import concurrent.futures as cf

T   = os.environ["TOKEN"]
S   = os.path.dirname(os.path.abspath(__file__)) + "/"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/tmp/vqa"
LIM = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0

def api(u, tr=5):
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(
            "https://api.hubapi.com" + u, headers={"Authorization": "Bearer " + T})))
        except Exception:
            if i == tr - 1: raise
            time.sleep(2 * (i + 1))

def fetch(u, tr=3):
    for i in range(tr):
        try: return urllib.request.urlopen(urllib.request.Request(
            u, headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read()
        except Exception:
            if i == tr - 1: raise
            time.sleep(1.5 * (i + 1))

idx   = json.load(open(S + "../reference/page_index.json"))
pages = idx["production"][:LIM] if LIM else idx["production"]
os.makedirs(OUT + "/a", exist_ok=True)

# ---- one asset cache for all pages -------------------------------------------
seen, lock = {}, threading.Lock()
def local(u, base, depth=0):
    u = urllib.parse.urljoin(base, u.strip())
    if not u.startswith("http"): return None
    with lock:
        if u in seen: return seen[u]
    ext = os.path.splitext(urllib.parse.urlparse(u).path)[1][:6] or ".bin"
    name = "a/" + hashlib.md5(u.encode()).hexdigest()[:12] + ext
    try: b = fetch(u)
    except Exception: return None
    if ext == ".css" and depth < 2:
        t = b.decode("utf8", "replace")
        for m in set(re.findall(r"url\(([^)]+)\)", t)):
            p = local(m.strip("'\""), u, depth + 1)
            if p: t = t.replace(m, "../" + p)
        b = t.encode()
    with lock:
        if u not in seen:
            open(OUT + "/" + name, "wb").write(b); seen[u] = name
    return seen[u]

def mirror(p):
    try:
        d  = api(f"/cms/v3/pages/site-pages/{p['id']}/draft")
        v2 = api(f"/content/api/v2/pages/{p['id']}")
        url = f"{d['url']}?hs_preview={v2['preview_key']}-{p['id']}"
        html = fetch(url).decode("utf8", "replace")
    except Exception as e:
        return p["slug"], None, f"could not fetch: {str(e)[:60]}"
    base = "https://" + urllib.parse.urlparse(d["url"]).netloc
    html = re.sub(r'\bsrcset="[^"]*"', "", html)
    def rew(m):
        loc = local(m.group(2), base)
        return f'{m.group(1)}="{loc}"' if loc else ""
    html = re.sub(r'\b(href|src)="([^"]+\.(?:css|png|jpg|jpeg|svg|webp|gif|woff2?|ico)(?:\?[^"]*)?)"',
                  rew, html)
    fn = re.sub(r"[^a-z0-9]+", "_", p["slug"].lower()) + ".html"
    open(OUT + "/" + fn, "w").write(html)
    return p["slug"], fn, None

print(f"mirroring {len(pages)} pages...")
with cf.ThreadPoolExecutor(6) as ex: mirrored = list(ex.map(mirror, pages))
ok  = [(s, f) for s, f, e in mirrored if f]
err = [(s, e) for s, f, e in mirrored if e]
print(f"  mirrored {len(ok)}   failed {len(err)}   assets cached {len(seen)}")
for s, e in err: print(f"    !! {s}: {e}")

# ---- one browser over the lot -------------------------------------------------
class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=OUT, **k)
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", 0), Q); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright
PROBE = """() => {
  const out = {broken:[], icons:[], halfrows:[], overflow:false, h:document.body.scrollHeight,
               empty:0, tiny:[]};
  document.querySelectorAll('img').forEach(i => {
    if (i.naturalWidth === 0) out.broken.push((i.currentSrc||i.src).split('/').pop());
  });
  document.querySelectorAll('.pl-cg__icon img, .pl-stat__icon img').forEach(i => {
    const r = i.getBoundingClientRect();
    out.icons.push({w:Math.round(r.width), h:Math.round(r.height), nw:i.naturalWidth});
    if (r.width && r.width < 14) out.tiny.push((i.currentSrc||i.src).split('/').pop());
  });
  document.querySelectorAll('.pl-cg__grid').forEach(g => {
    const cards = g.querySelectorAll('.pl-cg__card');
    const withI = g.querySelectorAll('.pl-cg__card .pl-cg__icon').length;
    if (withI > 0 && withI < cards.length)
      out.halfrows.push(cards.length + ' cards, ' + withI + ' icons');
  });
  out.overflow = document.documentElement.scrollWidth > window.innerWidth + 2;
  document.querySelectorAll('section, .pl-cg').forEach(s => {
    if (s.getBoundingClientRect().height < 4) out.empty++;
  });
  const t = document.body.innerText;
  out.davinci = (t.match(/da\\s?vinci/gi)||[]).length;
  out.prexera = (t.match(/prexera/gi)||[]).length;
  return out;
}"""
findings = []
with sync_playwright() as pw:
    b  = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                            args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:90]))
    for n, (slug, fn) in enumerate(ok, 1):
        errs.clear()
        try:
            pg.goto(f"http://127.0.0.1:{port}/{fn}", wait_until="load", timeout=45000)
            pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
            pg.evaluate("""async()=>{for(let y=0;y<document.body.scrollHeight;y+=900){
                window.scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}window.scrollTo(0,0);}""")
            pg.wait_for_timeout(500)
            r = pg.evaluate(PROBE); r["errors"] = list(errs)
        except Exception as e:
            r = {"fatal": str(e)[:80]}
        # AOS and hbspt come from scripts the mirror cannot fetch through the
        # proxy, so their absence is this harness talking, not the page.
        if "errors" in r:
            r["errors"] = [e for e in r["errors"]
                           if not re.search(r"\b(AOS|hbspt|_hsq|jQuery|\$)\b.*not defined", e)]
        r["slug"] = slug; findings.append(r)
        print(f"  [{n:>2}/{len(ok)}] {slug}", flush=True)
    b.close()
srv.shutdown()
json.dump(findings, open(OUT + "/findings.json", "w"), indent=1)
print(f"\nwrote {OUT}/findings.json")
