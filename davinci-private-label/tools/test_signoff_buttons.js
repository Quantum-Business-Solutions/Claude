// Smoke test for the sign-off app's approval buttons.
//
// Melinda could not approve anything: the portal signs her in with a `kind` the
// sheet read as team, that set her side to QBS, and the Client ✓ button then
// rendered `disabled`. The page looked broken. Shawn's call is that anyone may
// press any button as long as the sheet records who pressed it and from which
// side, so QBS can also tick on the client's behalf.
//
// This drives the real minified build in a browser, inside an iframe with a
// stub ClientCommand host in the parent (which is where the app posts to), and
// asserts exactly that.
//
// usage: NODE_PATH=/opt/node22/lib/node_modules node tools/test_signoff_buttons.js [build.js]
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const os = require('os');
const path = require('path');

const BUILD = process.argv[2] || '/tmp/new_boot.js';

const META = {
  title: 'Test sheet', brandline: 'test', stamp: 'today', note: '', file: 'test',
  groups: [['p', 'Website pages', 'What changes']],
  keys: { p: 'p' }, labels: [], types: [], hs: {}, live: {}, gc: [],
};
const ROWS = [{ k: 'p', id: 'home', n: '(home)', r: '', i: [] }];

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'signoff-test-'));

fs.writeFileSync(path.join(dir, 'inner.html'), `<!doctype html><html><body>
<div id="root"></div>
<script type="application/json" id="meta">${JSON.stringify(META)}</script>
<script type="application/json" class="rowdata">${JSON.stringify(ROWS)}</script>
<script src="app.js"></script>
</body></html>`);

fs.writeFileSync(path.join(dir, 'app.js'), fs.readFileSync(BUILD, 'utf8'));

// The stub host lives in the PARENT, because that is where the app postMessages.
// It answers whoami as a user whose kind the sheet maps to the QBS side -
// Melinda's exact situation - and records every write.
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
    if (location.search.indexOf('anon=1') >= 0) return;   // share link: no user
    w.postMessage({ source: 'clientcommand-host', type: 'whoami',
      user: { name: 'Melinda Elmadjian', email: 'm@example.com', kind: 'team' } }, '*');
  }
});
</script></body></html>`);

// charset matters: without it the ✓ in the button labels arrives mojibaked and
// every selector below silently misses.
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8' };
const srv = http.createServer((req, res) => {
  const f = path.join(dir, path.basename(req.url.split('?')[0]) || 'outer.html');
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'text/plain' });
  fs.createReadStream(f).pipe(res);
});

const fail = [];
const ok = [];
function check(name, cond) { (cond ? ok : fail).push(name); }

(async () => {
  await new Promise((r) => srv.listen(0, '127.0.0.1', r));
  const port = srv.address().port;
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e)));
  await page.goto(`http://127.0.0.1:${port}/outer.html`, { waitUntil: 'load' });
  await page.waitForTimeout(1200);
  const f = page.frames().find((fr) => fr !== page.mainFrame());

  const seen = await f.evaluate(() => {
    const b = [...document.querySelectorAll('button')];
    const pick = (t) => b.find((x) => x.textContent.trim() === t);
    return {
      signedIn: (document.querySelector('.me') || {}).textContent || '',
      qbs: pick('QBS ✓') ? pick('QBS ✓').disabled : null,
      client: pick('Client ✓') ? pick('Client ✓').disabled : null,
      reg: pick('Regulatory ✓') ? pick('Regulatory ✓').disabled : null,
      found: !!pick('Client ✓'),
    };
  });
  check('Client ✓ button exists', seen.found);
  check('QBS ✓ is not disabled', seen.qbs === false);
  check('Client ✓ is not disabled  <- the bug', seen.client === false);
  check('Regulatory ✓ is not disabled', seen.reg === false);
  check('signed in as Melinda, side QBS', /Melinda/.test(seen.signedIn) && /QBS/.test(seen.signedIn));

  // press Client ✓ while on the QBS side - an on-behalf tick
  await f.evaluate(() => [...document.querySelectorAll('button')]
    .find((x) => x.textContent.trim() === 'Client ✓').click());
  await page.waitForTimeout(800);

  const after = await f.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => x.textContent.trim() === 'Client ✓');
    // td.nm, not .nm - the table header is also .nm and comes first in the DOM
    return { pressed: b.getAttribute('aria-pressed'), row: document.querySelector('tr.r td.nm').textContent };
  });
  check('Client ✓ now reads as pressed', after.pressed === 'true');
  check('row shows it was given on their behalf', /on their behalf/i.test(after.row));
  check('row still names who did it', /Melinda/.test(after.row));

  const writes = await page.evaluate(() => window.__writes || []);
  const mark = writes.map((x) => x.value && x.value.home && x.value.home.c).filter(Boolean).pop();
  check('the mark was saved to the portal', !!mark);
  check('the mark records the name', !!mark && mark.by === 'Melinda Elmadjian');
  check('the mark records the side that gave it (sd:"qbs")', !!mark && mark.sd === 'qbs');
  check('no script errors', errs.length === 0);

  // Second scenario: the no-login share link, where the host sends NO user at
  // all. Pressing a button used to scroll the identity bar and nothing else,
  // which reads as "the button is broken". It must now say so out loud.
  await page.goto(`http://127.0.0.1:${port}/outer.html?anon=1`, { waitUntil: 'load' });
  await page.waitForTimeout(1200);
  const f2 = page.frames().find((fr) => fr !== page.mainFrame());
  const anon = await f2.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => x.textContent.trim() === 'Client \u2713');
    b.click();
    return { msg: (document.getElementById('save') || {}).textContent || '',
             picker: !!document.querySelector('.sideg') };
  });
  check('anonymous viewer is told to identify themselves', /who you are/i.test(anon.msg));
  check('anonymous viewer is offered the side picker', anon.picker === true);

  await browser.close();
  srv.close();
  ok.forEach((n) => console.log('  PASS  ' + n));
  fail.forEach((n) => console.log('  FAIL  ' + n));
  errs.forEach((e) => console.log('  js: ' + e.slice(0, 200)));
  console.log(`\n${ok.length} passed, ${fail.length} failed`);
  process.exit(fail.length ? 1 : 0);
})();
