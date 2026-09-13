// Renders the mirrored ad landing-page drafts (written by qa_ads_lp_render.py)
// at desktop, tablet and phone width and reports what a reader would see wrong.
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const OUT = '/tmp/adslp';
const FILES = ['alp_ads-mfg-usa.html', 'alp_ads-contract-mfg.html', 'alp_ads-pl-mfg.html'];
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.webp': 'image/webp', '.gif': 'image/gif', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.ico': 'image/x-icon' };

const srv = http.createServer((req, res) => {
  const f = path.join(OUT, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(OUT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404); return res.end();
  }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});

const PROBE = () => {
  const out = { broken: [], h: document.body.scrollHeight };
  document.querySelectorAll('img').forEach(i => {
    if (i.naturalWidth === 0) out.broken.push((i.currentSrc || i.src).split('/').pop());
  });
  out.overflow = document.documentElement.scrollWidth > window.innerWidth + 2;
  out.sw = document.documentElement.scrollWidth;
  const t = document.body.innerText;
  out.davinci = (t.match(/da\s?vinci/gi) || []).length;
  out.placeholder = (t.match(/PLACEHOLDER/gi) || []).length;
  out.customform = (t.match(/custom formulation/gi) || []).length;
  out.h1 = [...document.querySelectorAll('h1')].map(h => h.innerText.trim());
  out.ctas = [...document.querySelectorAll('a')]
    .filter(a => /schedule|get started/i.test(a.innerText))
    .map(a => a.innerText.trim().replace(/\s+/g, ' ') + ' -> ' + a.getAttribute('href'));
  out.empty = [...document.querySelectorAll('.dnd-section')]
    .filter(s => s.getBoundingClientRect().height < 4).length;
  return out;
};

(async () => {
  await new Promise(r => srv.listen(0, '127.0.0.1', r));
  const port = srv.address().port;
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox'],
  });
  for (const [w, h, tag, full] of [[1440, 1000, 'desktop', true], [900, 1000, 'tablet', false], [390, 844, 'phone', false]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    const errs = [];
    page.on('pageerror', e => errs.push(String(e).slice(0, 90)));
    for (const fn of FILES) {
      errs.length = 0;
      await page.goto(`http://127.0.0.1:${port}/${fn}`, { waitUntil: 'load', timeout: 45000 });
      await page.evaluate(() => document.querySelectorAll('img[loading=lazy]').forEach(i => (i.loading = 'eager')));
      await page.evaluate(async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 900) {
          window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60));
        }
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(400);
      const r = await page.evaluate(PROBE);
      const slug = fn.replace('.html', '');
      await page.screenshot({ path: `${OUT}/${slug}.${tag}.png`, fullPage: full });
      const flag = [];
      if (r.broken.length) flag.push(`broken images: ${r.broken.slice(0, 4).join(', ')}`);
      if (r.overflow) flag.push(`sideways scroll (${r.sw}px > ${w}px)`);
      if (r.davinci) flag.push(`DaVinci text x${r.davinci}`);
      if (r.placeholder) flag.push('PLACEHOLDER still visible');
      if (r.customform) flag.push('"custom formulation" visible');
      if (r.h1.length !== 1) flag.push(`h1 count = ${r.h1.length}`);
      if (r.empty) flag.push(`${r.empty} empty section(s)`);
      if (errs.length) flag.push(`js errors: ${errs.slice(0, 2).join(' | ')}`);
      console.log(`${tag.padEnd(8)} ${slug.padEnd(24)} ${String(r.h).padStart(6)}px  ${flag.length ? flag.join('; ') : 'clean'}`);
      if (tag === 'desktop') {
        console.log(`         h1: ${JSON.stringify(r.h1)}`);
        r.ctas.forEach(c => console.log(`         cta: ${c}`));
      }
    }
    await page.close();
  }
  await browser.close();
  srv.close();
  console.log(`\nscreenshots in ${OUT}`);
})();
