// Round 5: attacker. IDOR, injection, rate limits, malformed inputs, admin probing.
const { launch, newPage, typeIn, sleep } = require('./lib.cjs');
const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const log = [], fail = [];
const ok = (n, d) => log.push('PASS ' + n + (d ? ' - ' + d : ''));
const bad = (n, d) => fail.push('FAIL ' + n + (d ? ' - ' + d : ''));

(async () => {
  const browser = await launch();
  const { page, problems } = await newPage(browser, BASE + '/');
  const api = (path, opts) => page.evaluate(async (p, o) => {
    try {
      const r = await fetch(p, Object.assign({ headers: { 'Content-Type': 'application/json' } }, o || {}));
      const t = await r.text();
      return { status: r.status, body: t.slice(0, 200) };
    } catch (e) { return { status: 0, body: String(e) }; }
  }, path, opts);

  // 1. Malformed / bogus session IDs
  for (const sid of ['bogus', '../../etc/passwd', 'null', '1'.repeat(40), '<script>']) {
    const r = await api('/api/session/' + encodeURIComponent(sid) + '/state');
    (r.status >= 400 && r.status < 500 && !/stack|trace|exception|sqlite|postgres/i.test(r.body) ? ok : bad)('bogus session id rejected cleanly', sid.slice(0, 16) + ' -> ' + r.status);
  }

  // 2. Create a real guest session, then try to read it from a second context without the tab's bearer
  await page.evaluate(() => document.querySelector('#sampleFill').click());
  await sleep(300);
  await page.evaluate(() => document.querySelector('#tabs button[data-t="interview"]').click());
  await typeIn(page, '#role', 'Analyst');
  await page.evaluate(() => document.querySelector('#btnStart').click());
  await sleep(4000);
  const sid = await page.evaluate(() => sessionStorage.getItem('mr_interview'));
  ok('guest session created', sid);
  const ctx2 = await browser.createBrowserContext();
  const p2 = await ctx2.newPage();
  await p2.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  const stolen = await p2.evaluate(async (s) => {
    const r = await fetch('/api/session/' + s + '/state');
    return { status: r.status, body: (await r.text()).slice(0, 200) };
  }, sid);
  ((stolen.status === 401 || stolen.status === 403 || stolen.status === 404) && !/question|answer/i.test(stolen.body) ? ok : bad)('IDOR: session state not readable from another browser', 'status=' + stolen.status);
  const stolenRep = await p2.evaluate(async (s) => {
    const r = await fetch('/api/session/' + s + '/report');
    return { status: r.status };
  }, sid);
  ((stolenRep.status === 401 || stolenRep.status === 403 || stolenRep.status === 404) ? ok : bad)('IDOR: report not readable from another browser', 'status=' + stolenRep.status);

  // 3. XSS payload as an interview answer - must be stored/rendered escaped
  const xss = '<img src=x onerror="window.__xss=1"><svg onload="window.__xss=2">';
  await page.evaluate(() => { const a = document.querySelector('#ans'); a.value = ''; });
  await typeIn(page, '#ans', xss + ' I handled a production incident by rolling back within minutes.');
  await page.evaluate(() => document.querySelector('#btnAns').click());
  await sleep(4000);
  const xssFired = await page.evaluate(() => !!(window.__xss || document.querySelector('#fb img[src="x"], #fb svg')));
  (!xssFired ? ok : bad)('XSS payload in answer is escaped');
  const histXss = await page.evaluate(() => {
    const fb = document.querySelector('#fb');
    return fb ? fb.innerHTML.includes('onerror') && !fb.innerHTML.includes('&lt;img') ? 'RAW-HTML' : 'escaped-or-stripped' : 'no-fb';
  });
  (histXss !== 'RAW-HTML' ? ok : bad)('feedback HTML does not contain raw payload', histXss);

  // 4. Oversized answer
  const big = 'x'.repeat(60000);
  const bigRes = await api('/api/session/' + sid + '/answer', { method: 'POST', body: JSON.stringify({ answer: big }) });
  ((bigRes.status === 400 || bigRes.status === 413 || bigRes.status === 422) ? ok : bad)('oversized answer rejected', 'status=' + bigRes.status);

  // 5. Rate limiting on login
  let last = 0;
  for (let i = 0; i < 15; i++) {
    const r = await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ email: 'attacker@example.com', password: 'wrong-pass-' + i, role: 'candidate' }) });
    last = r.status;
    if (last === 429) break;
  }
  (last === 429 ? ok : bad)('login rate limit kicks in', 'final status=' + last);

  // 6. Admin endpoint without token
  const adm = await api('/api/admin/block-card', { method: 'POST', body: JSON.stringify({ token: 'x' }) });
  ((adm.status === 401 || adm.status === 403) ? ok : bad)('admin endpoint rejects no-token call', 'status=' + adm.status);

  // 7. Shared card token guessing
  const card = await api('/c/definitely-not-a-real-token-123');
  (card.status === 404 ? ok : bad)('card token guess 404s', 'status=' + card.status);

  // 8. History/progress of another user without auth
  const hist = await api('/api/history');
  (hist.status === 401 ? ok : bad)('history requires auth', 'status=' + hist.status);

  console.log('--- ROUND5 RESULTS ---');
  log.forEach(l => console.log(l)); fail.forEach(l => console.log(l));
  const realProblems = problems.filter(p => !/HTTP(401|403|404|429|400|413|422):/.test(p) && !/CONSOLE: Failed to load resource/.test(p));
  console.log('PAGE PROBLEMS (beyond expected 4xx): ' + (realProblems.length ? '\n' + realProblems.join('\n') : 'none'));
  console.log(fail.length === 0 ? 'ROUND5 VERDICT: PASS' : 'ROUND5 VERDICT: ISSUES');
  await browser.close();
})().catch(e => { console.error('ROUND5 CRASH', e); process.exit(1); });
