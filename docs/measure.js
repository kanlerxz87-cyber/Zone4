// Zone4 measurement script: five defined events, inert unless an endpoint is set.
// No cookies, no storage, no identifiers. Honours Do Not Track and Global Privacy Control.
(function () {
  'use strict';
  var meta = document.querySelector('meta[name="zone4-measure-endpoint"]');
  var endpoint = meta ? meta.getAttribute('content') : '';
  if (!endpoint) { return; }
  if (navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true) { return; }
  var base = new URL('./', document.currentScript.src);
  var countedPath = location.pathname;
  var EVENTS = { page_view: 1, outbound_click: 1, guide_read_75: 1, category_click: 1, feed_click: 1 };
  function send(name, field, value) {
    if (!EVENTS[name]) { return; }
    var payload = { event: name, path: countedPath };
    if (field) { payload[field] = value; }
    try {
      // Unlike sendBeacon, fetch can explicitly omit credentials.
      fetch(endpoint, {
        method: 'POST', body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
        keepalive: true, mode: 'cors', credentials: 'omit', redirect: 'error', referrerPolicy: 'no-referrer'
      }).catch(function () {});
    } catch (e) { /* measurement must never break reading or navigation */ }
  }
  send('page_view');
  function onClick(ev) {
    if (ev.isTrusted === false || (ev.type === 'auxclick' && ev.button !== 1)) { return; }
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
    if (!a) { return; }
    var dest = new URL(a.href, location.href);
    var rel = (a.getAttribute('rel') || '').toLowerCase().split(/\s+/);
    var product = dest.pathname.match(/^\/dp\/(B[0-9A-Z]{9})(?:\/|$)/);
    if (rel.indexOf('sponsored') !== -1 && dest.origin === 'https://www.amazon.com' && product) {
      send('outbound_click', 'asin', product[1]);
    } else if (dest.origin === base.origin && dest.pathname.indexOf(base.pathname) === 0) {
      var relativePath = dest.pathname.slice(base.pathname.length);
      var category = relativePath.match(/^categories\/([a-z0-9-]+)\.html$/);
      if (relativePath === 'feed.xml') { send('feed_click'); }
      else if (category) { send('category_click', 'target', category[1]); }
    }
  }
  document.addEventListener('click', onClick, false);
  document.addEventListener('auxclick', onClick, false);
  var article = document.querySelector('article.guide, article.post');
  if (article && 'IntersectionObserver' in window) {
    // Marker sits at 75% of the article's own height, not of the viewport (fixed 2026-11-17).
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
