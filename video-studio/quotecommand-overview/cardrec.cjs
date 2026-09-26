// node cardrec.cjs  → records every card into cards/<name>.webm
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("fs"), path = require("path");
const CARDS = require("./cards.json");
(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", proxy: { server: process.env.HTTPS_PROXY } });
  fs.mkdirSync(__dirname + "/cards", { recursive: true });
  const only = process.argv.slice(2);
  for (const c of CARDS) {
    if (only.length && !only.includes(c.name)) continue;
    const dir = __dirname + "/cards/tmp-" + c.name; fs.rmSync(dir, { recursive: true, force: true });
    const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir, size: { width: 1920, height: 1080 } } });
    const page = await ctx.newPage();
    const t0 = Date.now();
    await page.goto("file://" + __dirname + "/cards.html?" + new URLSearchParams(c.q).toString());
    await page.evaluate(() => document.fonts.ready);
    const ready = Date.now() - t0;
    await page.waitForTimeout(c.ms);
    const v = await page.video().path(); await ctx.close();
    fs.renameSync(v, __dirname + `/cards/${c.name}.webm`); fs.rmSync(dir, { recursive: true, force: true });
    fs.writeFileSync(__dirname + `/cards/${c.name}.json`, JSON.stringify({ ready, ms: c.ms }));
    console.log(c.name, "ready", ready);
  }
  await b.close();
})();
