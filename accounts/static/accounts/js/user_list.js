/* ═══════════════════════════════════════════
   User List — Staff management page
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Deactivation confirmation modal ──
  document.querySelectorAll('[data-deactivate-user]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var nameEl = document.getElementById('deactivateModalName');
      if (nameEl) {
        nameEl.textContent = 'Deactivate "' + this.getAttribute('data-deactivate-user') + '"? They will not be able to log in.';
      }
      var form = document.getElementById('deactivateForm');
      if (form) form.action = this.getAttribute('data-toggle-url');
      new bootstrap.Modal(document.getElementById('deactivateModal')).show();
    });
  });

  // ── Loading state on deactivation form submit ──
  document.addEventListener('DOMContentLoaded', function () {
    var forms = document.querySelectorAll('form[action*="/toggle/"]');
    for (var i = 0; i < forms.length; i++) {
      forms[i].addEventListener('submit', function () {
        var btn = this.querySelector('button[type="submit"]');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span style="display:inline-flex;align-items:center;gap:6px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Activating...</span>';
        }
      });
    }

    // Loading state on deactivate modal button
    var deactivateForm = document.getElementById('deactivateForm');
    if (deactivateForm) {
      deactivateForm.addEventListener('submit', function () {
        var btn = this.querySelector('button[type="submit"]');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span style="display:inline-flex;align-items:center;gap:6px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Deactivating...</span>';
        }
      });
    }
  });
})();
