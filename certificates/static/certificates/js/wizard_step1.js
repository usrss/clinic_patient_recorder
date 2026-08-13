/* ═══════════════════════════════════════════
   Wizard Step 1 — certificate type selection
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Type card selection ──
  document.querySelectorAll('.type-card').forEach(function (card) {
    card.addEventListener('click', function () {
      document.querySelectorAll('.type-card').forEach(function (c) {
        c.classList.remove('selected');
      });
      this.classList.add('selected');
      this.querySelector('input[type="radio"]').checked = true;
    });
  });

  // Select default
  var firstCard = document.querySelector('.type-card');
  if (firstCard) firstCard.classList.add('selected');
})();
