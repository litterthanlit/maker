const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 1000 }, deviceScaleFactor: +(process.argv[4] || 1) });
  await p.goto('file://' + process.argv[2]);
  await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(500);
  await p.screenshot({ path: process.argv[3], fullPage: true });
  await b.close();
})();
