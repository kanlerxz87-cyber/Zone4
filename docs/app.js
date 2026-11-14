// Client-side row filter for tables. No network requests, no external libraries.
(function () {
  var input = document.getElementById('filter');
  if (!input) return;
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    var rows = document.querySelectorAll('table tbody tr');
    rows.forEach(function (row) {
      row.style.display = !q || row.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
    });
  });
})();
