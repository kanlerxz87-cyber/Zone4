// Zone4 measurement script: five defined events, inert unless an endpoint is set.
// No cookies, no storage, no identifiers. Honours Do Not Track and Global Privacy Control.
(function () {
  'use strict';
  var meta = document.querySelector('meta[name="zone4-measure-endpoint"]');
  var endpoint = meta ? meta.getAttribute('content') : '';
  if (!endpoint) { return; }
  if (navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true) { return; }
  var EVENTS = { page_view: 1, outbound_click: 1, guide_read_75: 1, category_click: 1, feed_click: 1 };
  function send(name, extra) {
    if (!EVENTS[name]) { return; }
    var payload = { event: name, path: location.pathname };
    if (extra) { for (var k in extra) { payload[k] = extra[k]; } }
    var body = JSON.stringify(payload);
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(endpoint, new Blob([body], { type: 'application/json' }));
      } else {
        fetch(endpoint, { method: 'POST', body: body, keepalive: true, mode: 'cors' });
      }
    } catch (e) { /* the measurement must never break the page */ }
  }
  send('page_view');
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a') : null;
    if (!a) { return; }
    var rel = (a.getAttribute('rel') || '');
    if (rel.indexOf('sponsored') !== -1) {
      send('outbound_click', { asin: a.getAttribute('data-track-asin') || '' });
    } else if (a.getAttribute('data-measure') === 'category') {
      send('category_click', { target: a.getAttribute('href') || '' });
    } else if (a.getAttribute('data-measure') === 'feed') {
      send('feed_click');
    }
  }, false);
  var article = document.querySelector('article.guide');
  if (article && 'IntersectionObserver' in window) {
    // Marker sits at 75% of the article's own height, not of the viewport (fixed 2026-11-17).
    article.style.position = 'relative';
    var marker = document.createElement('div');
    marker.setAttribute('aria-hidden', 'true');
    marker.style.cssText = 'position:absolute;top:75%;height:1px;width:1px;pointer-events:none;';
    article.appendChild(marker);
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { send('guide_read_75'); io.disconnect(); } });
    });
    io.observe(marker);
  }
})();
