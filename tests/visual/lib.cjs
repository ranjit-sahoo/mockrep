const puppeteer = require('puppeteer-core');

async function launch(width = 1366, height = 900, opts = {}) {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--force-device-scale-factor=1'],
    defaultViewport: { width, height },
  });
  return browser;
}

async function newPage(browser, url, opts = {}) {
  const page = await browser.newPage();
  const problems = [];
  page.on('pageerror', e => problems.push('PAGEERROR: ' + e.message));
  page.on('console', m => {
    if (m.type() === 'error') problems.push('CONSOLE: ' + m.text());
  });
  page.on('response', r => {
    if (r.status() >= 400 && !/favicon/.test(r.url())) problems.push('HTTP' + r.status() + ': ' + r.url());
  });
  page.on('requestfailed', r => {
    if (!/favicon|analytics/.test(r.url())) problems.push('REQFAIL: ' + r.url() + ' ' + (r.failure() || {}).errorText);
  });
  if (opts.reducedMotion) await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 45000 });
  return { page, problems };
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function click(page, sel) {
  await page.waitForSelector(sel, { timeout: 8000 });
  await page.evaluate(s => { const el = document.querySelector(s); if (!el) throw new Error('missing ' + s); el.click(); }, sel);
}

async function typeIn(page, sel, text) {
  await page.waitForSelector(sel, { timeout: 8000 });
  await page.evaluate((s, t) => {
    const el = document.querySelector(s);
    if (!el) throw new Error('missing ' + s);
    el.focus(); el.value = t;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, sel, text);
}

async function visibleText(page, sel) {
  return page.$eval(sel, el => el.innerText).catch(() => null);
}

async function isVisible(page, sel) {
  return page.$eval(sel, el => !!(el.offsetWidth || el.offsetHeight)).catch(() => false);
}

// Enumerate visible, enabled buttons and links within a root, click each in isolation
// (reload between clicks), and record outcome signals.
async function buttonSweep(browser, url, rootSel, opts = {}) {
  const results = [];
  const { page, problems } = await newPage(browser, url, opts);
  if (rootSel) await page.waitForSelector(rootSel, { timeout: 8000 });
  const targets = await page.evaluate((root) => {
    const scope = root ? document.querySelector(root) : document;
    const els = [...scope.querySelectorAll('button, a[href], [role=button]')];
    return els.map((el, i) => {
      const r = el.getBoundingClientRect();
      const vis = r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
      return {
        i, vis, disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
        tag: el.tagName.toLowerCase(),
        id: el.id || null,
        label: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('href') || '').trim().slice(0, 60),
        sel: el.id ? '#' + el.id : null,
      };
    }).filter(t => t.vis && !t.disabled);
  }, rootSel || null);
  await page.close();
  return { targets, problems };
}

// Click a single target by index among visible buttons, return outcome signals.
async function clickProbe(browser, url, rootSel, index, opts = {}) {
  const { page, problems } = await newPage(browser, url, opts);
  const before = page.url();
  const outcome = await page.evaluate((root, idx) => {
    const scope = root ? document.querySelector(root) : document;
    const els = [...scope.querySelectorAll('button, a[href], [role=button]')].filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && !el.disabled && getComputedStyle(el).visibility !== 'hidden';
    });
    const el = els[idx];
    if (!el) return { found: false };
    const mutBefore = document.body.innerHTML.length;
    el.click();
    return new Promise(res => setTimeout(() => {
      res({
        found: true,
        domChanged: document.body.innerHTML.length !== mutBefore,
        dialogOpen: !!document.querySelector('dialog[open], [role=dialog]:not([hidden])'),
      });
    }, 700));
  }, rootSel || null, index);
  await sleep(700);
  const after = page.url();
  outcome.navigated = after !== before;
  outcome.problems = problems.slice();
  await page.close();
  return outcome;
}

module.exports = { launch, newPage, click, typeIn, visibleText, isVisible, sleep, buttonSweep, clickProbe };
