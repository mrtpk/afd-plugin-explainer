const { chromium } = require(process.env.HOME + '/.npm/_npx/d537ee5ee2a13f03/node_modules/playwright-core');
(async () => {
  const [url, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath: process.env.HOME + '/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome' });
  const p = await b.newPage({ viewport: { width: +w, height: +h } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto(url); await p.waitForTimeout(1500);
  const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  await p.screenshot({ path: out, fullPage: false });
  console.log(out, 'overflow', ov, 'errors', JSON.stringify(errs));
  await b.close();
})();
