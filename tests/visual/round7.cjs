// Round 7: audit items 6 (flicker/layout shift) + 10 (horizontal scroll on remaining pages)
const lib = require('./lib.cjs');
const BASE = 'http://127.0.0.1:8123';
const PAGES = ['/', '/about', '/help', '/terms', '/privacy', '/cookies', '/delete-account', '/s/invalid-token-probe', '/static/offline.html', '/definitely-not-a-page'];
const WIDTHS = [1366, 1024, 768, 390];

(async () => {
  const fails = [];
  // --- item 10: horizontal overflow sweep ---
  for (const w of WIDTHS) {
    const browser = await lib.launch(w, 900);
    for (const p of PAGES) {
      const { page, problems } = await lib.newPage(browser, BASE + p);
      const m = await page.evaluate(() => ({
        sw: document.documentElement.scrollWidth,
        iw: window.innerWidth,
        clsSupported: !!window.PerformanceObserver,
      }));
      const overflow = m.sw > m.iw + 1;
      if (overflow) fails.push(`OVERFLOW ${p} @${w}px: scrollWidth=${m.sw} innerWidth=${m.iw}`);
      const errs = problems.filter(x => !/HTTP404.*definitely-not-a-page/.test(x));
      if (errs.length) fails.push(`ERRORS ${p} @${w}px: ${errs.join(' | ')}`);
      await page.close();
    }
    await browser.close();
    console.log(`width ${w}: done`);
  }
  // --- item 6: layout-shift (flicker) measurement on the two app pages ---
  for (const p of ['/', '/s/invalid-token-probe']) {
    const browser = await lib.launch(1366, 900);
    const page = (await lib.newPage(browser, BASE + p, { })).page;
    const cls = await page.evaluate(() => new Promise(res => {
      let cls = 0;
      try {
        new PerformanceObserver(list => {
          for (const e of list.getEntries()) if (!e.hadRecentInput) cls += e.value;
        }).observe({ type: 'layout-shift', buffered: true });
      } catch (e) { return res(-1); }
      setTimeout(() => res(cls), 3000);
    }));
    console.log(`CLS ${p}: ${cls}`);
    if (cls > 0.1) fails.push(`FLICKER ${p}: CLS=${cls.toFixed(3)} (>0.1 threshold)`);
    // open each main tab and re-measure quick shifts
    await browser.close();
  }
  console.log(fails.length ? 'FAILS:\n' + fails.join('\n') : 'ROUND7 PASS: no overflow on 10 pages x 4 widths, CLS within 0.1');
})().catch(e => { console.error('ROUND7 ERROR', e); process.exit(1); });
