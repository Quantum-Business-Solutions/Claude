// Scene recorder for the QuoteCommand film.
// usage: node rec.cjs <sceneId> [<sceneId> ...]   (scenes defined in scenes.cjs)
// Each scene records into rec/<id>/ ; rec/<id>/meta.json holds the ms offset when the
// page was ready (so the editor trims the loading), and the recorded action span.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("fs");
const DIR = __dirname;
const B = process.env.QC_BASE || "https://quotecommand.thequantumleap.business";
const DEALER = "8c3dfd49-71ad-4615-a727-96689bdb4bc0";
const STATE = DIR + "/rec-state.json";
const WRITES = DIR + "/rec-writes.log";
const LOGIN = { email: process.env.QC_EMAIL, pass: process.env.QC_PASSWORD }; // set in the shell, never committed

/* Film dressing, applied to every page: a visible cursor (headless video has none),
   the QA login's email hidden in the user menu, the floating help pills hidden. */
const DRESS = `
(() => {
  const css = \`
    #qc-film-cursor{position:fixed;left:0;top:0;width:22px;height:22px;margin:-3px 0 0 -3px;z-index:2147483647;pointer-events:none;
      background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 22 22'><path d='M3 2 L3 18 L7.5 13.8 L10.6 20.4 L13.4 19.1 L10.4 12.6 L16.6 12.4 Z' fill='white' stroke='black' stroke-width='1.4' stroke-linejoin='round'/></svg>") no-repeat;
      transition:transform .08s ease-out; filter: drop-shadow(0 1px 2px rgba(0,0,0,.35));}
    #qc-film-cursor.down{transform:scale(.86)}
    #qc-film-ripple{position:fixed;z-index:2147483646;pointer-events:none;width:36px;height:36px;margin:-18px 0 0 -18px;border-radius:50%;
      border:2px solid rgba(201,162,75,.9);opacity:0;}
    #qc-film-ripple.go{animation:qcr .5s ease-out}
    @keyframes qcr{0%{opacity:.9;transform:scale(.3)}100%{opacity:0;transform:scale(1.4)}}
    [data-film-hide]{visibility:hidden !important}
  \`;
  const add = () => {
    if (document.getElementById('qc-film-style')) return;
    const s = document.createElement('style'); s.id='qc-film-style'; s.textContent = css; document.documentElement.appendChild(s);
    const c = document.createElement('div'); c.id='qc-film-cursor'; document.documentElement.appendChild(c);
    const r = document.createElement('div'); r.id='qc-film-ripple'; document.documentElement.appendChild(r);
    window.__qcCursor = (x,y) => { c.style.left = x+'px'; c.style.top = y+'px'; };
    window.__qcClick = (x,y) => { r.style.left=x+'px'; r.style.top=y+'px'; r.classList.remove('go'); void r.offsetWidth; r.classList.add('go'); c.classList.add('down'); setTimeout(()=>c.classList.remove('down'),140); };
  };
  const hide = () => {
    // user-menu email label, help pills ("Tour this page", "Next: …")
    for (const el of document.querySelectorAll('button, a, span, div')) {
      if (el.children.length > 2) continue;
      const t = (el.textContent || '').trim();
      if (window.__qcHideEmail && t.toLowerCase().includes(window.__qcHideEmail)) el.setAttribute('data-film-hide','');
      if (/^Tour this page$/i.test(t) || /^Next:/.test(t)) {
        let b = el; for (let i = 0; i < 6 && b && b.parentElement; i++) { if (getComputedStyle(b).position === 'fixed') break; b = b.parentElement; }
        (b && getComputedStyle(b).position === 'fixed' ? b : el).setAttribute('data-film-hide','');
      }
    }
  };
  const scrub = () => {
    if (!document.body) return;
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: n => /ZZ TEST/.test(n.nodeValue) ? 1 : 3 });
    const hits = []; while (w.nextNode()) hits.push(w.currentNode);
    for (const n of hits) n.nodeValue = n.nodeValue.replace(/([·•|]\\s*)?ZZ TEST[\\s\\p{Pd}·:]*/gu, (m, sep) => sep || '');
  };
  new MutationObserver(scrub).observe(document, { childList: true, subtree: true, characterData: true });
  document.addEventListener('DOMContentLoaded', add); if (document.readyState !== 'loading') add();
  setInterval(() => { add(); hide(); }, 250);
})();
`;

async function main() {
  const ids = process.argv.slice(2);
  const scenes = Object.assign({}, require(DIR + "/scenes.cjs"), require(DIR + "/scenes2.cjs"));
  const browser = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    proxy: { server: process.env.HTTPS_PROXY, bypass: "192.0.2.2" },
    args: ["--font-render-hinting=none", "--disable-lcd-text"],
  });

  if (!fs.existsSync(STATE) || process.env.RELOGIN) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(B + "/auth");
    await page.fill("#signin-email", LOGIN.email);
    await page.fill("#signin-password", LOGIN.pass);
    await page.keyboard.press("Enter");
    await page.waitForURL(u => !/\/auth/.test(u.toString()), { timeout: 60000 });
    await page.waitForTimeout(2000);
    await ctx.storageState({ path: STATE });
    await ctx.close();
  }

  for (const id of ids) {
    const sc = scenes[id];
    if (!sc) { console.log("no scene", id); continue; }
    const phone = !!sc.phone;
    const vp = phone ? { width: 390, height: 844 } : { width: 1920, height: 1080 };
    const out = `${DIR}/rec/${id}`;
    fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true });
    const ctx = await browser.newContext({
      viewport: vp, deviceScaleFactor: phone ? 2 : 1, isMobile: phone, hasTouch: phone,
      storageState: sc.anon ? undefined : STATE,
      recordVideo: { dir: out, size: phone ? { width: 390, height: 844 } : { width: 1920, height: 1080 } },
      colorScheme: "light",
    });
    await ctx.addInitScript(([d, rep]) => {
      try { localStorage.setItem("qc-active-dealer", d); if (rep) sessionStorage.setItem("qc-role-preview", "rep"); else sessionStorage.removeItem("qc-role-preview"); } catch {}
    }, [DEALER, !!sc.rep]);
    await ctx.addInitScript((e) => { window.__qcHideEmail = (e || '').toLowerCase(); }, LOGIN.email);
    await ctx.addInitScript(DRESS);
    if (sc.clock) await ctx.clock.install({ time: new Date() });   // real time for sign-in; the scene moves it after load
    const page = await ctx.newPage();
    const t0 = Date.now();
    const errs = [];
    page.on("pageerror", e => errs.push("PAGEERROR " + e.message.slice(0, 160)));
    page.on("response", r => { if (r.status() >= 500) errs.push(`HTTP ${r.status()} ${r.url().slice(0, 120)}`); });
    page.on("request", r => { const m = r.method(); if (!["GET", "OPTIONS", "HEAD"].includes(m)) fs.appendFileSync(WRITES, `${new Date().toISOString()} ${id} ${m} ${r.url().slice(0, 160)}\n`); });

    let mx = vp.width / 2, my = vp.height / 2;
    const h = {
      B, page, vp,
      async go(url) {
        for (let i = 0; i < 6; i++) {
          const r = await page.goto(B + url).catch(() => null);
          const t = await page.innerText("body").catch(() => "");
          if (r && r.status() < 500 && !/upstream request failed|Bad Gateway/i.test(t)) {
            // the HTML can load while a JS chunk 502s, leaving a blank app: wait for #root to render
            const rendered = await page.waitForFunction(() => { const r = document.getElementById("root"); return r && r.children.length > 0 && (r.innerText || "").trim().length > 20; }, null, { timeout: 25000 }).then(() => true).catch(() => false);
            if (rendered) return;
          }
          await page.waitForTimeout(3000);
        }
        throw new Error("could not load " + url);
      },
      async setClock() { if (sc.clock) await page.clock.setSystemTime(new Date(sc.clock)); },
      marks: {},
      mark(name) { this.marks[name] = Date.now() - t0; },
      wait: (ms) => page.waitForTimeout(ms),
      async move(x, y, ms = 700) {
        const steps = Math.max(8, Math.round(ms / 16));
        const sx = mx, sy = my;
        for (let i = 1; i <= steps; i++) {
          const t = i / steps, e = t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
          mx = sx + (x - sx) * e; my = sy + (y - sy) * e;
          await page.mouse.move(mx, my);
          await page.evaluate(([a, b]) => window.__qcCursor && window.__qcCursor(a, b), [mx, my]);
          await page.waitForTimeout(ms / steps);
        }
      },
      async hoverSel(sel, ms = 700) {
        const el = typeof sel === "string" ? page.locator(sel).first() : sel;
        await el.scrollIntoViewIfNeeded().catch(() => {});
        const bb = await el.boundingBox(); if (!bb) throw new Error("no box " + sel);
        await this.move(bb.x + Math.min(bb.width / 2, 60), bb.y + bb.height / 2, ms);
        return bb;
      },
      async click(sel, { ms = 700, after = 600 } = {}) {
        await this.hoverSel(sel, ms);
        await page.evaluate(([a, b]) => window.__qcClick && window.__qcClick(a, b), [mx, my]);
        await page.mouse.down(); await page.waitForTimeout(70); await page.mouse.up();
        await page.waitForTimeout(after);
      },
      async type(sel, text, { delay = 55 } = {}) {
        await this.click(sel, { after: 200 });
        await page.keyboard.type(text, { delay });
      },
      async scrollBy(dy, ms = 1400) {
        const steps = Math.max(10, Math.round(ms / 16));
        for (let i = 0; i < steps; i++) {
          await page.mouse.wheel(0, dy / steps);
          await page.waitForTimeout(ms / steps);
        }
      },
      async scrollTo(sel, ms = 1400, offset = 140) {
        const el = page.locator(sel).first();
        const y = await el.evaluate((n, off) => n.getBoundingClientRect().top - off, offset);
        await this.scrollBy(y, ms);
      },
      async ready(sel, timeout = 90000) {
        if (sel) await (typeof sel === "string" ? page.waitForSelector(sel, { timeout }) : sel.first().waitFor({ timeout }));
        await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
        await page.waitForTimeout(1200);
        await this.move(vp.width * 0.62, vp.height * 0.55, 10);
        this.mark("ready");
      },
    };
    let ok = true;
    try { await sc.run(h); } catch (e) { ok = false; console.log(`[${id}] FAILED: ${e.message.split("\n")[0]}`); await page.screenshot({ path: `${out}/fail.png` }).catch(() => {}); }
    h.mark("end");
    await page.screenshot({ path: `${out}/last.png` }).catch(() => {});
    const vpath = await page.video().path();
    await ctx.close();
    const final = `${out}/raw.webm`; fs.renameSync(vpath, final);
    fs.writeFileSync(`${out}/meta.json`, JSON.stringify({ id, ok, phone, marks: h.marks, errs: [...new Set(errs)].slice(0, 12) }, null, 1));
    console.log(`[${id}] ${ok ? "ok" : "FAIL"} ready=${h.marks.ready} end=${h.marks.end} errs=${errs.length}`);
  }
  await browser.close();
}
main().catch(e => { console.error("FATAL", e.stack); process.exit(1); });
