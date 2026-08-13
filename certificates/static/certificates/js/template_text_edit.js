/* ═══════════════════════════════════════════
   Template Text Edit — character counter
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Character counter ──
  var textarea = document.querySelector('textarea');
  var counter = document.getElementById('charCount');
  if (textarea && counter) {
    textarea.addEventListener('input', function () {
      counter.textContent = this.value.length + ' characters';
    });
    counter.textContent = textarea.value.length + ' characters';
  }
})();
