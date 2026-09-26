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
    // Shot 2 of 2: a fresh local quote (nothing is saved). Add a C450i, tick the FS-539 staple
    // finisher; the RU-519 relay it needs is added for you, with the reason in words.
    const p = h.page;
    await h.go("/configurator");
    await p.locator("text=Search all products").first().waitFor({ timeout: 60000 });
    await p.waitForFunction(() => /10844 rules|\d+ rules/.test(document.body.innerText) && !/loading rules/.test(document.body.innerText), null, { timeout: 90000 }).catch(() => {});
    await h.ready(null); await tidy(h);
    const t0 = Date.now();
    await h.hoverSel(p.getByText(/\d{4,} rules/).first(), 800); await h.wait(1100);          // "…ten thousand compatibility rules"
    await h.click(p.locator("text=Search all products").first(), { after: 250 });
    await p.keyboard.type("C450i", { delay: 70 }); await h.wait(700);
    await h.hoverSel(p.locator("text=Konica Minolta bizhub C450i").first(), 600);
    await p.evaluate(() => { const c = document.getElementById("qc-film-cursor"); if (c) { const r = c.getBoundingClientRect(); window.__qcClick && window.__qcClick(r.left + 3, r.top + 3); } });
    await p.keyboard.press("Enter"); await h.wait(600);
    const addBtn = p.getByRole("button", { name: "Add Konica Minolta bizhub C450i to the quote" });
    if (!(await addBtn.isVisible().catch(() => false))) { await p.locator("text=Konica Minolta bizhub C450i").first().click().catch(() => {}); await h.wait(600); }
    await h.click(addBtn, { after: 700 });
    const sku = p.getByText("FS-539", { exact: true }).first();
    await sku.waitFor({ timeout: 20000 });
    const y = await sku.evaluate(n => n.getBoundingClientRect().top);
    await h.scrollBy(y - 430, 1300);                                                            // "Add a staple finisher…"
    const row = sku.locator("xpath=ancestor::*[.//button][1]");
    await h.click(row.getByText("Staple Finisher", { exact: true }).first(), { ms: 600, after: 900 });
    const toast = p.locator("[data-sonner-toast]").filter({ hasText: "RU-519" }).first();
    if (await toast.isVisible().catch(() => false)) { await h.hoverSel(toast, 1100); }
    await h.wait(2400);                                                                         // "…tells you in plain English…"
    const relay = p.getByText("Relay Unit", { exact: true }).first();
    if (await relay.isVisible().catch(() => false)) await h.hoverSel(relay, 1100);              // "…adds it in one click"
    await h.wait(2000);
    const badge = p.getByText("NEEDS RU-519", { exact: false }).first();
    if (await badge.isVisible().catch(() => false)) await h.hoverSel(badge, 1200);              // "A finisher that doesn't fit…"
    await h.wait(2600);
    await h.scrollBy(-(y - 430) - 200, 1800);                                                   // back up to the running total
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
