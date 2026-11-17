// Northstar first-party event tracker — local-only, starts at zero.
// Records events in localStorage; no network calls; no fabricated data.
// Event schema (five measured events, decision D-42, 2026-11-17):
//   page_view, outbound_click, chooser_answer  -> recorded here (site-side)
//   reported_click, reported_order             -> Associates reports only; never generated here
// The 'test' type is the explicitly labelled mechanism self-check and is not one of the five.
// Optional endpoint hook (D-44): leave ENDPOINT empty. Nothing is sent anywhere while it is empty.
(function () {
  'use strict';
  var KEY = 'ns_tracker_events_v1';
  var rows = document.getElementById('event-rows');
  var empty = document.getElementById('log-empty');
  var mClicks = document.getElementById('m-clicks');
  var mEvents = document.getElementById('m-events');
  var mLast = document.getElementById('m-last');

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
  }
  function save(events) {
    try { localStorage.setItem(KEY, JSON.stringify(events)); } catch (e) { /* storage unavailable */ }
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function render() {
    var events = load();
    var clicks = events.filter(function (e) {
      return e.type === 'outbound_click' || e.type === 'click'; // 'click' is the legacy label
    }).length;
    if (mClicks) mClicks.textContent = String(clicks);
    if (mEvents) mEvents.textContent = String(events.length);
    if (mLast) mLast.textContent = events.length ? events[events.length - 1].ts.replace('T', ' ').replace('Z', '') : '—';
    if (empty) empty.hidden = events.length > 0;
    if (!rows) return;
    var html = '';
    for (var i = events.length - 1; i >= 0; i--) {
      var e = events[i];
      html += '<tr><td class="mono">' + esc(e.ts) + '</td><td><span class="pill ' +
        (e.type === 'test' ? 'pill-warn' : 'pill-ok') + '">' + esc(e.type) + '</span></td><td>' +
        esc(e.target || '—') + '</td><td class="mono">' + esc(e.asin || '—') + '</td></tr>';
    }
    rows.innerHTML = html;
  }
  // The three site-side event names of the five-event schema (D-42).
  var SITE_EVENTS = ['page_view', 'outbound_click', 'chooser_answer'];
  function addEvent(type, target, asin) {
    if (SITE_EVENTS.indexOf(type) === -1 && type !== 'test' && type !== 'click') return; // 'click' is the legacy label
    var events = load();
    events.push({
      ts: new Date().toISOString(),
      type: type,
      target: target || '',
      asin: asin || ''
    });
    if (events.length > 500) { events = events.slice(events.length - 500); }
    save(events);
    render();
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

  // Auto-track any element carrying data-track and optional data-track-target / data-track-asin.
  document.addEventListener('click', function (ev) {
    var el = ev.target && ev.target.closest ? ev.target.closest('[data-track]') : null;
    if (!el) return;
    addEvent(el.getAttribute('data-track') || 'click',
      el.getAttribute('data-track-target') || (el.getAttribute('href') || el.textContent || '').trim(),
      el.getAttribute('data-track-asin') || '');
  }, false);

  var b1 = document.getElementById('btn-test');
  if (b1) b1.addEventListener('click', function () {
    addEvent('test', 'Mechanism self-check (explicitly labeled test — not a product click)', '');
  });
  var b2 = document.getElementById('btn-export-json');
  if (b2) b2.addEventListener('click', function () {
    download('northstar-tracker-events.json', JSON.stringify(load(), null, 2), 'application/json');
  });
  var b3 = document.getElementById('btn-export-csv');
  if (b3) b3.addEventListener('click', function () {
    var events = load();
    var csv = 'timestamp_utc,type,target,asin\n' + events.map(function (e) {
      return [e.ts, e.type, '"' + String(e.target || '').replace(/"/g, '""') + '"', e.asin || ''].join(',');
    }).join('\n');
    download('northstar-tracker-events.csv', csv, 'text/csv');
  });
  var b4 = document.getElementById('btn-clear');
  if (b4) b4.addEventListener('click', function () {
    if (window.confirm('Delete all locally stored events? This cannot be undone.')) {
      save([]);
      render();
    }
  });

  // One site-side page_view per page load (event schema, D-42). Path only —
  // no referrer, no identifiers, nothing that leaves this browser.
  addEvent('page_view', location.pathname, '');

  render();
})();
