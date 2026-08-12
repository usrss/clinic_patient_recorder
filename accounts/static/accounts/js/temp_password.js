/* ═══════════════════════════════════════════
   Temp Passwords — Shared modal behavior for the
   Staff Temp Password list & Walk-in Patient list
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  function byId(id) { return document.getElementById(id); }

  let currentUrl = null;
  let currentPassword = '';

  // ── Open modal & fetch stored password ──
  document.querySelectorAll('.pw-show-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      currentUrl = this.getAttribute('data-url');
      var nameEl = byId('modalStaffName') || byId('modalPatientName');
      var metaEl = byId('modalStaffUsername') || byId('modalPatientId');
      if (nameEl) nameEl.textContent = this.getAttribute('data-name');
      if (metaEl) {
        var userVal = this.getAttribute('data-username');
        if (byId('modalStaffUsername')) metaEl.textContent = '@' + userVal;
        else metaEl.textContent = 'ID: ' + userVal;
      }
      byId('pwText').textContent = '';
      byId('pwSpinner').style.display = 'flex';
      byId('copyFeedback').style.display = 'none';
      byId('errorFeedback').style.display = 'none';
      byId('pwModal').classList.add('open');
      fetchPassword();
    });
  });

  function closePwModal() {
    byId('pwModal').classList.remove('open');
    byId('pwSpinner').style.display = 'none';
  }

  // ── Fetch the stored temp password ──
  function fetchPassword() {
    if (!currentUrl) return;
    byId('pwSpinner').style.display = 'flex';
    byId('pwText').textContent = '';

    var csrf = byId('pwModal').getAttribute('data-csrf') || '';

    fetch(currentUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrf,
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      byId('pwSpinner').style.display = 'none';
      if (data.success) {
        currentPassword = data.access_code;
        byId('pwText').textContent = currentPassword;
        byId('pwText').style.color = '#0078d4';
      } else {
        byId('pwText').textContent = 'Not available';
        byId('pwText').style.color = '#ef4444';
        byId('errorFeedback').textContent = data.error || 'Unknown error';
        byId('errorFeedback').style.display = 'block';
      }
    })
    .catch(function (err) {
      byId('pwSpinner').style.display = 'none';
      byId('pwText').textContent = 'Error';
      byId('pwText').style.color = '#ef4444';
      byId('errorFeedback').textContent = 'Request failed — check console (F12)';
      byId('errorFeedback').style.display = 'block';
      console.error('Temp password fetch error:', err);
    });
  }

  // ── Copy to clipboard ──
  function copyPassword() {
    if (!currentPassword) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(currentPassword).then(function () {
        showCopied();
      }).catch(function () { fallbackCopy(); });
    } else {
      fallbackCopy();
    }
  }

  function fallbackCopy() {
    var ta = document.createElement('textarea');
    ta.value = currentPassword;
    ta.style.position = 'fixed'; ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); showCopied(); } catch (e) {}
    document.body.removeChild(ta);
  }

  function showCopied() {
    var el = byId('copyFeedback');
    el.style.display = 'block';
    setTimeout(function () { el.style.display = 'none'; }, 2000);
  }

  // ── Modal controls (close button, overlay click, copy button) ──
  var closeBtn = document.querySelector('.pw-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', closePwModal);

  var modal = byId('pwModal');
  if (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === modal) closePwModal();
    });
  }

  var copyBtn = byId('copyBtn');
  if (copyBtn) copyBtn.addEventListener('click', copyPassword);
})();
