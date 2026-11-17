// Smoke test for docs/tracker.js - the five-event counter.
//
// Run: node tools/node/tracker-smoke.mjs
//
// It stubs just enough DOM to execute the real tracker and asserts four things
// that matter for compliance rather than for marketing:
//   1. the three viewport events fire after the 1-second dwell;
//   2. a click on a sponsored link records affiliate_click with the ASIN and host;
//   3. NO network call is attempted while the endpoint is null (F-56) - the
//      fetch stub throws, so a regression fails loudly rather than silently
//      shipping reader events to an unintended host;
//   4. the local log holds no cookie, identifier or personal field.
//
// Node is a development dependency only; the published site has no runtime
// dependency on it.
const store = new Map();
const docListeners = []; const ios = [];
function mk(tag, attrs = {}) {
  const e = { tagName: tag, attrs, hidden: false, checked: false, _t: '',
    getAttribute(k){return attrs[k] ?? null;}, addEventListener(){}, textContent:'', innerHTML:'',
    classList:{add(){},remove(){}}, appendChild(){}, removeChild(){}, click(){}, querySelectorAll(){return [];} };
  Object.defineProperty(e, 'textContent', { get(){return e._t;}, set(v){e._t = String(v);} });
  return e;
}
const cardA = mk('article', {'data-product-card':'B0CDY277D3'});
const disclosure = mk('div'); const marker = mk('p');
global.document = {
  getElementById: () => null,
  querySelectorAll: s => s === '[data-product-card]' ? [cardA] : [],
  querySelector: s => s === '.disclosure' ? disclosure : s === '[data-read-complete]' ? marker : null,
  addEventListener: (t, fn, cap) => docListeners.push({t, fn, cap}),
  body: mk('body'), createElement: mk,
};
global.IntersectionObserver = class {
  constructor(cb) { this.cb = cb; }
  observe(target) { ios.push({ cb: this.cb, target }); }
  disconnect() {}
};
Object.defineProperty(globalThis, 'navigator', { value: {}, configurable: true });
global.localStorage = { getItem: k => store.get(k) ?? null, setItem: (k,v) => store.set(k,v) };
global.fetch = () => { throw new Error('network call must never happen'); };
global.location = { pathname: '/Zone4/docs/x.html', href: 'https://t/Zone4/docs/x.html' };
global.window = { IntersectionObserver: global.IntersectionObserver };
console.log('observers registered on load:', ios.length);
const src = (await import('node:fs')).readFileSync('docs/tracker.js','utf8');
new Function(src)();
console.log('observers after load:', ios.length, 'targets:', ios.map(o => o.target === cardA ? 'cardA' : o.target === disclosure ? 'disclosure' : o.target === marker ? 'marker' : '?'));
// fire intersecting now; tracker should arm a 1s timer
ios.forEach(o => o.cb([{ isIntersecting: true, target: o.target }]));
// A click on a sponsored link, dispatched to the document-level listeners.
const anchor = { getAttribute: k => ({ href: 'https://www.amazon.com/dp/B0CDY277D3?tag=shopnow047c-20',
                                       'data-track-asin': 'B0CDY277D3' }[k] ?? null) };
const clickEv = { target: { closest: sel => sel.includes('affiliate_click') ? anchor : null } };
docListeners.filter(l => l.t === 'click' && 'cap' in l).forEach(l => l.fn(clickEv));

setTimeout(() => {
  const ev = JSON.parse(store.get('zone4.events.v1') || '[]');
  const names = ev.map(e => e.event);
  const failures = [];
  for (const want of ['product_impression', 'disclosure_viewed', 'guide_read_complete', 'affiliate_click'])
    if (!names.includes(want)) failures.push(`missing event: ${want}`);
  const click = ev.find(e => e.event === 'affiliate_click');
  if (!click || click.asin !== 'B0CDY277D3') failures.push('affiliate_click did not record the ASIN');
  if (!click || click.destination_host !== 'www.amazon.com') failures.push('affiliate_click did not record the host');
  const allowed = new Set(['event', 'page_path', 'asin', 'destination_host', 'ts']);
  for (const e of ev)
    for (const k of Object.keys(e))
      if (!allowed.has(k)) failures.push(`unexpected field in event record: ${k} (privacy rule)`);
  console.log('events recorded:', names.join(', '));
  if (failures.length) {
    console.error('FAIL\n - ' + failures.join('\n - '));
    process.exit(1);
  }
  console.log('PASS: four events fired, the click carried its ASIN and host, no network call, no extra fields');
}, 1300);
