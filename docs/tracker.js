/* Zone4 event tracker — the five events defined in data/tracking-events.json.
 *
 * Privacy position (deliberate, and the reason this file is small):
 *   - no cookie, no localStorage identifier, no fingerprint, no session replay;
 *   - no third-party script, no external request, ever, by default;
 *   - an event holds: name, page path, ASIN (when there is one), and the
 *     browser's own clock. That is all.
 *
 * Transmission is off. An endpoint is only called when BOTH of these are true:
 *   1. the reader has ticked the opt-in box on the analytics page, and
 *   2. ZONE4_ENDPOINT is a non-empty string (built from
 *      data/tracking-events.json -> endpoint_step1).
 * With the endpoint null — which is how this repository ships — no fetch call
 * is constructed at all. That is the guarantee F-56 records.
 *
 * The events are counted, never estimated: a row in the local log means the
 * thing it names actually happened in this browser.
 */
(function () {
  'use strict';

  var KEY = 'zone4.events.v1';
  var OPT_IN = 'zone4.optin.v1';

  // Published by the build from data/tracking-events.json. Null = not configured.
  var ZONE4_ENDPOINT = null;

  var EVENTS = {
    product_impression: 'product_impression',
    product_cta_click: 'product_cta_click',
    affiliate_click: 'affiliate_click',
    guide_read_complete: 'guide_read_complete',
    disclosure_viewed: 'disclosure_viewed'
  };

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
  }

  function save(events) {
    // Cap the log so a long-lived browser cannot fill its storage quota.
    var trimmed = events.length > 2000 ? events.slice(events.length - 2000) : events;
    try { localStorage.setItem(KEY, JSON.stringify(trimmed)); } catch (e) { /* storage unavailable */ }
  }

  function optedIn() {
    try { return localStorage.getItem(OPT_IN) === '1'; } catch (e) { return false; }
  }

  function transmit(row) {
    // Two gates, both required. No endpoint, no call.
    if (!ZONE4_ENDPOINT || !optedIn()) return;
    try {
      var body = JSON.stringify(row);
      if (navigator.sendBeacon) {
        navigator.sendBeacon(ZONE4_ENDPOINT, new Blob([body], { type: 'application/json' }));
      } else {
        fetch(ZONE4_ENDPOINT, {
          method: 'POST', body: body, keepalive: true,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    } catch (e) { /* never break the page for a counter */ }
  }

  function record(name, extra) {
    var row = {
      event: name,
      page_path: location.pathname.replace(/\/docs\//, '/'),
      ts: new Date().toISOString()
    };
    if (extra && extra.asin) row.asin = extra.asin;
    if (extra && extra.destination_host) row.destination_host = extra.destination_host;
    var events = load();
    events.push(row);
    save(events);
    transmit(row);
    renderDashboard(events);
    return row;
  }

  // ---- once-per-page-view guard -------------------------------------------
  var fired = {};
  function once(key, fn) {
    if (fired[key]) return;
    fired[key] = true;
    fn();
  }

  // ---- 1 + 5: viewport events (impression, disclosure viewed) --------------
  function whenVisible(el, fn) {
    if (!el) return;
    if (!('IntersectionObserver' in window)) return;   // no observer, no claim
    var timer = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          if (!timer) timer = setTimeout(function () { io.disconnect(); fn(); }, 1000);
        } else if (timer) {
          clearTimeout(timer); timer = null;             // must be seen for a full second
        }
      });
    }, { threshold: 0.5 });
    io.observe(el);
  }

  document.querySelectorAll('[data-product-card]').forEach(function (card) {
    var asin = card.getAttribute('data-product-card');
    whenVisible(card, function () {
      once('impression:' + asin, function () { record(EVENTS.product_impression, { asin: asin }); });
    });
  });

  whenVisible(document.querySelector('.disclosure'), function () {
    once('disclosure', function () { record(EVENTS.disclosure_viewed); });
  });

  // ---- 2: call-to-action clicks that are not the outbound link -------------
  document.addEventListener('click', function (ev) {
    var el = ev.target && ev.target.closest ? ev.target.closest('[data-track="product_cta_click"]') : null;
    if (!el) return;
    record(EVENTS.product_cta_click, { asin: el.getAttribute('data-track-asin') || '' });
  }, false);

  // ---- 3: the outbound affiliate click ------------------------------------
  // Written in the capture phase and synchronously, so the row exists before
  // the browser starts the navigation.
  document.addEventListener('click', function (ev) {
    var el = ev.target && ev.target.closest ? ev.target.closest('a[data-track="affiliate_click"]') : null;
    if (!el) return;
    var href = el.getAttribute('href') || '';
    var host = '';
    try { host = new URL(href, location.href).hostname; } catch (e) { host = ''; }
    record(EVENTS.affiliate_click, { asin: el.getAttribute('data-track-asin') || '', destination_host: host });
  }, true);
  // Keyboard activation fires a click event on the anchor too, so Enter and
  // Space are counted by the same listener - no separate handler to drift.

  // ---- 4: read to the end of an article -----------------------------------
  var endMarker = document.querySelector('[data-read-complete]');
  whenVisible(endMarker, function () {
    once('read', function () { record(EVENTS.guide_read_complete); });
  });

  // ---- the dashboard on analytics.html ------------------------------------
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function renderDashboard(events) {
    events = events || load();
    var rows = document.getElementById('event-rows');
    var empty = document.getElementById('log-empty');
    var counts = {};
    Object.keys(EVENTS).forEach(function (k) { counts[k] = 0; });
    events.forEach(function (e) { if (counts[e.event] != null) counts[e.event] += 1; });
    Object.keys(counts).forEach(function (k) {
      var el = document.getElementById('count-' + k);
      if (el) el.textContent = String(counts[k]);
    });
    var last = document.getElementById('m-last');
    if (last) {
      last.textContent = events.length
        ? events[events.length - 1].ts.replace('T', ' ').replace(/\.\d+Z$/, ' UTC')
        : '—';
    }
    if (empty) empty.hidden = events.length > 0;
    if (!rows) return;
    var html = '';
    for (var i = events.length - 1; i >= 0 && i > events.length - 201; i--) {
      var e = events[i];
      html += '<tr><td class="mono">' + esc(e.ts) + '</td><td>' + esc(e.event) + '</td><td>'
        + esc(e.page_path) + '</td><td class="mono">' + esc(e.asin || '—') + '</td><td>'
        + esc(e.destination_host || '—') + '</td></tr>';
    }
    rows.innerHTML = html;
  }

  // ---- controls -----------------------------------------------------------
  var testBtn = document.getElementById('btn-test');
  if (testBtn) {
    testBtn.addEventListener('click', function () {
      // Explicitly labelled: a test event can never be read as a product click.
      record(EVENTS.product_impression, { asin: 'TEST-EVENT-NOT-A-PRODUCT' });
    });
  }

  function download(name, text, mime) {
    var blob = new Blob([text], { type: mime });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  }

  var expJson = document.getElementById('btn-export-json');
  if (expJson) {
    expJson.addEventListener('click', function () {
      download('zone4-events.json', JSON.stringify(load(), null, 2), 'application/json');
    });
  }
  var expCsv = document.getElementById('btn-export-csv');
  if (expCsv) {
    expCsv.addEventListener('click', function () {
      var cols = ['ts', 'event', 'page_path', 'asin', 'destination_host'];
      var csv = cols.join(',') + '\n' + load().map(function (e) {
        return cols.map(function (c) {
          return '"' + String(e[c] == null ? '' : e[c]).replace(/"/g, '""') + '"';
        }).join(',');
      }).join('\n');
      download('zone4-events.csv', csv, 'text/csv');
    });
  }
  var clearBtn = document.getElementById('btn-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      if (window.confirm('Delete every event stored in this browser? This cannot be undone.')) {
        save([]);
        renderDashboard([]);
      }
    });
  }
  var optIn = document.getElementById('opt-in');
  if (optIn) {
    try { optIn.checked = optedIn(); } catch (e) { /* ignore */ }
    optIn.addEventListener('change', function () {
      try { localStorage.setItem(OPT_IN, optIn.checked ? '1' : '0'); } catch (e) { /* ignore */ }
      var note = document.getElementById('opt-in-note');
      if (note) note.hidden = !optIn.checked;
    });
  }

  renderDashboard();
})();
