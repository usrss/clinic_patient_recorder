// ═══════════════════════════════════════════════════════════════════
// Sidebar + notification badges — only show red badge when count > 0
// ═══════════════════════════════════════════════════════════════════
// Sidebar nav badges use data-sidebar-count="<key>" to map to the
// JSON response from the sidebar-counts endpoint.
// Notification badges use the separate unread-count endpoint.
// All badges are hidden when count is 0.
// ═══════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  const scriptTag = document.currentScript;
  const unreadUrl = scriptTag.dataset.unreadUrl;
  const sidebarCountsUrl = scriptTag.dataset.sidebarCountsUrl;

  /* ── Update notification badges (desktop + mobile + sidebar) ── */
  function updateNotifBadges(count) {
    var ids = ['unread-badge', 'unread-badge-mobile', 'sidebar-notif-badge'];
    ids.forEach(function(id) {
      var el = document.getElementById(id);
      if (!el) return;
      if (count > 0) {
        el.textContent = count;
        el.style.display = 'inline';
        el.style.background = '#ef4444';
        el.style.color = '#fff';
      } else {
        el.style.display = 'none';
      }
    });
    // Notification dot in topbar
    var dot = document.getElementById('notif-dot');
    if (dot) {
      dot.style.display = count > 0 ? 'inline' : 'none';
    }
  }

  function fetchUnreadCount() {
    fetch(unreadUrl)
      .then(function(r) { if (!r.ok) throw new Error('fetch failed'); return r.json(); })
      .then(function(data) { updateNotifBadges(data.count || 0); })
      .catch(function() {});
  }

  /* ── Update sidebar navigation count badges ── */
  function updateSidebarBadges(counts) {
    document.querySelectorAll('[data-sidebar-count]').forEach(function(badge) {
      var key = badge.getAttribute('data-sidebar-count');
      var count = (counts[key] !== undefined) ? counts[key] : 0;
      if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'inline';
        badge.style.background = '#ef4444';
        badge.style.color = '#fff';
      } else {
        badge.style.display = 'none';
      }
    });
  }

  function fetchSidebarCounts() {
    fetch(sidebarCountsUrl)
      .then(function(r) { if (!r.ok) throw new Error('fetch failed'); return r.json(); })
      .then(function(data) { updateSidebarBadges(data); })
      .catch(function() {});
  }

  /* ── Initial fetch + polling ── */
  fetchUnreadCount();
  fetchSidebarCounts();
  setInterval(fetchUnreadCount, 10000);
  setInterval(fetchSidebarCounts, 15000);
})();

// Toast initialization
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.toast').forEach(el => {
    new bootstrap.Toast(el).show();
  });
});

// ── Global Toast Notification ──
window.showToast = function(message, type) {
  if (typeof type === 'undefined') type = 'success';
  var existing = document.querySelector('.global-toast');
  if (existing) existing.remove();

  var colors = {
    success: { bg: '#065f46', icon: 'checkmark-circle-outline' },
    error:   { bg: '#991b1b', icon: 'alert-circle-outline' },
    warning: { bg: '#92400e', icon: 'warning-outline' },
    info:    { bg: '#1e40af', icon: 'information-circle-outline' }
  };
  var c = colors[type] || colors.info;

  var toast = document.createElement('div');
  toast.className = 'global-toast';
  toast.innerHTML = '<ion-icon name="' + c.icon + '"></ion-icon> ' + message;
  Object.assign(toast.style, {
    position: 'fixed',
    bottom: '24px',
    left: '50%',
    transform: 'translateX(-50%)',
    background: c.bg,
    color: '#fff',
    padding: '12px 20px',
    borderRadius: '10px',
    fontSize: '13px',
    fontWeight: '500',
    zIndex: '9999',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
    fontFamily: "'Inter', sans-serif",
    transition: 'opacity 0.3s'
  });
  document.body.appendChild(toast);
  setTimeout(function() { toast.style.opacity = '0'; setTimeout(function() { toast.remove(); }, 300); }, 3000);
};

// ── Confirmation Modal ──
window.confirmAction = function(message) {
  return new Promise(function(resolve) {
    var modal = document.getElementById('confirmModal');
    if (!modal) { resolve(true); return; }
    var msgEl = document.getElementById('confirmModalMessage');
    if (msgEl) msgEl.textContent = message;
    var confirmBtn = document.getElementById('confirmModalBtn');
    var cancelBtn = document.getElementById('confirmModalCancel');
    var bsModal = new bootstrap.Modal(modal);

    function cleanup() {
      modal.removeEventListener('hidden.bs.modal', onHide);
      if (confirmBtn) confirmBtn.removeEventListener('click', onConfirm);
      if (cancelBtn) cancelBtn.removeEventListener('click', onCancel);
    }

    function onConfirm() {
      cleanup();
      bsModal.hide();
      resolve(true);
    }

    function onCancel() {
      cleanup();
      bsModal.hide();
      resolve(false);
    }

    function onHide() {
      cleanup();
      resolve(false);
    }

    if (confirmBtn) confirmBtn.addEventListener('click', onConfirm);
    if (cancelBtn) cancelBtn.addEventListener('click', onCancel);
    modal.addEventListener('hidden.bs.modal', onHide);

    bsModal.show();
  });
};

// ── Auto-confirm forms with data-confirm attribute ──
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('form[data-confirm]').forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var message = form.getAttribute('data-confirm');
      window.confirmAction(message).then(function(confirmed) {
        if (confirmed) {
          // Remove the data-confirm attribute to prevent loop
          form.removeAttribute('data-confirm');
          form.submit();
        }
      });
    });
  });
});

// ── Loading State on Form Submit ──
document.addEventListener('DOMContentLoaded', function() {
  // Auto-loading on form submit
  // Opt out with data-loading="false" on the form element
  document.querySelectorAll('form').forEach(function(form) {
    var loadingAttr = form.getAttribute('data-loading');
    if (loadingAttr === 'false') return;
    if (loadingAttr !== null && loadingAttr !== 'true') return; // custom value, skip

    form.addEventListener('submit', function(event) {
      var active = document.activeElement;
      var submitter = event.submitter;
      if (!submitter && active && active.form === form && active.type === 'submit') {
        submitter = active;
      }
      if (submitter && submitter.name && !submitter.disabled) {
        var preserved = document.createElement('input');
        preserved.type = 'hidden';
        preserved.name = submitter.name;
        preserved.value = submitter.value || '';
        preserved.setAttribute('data-preserved-submit', 'true');
        form.appendChild(preserved);
      }

      var buttons = form.querySelectorAll('[type="submit"]');
      buttons.forEach(function(btn) {
        btn.classList.add('btn-loading');
        btn.disabled = true;
      });
    });
  });
});

// ── Manual loading trigger ──
window.setLoading = function(btn, loading) {
  if (loading) {
    btn.classList.add('btn-loading');
    btn.disabled = true;
  } else {
    btn.classList.remove('btn-loading');
    btn.disabled = false;
  }
};

// ── Unsaved Changes Warning ──
window.initUnsavedChangesWarning = function(formOrId) {
  var form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
  if (!form) return;
  var formChanged = false;
  form.querySelectorAll('input, select, textarea').forEach(function(el) {
    el.addEventListener('change', function() { formChanged = true; });
    el.addEventListener('input', function() { formChanged = true; });
  });
  form.addEventListener('submit', function() { formChanged = false; });
  window.addEventListener('beforeunload', function(e) {
    if (formChanged) {
      e.preventDefault();
      e.returnValue = '';
    }
  });
};

// Auto-init forms with data-track-changes attribute
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('form[data-track-changes="true"]').forEach(function(form) {
    window.initUnsavedChangesWarning(form);
  });
});
