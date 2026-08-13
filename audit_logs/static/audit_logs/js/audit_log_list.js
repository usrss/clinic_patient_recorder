/* ═══════════════════════════════════════════
   Audit Log List — table row navigation
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Row click → detail page ──
  // Each row carries its detail URL in data-href (rendered by Django).
  document.addEventListener('DOMContentLoaded', function () {
    var rows = document.querySelectorAll('.al-table tbody tr[data-href]');
    for (var i = 0; i < rows.length; i++) {
      rows[i].addEventListener('click', function () {
        window.location = this.getAttribute('data-href');
      });
    }
  });
})();
