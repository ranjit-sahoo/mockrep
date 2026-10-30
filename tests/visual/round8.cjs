// Round 8: contrast-ratio computation on representative text elements (item 11 leftover)
const lib = require('./lib.cjs');
const BASE = 'http://127.0.0.1:8123';
function lum(rgb) {
  const m = rgb.match(/[\d.]+/g).map(Number);
  const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]);
}
function ratio(a, b) { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); }
(async () => {
  const browser = await lib.launch(1366, 900);
  const { page } = await lib.newPage(browser, BASE + '/');
  const samples = await page.evaluate(() => {
    const out = [];
    const pick = (sel, label) => {
      const el = document.querySelector(sel);
      if (!el) return;
      const cs = getComputedStyle(el);
      // find effective background by walking up
      // composite all background layers down the ancestor chain (alpha-aware)
      const parse = c => { const m = c.match(/[\d.]+/g).map(Number); return m.length === 3 ? [...m, 1] : m; };
      let base = [255, 255, 255, 1], n = el, grad = null;
      const stack = [];
      while (n) {
        const st = getComputedStyle(n);
        const b = st.backgroundColor;
        if (b && !b.endsWith(', 0)')) stack.push(parse(b));
        if (!grad && st.backgroundImage && st.backgroundImage.includes('gradient')) grad = st.backgroundImage;
        n = n.parentElement;
      }
      // composite top-down: start from opaque bottom (body/html)
      let comp = [0, 0, 0];
      for (let i = stack.length - 1; i >= 0; i--) {
        const [r, g, b, a] = stack[i];
        comp = [0, 1, 2].map(k => Math.round(stack[i][k] * a + comp[k] * (1 - a)));
      }
      let bg = 'rgb(' + comp.join(', ') + ')';
      if (grad) {
        const cols = [...grad.matchAll(/#[0-9a-fA-F]{6}|rgba?\([^)]*\)/g)].map(m => m[0]);
        if (cols.length) {
          // worst-case: use the LIGHTEST gradient stop for dark text, DARKEST for light text
          const toRgb = c => c.startsWith('#') ? [parseInt(c.slice(1,3),16), parseInt(c.slice(3,5),16), parseInt(c.slice(5,7),16)] : parse(c).slice(0,3);
          const rgbs = cols.map(toRgb);
          const tc = parse(cs.color).slice(0,3);
          const tLum = 0.2126*tc[0]+0.7152*tc[1]+0.0722*tc[2];
          const pickStop = tLum < 128 ? rgbs.reduce((a,b)=> (0.2126*a[0]+0.7152*a[1]+0.0722*a[2]) > (0.2126*b[0]+0.7152*b[1]+0.0722*b[2]) ? a : b)
                                      : rgbs.reduce((a,b)=> (0.2126*a[0]+0.7152*a[1]+0.0722*a[2]) < (0.2126*b[0]+0.7152*b[1]+0.0722*b[2]) ? a : b);
          bg = 'rgb(' + pickStop.join(', ') + ')';
        }
      }
      out.push({ label, sel, color: cs.color, bg, fs: parseFloat(cs.fontSize), bold: parseInt(cs.fontWeight) >= 700 });
    };
    pick('body', 'body text');
    pick('.foot', 'footer text');
    pick('.note', 'note text');
    pick('a', 'first link');
    pick('h1', 'h1');
    pick('.tab', 'tab');
    pick('button', 'first button');
    pick('.consent span', 'consent text');
    pick('details summary', 'faq summary');
    pick('details p', 'faq answer');
    return out;
  });
  let fails = 0;
  for (const s of samples) {
    if (!s.color || !s.bg || s.bg.includes('rgba(0, 0, 0, 0)')) { console.log('SKIP', s.label, s.color, s.bg); continue; }
    const r = ratio(s.color, s.bg);
    const need = (s.fs >= 18 || (s.fs >= 14 && s.bold)) ? 3.0 : 4.5;
    const ok = r >= need;
    if (!ok) fails++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${s.label}: ${r.toFixed(2)}:1 (needs ${need}) color=${s.color} bg=${s.bg} fs=${s.fs}`);
  }
  await browser.close();
  console.log(fails ? `ROUND8: ${fails} contrast failures` : 'ROUND8 PASS: all sampled text meets WCAG AA');
})().catch(e => { console.error('ROUND8 ERROR', e); process.exit(1); });
