// Generated-client contracts. No browser request or Amazon navigation is made by these fixtures.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const origin = 'https://kanlerxz87-cyber.github.io';
const root = `${origin}/Zone4/docs/`;
const endpoint = 'https://collector.example/event';
const client = fs.readFileSync('docs/measure.js', 'utf8');
const guidePath = 'guides/basket-or-oven-style-air-fryer-what-to-compare.html';
const guide = fs.readFileSync(`docs/${guidePath}`, 'utf8');
const home = fs.readFileSync('docs/index.html', 'utf8');

function browser({ url = endpoint, privacy = {}, dnt, fetchError = false, fetchThrow = false,
                   href = `${root}${guidePath}?utm_source=private#bookmark`, script = `${root}measure.js`,
                   noFetch = false, noObserver = false, hasGuide = true } = {}) {
  const requests = [], listeners = {}, observer = {};
  const article = { style: {}, appendChild(marker) { this.marker = marker; } };
  const window = { doNotTrack: dnt };
  if (!noObserver) { window.IntersectionObserver = true; }
  const document = {
    currentScript: script ? { src: script } : null,
    querySelector(selector) {
      return selector === 'article.guide, article.post' ? (hasGuide ? article : null) : { getAttribute: () => url };
    },
    addEventListener(name, handler) { listeners[name] = handler; },
    createElement() { return { style: {}, setAttribute() {} }; },
  };
  for (const field of ['cookie', 'referrer']) {
    Object.defineProperty(document, field, { get() { throw new Error(`must not read ${field}`); } });
  }
  Object.defineProperty(window, 'localStorage', { get() { throw new Error('must not read browser storage'); } });
  const context = {
    URL, document, window,
    navigator: new Proxy(privacy, { get(target, field) {
      if (field === 'userAgent') { throw new Error('must not read user agent'); }
      return target[field];
    } }),
    location: new URL(href),
    IntersectionObserver: class {
      constructor(handler) { observer.update = handler; }
      observe(marker) { observer.marker = marker; }
      disconnect() { observer.disconnected = true; }
    },
  };
  if (!noFetch) {
    context.fetch = (url, options) => {
      requests.push({ url, options });
      if (fetchThrow) { throw new Error('offline fixture'); }
      return fetchError ? Promise.reject(new Error('offline fixture')) : Promise.resolve();
    };
  }
  vm.runInNewContext(client, context);
  return {
    requests, listeners, observer, article, window,
    click(href, rel = '', { type = 'click', button = 0, isTrusted = true, defaultPrevented = false } = {}) {
      const ev = { type, button, isTrusted, defaultPrevented,
        preventDefault() { throw new Error('measurement must not prevent navigation'); },
        target: { closest: () => ({ href, getAttribute: key => key === 'rel' ? rel : null }) } };
      if (listeners[type]) { listeners[type](ev); }
      return ev;
    },
  };
}

// The three PR #119 contracts remain; extra cases tighten boundaries without replacing them.
test('blank config, Do Not Track and Global Privacy Control make the client inert', () => {
  for (const input of [{ url: '' }, { privacy: { doNotTrack: '1' } }, { dnt: '1' }, { privacy: { globalPrivacyControl: true } }]) {
    const app = browser(input);
    assert.deepEqual(app.requests, []);
    assert.deepEqual(app.listeners, {});
    assert.equal(app.observer.update, undefined);
  }
});

test('real generated relative links emit the five events without affiliate queries or visitor metadata', () => {
  const app = browser();
  const feed = guide.match(/<a\s+href="([^"]+)">RSS feed<\/a>/)[1];
  const category = guide.match(/href="(\.\.\/categories\/meat-thermometers\.html)"/)[1];
  const outbound = home.match(/href="(https:\/\/www\.amazon\.com\/dp\/B0CDY277D3\?tag=[^"]+)"/)[1];
  app.click(outbound, 'noopener Sponsored noreferrer');
  app.click(category);
  app.click(feed, '', { type: 'auxclick', button: 1 });
  assert.equal(app.observer.marker, app.article.marker);
  assert.match(app.article.marker.style.cssText, /top:75%/);
  app.observer.update([{ isIntersecting: false }]);
  app.observer.update([{ isIntersecting: true }, { isIntersecting: true }]);
  app.observer.update([{ isIntersecting: true }]);
  assert.ok(app.observer.disconnected);
  const payloads = app.requests.map(({ options }) => JSON.parse(options.body));
  assert.deepEqual(payloads, [
    { event: 'page_view', path: `/Zone4/docs/${guidePath}` },
    { event: 'outbound_click', path: `/Zone4/docs/${guidePath}`, asin: 'B0CDY277D3' },
    { event: 'category_click', path: `/Zone4/docs/${guidePath}`, target: '/Zone4/docs/categories/meat-thermometers.html' },
    { event: 'feed_click', path: `/Zone4/docs/${guidePath}` },
    { event: 'guide_read_75', path: `/Zone4/docs/${guidePath}` },
  ]);
  for (const { url, options } of app.requests) {
    assert.equal(url, endpoint);
    assert.equal(options.method, 'POST');
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.equal(options.credentials, 'omit');
    assert.equal(options.redirect, 'error');
    assert.equal(options.keepalive, true);
    assert.equal(options.referrerPolicy, 'no-referrer');
    assert.equal(options.cache, 'no-store');
  }
  // Used only by the Python end-to-end test in a TemporaryDirectory, never the public ledger.
  if (process.env.ZONE4_TEST_PAYLOAD_FILE) {
    fs.writeFileSync(process.env.ZONE4_TEST_PAYLOAD_FILE, JSON.stringify(payloads));
  }
});

test('unrelated links and scripted clicks are ignored; network failure is best effort', () => {
  const app = browser({ fetchError: true });
  app.click('https://www.amazon.com/dp/B0CDY277D3', 'not-sponsored');
  app.click('https://www.amazon.com/gp/help/customer/display.html', 'sponsored');
  app.click('https://other.example/Zone4/docs/feed.xml');
  app.click('/other/feed.xml');
  app.click('../feed.xml', '', { isTrusted: false });
  app.click('../feed.xml', '', { type: 'auxclick', button: 2 });
  assert.equal(app.requests.length, 1);
});

test('invalid and unsafe endpoint URLs are inert', () => {
  for (const url of ['http://collector.example/event', 'javascript:alert(1)', '/event', 'bad-url',
                     'https://collector.example/event?secret=1', 'https://collector.example/event#secret',
                     'https://user:secret@collector.example/event', 'https://collector.example/not-event']) {
    assert.deepEqual(browser({ url }).requests, [], url);
  }
});

test('missing fetch or script information is inert rather than breaking the page', () => {
  assert.deepEqual(browser({ noFetch: true }).requests, []);
  assert.deepEqual(browser({ script: null }).requests, []);
});

test('preview hosts and unknown page paths never send production telemetry', () => {
  assert.deepEqual(browser({ script: 'https://preview.example/docs/measure.js' }).requests, []);
  for (const href of ['https://preview.example/docs/index.html', `${root}private-user`, `${root}missing.html`,
                      `${root}categories/private-name.html`, `${root}customer%40example.com`]) {
    assert.deepEqual(browser({ href }).requests, [], href);
  }
});

test('directory aliases share the known canonical index path', () => {
  for (const [href, expected] of [[root, '/Zone4/docs/index.html'], [`${root}guides/`, '/Zone4/docs/guides/index.html']]) {
    const app = browser({ href, hasGuide: false });
    assert.deepEqual(JSON.parse(app.requests[0].options.body), { event: 'page_view', path: expected });
  }
});

test('outbound clicks require catalog ASIN, exact product path, sponsored token and selected tag', () => {
  const app = browser();
  for (const href of ['https://www.amazon.com/dp/B000000000?tag=shopnow047c-20',
                      'https://www.amazon.com/dp/B0CDY277D3?tag=someoneelse-20',
                      'https://www.amazon.com/dp/B0CDY277D3',
                      'https://www.amazon.com/dp/B0CDY277D3/extra?tag=shopnow047c-20',
                      'https://www.amazon.com.evil.example/dp/B0CDY277D3?tag=shopnow047c-20']) {
    app.click(href, 'sponsored');
  }
  app.click('https://www.amazon.com/dp/B0CDY277D3?tag=shopnow047c-20', 'not-sponsored');
  assert.equal(app.requests.length, 1);
  app.click('https://www.amazon.com/dp/B0CDY277D3?tag=shopnow047c-20', 'sponsored');
  assert.equal(JSON.parse(app.requests[1].options.body).asin, 'B0CDY277D3');
});

test('category targets are allowlisted public paths without query strings', () => {
  const app = browser();
  app.click('../categories/missing.html');
  app.click('../categories/meat-thermometers.html?email=private#bookmark');
  const payload = JSON.parse(app.requests[1].options.body);
  assert.deepEqual(payload, { event: 'category_click', path: `/Zone4/docs/${guidePath}`,
    target: '/Zone4/docs/categories/meat-thermometers.html' });
  assert.equal(app.requests.length, 2);
});

test('cancelled, right-button, synthetic and malformed link activations are ignored', () => {
  const app = browser();
  app.click('../feed.xml', '', { defaultPrevented: true });
  app.click('../feed.xml', '', { button: 2 });
  app.click('../feed.xml', '', { isTrusted: false });
  app.click('http://[');
  assert.equal(app.requests.length, 1);
  app.click('../feed.xml'); // includes keyboard activation's zero-button contract
  app.click('../feed.xml', '', { type: 'auxclick', button: 1 });
  assert.equal(app.requests.length, 3);
});

test('privacy signals are rechecked before every event, not only at page load', () => {
  const privacy = {};
  const app = browser({ privacy });
  privacy.globalPrivacyControl = true;
  app.click('../feed.xml');
  assert.equal(app.requests.length, 1);
  privacy.globalPrivacyControl = false;
  privacy.doNotTrack = '1';
  app.click('../feed.xml');
  assert.equal(app.requests.length, 1);
  privacy.doNotTrack = '0';
  app.window.doNotTrack = '1';
  app.click('../feed.xml');
  assert.equal(app.requests.length, 1);
});

test('published article milestones remain supported but hubs and other pages have no marker', () => {
  const article = browser({ href: `${root}articles/air-fryer-buying-guide-2026.html` });
  assert.equal(article.observer.marker, article.article.marker);
  article.observer.update([{ isIntersecting: true }]);
  assert.deepEqual(JSON.parse(article.requests[1].options.body), {
    event: 'guide_read_75', path: '/Zone4/docs/articles/air-fryer-buying-guide-2026.html',
  });
  for (const href of [`${root}articles/index.html`, `${root}guides/index.html`, `${root}products.html`]) {
    assert.equal(browser({ href }).observer.marker, undefined);
  }
});

test('no IntersectionObserver leaves reading and other counters functional', () => {
  const app = browser({ noObserver: true });
  assert.equal(app.article.marker, undefined);
  app.click('../feed.xml');
  assert.equal(app.requests.length, 2);
});

test('synchronous fetch failures do not interfere with navigation', () => {
  const app = browser({ fetchThrow: true });
  assert.doesNotThrow(() => app.click('../feed.xml'));
  assert.equal(app.requests.length, 2);
});

test('the compiled allowlist covers exactly the built routes and published product intents', () => {
  const config = JSON.parse(client.match(/var CONFIG = (\{[^\n]+\});/)[1]);
  function pages(dir) {
    return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
      const name = path.join(dir, entry.name);
      return entry.isDirectory() ? pages(name) : (name.endsWith('.html') ? [name.slice(5)] : []);
    });
  }
  assert.deepEqual(config.paths, pages('docs').sort());
  assert.deepEqual(config.categories, config.paths.filter(p => p.startsWith('categories/')));
  assert.deepEqual(config.guides, config.paths.filter(p => /^(guides|articles)\//.test(p) && !p.endsWith('/index.html')));
  const intents = JSON.parse(fs.readFileSync('data/intent-links.json', 'utf8'));
  assert.deepEqual(config.asins, intents.links.filter(l => l.published_outbound_url).map(l => l.intended_asin).sort());
  assert.equal(config.tracking_id, intents._meta.tracking_id);
  const source = fs.readFileSync('analytics-endpoint/client.js', 'utf8');
  assert.equal(source.replace('__ZONE4_CONFIG__', client.match(/var CONFIG = (\{[^\n]+\});/)[1]), client);
});
