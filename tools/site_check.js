// Site check (supervisor script): every built page at 1280 and 390 px with all deep dives open.
// Reports page-level horizontal overflow, JS errors, broken internal links and anchors, missing images.
// Usage: node tools/site_check.js [site-dir]   (exit 1 on any problem)
// Needs playwright-core (cached by npx) and the Chromium in ~/.cache/ms-playwright (see progress.md).
const fs = require('fs');
const path = require('path');
const HOME = process.env.HOME;
const { chromium } = require(HOME + '/.npm/_npx/d537ee5ee2a13f03/node_modules/playwright-core');
const EXE = HOME + '/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome';

const SITE = path.resolve(process.argv[2] || path.join(__dirname, '..', 'site'));
const WIDTHS = [1280, 390];

function pages(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (e.name !== 'assets' && e.name !== 'diagrams') out.push(...pages(p)); }
    else if (e.name.endsWith('.html')) out.push(p);
  }
  return out;
}

(async () => {
  const files = pages(SITE).sort();
  const browser = await chromium.launch({ executablePath: EXE });
  const problems = [];
  const idCache = new Map();
  let links = 0;
  for (const file of files) {
    const rel = path.relative(SITE, file);
    for (const w of WIDTHS) {
      const page = await browser.newPage({ viewport: { width: w, height: 900 } });
      const errs = [];
      page.on('pageerror', e => errs.push(e.message));
      page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      await page.goto('file://' + file);
      await page.waitForTimeout(400);
      await page.evaluate(() => document.querySelectorAll('details').forEach(d => { d.open = true; }));
      await page.waitForTimeout(150);
      const r = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth - window.innerWidth,
        ids: [...document.querySelectorAll('[id]')].map(e => e.id),
        hrefs: [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')),
        brokenImgs: [...document.querySelectorAll('img')].filter(i => i.complete && i.naturalWidth === 0).map(i => i.getAttribute('src')),
      }));
      if (r.overflow > 1) problems.push(`${rel} @${w}: page overflow ${r.overflow}px`);
      // fonts and Prism come from CDNs; ignore network errors for them only
      for (const e of errs.filter(e => !/fonts\.g|cdnjs|ERR_INTERNET|net::/.test(e))) problems.push(`${rel} @${w}: JS error: ${e}`);
      for (const s of r.brokenImgs) problems.push(`${rel} @${w}: broken image ${s}`);
      if (w === WIDTHS[0]) {
        idCache.set(file, new Set(r.ids));
        for (const h of r.hrefs) {
          if (/^(https?:|mailto:|javascript:)/.test(h)) continue;
          links++;
          const [p, anchor] = h.split('#');
          const target = p ? path.resolve(path.dirname(file), p) : file;
          if (!fs.existsSync(target)) { problems.push(`${rel}: broken link ${h}`); continue; }
          if (anchor) {
            if (!idCache.has(target)) {
              const html = fs.readFileSync(target, 'utf8');
              idCache.set(target, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1])));
            }
            if (!idCache.get(target).has(decodeURIComponent(anchor))) problems.push(`${rel}: missing anchor ${h}`);
          }
        }
      }
      await page.close();
    }
  }
  await browser.close();
  console.log(`pages ${files.length} x widths ${WIDTHS.join('/')} · internal links ${links} · problems ${problems.length}`);
  for (const p of problems) console.log('  ' + p);
  process.exit(problems.length ? 1 : 0);
})();
