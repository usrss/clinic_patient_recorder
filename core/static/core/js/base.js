// Notification badges — updates all badge elements on the page (desktop, mobile, sidebar)
(function() {
  const scriptTag = document.currentScript;
  const unreadUrl = scriptTag.dataset.unreadUrl;

  // Collect all notification badge elements
  function getBadges() {
    const badges = [];
    // Known badge element IDs
    const ids = ['unread-badge', 'unread-badge-mobile', 'sidebar-notif-badge', 'notif-dot'];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) badges.push(el);
    }
    // Also find elements with data-notif-badge attribute
    document.querySelectorAll('[data-notif-badge]').forEach(el => badges.push(el));
    return badges;
  }

  function fetchUnreadCount() {
    fetch(unreadUrl)
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        const count = data.count || 0;
        const badges = getBadges();
        badges.forEach(badge => {
          if (count > 0) {
            if (badge.id === 'notif-dot') {
              badge.style.display = 'inline';
            } else {
              badge.textContent = count;
              badge.style.display = 'inline';
            }
          } else {
            badge.style.display = 'none';
          }
        });
      })
      .catch(() => {
        // Silently retry on next interval
      });
  }

  fetchUnreadCount();
  setInterval(fetchUnreadCount, 10000);
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
