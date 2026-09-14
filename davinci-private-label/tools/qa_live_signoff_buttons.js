// Drives the REAL Praxera sign-off sheet on the client share link, exactly as
// Melinda would open it, and confirms the approval buttons become usable once
// she identifies herself.
//
// Deliberately stops short of pressing an approval button: that would write a
// real client approval onto the client's sheet. It asserts the buttons are
// present and enabled, and that clicking one would be accepted - never that it
// was clicked.
//
// usage: NODE_PATH=/opt/node22/lib/node_modules node tools/qa_live_signoff_buttons.js
const { chromium } = require('playwright');

const SHARE = 'https://clientcommand.thequantumleap.business/portal/'
  + '2a5c361066202d71fa47ee598d2bcb95/pages/94f31f00-08a7-4f9c-905e-fe4a5e6b8c7d';
const SHOTS = '/tmp/signoff-live';

const ok = [], fail = [];
const check = (n, c) => (c ? ok : fail).push(n);

// The sheet renders inside a sandboxed iframe; find whichever frame has the app.
async function appFrame(page) {
  for (let i = 0; i < 40; i++) {
    for (const f of page.frames()) {
      try {
        const has = await f.evaluate(() => !!document.querySelector('#idbar, .idbar'));
        if (has) return f;
      } catch (e) { /* frame still navigating */ }
    }
    await page.waitForTimeout(500);
  }
  return null;
}

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 160)));

  await page.goto(SHARE, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(4000);

  const f = await appFrame(page);
  check('the sign-off sheet loads on the share link', !!f);
  if (!f) {
    await page.screenshot({ path: `${SHOTS}/00-no-app.png`, fullPage: false });
    console.log('  FAIL  the sign-off sheet loads on the share link');
    console.log(`  (screenshot: ${SHOTS}/00-no-app.png)`);
    await browser.close();
    process.exit(1);
  }

  const before = await f.evaluate(() => {
    const b = [...document.querySelectorAll('button')];
    const pick = (t) => b.find((x) => x.textContent.trim() === t);
    return {
      rows: document.querySelectorAll('tr.r').length,
      picker: !!document.querySelector('.sideg'),
      whoInput: !!document.getElementById('who'),
      signedIn: (document.querySelector('.me') || {}).textContent || '',
      clientBtn: pick('Client ✓') ? pick('Client ✓').disabled : null,
      qbsBtn: pick('QBS ✓') ? pick('QBS ✓').disabled : null,
      status: (document.getElementById('save') || {}).textContent || '',
    };
  });
  await page.screenshot({ path: `${SHOTS}/01-as-melinda-opens-it.png` });

  check('rows are rendered', before.rows > 0);
  console.log(`        rows on screen: ${before.rows}`);
  console.log(`        identity bar: ${before.whoInput ? 'name box + side picker (anonymous share link)'
    : 'signed in as "' + before.signedIn.trim() + '"'}`);
  console.log(`        Client checkmark disabled? ${before.clientBtn}`);

  // Melinda's two steps: type her name, pick her side. Neither writes anything.
  if (before.whoInput) {
    await f.fill('#who', 'Melinda Elmadjian');
    await f.evaluate(() => {
      const b = [...document.querySelectorAll('button.sd')]
        .find((x) => /I am the client/i.test(x.textContent));
      if (b) b.click();
    });
    await page.waitForTimeout(800);
  }

  const after = await f.evaluate(() => {
    const b = [...document.querySelectorAll('button')];
    const pick = (t) => b.find((x) => x.textContent.trim() === t);
    const cb = pick('Client ✓');
    const r = cb ? cb.getBoundingClientRect() : null;
    return {
      side: (document.querySelector('.side') || {}).textContent || '',
      clientDisabled: cb ? cb.disabled : null,
      clientVisible: !!r && r.width > 0 && r.height > 0,
      qbsDisabled: pick('QBS ✓') ? pick('QBS ✓').disabled : null,
      regDisabled: pick('Regulatory ✓') ? pick('Regulatory ✓').disabled : null,
      pressed: cb ? cb.getAttribute('aria-pressed') : null,
      status: (document.getElementById('save') || {}).textContent || '',
    };
  });
  await page.screenshot({ path: `${SHOTS}/02-after-i-am-the-client.png` });

  check('the sheet accepts "I am the client"', /client/i.test(after.side));
  check('Client ✓ is present and visible', after.clientVisible === true);
  check('Client ✓ is ENABLED for her', after.clientDisabled === false);
  check('QBS ✓ is not disabled', after.qbsDisabled === false);
  check('Regulatory ✓ is not disabled', after.regDisabled === false);
  check('nothing was approved by this test', after.pressed === 'false');
  check('the sheet is connected to the portal', !/not saved/i.test(after.status));
  check('no script errors on the page', errs.length === 0);

  console.log(`        side now: "${after.side.trim()}"  ·  status: "${after.status.trim()}"`);

  await browser.close();
  ok.forEach((n) => console.log('  PASS  ' + n));
  fail.forEach((n) => console.log('  FAIL  ' + n));
  errs.forEach((e) => console.log('  js: ' + e));
  console.log(`\n${ok.length} passed, ${fail.length} failed`);
  console.log(`screenshots in ${SHOTS}`);
  process.exit(fail.length ? 1 : 0);
})();
