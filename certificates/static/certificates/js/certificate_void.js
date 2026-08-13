/* ═══════════════════════════════════════════
   Certificate Void — confirm dialog
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Confirm before voiding ──
  var form = document.querySelector('.void-card form');
  if (form) {
    form.addEventListener('submit', function (e) {
      if (!window.confirm('Are you sure you want to void this certificate? This cannot be undone.')) {
        e.preventDefault();
      }
    });
  }
})();
