// Round 2: account user. Signup validation gates, register, logout, wrong/right
// login, session persistence across reload, history tab gating.
const { launch, newPage, typeIn, visibleText, isVisible, sleep } = require('./lib.cjs');
const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const log = [], fail = [];
const ok = (n, d) => log.push('PASS ' + n + (d ? ' - ' + d : ''));
const bad = (n, d) => fail.push('FAIL ' + n + (d ? ' - ' + d : ''));
const EMAIL = 'round2-' + Date.now() + '@example.com';

(async () => {
  const browser = await launch();
  const { page, problems } = await newPage(browser, BASE + '/');
  const err = () => visibleText(page, '#acErr');
  const loggedIn = () => page.evaluate(() => !document.querySelector('#acctOut').classList.contains('hide'));

  await page.evaluate(() => document.querySelector('#acctOpen').click());
  await sleep(300);

  // Validation gates
  await typeIn(page, '#acEmail', 'not-an-email');
  await page.evaluate(() => document.querySelector('#acAge').click());
  await page.evaluate(() => document.querySelector('#acAgree').click());
  await page.evaluate(() => document.querySelector('#acReg').click()); await sleep(400);
  (/valid email/.test(await err()) ? ok : bad)('gate: bad email rejected', await err());

  await typeIn(page, '#acEmail', EMAIL);
  await typeIn(page, '#acPw', 'short');
  await page.evaluate(() => document.querySelector('#acReg').click()); await sleep(400);
  (/at least 8/.test(await err()) ? ok : bad)('gate: short password rejected', await err());

  await typeIn(page, '#acPw', 'correct-horse-9');
  await page.evaluate(() => document.querySelector('#acAgree').click()); // untick agree
  await page.evaluate(() => document.querySelector('#acReg').click()); await sleep(400);
  (/Terms of Use/.test(await err()) ? ok : bad)('gate: consent required', await err());

  await page.evaluate(() => document.querySelector('#acAgree').click()); // retick
  await page.evaluate(() => document.querySelector('#acAge').click()); // untick age
  await page.evaluate(() => document.querySelector('#acReg').click()); await sleep(400);
  (/18 and above/.test(await err()) ? ok : bad)('gate: age required', await err());
  await page.evaluate(() => document.querySelector('#acAge').click()); // retick

  // Real register
  await page.evaluate(() => document.querySelector('#acReg').click()); await sleep(1500);
  (await loggedIn() ? ok : bad)('register succeeds', EMAIL);

  // History tab visible only when logged in
  (await page.evaluate(() => !document.querySelector('#tabHist').classList.contains('hide')) ? ok : bad)('history tab visible when logged in');

  // Logout
  await page.evaluate(() => document.querySelector('#acctOut').click()); await sleep(1200);
  (!(await loggedIn()) ? ok : bad)('logout works');
  (await page.evaluate(() => document.querySelector('#tabHist').classList.contains('hide')) ? ok : bad)('history tab hidden after logout');

  // Wrong password
  await typeIn(page, '#acEmail', EMAIL);
  await typeIn(page, '#acPw', 'wrong-password-1');
  await page.evaluate(() => document.querySelector('#acLogin').click()); await sleep(1200);
  const e1 = await err();
  (e1 && e1.trim().length > 3 ? ok : bad)('wrong password rejected', e1 && e1.trim().slice(0, 60));

  // Right password
  await typeIn(page, '#acPw', 'correct-horse-9');
  await page.evaluate(() => document.querySelector('#acLogin').click()); await sleep(1500);
  (await loggedIn() ? ok : bad)('login succeeds');

  // Persistence across reload
  await page.reload({ waitUntil: 'networkidle0' }); await sleep(1000);
  (await loggedIn() ? ok : bad)('session persists across reload');

  // Duplicate register rejected
  await page.evaluate(() => document.querySelector('#acctOut').click()); await sleep(1000);
  await typeIn(page, '#acEmail', EMAIL);
  await typeIn(page, '#acPw', 'correct-horse-9');
  await page.evaluate(() => document.querySelector('#acReg').click()); await sleep(1500);
  const e2 = await err();
  (e2 && e2.trim().length > 3 ? ok : bad)('duplicate register rejected', e2 && e2.trim().slice(0, 60));

  const realProblems = problems.filter(p => !/HTTP401: .*\/(api\/progress|api\/history|api\/auth\/login|api\/auth\/register)$/.test(p) && !/CONSOLE: Failed to load resource.*40[13]/.test(p));
  console.log('--- ROUND2 RESULTS ---');
  log.forEach(l => console.log(l)); fail.forEach(l => console.log(l));
  console.log('PAGE PROBLEMS: ' + (realProblems.length ? '\n' + realProblems.join('\n') : 'none unexpected (401s on auth probes are by design)'));
  console.log(fail.length === 0 && realProblems.length === 0 ? 'ROUND2 VERDICT: PASS' : 'ROUND2 VERDICT: ISSUES');
  await browser.close();
})().catch(e => { console.error('ROUND2 CRASH', e); process.exit(1); });
