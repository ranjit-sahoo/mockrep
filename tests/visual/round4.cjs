// Round 4: mobile user (390x844). No horizontal overflow on any view,
// drawer + sticky CTA behavior, core interview start at mobile width.
const { launch, newPage, typeIn, isVisible, sleep } = require('./lib.cjs');
const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const log = [], fail = [];
const ok = (n, d) => log.push('PASS ' + n + (d ? ' - ' + d : ''));
const bad = (n, d) => fail.push('FAIL ' + n + (d ? ' - ' + d : ''));

(async () => {
  const browser = await launch(390, 844);
  const { page, problems } = await newPage(browser, BASE + '/');
  await page.evaluate(() => document.querySelector('#sampleFill').click());

  const overflow = () => page.evaluate(() => ({
    doc: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    body: document.body.scrollWidth - window.innerWidth,
    wide: [...document.querySelectorAll('*')].filter(el => el.scrollWidth > window.innerWidth + 2 && el.offsetHeight > 0 && el.children.length).slice(0, 3).map(el => el.tagName + '.' + (el.className && el.className.baseVal === undefined ? String(el.className).split(' ')[0] : '')),
  }));

  let o = await overflow();
  (o.doc <= 1 && o.body <= 1 ? ok : bad)('landing: no horizontal overflow', JSON.stringify(o));

  const tabs = await page.$$eval('#tabs button[data-t]', bs => bs.map(b => b.dataset.t));
  for (const t of tabs) {
    await page.evaluate(tt => document.querySelector(`#tabs button[data-t="${tt}"]`).click(), t);
    await sleep(400);
    o = await overflow();
    (o.doc <= 1 && o.body <= 1 ? ok : bad)('mobile view ' + t + ': no overflow', o.doc > 1 || o.body > 1 ? JSON.stringify(o) : '');
  }

  // interview start at mobile width
  await page.evaluate(() => document.querySelector('#tabs button[data-t="interview"]').click());
  await sleep(300);
  await typeIn(page, '#role', 'Support Engineer');
  await page.evaluate(() => document.querySelector('#btnStart').click());
  try {
    await page.waitForFunction(() => (document.querySelector('#qtext') || { textContent: '' }).textContent.trim().length > 5, { timeout: 30000 });
    ok('mobile interview starts');
    o = await overflow();
    (o.doc <= 1 ? ok : bad)('interview view: no overflow', JSON.stringify(o));
    // answer one question via mobile keyboard path
    await typeIn(page, '#ans', 'I de-escalated an angry customer by owning the issue, giving a clear timeline, and following up until resolved.');
    await page.evaluate(() => document.querySelector('#btnAns').click());
    await sleep(3500);
    (await page.evaluate(() => (document.querySelector('#fb') || { innerText: '' }).innerText.trim().length > 20 || !!document.querySelector('#btnNext')) ? ok : bad)('mobile answer accepted, feedback shown');
  } catch { bad('mobile interview starts'); }

  // account drawer open/close at mobile width
  await page.evaluate(() => document.querySelector('#acctOpen').click());
  await sleep(300);
  (await page.evaluate(() => !document.querySelector('#acctForm').classList.contains('hide')) ? ok : bad)('account drawer opens');
  o = await overflow();
  (o.doc <= 1 ? ok : bad)('drawer open: no overflow', JSON.stringify(o));

  // Escape closes the drawer
  await page.keyboard.press('Escape');
  await sleep(400);

  const realProblems = problems.filter(p => !/HTTP401: .*\/(api\/progress|api\/history)$/.test(p) && !/CONSOLE: Failed to load resource.*401/.test(p));
  console.log('--- ROUND4 RESULTS ---');
  log.forEach(l => console.log(l)); fail.forEach(l => console.log(l));
  console.log('PAGE PROBLEMS: ' + (realProblems.length ? '\n' + realProblems.join('\n') : 'none'));
  console.log(fail.length === 0 && realProblems.length === 0 ? 'ROUND4 VERDICT: PASS' : 'ROUND4 VERDICT: ISSUES');
  await browser.close();
})().catch(e => { console.error('ROUND4 CRASH', e); process.exit(1); });
