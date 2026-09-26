const D = require("./vo_durations.json");
const dur = (id) => Math.round((D[id] || 10) * 1000);
async function tidy(h) {
  const p = h.page;
  for (const name of ["Hide the next-step tip", "Dismiss until the blanks change"]) {
    const b = p.getByRole("button", { name }).first();
    if (await b.isVisible().catch(() => false)) await b.click().catch(() => {});
  }
  const got = p.getByRole("button", { name: "Got it" }).first();
  if (await got.isVisible().catch(() => false)) await got.click().catch(() => {});
  // the "Prices changed" banner has a close X (per-view only)
  const x = p.locator("text=Prices changed").locator("xpath=ancestor::div[.//button][1]").locator("button").first();
  if (await x.isVisible().catch(() => false)) { const t = await x.innerText().catch(() => ""); if (!t.trim()) await x.click().catch(() => {}); }
  await p.waitForTimeout(400);
}
async function fill(h, id, t0) { const left = dur(id) + 1200 - (Date.now() - t0); if (left > 0) await h.wait(left); }
const FLAG = "/configurator?deal=f1a95000-0000-4000-8000-000000000001";

module.exports = {
  s01: { run: async (h) => {
    await h.go("/"); await h.ready("text=OPEN DEALS"); await tidy(h);
    const t0 = Date.now();
    await h.move(520, 300, 1500); await h.wait(1500);
    await h.move(760, 480, 1400); await h.wait(1600);
    await h.scrollBy(760, 3200); await h.wait(1800);
    await h.move(1180, 700, 1500);
    await fill(h, "s01", t0);
  }},
  s03: { run: async (h) => {
    await h.go("/assessments"); await h.ready("h1"); await tidy(h);
    const t0 = Date.now();
    await h.wait(800);
    await h.click(h.page.locator("a[href*='/assessments/']").first(), { after: 2200 });
    await tidy(h);
    await h.move(700, 380, 1200); await h.wait(1500);
    await h.scrollBy(650, 2600);
    await fill(h, "s03", t0);
  }},
  s04: { run: async (h) => {
    await h.go("/configurator"); await h.ready(h.page.getByRole("button", { name: "Quick start" }).last()); await tidy(h);
    const t0 = Date.now();
    await h.wait(600);
    await h.click(h.page.getByRole("button", { name: "Quick start" }).last(), { after: 1800 });
    await h.move(960, 520, 1200); await h.wait(2500);
    const show = h.page.getByRole("button", { name: /Show recommended|recommended machines|Show matches|Find machines/i }).first();
    if (await show.isVisible().catch(() => false)) await h.click(show, { after: 3500 });
    await h.move(960, 600, 1500);
    await fill(h, "s04", t0);
  }},
  s05: { run: async (h) => {
    // Shot 1 of 2 (about 16s, "Here is the full build for Northwind..."): the flagship build sheet.
    await h.go(FLAG); await h.ready("text=Build sheet"); await tidy(h);
    const t0 = Date.now();
    await h.move(1600, 470, 1300); await h.wait(1600);
    const mach = h.page.getByText("Machines", { exact: true }).first();
    if (await mach.isVisible().catch(() => false)) await h.click(mach, { after: 2200 });
    await h.move(1600, 700, 1600); await h.wait(2200);
    await h.move(1600, 820, 1400);
    const left = 17500 - (Date.now() - t0); if (left > 0) await h.wait(left);
  }},
  s05b: { run: async (h) => {
    // Shot 2 of 2: a fresh local quote (nothing is saved). The C450i is added off camera; on camera
    // we look at the rules, tick the FS-539 staple finisher, and the RU-519 relay it needs is added
    // for us with the reason in words.
    const p = h.page;
    await h.go("/configurator");
    await p.locator("text=Search all products").first().waitFor({ timeout: 60000 });
    await p.waitForFunction(() => /\d{4,} rules/.test(document.body.innerText) && !/loading rules/.test(document.body.innerText), null, { timeout: 90000 }).catch(() => {});
    await tidy(h);
    await p.locator("text=Search all products").first().click();
    await p.keyboard.type("C450i"); await h.wait(1200);
    await p.locator("text=Konica Minolta bizhub C450i").first().click(); await h.wait(1000);
    await p.getByRole("button", { name: "Add Konica Minolta bizhub C450i to the quote" }).click();
    await p.getByText("Staple Finisher", { exact: true }).first().waitFor({ timeout: 20000 });
    await h.wait(5000);                                                   // let the "added" toast clear
    await p.evaluate(() => window.scrollTo(0, 0)); await h.wait(800);
    await h.ready(null);
    const t0 = Date.now();
    await h.hoverSel(p.getByText(/\d{4,} rules/).first(), 700); await h.wait(900);   // "…ten thousand compatibility rules"
    const fin = p.getByText("Staple Finisher", { exact: true }).first();              // the FS-539 row
    const y = await fin.evaluate(n => n.getBoundingClientRect().top);
    await h.scrollBy(y - 480, 1300);
    const compat = p.getByText(/\d+ compatible/).first();
    if (await compat.isVisible().catch(() => false)) { await h.hoverSel(compat, 600); await h.wait(500); }
    const finRow = fin.locator("xpath=ancestor::*[.//button][1]");
    const need = finRow.getByText(/NEEDS RU-519/i).first();
    if (await need.isVisible().catch(() => false)) { await h.hoverSel(need, 600); await h.wait(400); }
    await h.click(fin, { ms: 500, after: 900 });                                      // "Add a staple finisher…"
    const toast = p.locator("[data-sonner-toast]").filter({ hasText: "RU-519" }).first();
    if (await toast.isVisible().catch(() => false)) await h.hoverSel(toast, 1000);
    await h.wait(2400);                                                               // "…tells you in plain English…"
    const relay = p.getByText("Relay Unit", { exact: true }).first();
    if (await relay.isVisible().catch(() => false)) await h.hoverSel(relay, 1000);    // "…adds it in one click"
    await h.wait(2200);
    const badge = p.getByText(/NEEDS RU-519/i).first();
    if (await badge.isVisible().catch(() => false)) await h.hoverSel(badge, 1100);    // "A finisher that doesn't fit…"
    await h.wait(2600);
    await h.scrollBy(-(y - 480) - 300, 1800);                                         // back up to the running total
    await h.move(420, 180, 1200);
    const left = 27500 - (Date.now() - t0); if (left > 0) await h.wait(left);
  }},
  s06: { run: async (h) => {
    await h.go(FLAG); await h.ready("text=Build sheet"); await tidy(h);
    const t0 = Date.now();
    await h.move(230, 262, 1200); await h.wait(1600);            // customer pays
    await h.move(470, 262, 900); await h.wait(1400);             // margin
    await h.move(650, 262, 900); await h.wait(1600);             // approved
    const hgm = h.page.getByText("Hardware gross margin").first();
    await h.hoverSel(hgm, 1300); await h.wait(1800);
    await h.scrollBy(260, 1600); await h.wait(2500);
    await fill(h, "s06", t0);
  }},
  s07: { run: async (h) => {
    await h.go("/approvals"); await h.ready("h1"); await tidy(h);
    const t0 = Date.now();
    await h.move(800, 380, 1400); await h.wait(2500);
    await h.move(1300, 420, 1200); await h.wait(2500);
    await fill(h, "s07", t0);
  }},
  s07p: { phone: true, run: async (h) => {
    await h.go("/approvals"); await h.ready("h1"); await tidy(h);
    await h.wait(2500); await h.scrollBy(400, 2200); await h.wait(2500);
  }},
  s09: { run: async (h) => {
    await h.go(FLAG); await h.ready("text=Build sheet"); await tidy(h);
    const t0 = Date.now();
    await h.scrollTo("text=Trade-up — buy out their current lease", 3000, 120); await h.wait(1500);
    await h.move(700, 400, 1400); await h.wait(2000);
    await h.move(1000, 520, 1400);
    await fill(h, "s09", t0);
  }},
  s10: { run: async (h) => {
    await h.go(FLAG); await h.ready("text=Build sheet"); await tidy(h);
    const t0 = Date.now();
    await h.scrollTo("text=Service & commission terms", 3200, 120); await h.wait(1500);
    await h.move(700, 420, 1400); await h.wait(2000);
    await h.scrollBy(400, 2200);
    await fill(h, "s10", t0);
  }},
  s14: { run: async (h) => {
    await h.go("/deals/f1a95000-0000-4000-8000-0000000000d1"); await h.ready("text=Customer engagement"); await tidy(h);
    const t0 = Date.now();
    await h.scrollTo("text=Customer engagement", 2400, 140); await h.wait(1200);
    await h.move(700, 330, 1300); await h.wait(2000);
    await h.move(1100, 420, 1300); await h.wait(1500);
    await h.click(h.page.getByRole("button", { name: "Notifications" }).first(), { after: 2600 });
    await fill(h, "s14", t0);
  }},
  s17: { clock: process.env.S17_CLOCK || "2026-09-10T09:00:00-05:00", run: async (h) => {
    await h.go("/orders"); await h.page.locator("text=Contract Signed").first().waitFor({ timeout: 90000 });
    await h.setClock(); await h.page.getByRole("button", { name: "Refresh" }).first().click(); await h.wait(4000);
    await h.ready("text=Contract Signed"); await tidy(h);
    const t0 = Date.now();
    await h.move(300, 330, 1300); await h.wait(1200);
    await h.move(1150, 330, 2200); await h.wait(1200);
    await h.hoverSel(h.page.locator("text=ORD-00054").first(), 1500); await h.wait(2200);
    await h.move(1700, 330, 1800);
    await fill(h, "s17", t0);
  }},
  s18: { run: async (h) => {
    await h.go("/orders/ORD-00054"); await h.ready("text=History"); await tidy(h);
    const t0 = Date.now();
    await h.move(700, 300, 1300); await h.wait(1500);
    await h.scrollBy(700, 3000); await h.wait(1500);
    await h.scrollBy(900, 3000); await h.wait(1500);
    await fill(h, "s18", t0);
  }},
  s19: { run: async (h) => {
    await h.go("/orders?view=erp"); await h.ready("text=Orders"); await tidy(h);
    const t0 = Date.now();
    await h.move(500, 360, 1300); await h.wait(2000);
    await h.move(1300, 360, 1600); await h.wait(2000);
    await fill(h, "s19", t0);
  }},
  s21: { rep: true, run: async (h) => {
    await h.go(FLAG); await h.ready("text=Build sheet"); await tidy(h);
    const t0 = Date.now();
    await h.move(700, 90, 1200); await h.wait(2200);             // the View-as-rep banner
    await h.move(470, 300, 1300); await h.wait(2200);            // rep margin
    await h.move(1600, 740, 1500); await h.wait(2500);           // build sheet, no cost
    await h.scrollBy(300, 1800);
    await fill(h, "s21", t0);
  }},
  s25: { phone: true, run: async (h) => {
    await h.go("/configurator?quick=1"); await h.ready("text=Start the quote"); await tidy(h);
    await h.wait(1500);
    const pick = h.page.getByRole("button", { name: /Pick a machine/i }).first();
    if (await pick.isVisible().catch(() => false)) await h.click(pick, { after: 2500 });
    await h.scrollBy(500, 2400); await h.wait(2500); await h.scrollBy(500, 2400); await h.wait(3000);
  }},
};
