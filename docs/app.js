// Client-side table filter and the three-question chooser. No network requests,
// no external libraries, no data leaves the browser (analytics.html stays local).
(function () {
  // ---- row filter for tables ------------------------------------------------
  var input = document.getElementById('filter');
  if (input) {
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var rows = document.querySelectorAll('table tbody tr');
      rows.forEach(function (row) {
        row.style.display = !q || row.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
      });
    });
  }

  // ---- three-question chooser (suggestion S-19, decision D-23) --------------
  // Routing uses only the listed specifications the page already publishes; the
  // reasoning is rendered alongside the answer so the route is checkable. The
  // plain-text version of the same logic sits in a table below the chooser.
  var go = document.getElementById('chooser-go');
  if (!go) return;

  var PRODUCTS = {
    p1: {
      name: 'The 6-quart dual basket',
      href: 'articles/chefman-6-quart-dual-basket-air-fryer-oven.html',
      blurb: 'Two independent 3-quart baskets with a Sync Finish option listed in the title: built for a main and a side finishing together.'
    },
    p3: {
      name: 'The 8-quart single basket',
      href: 'articles/chefman-8-quart-single-basket-air-fryer.html',
      blurb: 'One 8-quart basket, four presets, 12.75 inches of listed depth: the compact workhorse.'
    },
    p2: {
      name: 'The 26QT French-door oven',
      href: 'articles/26qt-french-door-air-fryer-toaster-oven.html',
      blurb: '24.6 liters listed, 24 one-touch presets in its current title segment: for crowds and deep counters (16.9 inches listed).'
    }
  };

  go.addEventListener('click', function () {
    var pick = function (n) {
      var el = document.querySelector('input[name="' + n + '"]:checked');
      return el ? el.value : null;
    };
    var cook = pick('cook-for'), depth = pick('depth'), sync = pick('sync');
    var score = { p1: 0, p2: 0, p3: 0 };
    var why = [];
    if (cook === 'small') { score.p1 += 2; score.p3 += 2; why.push('cooking for one or two favors the two compact formats'); }
    if (cook === 'mid') { score.p1 += 2; score.p3 += 1; score.p2 += 1; why.push('cooking for three or four sits in the middle of the capacity range'); }
    if (cook === 'large') { score.p2 += 3; score.p1 += 1; why.push('five or more (or hosting) favors the largest listed interior'); }
    if (depth === 'shallow') { score.p3 += 2; score.p1 += 1; why.push('under 13.5 inches of depth, only the 12.75-inch unit fits comfortably as listed'); }
    if (depth === 'mid') { score.p1 += 2; score.p3 += 1; why.push('13.5 to 15.5 inches of depth clears the 13.38-inch dual basket'); }
    if (depth === 'deep') { score.p2 += 3; score.p1 += 1; why.push('over 15.5 inches of depth clears the 16.9-inch French-door oven'); }
    if (sync === 'yes') { score.p1 += 2; why.push('two dishes finishing together is exactly what the dual basket lists Sync Finish for'); }
    if (sync === 'no') { score.p3 += 1; score.p2 += 1; why.push('one dish at a time widens the choice'); }

    var best = Math.max(score.p1, score.p2, score.p3);
    var winners = Object.keys(score).filter(function (k) { return score[k] === best; });
    var out = document.getElementById('chooser-result');
    if (!out) return;

    var html = '<strong>Our match:</strong> ';
    html += winners.map(function (k) { return PRODUCTS[k].name; }).join(' and ');
    html += '. <span class="small">Editorial routing on listed figures, not a rating: nobody on this project has used these appliances.</span>';
    html += '<ul>' + winners.map(function (k) {
      return '<li><a href="' + PRODUCTS[k].href + '">' + PRODUCTS[k].name + '</a> — ' + PRODUCTS[k].blurb + '</li>';
    }).join('') + '</ul>';
    html += '<p class="small"><strong>Why, from your answers:</strong> ' + why.join('; ') + '.</p>';
    html += '<p class="small muted">Skeptical? The table below shows the same routing with the listed figures beside it.</p>';
    out.innerHTML = html;
    out.hidden = false;
  });
})();
