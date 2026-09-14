// Tests the client-link bridge against the app that is ACTUALLY LIVE on the
// sheet (/tmp/live_boot.js, extracted from the portal document), not against
// the new build. That is the point: it has to unblock Melinda on what is
// deployed today, without deploying anything large.
//
// Asserts both halves: an anonymous share-link viewer can approve on the first
// click with nothing typed, and a signed-in QBS user is completely unaffected.
//
// usage: NODE_PATH=/opt/node22/lib/node_modules node tools/test_clientlink_bridge.js [liveboot.js]
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const os = require('os');
const path = require('path');

const APP = process.argv[2] || '/tmp/live_boot.js';
const BRIDGE = fs.readFileSync(
  path.join(__dirname, 'signoff_clientlink_bridge.html'), 'utf8')
  .replace(/^<script>/, '').replace(/<\/script>\s*$/, '');

const META = {
  title: 'Test sheet', brandline: 'test', stamp: 'today', note: '', file: 'test',
  groups: [['p', 'Website pages', 'What changes']],
  keys: { p: 'p' }, labels: [], types: [], hs: {}, live: {}, gc: [],
};
const ROWS = [{ k: 'p', id: 'home', n: '(home)', r: '', i: [] }];

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-test-'));
fs.writeFileSync(path.join(dir, 'app.js'), fs.readFileSync(APP, 'utf8'));
fs.writeFileSync(path.join(dir, 'bridge.js'), BRIDGE);
fs.writeFileSync(path.join(dir, 'inner.html'), `<!doctype html><html><body>
<div id="root"></div>
<script type="application/json" id="meta">${JSON.stringify(META)}</script>
<script type="application/json" class="rowdata">${JSON.stringify(ROWS)}</script>
<script src="app.js"></script>
<script src="bridge.js"></script>
</body></html>`);
fs.writeFileSync(path.join(dir, 'outer.html'), `<!doctype html><html><body>
<iframe id="f" src="inner.html" style="width:1200px;height:900px;border:0"></iframe>
<script>
window.__writes = [];
window.addEventListener('message', function (e) {
  var d = e.data; if (!d || d.source !== 'clientcommand-page') return;
  var w = document.getElementById('f').contentWindow;
  if (d.type === 'ready') {
    w.postMessage({ source: 'clientcommand-host', type: 'state', key: d.key, value: {} }, '*');
  } else if (d.type === 'state:set') {
    window.__writes.push({ key: d.key, value: JSON.parse(JSON.stringify(d.value)) });
    w.postMessage({ source: 'clientcommand-host', type: 'saved', key: d.key, ok: true }, '*');
  } else if (d.type === 'whoami') {
    if (location.search.indexOf('anon=1') >= 0) return;          // share link: no user
    w.postMessage({ source: 'clientcommand-host', type: 'whoami',
      user: { name: 'Patrick Dodge', email: 'p@example.com', kind: 'team' } }, '*');
  }
});
</script></body></html>`);

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8' };
const srv = http.createServer((req, res) => {
  const f = path.join(dir, path.basename(req.url.split('?')[0]) || 'outer.html');
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'text/plain' });
  fs.createReadStream(f).pipe(res);
});

const ok = [], fail = [];
const check = (n, c) => (c ? ok : fail).push(n);
const CLIENT_TICK = 'Client ✓';

(async () => {
  await new Promise((r) => srv.listen(0, '127.0.0.1', r));
  const port = srv.address().port;
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 160)));

  // ---- the client, on the share link, touching nothing ----
  await page.goto(`http://127.0.0.1:${port}/outer.html?anon=1`, { waitUntil: 'load' });
  await page.waitForTimeout(2500);          // bridge waits 600ms then polls
  const f = page.frames().find((fr) => fr !== page.mainFrame());

  const box = await f.evaluate(() => {
    const d = document.querySelector('[role="dialog"]');
    return {
      shown: !!d,
      heading: d ? (d.querySelector('h2') || {}).textContent : '',
      people: d ? [...d.querySelectorAll('button')].map((b) => b.textContent.trim()) : [],
      hasFreeText: d ? !!d.querySelector('input[type=text]') : false,
    };
  });
  check('a box appears on arrival', box.shown === true);
  check('it asks who is reviewing', /who is reviewing/i.test(box.heading));
  check('it names Tammy, Melinda and Sarah', ['Tammy Johnson', 'Melinda Elmadjian', 'Sarah Miller']
    .every((n) => box.people.includes(n)));
  check('there is a box for anyone else', box.hasFreeText === true);
  await page.screenshot({ path: '/tmp/signoff-shots/bridge-who-box.png' });

  // Melinda picks herself - one click, nothing typed
  await f.evaluate(() => [...document.querySelectorAll('[role="dialog"] button')]
    .find((b) => b.textContent.trim() === 'Melinda Elmadjian').click());
  await page.waitForTimeout(900);

  const armed = await f.evaluate((label) => {
    const b = [...document.querySelectorAll('button')].find((x) => x.textContent.trim() === label);
    const sd = document.querySelector('button.sd[data-s="client"]');
    return {
      boxGone: !document.querySelector('[role="dialog"]'),
      sidePicked: sd ? sd.getAttribute('aria-pressed') : null,
      name: (document.getElementById('who') || {}).value || '',
      disabled: b ? b.disabled : null,
    };
  }, CLIENT_TICK);
  check('the box closes once she picks', armed.boxGone === true);
  check('her name is filled in for her', armed.name === 'Melinda Elmadjian');
  check('the client side is selected for her', armed.sidePicked === 'true');
  check('Client \u2713 is enabled', armed.disabled === false);

  await f.evaluate((label) => [...document.querySelectorAll('button')]
    .find((x) => x.textContent.trim() === label).click(), CLIENT_TICK);
  await page.waitForTimeout(800);
  await page.screenshot({ path: '/tmp/signoff-shots/bridge-client-approved.png' });

  const done = await f.evaluate((label) => {
    const b = [...document.querySelectorAll('button')].find((x) => x.textContent.trim() === label);
    return { pressed: b.getAttribute('aria-pressed'),
             row: document.querySelector('tr.r td.nm').textContent,
             status: (document.getElementById('save') || {}).textContent || '' };
  }, CLIENT_TICK);
  check('approves on the FIRST click after picking  <- the ask', done.pressed === 'true');
  check('it saved rather than being refused', !/not saved/i.test(done.status));
  check('the row is credited to Melinda', /Melinda Elmadjian/.test(done.row));

  const writes = await page.evaluate(() => window.__writes || []);
  const mark = writes.map((x) => x.value && x.value.home && x.value.home.c).filter(Boolean).pop();
  check('the approval reached the portal', !!mark);
  check('the mark names her', !!mark && mark.by === 'Melinda Elmadjian');
  const logged = writes.filter((x) => /log$/.test(x.key))
    .flatMap((x) => (x.value && x.value.e) || [])
    .filter((e) => e.a === 'client-approve').pop();
  check('the activity log records it', !!logged);
  check('logged as the CLIENT side, not QBS', !!logged && logged.sd === 'client');
  check('logged under her name', !!logged && logged.by === 'Melinda Elmadjian');

  // ---- QBS, signed in: the bridge must not touch them ----
  await page.goto(`http://127.0.0.1:${port}/outer.html`, { waitUntil: 'load' });
  await page.waitForTimeout(2500);
  const f2 = page.frames().find((fr) => fr !== page.mainFrame());
  const team = await f2.evaluate(() => ({
    signedIn: (document.querySelector('.me') || {}).textContent || '',
    whoBox: !!document.getElementById('who'),
    sidePicker: !!document.querySelector('button.sd[data-s="client"]'),
  }));
  check('a signed-in QBS user still shows as themselves', /Patrick Dodge/.test(team.signedIn));
  check('the bridge cannot fire for QBS (no #who box)', team.whoBox === false);
  check('QBS is not flipped to the client side', /QBS/.test(team.signedIn));

  check('no script errors', errs.length === 0);

  await browser.close();
  srv.close();
  ok.forEach((n) => console.log('  PASS  ' + n));
  fail.forEach((n) => console.log('  FAIL  ' + n));
  errs.forEach((e) => console.log('  js: ' + e));
  console.log(`\n${ok.length} passed, ${fail.length} failed`);
  process.exit(fail.length ? 1 : 0);
})();
