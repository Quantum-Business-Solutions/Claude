// Renders HTML screen inserts and tag overlays to frame sequences, frame-accurately.
// node build/render_inserts.js <insert_name> <seconds>   -> build/tmp/<name>/f%04d.png
// node build/render_inserts.js --tag <text> <color> <out.png>
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const ROOT = path.resolve(__dirname, '..');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const args = process.argv.slice(2);
  if (args[0] === '--tag') {
    const [, text, color, out] = args;
    await p.goto('file://'+path.join(ROOT,'inserts','insert.html'));
    await p.setContent(`<html><head><style>@font-face{font-family:Anton;src:url(file://${path.join(ROOT,'assets','anton-latin-400-normal.woff2')})}</style></head>
      <body style="margin:0;background:transparent"><div style="position:absolute;left:70px;top:64px;font-family:Anton,Impact,sans-serif;font-size:64px;letter-spacing:.04em;
      color:#06070C;background:${color};padding:10px 30px 12px;transform:rotate(-2deg);box-shadow:0 20px 50px -12px rgba(0,0,0,.6)">${text}</div></body></html>`);
    await p.waitForTimeout(800);
    await p.screenshot({ path: out, omitBackground: true });
  } else {
    const [name, secs] = args;
    const dir = path.join(ROOT, 'build', 'tmp', name);
    fs.mkdirSync(dir, { recursive: true });
    await p.goto('file://' + path.join(ROOT, 'inserts', 'insert.html'));
    await p.waitForTimeout(1200);
    const n = Math.round(parseFloat(secs) * 30);
    for (let i = 0; i < n; i++) {
      await p.evaluate(([nm, t]) => window.setT(nm, t), [name, i / 30]);
      await p.screenshot({ path: path.join(dir, 'f' + String(i).padStart(4, '0') + '.png') });
    }
  }
  await b.close();
})();
