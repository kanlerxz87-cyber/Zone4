// Copy-to-clipboard for the design prompt on docs/design.html.
// No network requests, no external libraries, no storage. If the clipboard
// API is unavailable the button simply does nothing and the reader can select
// the text by hand.
(function () {
  var button = document.getElementById('copy-prompt');
  var status = document.getElementById('copy-status');
  var target = document.getElementById('design-prompt');
  if (!button || !target) return;

  function say(message) {
    if (status) status.textContent = message;
  }

  button.addEventListener('click', function () {
    var text = target.textContent || '';
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { say('Copied to clipboard.'); },
        function () { say('Copy failed - select the text and copy it manually.'); }
      );
      return;
    }
    // Fallback for browsers without the async clipboard API.
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'absolute';
    area.style.left = '-9999px';
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(area);
    say(ok ? 'Copied to clipboard.' : 'Copy failed - select the text and copy it manually.');
  });
})();
