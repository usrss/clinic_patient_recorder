/* ═══════════════════════════════════════════
   User Form — Admin "Add/Edit Staff" page
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Loading state on submit ──
  var form = document.querySelector('form');
  if (form) {
    form.addEventListener('submit', function () {
      var btn = document.getElementById('userFormSubmitBtn');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Saving...';
      }
    });
  }
})();
