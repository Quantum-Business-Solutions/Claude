// Scene scripts. Each run(h) must call h.ready() once the page is presentable, then
// perform the on-camera actions, lasting roughly the scene's narration (vo_durations.json).
const D = require("./vo_durations.json");
const dur = (id) => Math.round((D[id] || 10) * 1000);
const TOKEN = "f76017fbb90149c4a7db44b750ce8ac8954cb98859574d77928a033b828b2df0";

/* Per-browser UI chrome only — nothing here writes data: hide the next-step tip and
   dismiss the profile banner and the guide strip if they are showing. */
async function tidy(h) {
  const p = h.page;
  for (const name of ["Hide the next-step tip", "Dismiss until the blanks change"]) {
    const b = p.getByRole("button", { name }).first();
    if (await b.isVisible().catch(() => false)) await b.click().catch(() => {});
  }
  const got = p.getByRole("button", { name: "Got it" }).first();
  if (await got.isVisible().catch(() => false)) await got.click().catch(() => {});
  await p.waitForTimeout(400);
}
/* Fill the remaining time so the clip covers the narration (plus a beat). */
async function fill(h, id, t0) { const left = dur(id) + 1200 - (Date.now() - t0); if (left > 0) await h.wait(left); }

module.exports = {
  s02: { run: async (h) => {
    await h.go("/fleet");
    await h.ready(h.page.getByPlaceholder(/Customer, site/i)); await tidy(h);
    const t0 = Date.now();
    await h.wait(900);
    await h.type(h.page.getByPlaceholder(/Customer, site/i), "Northwind", { delay: 110 });
    await h.wait(2200);
    await h.move(560, 290, 1300); await h.wait(1600);
    await h.move(900, 290, 1100); await h.wait(1600);
    await h.move(1460, 290, 1300); await h.wait(1800);
    await h.move(900, 560, 1400);
    await fill(h, "s02", t0);
  }},

  s08: { run: async (h) => {
    await h.go("/leasing?tab=rates");
    await h.ready("text=Rate factor grid"); await tidy(h);
    const t0 = Date.now();
    await h.wait(800);
    await h.move(330, 460, 1400); await h.wait(1500);
    await h.move(330, 655, 1400); await h.wait(1500);
    await h.click(h.page.getByRole("button", { name: "$1 buyout" }), { after: 1600 });
    await h.click(h.page.getByRole("button", { name: "FMV" }), { after: 1400 });
    await h.move(390, 610, 1200);
    await fill(h, "s08", t0);
  }},

  s11: { run: async (h) => {
    await h.go("/proposals?id=f1a95000-0000-4000-8000-0000000000d2");
    await h.ready(h.page.getByRole("button", { name: "Preview" })); await tidy(h);
    const t0 = Date.now();
    await h.wait(900);
    await h.move(300, 420, 1200); await h.wait(1200);
    await h.click(h.page.getByRole("button", { name: "Preview" }), { after: 2200 });
    await h.scrollBy(900, 3000); await h.wait(1200);
    await h.scrollBy(1100, 3000); await h.wait(1200);
    await fill(h, "s11", t0);
  }},

  s12: { anon: true, run: async (h) => {
    await h.go("/p/" + TOKEN);
    await h.ready("text=Northwind Orthopedics, PC");
    const t0 = Date.now();
    await h.wait(2400);
    await h.scrollTo("text=RECOMMENDED SOLUTION", 3200, 90); await h.wait(2600);
    await h.scrollBy(700, 2600); await h.wait(1600);
    await h.scrollTo("text=INVESTMENT", 3000, 90); await h.wait(3200);
    await h.scrollTo("text=OPTIONS COMPARED", 3000, 90); await h.wait(3000);
    await h.move(960, 560, 1400);
    await fill(h, "s12", t0);
  }},

  s12p: { anon: true, phone: true, run: async (h) => {
    await h.go("/p/" + TOKEN);
    await h.ready("text=Northwind Orthopedics, PC");
    await h.wait(1800);
    await h.scrollBy(900, 2600); await h.wait(1200);
    await h.scrollTo("text=INVESTMENT", 2600, 60); await h.wait(2200);
    await h.scrollBy(700, 2400); await h.wait(1400);
  }},

  s13: { anon: true, run: async (h) => {
    await h.go("/p/" + TOKEN);
    await h.ready("text=Northwind Orthopedics, PC");
    const t0 = Date.now();
    await h.scrollTo("text=Which option works best for you?", 2200, 110); await h.wait(900);
    const choose = h.page.getByRole("button", { name: "Choose this option" }).nth(1);
    await h.click(choose, { after: 2600 });            // the confirm dialog — nothing is confirmed
    await h.page.keyboard.press("Escape"); await h.wait(700);
    await h.click(h.page.getByRole("button", { name: /Ask a question/i }).first(), { after: 1200 });
    await fill(h, "s13", t0);
  }},

  s15: { run: async (h) => {
    await h.go("/documents?deal=f1a95000-0000-4000-8000-000000000001");
    await h.ready("text=Quote Builder"); await tidy(h);
    const t0 = Date.now();
    await h.wait(900);
    const tog = h.page.getByRole("button", { name: "Toggle navigation" }).first();
    if (await tog.isVisible().catch(() => false)) await h.click(tog, { after: 1200 });
    for (const n of ["^Quote$", "^FMV Lease", "^Service Agreement", "^Credit Application", "^Schedule A"]) {
      const b = h.page.getByRole("button", { name: new RegExp(n) }).filter({ visible: true }).first();
      if (await b.isVisible().catch(() => false)) await h.click(b, { after: 1900 });
    }
    await h.move(1100, 600, 1400);
    await fill(h, "s15", t0);
  }},

  s16: { run: async (h) => {
    await h.go("/signed-orders");
    await h.ready("text=Signed Orders"); await tidy(h);
    const t0 = Date.now();
    await h.wait(900);
    const nw = h.page.locator("text=Northwind Orthopedics, PC").first();
    await h.hoverSel(nw, 1300); await h.wait(1200);
    const card = nw.locator("xpath=ancestor::*[.//button[normalize-space()='Audit trail']][1]");
    await h.click(card.getByRole("button", { name: "Audit trail" }).first(), { after: 2400 });
    await h.scrollBy(500, 2400); await h.wait(2000);
    await fill(h, "s16", t0);
  }},

  s20: { run: async (h) => {
    await h.go("/settings/integrations");
    await h.ready("text=HubSpot"); await tidy(h);
    const t0 = Date.now();
    await h.wait(1200);
    await h.hoverSel(h.page.locator("text=HubSpot").first(), 1300); await h.wait(2200);
    const map = h.page.getByRole("link", { name: /Field Mapping/i }).first();
    if (await map.isVisible().catch(() => false)) { await h.click(map, { after: 3000 }); await h.scrollBy(500, 2600); }
    await fill(h, "s20", t0);
  }},

  s22: { run: async (h) => {
    await h.go("/settings/teams");
    await h.ready("text=Limit what reps and managers see", 120000); await tidy(h);
    const t0 = Date.now();
    await h.wait(900);
    await h.hoverSel(h.page.getByRole("switch", { name: "Limit what reps and managers see" }), 1400); await h.wait(1800);
    await h.scrollBy(650, 2800); await h.wait(1800);
    await h.scrollBy(650, 2800);
    await fill(h, "s22", t0);
  }},

  s23: { run: async (h) => {
    await h.go("/commissions");
    for (let i = 0; i < 5; i++) {
      if (await h.page.locator("text=Monthly commission summary").first().isVisible().catch(() => false)) break;
      const ok = await h.page.locator("text=Monthly commission summary").first().waitFor({ timeout: 30000 }).then(() => true).catch(() => false);
      if (ok) break;
      await h.page.reload().catch(() => {});
    }
    await h.ready("text=Monthly commission summary", 60000); await tidy(h);
    const t0 = Date.now();
    await h.wait(1000);
    await h.move(700, 330, 1300); await h.wait(1600);
    await h.scrollBy(500, 2600); await h.wait(1600);
    await fill(h, "s23", t0);
  }},

  s24: { run: async (h) => {
    await h.go("/analytics");
    await h.ready("text=Margin distribution"); await tidy(h);
    const t0 = Date.now();
    await h.wait(900);
    await h.move(700, 420, 1200); await h.wait(1400);
    await h.click(h.page.getByRole("tab", { name: "Audit log" }).or(h.page.getByRole("button", { name: "Audit log" })).first(), { after: 2400 });
    await fill(h, "s24", t0);
  }},

  s26: { run: async (h) => {
    await h.go("/settings/integrations");
    await h.ready("text=HubSpot"); await tidy(h);
    const t0 = Date.now();
    await h.scrollTo("text=Connect Claude", 2600, 160); await h.wait(1500);
    await h.move(900, 520, 1600);
    await fill(h, "s26", t0);
  }},
};
