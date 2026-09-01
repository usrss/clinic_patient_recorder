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

// ═══════════════════════════════════════════════════════════════════
// Notification Banner Management — dismiss, dismiss-all, stacking
// ═══════════════════════════════════════════════════════════════════

// Dismiss a single banner with smooth animated collapse
window.dismissBanner = function(el, removeImmediate) {
  if (!el || el.classList.contains('dismissing')) return;
  el.classList.add('dismissing');
  var container = el.closest('.msg-banner-container');
  setTimeout(function() {
    el.remove();
    // Remove dismiss-all button if no banners remain
    if (container && !container.querySelector('.msg-banner')) {
      var da = container.querySelector('.msg-banner-dismiss-all-wrap');
      if (da) da.remove();
    }
  }, 350);
}

// Dismiss all banners with staggered animation
window.dismissAllBanners = function() {
  var container = document.querySelector('.msg-banner-container');
  if (!container) return;
  var banners = container.querySelectorAll('.msg-banner');
  // Hide dismiss-all button immediately
  var da = container.querySelector('.msg-banner-dismiss-all-wrap');
  if (da) da.style.display = 'none';
  // Dismiss each banner with staggered delay
  banners.forEach(function(el, idx) {
    setTimeout(function() {
      window.dismissBanner(el);
    }, idx * 80);
  });
}

// Auto-initialize banners on page load
window.initBanners = function() {
  var container = document.querySelector('.msg-banner-container');
  if (!container) return;
  var banners = container.querySelectorAll('.msg-banner');
  if (!banners.length) return;

  // Add animation class to each banner with staggered delay
  banners.forEach(function(el, idx) {
    setTimeout(function() {
      el.classList.add('success-anim');
    }, idx * 100);
  });

  // Show dismiss-all button if multiple banners
  if (banners.length > 1) {
    var daWrap = document.createElement('div');
    daWrap.className = 'msg-banner-dismiss-all-wrap';
    daWrap.innerHTML = '<button class="msg-banner-dismiss-all-btn" onclick="dismissAllBanners()">'
      + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
      + '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
      + 'Dismiss All (' + banners.length + ')'
      + '</button>';
    container.appendChild(daWrap);
  }

  // Auto-dismiss each banner after 2 seconds
  banners.forEach(function(el) {
    setTimeout(function() {
      window.dismissBanner(el);
    }, 2000);
  });
}

document.addEventListener('DOMContentLoaded', function() {
  window.initBanners();
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
        } else {
          // Re-enable any buttons disabled by the global loading handler
          form.querySelectorAll('[type="submit"]').forEach(function(btn) {
            btn.classList.remove('btn-loading');
            btn.disabled = false;
          });
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

// ── Combo widgets: ARIA + keyboard support ──
// Enhances any .combo-wrap (input + .combo-dropdown + .combo-option) with
// combobox semantics and arrow/Enter/Escape navigation. Idempotent via
// data-combo-enhanced. Existing inline handlers keep doing open/filter/select;
// this only adds accessibility + keyboard behavior on top.
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.combo-wrap').forEach(function(wrap) {
    var input = wrap.querySelector('input');
    var dd = wrap.querySelector('.combo-dropdown');
    if (!input || !dd || wrap.getAttribute('data-combo-enhanced')) return;
    wrap.setAttribute('data-combo-enhanced', 'true');

    var opts = Array.prototype.slice.call(dd.querySelectorAll('.combo-option'));
    var ddId = dd.id || ('combo-dd-' + Math.random().toString(36).slice(2, 8));
    if (!dd.id) dd.id = ddId;
    if (!input.id) input.id = ddId + '-input';

    dd.setAttribute('role', 'listbox');
    dd.setAttribute('id', ddId);
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-controls', ddId);
    input.setAttribute('aria-expanded', 'false');

    var activeIndex = -1;
    var visibleOpts = [];

    function setExpanded(open) {
      input.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    function refreshVisible() {
      visibleOpts = opts.filter(function(o) { return o.style.display !== 'none'; });
      if (activeIndex >= visibleOpts.length) activeIndex = visibleOpts.length - 1;
      if (activeIndex < 0 && visibleOpts.length) activeIndex = 0;
      highlight();
    }

    function highlight() {
      opts.forEach(function(o, i) {
        var active = o === visibleOpts[activeIndex];
        o.classList.toggle('active', active);
        if (active) {
          o.setAttribute('id', ddId + '-opt-' + i);
          input.setAttribute('aria-activedescendant', ddId + '-opt-' + i);
          if (o.scrollIntoView) o.scrollIntoView({ block: 'nearest' });
        }
      });
      if (!visibleOpts.length) input.removeAttribute('aria-activedescendant');
    }

    function selectActive() {
      if (!visibleOpts.length || activeIndex < 0) return;
      var o = visibleOpts[activeIndex];
      input.value = o.getAttribute('data-val') || o.textContent.trim();
      dd.classList.remove('open');
      setExpanded(false);
      input.focus();
    }

    // Give every option listbox semantics + a stable id.
    opts.forEach(function(o, i) {
      o.setAttribute('role', 'option');
      o.setAttribute('id', ddId + '-opt-' + i);
    });

    // Sync aria-expanded with open/close driven by inline handlers.
    input.addEventListener('focus', function() {
      setExpanded(true);
      refreshVisible();
    });
    input.addEventListener('input', function() {
      setExpanded(true);
      activeIndex = 0;
      refreshVisible();
    });
    input.addEventListener('blur', function() {
      setTimeout(function() {
        if (!dd.classList.contains('open')) setExpanded(false);
      }, 200);
    });
    dd.addEventListener('mouseleave', function() {
      activeIndex = -1;
      highlight();
    });

    // Keyboard navigation.
    input.addEventListener('keydown', function(e) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (!visibleOpts.length) { refreshVisible(); return; }
        activeIndex = (activeIndex + 1) % visibleOpts.length;
        highlight();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (!visibleOpts.length) { refreshVisible(); return; }
        activeIndex = (activeIndex - 1 + visibleOpts.length) % visibleOpts.length;
        highlight();
      } else if (e.key === 'Enter') {
        if (visibleOpts.length && activeIndex >= 0) {
          e.preventDefault();
          selectActive();
        }
      } else if (e.key === 'Escape') {
        dd.classList.remove('open');
        setExpanded(false);
        activeIndex = -1;
        highlight();
      }
    });
  });
});
