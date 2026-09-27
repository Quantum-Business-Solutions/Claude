// Render caption PNGs (1920x1080, transparent) for build/captions.py. Usage: node render_captions.js <dir>
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const dir = process.argv[2], list = JSON.parse(fs.readFileSync(path.join(dir, 'list.json')));
  const A = 'file://' + path.resolve(__dirname, '..', 'assets') + '/';
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const css = `@font-face{font-family:'DM Sans';font-weight:700;src:url(${A}dm-sans-latin-700-normal.woff2)}
    html,body{margin:0;background:transparent}#c{position:absolute;left:50%;bottom:118px;transform:translateX(-50%);max-width:1360px;
    text-align:center;font:700 50px/1.2 'DM Sans';color:#fff;padding:12px 30px;border-radius:14px;background:rgba(6,7,12,.62);
    text-shadow:0 2px 8px rgba(0,0,0,.6)}#c:empty{display:none}`;
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  for (let i = -1; i < list.length; i++) {
    const f = path.join(dir, 'page.html');
    fs.writeFileSync(f, `<!doctype html><meta charset="utf-8"><style>${css}</style><div id="c">${i < 0 ? '' : esc(list[i])}</div>`);
    await p.goto('file://' + f);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(dir, i < 0 ? 'blank.png' : 'c' + String(i).padStart(3, '0') + '.png'), omitBackground: true });
  }
  await b.close();
})();
