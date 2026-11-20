// Source of docs/measure.js; the build supplies only known public paths and catalog ASINs.
// Five best-effort counters, not visitor identities, Amazon reporting or purchases.
(function () {
  'use strict';
  var CONFIG = __ZONE4_CONFIG__;
  var meta = document.querySelector('meta[name="zone4-measure-endpoint"]');
  var endpoint = meta ? meta.getAttribute('content') : '';
  function optedOut() {
    return navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true;
  }
  if (!endpoint || optedOut() || typeof fetch !== 'function') { return; }

  var base, receiver;
  try {
    base = new URL('./', document.currentScript.src);
    receiver = new URL(endpoint);
    // Never send preview traffic to production, or follow an endpoint redirect.
    if (base.href !== CONFIG.site_url || receiver.protocol !== 'https:' ||
        receiver.username || receiver.password || receiver.search || receiver.hash ||
        receiver.pathname !== '/event') { return; }
  } catch (e) { return; }

  function knownPath(url) {
    if (url.origin !== base.origin || url.pathname.indexOf(base.pathname) !== 0) { return ''; }
    var relative = url.pathname.slice(base.pathname.length);
    if (!relative || relative.slice(-1) === '/') { relative += 'index.html'; }
    return CONFIG.paths.indexOf(relative) !== -1 ? base.pathname + relative : '';
  }
  var countedPath = knownPath(new URL(location.href));
  if (!countedPath) { return; }
  var EVENTS = { page_view: 1, outbound_click: 1, guide_read_75: 1, category_click: 1, feed_click: 1 };
  function send(name, field, value) {
    if (!EVENTS[name] || optedOut()) { return; }
    var payload = { event: name, path: countedPath };
    if (field) { payload[field] = value; }
    try {
      // Do not read browsing history or credentials. These options suppress their transport too.
      fetch(endpoint, {
        method: 'POST', body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
        keepalive: true, mode: 'cors', credentials: 'omit', redirect: 'error',
        referrerPolicy: 'no-referrer', cache: 'no-store'
      }).catch(function () {});
    } catch (e) { /* Counting must never block a purchase link or reading the page. */ }
  }
  send('page_view');

  function onClick(ev) {
    if (ev.isTrusted === false || ev.defaultPrevented ||
        (ev.type === 'auxclick' ? ev.button !== 1 : ev.button > 0)) { return; }
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
    if (!a) { return; }
    var dest;
    try { dest = new URL(a.href, location.href); } catch (e) { return; }
    var rel = (a.getAttribute('rel') || '').toLowerCase().split(/\s+/);
    var product = dest.pathname.match(/^\/dp\/(B[0-9A-Z]{9})\/?$/);
    if (rel.indexOf('sponsored') !== -1 && dest.origin === 'https://www.amazon.com' &&
        product && CONFIG.asins.indexOf(product[1]) !== -1 &&
        dest.searchParams.get('tag') === CONFIG.tracking_id) {
      send('outbound_click', 'asin', product[1]);
    } else if (dest.origin === base.origin && dest.pathname === base.pathname + 'feed.xml') {
      send('feed_click');
    } else {
      var target = knownPath(dest);
      if (target && CONFIG.categories.indexOf(target.slice(base.pathname.length)) !== -1) {
        send('category_click', 'target', target);
      }
    }
  }
  document.addEventListener('click', onClick, false);
  document.addEventListener('auxclick', onClick, false);

  var article = document.querySelector('article.guide, article.post');
  if (article && CONFIG.guides.indexOf(countedPath.slice(base.pathname.length)) !== -1 && 'IntersectionObserver' in window) {
    // A visibility milestone only: it cannot establish that a person read or understood the guide.
    article.style.position = 'relative';
    var marker = document.createElement('div');
    marker.setAttribute('aria-hidden', 'true');
    marker.style.cssText = 'position:absolute;top:75%;height:1px;width:1px;pointer-events:none;';
    article.appendChild(marker);
    var seen = false;
    var io = new IntersectionObserver(function (entries) {
      if (!seen && entries.some(function (entry) { return entry.isIntersecting; })) {
        seen = true;
        io.disconnect();
        send('guide_read_75');
      }
    });
    io.observe(marker);
  }
})();
