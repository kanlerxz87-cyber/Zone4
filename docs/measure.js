// Source of docs/measure.js; the build supplies only known public paths and catalog ASINs.
// Five best-effort counters, not visitor identities, Amazon reporting or purchases.
(function () {
  'use strict';
  var CONFIG = {"asins":["B08DKYBTPH","B09B7SB46R","B0CDY277D3","B0DHZTCNR5","B0DZFD6R9Z"],"categories":["categories/air-fryer-toaster-ovens.html","categories/dual-basket-air-fryers.html","categories/meat-thermometers.html","categories/single-basket-air-fryers.html"],"guides":["articles/26qt-french-door-air-fryer-toaster-oven.html","articles/air-fryer-buying-guide-2026.html","articles/air-fryer-feature-names-explained.html","articles/air-fryer-listing-says-24-functions-25-presets.html","articles/air-fryer-sizes-explained-6qt-vs-8qt-vs-26qt.html","articles/chefman-6-quart-dual-basket-air-fryer-oven.html","articles/chefman-8-quart-single-basket-air-fryer.html","articles/dual-basket-vs-single-basket-vs-toaster-oven-air-fryer.html","articles/first-air-fryer-checklist-seven-numbers.html","articles/holiday-2026-air-fryer-gift-guide.html","guides/air-fryer-capacity-checklist.html","guides/basket-or-oven-style-air-fryer-what-to-compare.html","guides/counter-space-and-cleanup-trade-offs.html","guides/questions-before-a-multi-function-kitchen-appliance.html"],"paths":["about.html","analysis.html","analytics.html","articles/26qt-french-door-air-fryer-toaster-oven.html","articles/air-fryer-buying-guide-2026.html","articles/air-fryer-feature-names-explained.html","articles/air-fryer-listing-says-24-functions-25-presets.html","articles/air-fryer-sizes-explained-6qt-vs-8qt-vs-26qt.html","articles/chefman-6-quart-dual-basket-air-fryer-oven.html","articles/chefman-8-quart-single-basket-air-fryer.html","articles/dual-basket-vs-single-basket-vs-toaster-oven-air-fryer.html","articles/first-air-fryer-checklist-seven-numbers.html","articles/holiday-2026-air-fryer-gift-guide.html","articles/index.html","automation.html","categories/air-fryer-toaster-ovens.html","categories/dual-basket-air-fryers.html","categories/meat-thermometers.html","categories/single-basket-air-fryers.html","decision-centre.html","decisions.html","design.html","executive-summary.html","flagged.html","guides/air-fryer-capacity-checklist.html","guides/basket-or-oven-style-air-fryer-what-to-compare.html","guides/counter-space-and-cleanup-trade-offs.html","guides/index.html","guides/questions-before-a-multi-function-kitchen-appliance.html","imagery.html","index.html","information-gaps.html","links.html","marketing.html","measurement.html","policy-compliance.html","products.html","questions.html","requirements.html","review.html","sources.html","suggestions.html","verification.html"],"site_url":"https://kanlerxz87-cyber.github.io/Zone4/docs/","tracking_id":"shopnow047c-20"};
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
