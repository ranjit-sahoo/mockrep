// Round 3: signed-in power user. Interview -> history saved, then every pro tool:
// review, match, star, brief, nego, bank, code, recruiter, builder with experience.
const { launch, newPage, typeIn, visibleText, isVisible, sleep } = require('./lib.cjs');
const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const log = [], fail = [];
const ok = (n, d) => log.push('PASS ' + n + (d ? ' - ' + d : ''));
const bad = (n, d) => fail.push('FAIL ' + n + (d ? ' - ' + d : ''));
const EMAIL = 'round3-' + Date.now() + '@example.com';
const tab = (page, t) => page.evaluate(tt => document.querySelector(`#tabs button[data-t="${tt}"]`).click(), t);

(async () => {
  const browser = await launch();
  const { page, problems } = await newPage(browser, BASE + '/');
  await page.evaluate(() => document.querySelector('#sampleFill').click());
  await sleep(400);

  // register
  await page.evaluate(() => document.querySelector('#acctOpen').click());
  await typeIn(page, '#acEmail', EMAIL);
  await typeIn(page, '#acPw', 'correct-horse-9');
  await page.evaluate(() => { document.querySelector('#acAge').click(); document.querySelector('#acAgree').click(); });
  await page.evaluate(() => document.querySelector('#acReg').click());
  await sleep(1500);
  (await page.evaluate(() => !document.querySelector('#acctOut').classList.contains('hide')) ? ok : bad)('registered', EMAIL);

  // short interview (2 questions, followups off)
  await tab(page, 'interview'); await sleep(300);
  await page.evaluate(() => { document.querySelector('#ivFu').checked = false; });
  await typeIn(page, '#role', 'Data Analyst');
  await page.evaluate(() => document.querySelector('#btnStart').click());
  await sleep(4000);
  let finished = false;
  for (let i = 0; i < 10 && !finished; i++) {
    const st = await page.evaluate(() => ({
      rep: !!document.querySelector('#btnRep'),
      next: !!(document.querySelector('#btnNext') && document.querySelector('#btnNext').offsetHeight),
      btnDis: document.querySelector('#btnAns') && document.querySelector('#btnAns').disabled,
      q: (document.querySelector('#qnum') || {}).textContent,
    }));
    if (st.rep) { await page.evaluate(() => document.querySelector('#btnRep').click()); await sleep(3000); finished = true; break; }
    if (st.next) { await page.evaluate(() => document.querySelector('#btnNext').click()); await sleep(1000); continue; }
    if (!st.btnDis) {
      await typeIn(page, '#ans', 'I built a churn model that flagged at-risk accounts, then worked with CS on playbooks that cut churn 12%.');
      await page.evaluate(() => document.querySelector('#btnAns').click());
      await sleep(3500); continue;
    }
    await sleep(1500);
  }
  const repLen = await page.evaluate(() => document.querySelector('#report').innerText.trim().length);
  (finished && repLen > 50 ? ok : bad)('interview complete, report shown', 'chars=' + repLen);

  // history shows the saved session
  await tab(page, 'history'); await sleep(1500);
  const hist = await page.evaluate(() => document.querySelector('#t-history').innerText);
  (/Data Analyst|interview|score/i.test(hist) ? ok : bad)('history lists the interview', hist.replace(/\n+/g, ' ').slice(0, 90));

  // review (resume review)
  await tab(page, 'review'); await sleep(300);
  if (await isVisible(page, '#btnReview')) {
    await page.evaluate(() => document.querySelector('#btnReview').click());
    try { await page.waitForFunction(() => document.querySelector('#reviewOut').innerText.trim().length > 60, { timeout: 30000 }); ok('resume review generated'); }
    catch { bad('resume review generated'); }
  }

  // match (JD match)
  await tab(page, 'match'); await sleep(300);
  if (await isVisible(page, '#btnMatch')) {
    await page.evaluate(() => document.querySelector('#btnMatch').click());
    try { await page.waitForFunction(() => document.querySelector('#matchOut').innerText.trim().length > 60, { timeout: 30000 }); ok('JD match generated'); }
    catch { bad('JD match generated'); }
  }

  // star
  await tab(page, 'star'); await sleep(300);
  if (await isVisible(page, '#btnStar')) {
    await typeIn(page, '#stQ', 'Tell me about a time you disagreed with a manager.'); await typeIn(page, '#stExp', 'At Acme I pushed back on a plan to skip load testing, showed the risk with data, and we agreed on a one-week hardening sprint.');
    await page.evaluate(() => document.querySelector('#btnStar').click());
    try { await page.waitForFunction(() => document.querySelector('#starOut').innerText.trim().length > 60, { timeout: 30000 }); ok('STAR answer generated'); }
    catch { bad('STAR answer generated'); }
  }

  // brief
  await tab(page, 'brief'); await sleep(300);
  if (await isVisible(page, '#btnBrief')) {
    await typeIn(page, '#bfCo', 'Zomato');
    await page.evaluate(() => document.querySelector('#btnBrief').click());
    try { await page.waitForFunction(() => document.querySelector('#briefOut').innerText.trim().length > 60, { timeout: 30000 }); ok('company brief generated'); }
    catch { bad('company brief generated'); }
  }

  // negotiation
  await tab(page, 'nego'); await sleep(300);
  if (await isVisible(page, '#btnNego')) {
    await typeIn(page, '#role', 'Data Analyst').catch(() => {});
    await page.evaluate(() => document.querySelector('#btnNego').click());
    try {
      await page.waitForFunction(() => !document.querySelector('#negoBox').classList.contains('hide') && document.querySelector('#chat').innerText.trim().length > 20, { timeout: 30000 });
      ok('negotiation started');
      await typeIn(page, '#negoMsg', 'Based on my research of the market range, I was expecting 14 LPA.');
      await page.evaluate(() => document.querySelector('#btnSay').click());
      await sleep(4000);
      const chat = await page.evaluate(() => document.querySelector('#chat').innerText.trim().length);
      (chat > 100 ? ok : bad)('negotiation reply received', 'chars=' + chat);
    } catch { bad('negotiation started'); }
  }

  // question bank
  await tab(page, 'bank'); await sleep(300);
  if (await isVisible(page, '#btnBank')) {
    await page.evaluate(() => document.querySelector('#btnBank').click());
    try { await page.waitForFunction(() => document.querySelector('#bankOut').innerText.trim().length > 40, { timeout: 15000 }); ok('question bank renders'); }
    catch { bad('question bank renders'); }
  }

  // coding practice
  await tab(page, 'code'); await sleep(500);
  const codeCount = await page.evaluate(() => document.querySelectorAll('#cpList [data-pid], #cpList button, #cpList .cp-item').length);
  if (codeCount > 0) {
    await page.evaluate(() => { const el = document.querySelector('#cpList [data-pid], #cpList button, #cpList .cp-item'); el.click(); });
    await sleep(800);
    (await page.evaluate(() => document.querySelector('#cpStmt').innerText.trim().length > 20) ? ok : bad)('coding problem opens');
    await typeIn(page, '#cpCode', 'def solve(nums):\n    return sorted(nums)');
    await page.evaluate(() => document.querySelector('#cpEval').click());
    try { await page.waitForFunction(() => document.querySelector('#cpOut').innerText.trim().length > 30, { timeout: 30000 }); ok('coding evaluation returns'); }
    catch { bad('coding evaluation returns'); }
    await page.evaluate(() => document.querySelector('#cpHint').click());
    try { await page.waitForFunction(() => document.querySelector('#cpHints').innerText.trim().length > 10, { timeout: 30000 }); ok('coding hint returns'); }
    catch { bad('coding hint returns'); }
  } else bad('coding list populated', 'count=0');

  // builder with one experience entry
  await tab(page, 'builder'); await sleep(300);
  await typeIn(page, '#rb_name', 'Round Three User');
  await page.evaluate(() => document.querySelector('#rbAddExp').click());
  await sleep(400);
  const expFields = await page.evaluate(() => {
    const card = document.querySelector('#rbExp').lastElementChild;
    if (!card) return 0;
    let n = 0;
    card.querySelectorAll('input,textarea').forEach((el, i) => { el.value = ['Data Analyst', 'Acme Corp', '2021-2024', 'Cut churn 12% with a risk model'][i] || 'x'; el.dispatchEvent(new Event('input', { bubbles: true })); n++; });
    return n;
  });
  await sleep(500);
  const prev = await page.evaluate(() => document.querySelector('#rbPrev').innerText);
  (prev.includes('Acme Corp') ? ok : bad)('builder experience renders in preview', expFields + ' fields');

  const realProblems = problems.filter(p => !/HTTP401: .*\/(api\/progress|api\/history)$/.test(p) && !/CONSOLE: Failed to load resource.*401/.test(p));
  console.log('--- ROUND3 RESULTS ---');
  log.forEach(l => console.log(l)); fail.forEach(l => console.log(l));
  console.log('PAGE PROBLEMS: ' + (realProblems.length ? '\n' + realProblems.join('\n') : 'none'));
  console.log(fail.length === 0 && realProblems.length === 0 ? 'ROUND3 VERDICT: PASS' : 'ROUND3 VERDICT: ISSUES');
  await browser.close();
})().catch(e => { console.error('ROUND3 CRASH', e); process.exit(1); });
