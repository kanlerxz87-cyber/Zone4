// Northstar first-party click tracker — local-only, starts at zero.
// Records events in localStorage; no network calls; no fabricated data.
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
    var clicks = events.filter(function (e) { return e.type === 'click'; }).length;
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
  function addEvent(type, target, asin) {
    var events = load();
    events.push({
      ts: new Date().toISOString(),
      type: type,
      target: target || '',
      asin: asin || ''
    });
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

  render();
})();
