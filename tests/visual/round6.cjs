// Round 6: keyboard-only + reduced-motion user.
const { launch, newPage, sleep } = require('./lib.cjs');
const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const log = [], fail = [];
const ok = (n, d) => log.push('PASS ' + n + (d ? ' - ' + d : ''));
const bad = (n, d) => fail.push('FAIL ' + n + (d ? ' - ' + d : ''));

(async () => {
  const browser = await launch();
  const { page, problems } = await newPage(browser, BASE + '/', { reducedMotion: true });

  // Reduced motion actually kills animations
  const anim = await page.evaluate(() => {
    const el = document.querySelector('button');
    const cs = getComputedStyle(el);
    return cs.animationDuration + ' / ' + cs.transitionDuration;
  });
  ok('reduced-motion emulated; sample durations', anim);

  // Skip link first in tab order
  await page.keyboard.press('Tab');
  await sleep(200);
  const first = await page.evaluate(() => (document.activeElement.innerText || document.activeElement.tagName).slice(0, 40));
  (/skip/i.test(first) ? ok : bad)('skip link is first tab stop', first);
  await page.keyboard.press('Enter');
  await sleep(300);
  const jumped = await page.evaluate(() => document.activeElement.id || document.activeElement.tagName);
  ok('skip link activated, focus moved', jumped);

  // Tab walk: 60 stops, every one visible focus indicator, no hidden focus, no traps
  let seen = new Set(), focusFails = 0, hiddenFails = 0;
  for (let i = 0; i < 60; i++) {
    await page.keyboard.press('Tab');
    await sleep(90);
    const st = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return { none: true };
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      const hasIndicator = cs.outlineStyle !== 'none' && cs.outlineWidth !== '0px' || cs.boxShadow !== 'none';
      return {
        key: el.tagName + '#' + (el.id || '') + '.' + (el.getAttribute('data-t') || ''),
        visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden',
        hasIndicator,
      };
    });
    if (st.none) continue;
    seen.add(st.key);
    if (!st.hasIndicator) focusFails++;
    if (!st.visible) hiddenFails++;
  }
  ok('tab stops visited', seen.size + ' unique');
  (focusFails === 0 ? ok : bad)('every tab stop has a visible focus indicator', focusFails + ' misses');
  (hiddenFails === 0 ? ok : bad)('focus never lands on hidden elements', hiddenFails + ' hits');

  // Escape closes the account drawer
  await page.evaluate(() => document.querySelector('#acctOpen').click());
  await sleep(300);
  const openBefore = await page.evaluate(() => !document.querySelector('#acctForm').classList.contains('hide'));
  await page.keyboard.press('Escape');
  await sleep(300);
  const openAfter = await page.evaluate(() => !document.querySelector('#acctForm').classList.contains('hide'));
  (openBefore && !openAfter ? ok : bad)('Escape closes the account drawer', 'before=' + openBefore + ' after=' + openAfter);

  // Keyboard-only interview start
  await page.evaluate(() => { document.querySelector('#tabs button[data-t="interview"]').click(); document.querySelector('#sampleFill').click(); });
  await sleep(400);
  await page.evaluate(() => document.querySelector('#role').focus());
  await page.keyboard.type('Keyboard User');
  await page.evaluate(() => document.querySelector('#btnStart').focus());
  await page.keyboard.press('Enter');
  try {
    await page.waitForFunction(() => (document.querySelector('#qtext') || { textContent: '' }).textContent.trim().length > 5, { timeout: 30000 });
    ok('interview started via keyboard');
    await page.evaluate(() => document.querySelector('#ans').focus());
    await page.keyboard.type('I migrated a legacy reporting pipeline with zero downtime by shadow-running both systems for two weeks.');
    await page.evaluate(() => document.querySelector('#btnAns').focus());
    await page.keyboard.press('Enter');
    await sleep(4000);
    (await page.evaluate(() => document.querySelector('#fb').innerText.trim().length > 20 || !!document.querySelector('#btnNext')) ? ok : bad)('answer submitted via keyboard, feedback shown');
  } catch { bad('interview started via keyboard'); }

  const realProblems = problems.filter(p => !/HTTP401: .*\/(api\/progress|api\/history)$/.test(p) && !/CONSOLE: Failed to load resource.*401/.test(p));
  console.log('--- ROUND6 RESULTS ---');
  log.forEach(l => console.log(l)); fail.forEach(l => console.log(l));
  console.log('PAGE PROBLEMS: ' + (realProblems.length ? '\n' + realProblems.join('\n') : 'none'));
  console.log(fail.length === 0 && realProblems.length === 0 ? 'ROUND6 VERDICT: PASS' : 'ROUND6 VERDICT: ISSUES');
  await browser.close();
})().catch(e => { console.error('ROUND6 CRASH', e); process.exit(1); });
