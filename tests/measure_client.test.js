// Exercise the generated client with representative links from the published tree.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const vm = require('node:vm');

const origin = 'https://kanlerxz87-cyber.github.io';
const root = `${origin}/Zone4/docs/`;
const endpoint = 'https://collector.example/event';
const client = fs.readFileSync('docs/measure.js', 'utf8');
const guidePath = 'guides/basket-or-oven-style-air-fryer-what-to-compare.html';
const guide = fs.readFileSync(`docs/${guidePath}`, 'utf8');
const home = fs.readFileSync('docs/index.html', 'utf8');

function browser({ url = endpoint, privacy = {}, dnt, fetchError = false } = {}) {
  const requests = [];
  const listeners = {};
  const article = { style: {}, appendChild(marker) { this.marker = marker; } };
  const observer = {};
  vm.runInNewContext(client, {
    URL,
    navigator: privacy,
    location: new URL(`${root}${guidePath}?utm_source=private#bookmark`),
    window: { doNotTrack: dnt, IntersectionObserver: true },
    document: {
      currentScript: { src: `${root}measure.js` },
      querySelector(selector) {
        return selector === 'article.guide, article.post' ? article : { getAttribute: () => url };
      },
      addEventListener(name, handler) { listeners[name] = handler; },
      createElement() { return { style: {}, setAttribute() {} }; },
    },
    IntersectionObserver: class {
      constructor(handler) { observer.update = handler; }
      observe(marker) { observer.marker = marker; }
      disconnect() { observer.disconnected = true; }
    },
    fetch(url, options) {
      requests.push({ url, options });
      return fetchError ? Promise.reject(new Error('offline')) : Promise.resolve();
    },
  });
  return {
    requests, listeners, observer, article,
    click(href, rel = '', { type = 'click', button = 0, isTrusted = true } = {}) {
      listeners[type]({ type, button, isTrusted, target: { closest: () => ({ href, getAttribute: () => rel }) } });
    },
  };
}

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
  assert.deepEqual(app.requests.map(({ options }) => JSON.parse(options.body)), [
    { event: 'page_view', path: `/Zone4/docs/${guidePath}` },
    { event: 'outbound_click', path: `/Zone4/docs/${guidePath}`, asin: 'B0CDY277D3' },
    { event: 'category_click', path: `/Zone4/docs/${guidePath}`, target: 'meat-thermometers' },
    { event: 'feed_click', path: `/Zone4/docs/${guidePath}` },
    { event: 'guide_read_75', path: `/Zone4/docs/${guidePath}` },
  ]);
  for (const { url, options } of app.requests) {
    assert.equal(url, endpoint);
    assert.equal(options.method, 'POST');
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.equal(options.credentials, 'omit');
    assert.equal(options.redirect, 'error');
    assert.equal(options.referrerPolicy, 'no-referrer');
    assert.equal(options.keepalive, true);
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
