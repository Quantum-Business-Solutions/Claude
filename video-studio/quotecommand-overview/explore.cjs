const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("fs");
const B = "https://quotecommand.thequantumleap.business";
const pages = JSON.parse(process.argv[2]);
(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", proxy: { server: process.env.HTTPS_PROXY } });
  for (const p of pages) {
    const phone = !!p.phone;
    const ctx = await b.newContext({ viewport: phone ? { width: 390, height: 844 } : { width: 1920, height: 1080 }, isMobile: phone, hasTouch: phone, storageState: p.anon ? undefined : __dirname + "/rec-state.json" });
    await ctx.addInitScript(([rep]) => { localStorage.setItem("qc-active-dealer", "8c3dfd49-71ad-4615-a727-96689bdb4bc0"); if (rep) sessionStorage.setItem("qc-role-preview", "rep"); }, [!!p.rep]);
    const page = await ctx.newPage();
    for (let i = 0; i < 5; i++) { const r = await page.goto(B + p.url).catch(() => null); const t = await page.innerText("body").catch(() => ""); if (r && r.status() < 500 && !/upstream request failed|Bad Gateway/i.test(t)) break; await page.waitForTimeout(2500); }
    await page.waitForLoadState("networkidle", { timeout: 45000 }).catch(() => {}); await page.waitForTimeout(p.wait || 5000);
    await page.screenshot({ path: `explore/${p.name}.png`, fullPage: !!p.full });
    const info = await page.evaluate(() => ({
      buttons: [...document.querySelectorAll("button,[role=tab],a[href]")].map(e => (e.innerText || e.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ")).filter(t => t && t.length < 60),
      inputs: [...document.querySelectorAll("input,textarea,select")].map(e => `${e.tagName}:${e.getAttribute("placeholder") || e.getAttribute("aria-label") || e.name || e.type}`),
      h: [...document.querySelectorAll("h1,h2,h3")].map(e => e.innerText.trim()).slice(0, 30),
      height: document.documentElement.scrollHeight,
    }));
    fs.writeFileSync(`explore/${p.name}.json`, JSON.stringify(info, null, 1));
    console.log(p.name, "h=", info.height, "| H:", info.h.slice(0, 8).join(" / ").slice(0, 200));
    await ctx.close();
  }
  await b.close();
})();
