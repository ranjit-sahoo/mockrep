// Round 1: guest user, desktop. Full journey through every tool, every tab,
// and a print-to-PDF byte check on the interview report.
const { launch, newPage, click, typeIn, visibleText, isVisible, sleep } = require('./lib.cjs');
const fs = require('fs');
const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const log = [];
const fail = [];
function ok(name, detail) { log.push('PASS ' + name + (detail ? ' - ' + detail : '')); }
function bad(name, detail) { fail.push('FAIL ' + name + (detail ? ' - ' + detail : '')); }

(async () => {
  const browser = await launch();
  const { page, problems } = await newPage(browser, BASE + '/');

  // Landing
  if (await isVisible(page, '#cookieBar')) { await click(page, '#cookieOk'); ok('cookie bar accept'); }
  for (const [sel, name] of [['#sampleH', 'sample toggle'], ['#sampleTry', 'sample try'], ['#sampleFill', 'sample fill']]) {
    if (await isVisible(page, sel)) { await page.evaluate(s => document.querySelector(s).click(), sel); await sleep(400); ok('landing button ' + name); }
  }
  // Waitlist with a test address
  if (await isVisible(page, '#wlEmail')) {
    await typeIn(page, '#wlEmail', 'round1-guest@example.com');
    await page.evaluate(s => document.querySelector(s).click(), '#wlBtn'); await sleep(800);
    const msg = await visibleText(page, '#wlMsg');
    (msg && !/fail|error/i.test(msg) ? ok : bad)('waitlist signup', msg && msg.trim().slice(0, 80));
  }

  // Every tab switches to its tool view
  const tabs = await page.$$eval('#tabs button[data-t]', bs => bs.map(b => b.dataset.t));
  ok('tabs enumerated', tabs.join(','));
  for (const t of tabs) {
    await page.evaluate(tt => document.querySelector(`#tabs button[data-t="${tt}"]`).click(), t);
    await sleep(500);
    (await isVisible(page, '#t-' + t) ? ok : bad)('tab switch ' + t);
  }

  // Interview flow (5 questions in mock mode)
  await page.evaluate(() => document.querySelector('#tabs button[data-t="interview"]').click());
  await sleep(400);
  await typeIn(page, '#role', 'Product Manager');
  await page.evaluate(s => document.querySelector(s).click(), '#btnStart');
  try {
    await page.waitForFunction(() => {
      const q = document.querySelector('#qtext');
      const iv = document.querySelector('#interview');
      return iv && !iv.classList.contains('hide') && q && q.textContent.trim().length > 5;
    }, { timeout: 30000 });
    ok('interview started', (await visibleText(page, '#qtext')).slice(0, 60));
  } catch { bad('interview started', 'no question appeared'); }

  let answers = 0, nexts = 0;
  for (let i = 0; i < 24; i++) {
    const st = await page.evaluate(() => ({
      rep: !!document.querySelector('#btnRep'),
      next: !!(document.querySelector('#btnNext') && document.querySelector('#btnNext').offsetHeight),
      btnDis: document.querySelector('#btnAns') && document.querySelector('#btnAns').disabled,
      reportLen: (document.querySelector('#report') || { innerText: '' }).innerText.trim().length,
      reportVis: !!(document.querySelector('#report') && document.querySelector('#report').offsetHeight),
      err: (document.querySelector('#ansErr') || {}).textContent,
    }));
    if (st.reportVis && st.reportLen > 50) break;
    if (st.rep) { await page.evaluate(() => document.querySelector('#btnRep').click()); await sleep(3000); break; }
    if (st.next) { await page.evaluate(() => document.querySelector('#btnNext').click()); nexts++; await sleep(1200); continue; }
    if (!st.btnDis) {
      await typeIn(page, '#ans', 'In my previous role I led a cross-functional launch. I set weekly goals, unblocked design and engineering, and we shipped on time with 18% adoption in the first month.');
      await page.evaluate(s => document.querySelector(s).click(), '#btnAns');
      answers++;
      await sleep(3500);
      continue;
    }
    if (st.err) { bad('answer error', st.err); break; }
    await sleep(1500);
  }
  ok('interview submissions', answers + ' answers, ' + nexts + ' next-clicks');
  const reportShown = await page.evaluate(() => {
    const r = document.querySelector('#report');
    return r && r.offsetHeight > 0 && r.innerText.trim().length > 50;
  });
  (reportShown ? ok : bad)('interview report after ' + answers + ' answers');

  // Print-to-PDF byte check on the report (blank-PDF regression)
  if (reportShown) {
    await page.evaluate(() => document.querySelector('[data-pdf="report"]').click());
    await sleep(800);
    const prLen = await page.evaluate(() => (document.querySelector('#prArea') || { innerText: '' }).innerText.trim().length);
    (prLen > 200 ? ok : bad)('report prArea populated for print', 'chars=' + prLen);
    const pdf = await page.pdf({ printBackground: true });
    fs.writeFileSync('/tmp/r1-report.pdf', pdf);
    (pdf.length > 8000 ? ok : bad)('report PDF captured', pdf.length + ' bytes');
  }

  // Prep pack
  await page.evaluate(() => document.querySelector('#tabs button[data-t="prep"]').click());
  await sleep(400);
  if (await isVisible(page, '#prepLead')) {
    await typeIn(page, '#prepLead', 'Product Manager at a fintech startup');
    await page.evaluate(s => document.querySelector(s).click(), '#btnPrep');
    try {
      await page.waitForFunction(() => document.querySelector('#prepOut').innerText.trim().length > 80, { timeout: 30000 });
      ok('prep pack generated');
      await page.evaluate(() => document.querySelector('[data-pdf="prep"]').click());
      await sleep(800);
      const prLen = await page.evaluate(() => (document.querySelector('#prArea') || { innerText: '' }).innerText.trim().length);
      (prLen > 200 ? ok : bad)('prep prArea populated for print', 'chars=' + prLen);
      const pdfp = await page.pdf({ printBackground: true });
      fs.writeFileSync('/tmp/r1-prep.pdf', pdfp);
      (pdfp.length > 8000 ? ok : bad)('prep PDF captured', pdfp.length + ' bytes');
    } catch { bad('prep pack generated', 'empty after 30s'); }
  }

  // Resume builder: fill basics, add one exp/edu/prj, verify preview renders
  await page.evaluate(() => document.querySelector('#tabs button[data-t="builder"]').click());
  await sleep(400);
  await typeIn(page, '#rb_name', 'Round One Guest');
  await typeIn(page, '#rb_title', 'Product Manager');
  await typeIn(page, '#rb_summary', 'PM with 5 years across fintech and SaaS.');
  await typeIn(page, '#rb_skills', 'roadmaps, SQL, experimentation');
  await page.evaluate(s => document.querySelector(s).click(), '#rbAddExp'); await sleep(300);
  await page.evaluate(() => {
    const card = document.querySelector('#rbExp .rb-item, #rbExp [data-i]');
    if (card) {
      const set = (k, v) => { const el = card.querySelector(`[data-k="${k}"]`); if (el) { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); } };
      set('role', 'Product Manager'); set('org', 'Acme'); set('dates', '2021-2024');
      set('bullets', 'Shipped onboarding revamp, +18% activation');
    }
  });
  await sleep(500);
  const prevLen = await page.evaluate(() => document.querySelector('#rbPrev').innerText.trim().length);
  (prevLen > 50 ? ok : bad)('builder preview renders', 'chars=' + prevLen);
  if (await isVisible(page, '#rbPrint')) { await page.evaluate(s => document.querySelector(s).click(), '#rbPrint'); await sleep(600); ok('builder print button'); }
  const pdf2 = await page.pdf({ printBackground: true });
  fs.writeFileSync('/tmp/r1-builder.pdf', pdf2);
  ok('builder PDF captured', pdf2.length + ' bytes');

  // Button coverage census across views (no clicks, just enumeration here)
  const census = {};
  for (const t of tabs) {
    await page.evaluate(tt => document.querySelector(`#tabs button[data-t="${tt}"]`).click(), t);
    await sleep(400);
    census['t-' + t] = await page.evaluate(tt => {
      const sec = document.querySelector('#t-' + tt);
      return [...sec.querySelectorAll('button, a[href]')].filter(el => el.offsetWidth > 0).length;
    }, t);
  }
  ok('button census', JSON.stringify(census));

  console.log('--- ROUND1 RESULTS ---');
  log.forEach(l => console.log(l));
  fail.forEach(l => console.log(l));
  const realProblems = problems.filter(p => !/HTTP401: .*\/(api\/progress|api\/history)$/.test(p) && !/CONSOLE: Failed to load resource.*401/.test(p));
  console.log('PAGE PROBLEMS: ' + (realProblems.length ? '\n' + realProblems.join('\n') : 'none (guest 401s on /api/progress and /api/history are expected)'));
  console.log(fail.length === 0 && realProblems.length === 0 ? 'ROUND1 VERDICT: PASS' : 'ROUND1 VERDICT: ISSUES');
  await browser.close();
})().catch(e => { console.error('ROUND1 CRASH', e); process.exit(1); });
