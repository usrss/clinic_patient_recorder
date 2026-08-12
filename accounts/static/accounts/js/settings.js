/* ═══════════════════════════════════════════
   Settings — Shared JS for patient & staff
   ═══════════════════════════════════════════ */

// ── Password visibility toggle ──
function togglePw(btn) {
  var wrap  = btn.parentElement;
  var input = wrap.querySelector('input');
  var eye   = btn.querySelector('.icon-eye');
  var eyeOff = btn.querySelector('.icon-eye-off');
  if (!input) return;
  var show = input.type === 'password';
  input.type           = show ? 'text'  : 'password';
  eye.style.display    = show ? 'none'  : '';
  eyeOff.style.display = show ? ''      : 'none';
}

// ── Live Avatar Preview ──
function initAvatarPreview() {
  var fileInput = document.querySelector('input[type="file"]');
  if (!fileInput) return;

  fileInput.addEventListener('change', function(e) {
    var file = e.target.files[0];
    if (!file) return;

    var maxSize = 5 * 1024 * 1024; // 5 MB
    if (file.size > maxSize) {
      alert('File size (' + Math.round(file.size / 1024) + ' KB) exceeds the maximum allowed size of 5 MB.');
      fileInput.value = '';
      return;
    }

    var allowed = ['image/jpeg', 'image/png', 'image/webp'];
    if (allowed.indexOf(file.type) === -1) {
      alert('Unsupported file type. Allowed types: JPG, PNG, WebP.');
      fileInput.value = '';
      return;
    }

    var reader = new FileReader();
    reader.onload = function(ev) {
      var preview = document.querySelector('.settings-avatar');
      if (!preview) return;
      var img = preview.querySelector('img') || document.createElement('img');
      img.src = ev.target.result;
      img.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;';
      var initials = preview.querySelector('.initials');
      if (initials) initials.remove();
      if (!preview.querySelector('img')) {
        preview.insertBefore(img, preview.firstChild);
      }
    };
    reader.readAsDataURL(file);
  });
}

// ── Open photo lightbox (called from inline onclick on avatar) ──
function openPhotoModalView() {
  var avatar = document.querySelector('.settings-avatar');
  if (!avatar) return;
  var avatarImg = avatar.querySelector('img');
  if (!avatarImg || !avatarImg.src) return;
  var overlay = document.getElementById('photoModalOverlay');
  if (!overlay) return;
  var modalImg = overlay.querySelector('.photo-modal-img');
  modalImg.src = avatarImg.src;
  modalImg.style.display = 'block';
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

// ── Photo Modal / Upload trigger ──
function initPhotoModal() {
  // Always attach close-button and dismiss listeners FIRST so they work
  // regardless of whether the avatar has an inline onclick attribute.
  var closeBtn = document.getElementById('photoModalClose');
  if (closeBtn) closeBtn.addEventListener('click', closePhotoModal);

  var overlay = document.getElementById('photoModalOverlay');
  if (overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) closePhotoModal();
    });
  }

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closePhotoModal();
  });

  var avatar = document.querySelector('.settings-avatar');
  if (!avatar) return;
  // Remove any legacy inline onclick (previously set by the Django template)
  // so the listener below is the single source of behavior.
  if (avatar.hasAttribute('onclick')) avatar.removeAttribute('onclick');

  avatar.addEventListener('click', function() {
    var avatarImg = avatar.querySelector('img');
    if (avatarImg && avatarImg.src && avatarImg.src !== window.location.href) {
      // Has a profile picture → show the photo lightbox (existing behavior)
      var overlay = document.getElementById('photoModalOverlay');
      if (!overlay) return;
      var modalImg = overlay.querySelector('.photo-modal-img');
      modalImg.src = avatarImg.src;
      modalImg.style.display = 'block';
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
    } else {
      // No profile picture → open file picker directly so user can upload one
      var fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.click();
    }
  });
}

function closePhotoModal() {
  var overlay = document.getElementById('photoModalOverlay');
  if (overlay) {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
  closePhotoDropdown();
}

// ── Three-dots dropdown ──
function initPhotoDropdown() {
  var dotsBtn = document.querySelector('.photo-modal-dots');
  if (!dotsBtn) return;

  dotsBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    var dropdown = document.querySelector('.photo-modal-dropdown');
    if (!dropdown) return;
    var isOpen = dropdown.classList.toggle('open');
    dotsBtn.classList.toggle('active', isOpen);
  });

  document.addEventListener('click', function(e) {
    var dropdown = document.querySelector('.photo-modal-dropdown');
    var dotsBtn = document.querySelector('.photo-modal-dots');
    if (dropdown && dotsBtn) {
      if (!dropdown.contains(e.target) && !dotsBtn.contains(e.target)) {
        closePhotoDropdown();
      }
    }
  });
}

function closePhotoDropdown() {
  var dropdown = document.querySelector('.photo-modal-dropdown');
  var dotsBtn = document.querySelector('.photo-modal-dots');
  if (dropdown) dropdown.classList.remove('open');
  if (dotsBtn) dotsBtn.classList.remove('active');
}

// ── Change Photo action ──
function handleChangePhoto() {
  closePhotoModal();
  setTimeout(function() {
    var fileInput = document.querySelector('input[type="file"]');
    if (fileInput) fileInput.click();
  }, 350);
}

// ── Remove Photo action ──
function handleRemovePhoto() {
  if (!confirm('Remove your profile picture?')) return;
  closePhotoModal();
  var removeCheckbox = document.querySelector('input[name="remove_picture"]');
  if (removeCheckbox) {
    removeCheckbox.checked = true;
    var form = document.getElementById('profileForm');
    if (form) {
      var btn = document.getElementById('saveProfileBtn');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Removing...';
      }
      form.submit();
    }
  } else {
    location.reload();
  }
}

// ── Loading state for form buttons ──
function initLoadingState(formId, btnId, loadingText) {
  var form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener('submit', function() {
    var btn = document.getElementById(btnId);
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> ' + loadingText;
    }
  });
}

// ── Collapsible sections ──
function toggleCollapsible(header) {
  var section = header.parentElement;
  var isClosed = section.classList.toggle('collapsible-closed');
  var key = header.getAttribute('data-section');
  if (key) localStorage.setItem(key, isClosed ? 'closed' : 'open');
}

function initCollapsibleSections() {
  document.querySelectorAll('.collapsible-header').forEach(function(header) {
    var key = header.getAttribute('data-section');
    if (key) {
      var state = localStorage.getItem(key);
      if (state === 'closed') header.parentElement.classList.add('collapsible-closed');
    }
    // Previously inline onclick="toggleCollapsible(this)"
    header.addEventListener('click', function() { toggleCollapsible(this); });
  });
}

// ── Password match & strength for patient template ──
function initPatientPwValidation() {
  var pw1 = document.getElementById('id_new_password1');
  var pw2 = document.getElementById('id_new_password2');
  var indicator = document.getElementById('pwMatchIndicator');
  if (!pw1 || !pw2 || !indicator) return;

  function checkPwMatch() {
    var v1 = pw1.value, v2 = pw2.value;
    if (v2.length === 0 && v1.length === 0) { indicator.style.display = 'none'; return; }
    indicator.style.display = 'flex';
    if (v1 && v2 && v1 === v2) {
      indicator.innerHTML = '<ion-icon name="checkmark-circle" style="color:#10b981;font-size:16px;"></ion-icon><span style="color:#10b981;">Passwords match</span>';
    } else if (v2.length > 0) {
      indicator.innerHTML = '<ion-icon name="close-circle" style="color:#ef4444;font-size:16px;"></ion-icon><span style="color:#ef4444;">Passwords do not match</span>';
      if (v1.length > 0 && v1 !== v2) {
        var strength = 'Weak', color = '#ef4444';
        if (v1.length >= 12 && /[A-Z]/.test(v1) && /[0-9]/.test(v1) && /[^A-Za-z0-9]/.test(v1)) { strength = 'Strong'; color = '#10b981'; }
        else if (v1.length >= 8 && /[A-Z]/.test(v1) && /[0-9]/.test(v1)) { strength = 'Medium'; color = '#f59e0b'; }
        indicator.innerHTML += '<span style="margin-left:12px;font-size:11px;color:' + color + ';">Password strength: ' + strength + '</span>';
      }
    } else { indicator.style.display = 'none'; }
  }

  pw1.addEventListener('input', checkPwMatch);
  pw2.addEventListener('input', checkPwMatch);

  // Strength on new_password1 alone
  pw1.addEventListener('input', function() {
    var v = pw1.value;
    if (!pw2 || pw2.value.length === 0 && v.length > 0) {
      indicator.style.display = 'flex';
      var strength = 'Weak', color = '#ef4444';
      if (v.length >= 12 && /[A-Z]/.test(v) && /[0-9]/.test(v) && /[^A-Za-z0-9]/.test(v)) { strength = 'Strong'; color = '#10b981'; }
      else if (v.length >= 8 && /[A-Z]/.test(v) && /[0-9]/.test(v)) { strength = 'Medium'; color = '#f59e0b'; }
      indicator.innerHTML = '<ion-icon name="information-circle" style="color:' + color + ';font-size:16px;"></ion-icon><span style="color:' + color + ';">Password strength: ' + strength + '</span>';
    }
  });
}

// ── Password strength & match for staff template ──
function getStaffPwStrength(val) {
  var score = 0;
  if (val.length >= 8) score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  return score;
}

function initStaffPwValidation() {
  var pw1 = document.querySelector('#id_new_password1');
  var pw2 = document.querySelector('#id_new_password2');
  var indicator = document.getElementById('pwMatchIndicator');
  if (!pw1) return;

  // Create strength meter
  if (indicator) {
    var meterDiv = document.createElement('div');
    meterDiv.id = 'staff-strength-wrap';
    meterDiv.style.cssText = 'display:none;margin-bottom:6px;';
    meterDiv.innerHTML = '<div style="display:flex;gap:4px;margin-bottom:4px;">'
      + '<div class="staff-sbar" id="ssb1" style="flex:1;height:4px;border-radius:2px;background:#e8ecf1;transition:background 0.3s;"></div>'
      + '<div class="staff-sbar" id="ssb2" style="flex:1;height:4px;border-radius:2px;background:#e8ecf1;transition:background 0.3s;"></div>'
      + '<div class="staff-sbar" id="ssb3" style="flex:1;height:4px;border-radius:2px;background:#e8ecf1;transition:background 0.3s;"></div>'
      + '<div class="staff-sbar" id="ssb4" style="flex:1;height:4px;border-radius:2px;background:#e8ecf1;transition:background 0.3s;"></div>'
      + '</div>'
      + '<span id="staff-strength-text" style="font-size:11px;font-weight:600;color:#94a3b8;transition:color 0.3s;">Too short</span>';
    indicator.parentElement.insertBefore(meterDiv, indicator);
  }

  function updateStaffPwUI() {
    var val = pw1.value;
    var wrap = document.getElementById('staff-strength-wrap');
    if (!val) { if (wrap) wrap.style.display = 'none'; } else {
      if (wrap) {
        wrap.style.display = 'block';
        var score = getStaffPwStrength(val);
        var level = score <= 1 ? 1 : score <= 2 ? 2 : score <= 3 ? 3 : 4;
        var colors = ['', '#ef4444', '#f97316', '#eab308', '#10b981'];
        var labels = ['', 'Too weak', 'Weak', 'Good', 'Strong'];
        for (var i = 1; i <= 4; i++) {
          document.getElementById('ssb' + i).style.background = i <= level ? colors[level] : '#e8ecf1';
        }
        document.getElementById('staff-strength-text').textContent = labels[level];
        document.getElementById('staff-strength-text').style.color = colors[level];
      }
    }

    if (!pw2 || !indicator) return;
    var v1 = pw1.value, v2 = pw2.value;
    if (v2.length === 0 && v1.length === 0) { indicator.style.display = 'none'; return; }
    indicator.style.display = 'flex';
    if (v1 && v2 && v1 === v2) {
      indicator.innerHTML = '<ion-icon name="checkmark-circle" style="color:#10b981;font-size:14px;"></ion-icon><span style="color:#10b981;">Passwords match</span>';
    } else if (v2.length > 0) {
      indicator.innerHTML = '<ion-icon name="close-circle" style="color:#ef4444;font-size:14px;"></ion-icon><span style="color:#ef4444;">Passwords do not match</span>';
    } else { indicator.style.display = 'none'; }
  }

  pw1.addEventListener('input', updateStaffPwUI);
  if (pw2) pw2.addEventListener('input', updateStaffPwUI);
}

// ── Course loading (patient template) ──
function loadProfileCourses() {
  var collegeId = document.getElementById('id_college');
  var courseSelect = document.getElementById('id_course');
  if (!collegeId || !courseSelect) return;
  var collegeVal = collegeId.value;
  var savedId = courseSelect.getAttribute('data-saved-course') || '';
  courseSelect.innerHTML = '<option value="">Select Course</option>';
  if (!collegeVal) return;
  var url = courseSelect.getAttribute('data-courses-url');
  if (!url) return;
  fetch(url + '?college_id=' + collegeVal)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      (data.courses || []).forEach(function(c) {
        var opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        courseSelect.appendChild(opt);
      });
      if (savedId) { courseSelect.value = savedId; }
    })
    .catch(function() {});
}

// ── Event bindings (previously inline onclick handlers) ──
function initInlineHandlers() {
  // Password visibility toggles
  document.querySelectorAll('.pw-toggle').forEach(function(btn) {
    btn.addEventListener('click', function() { togglePw(this); });
  });

  // Photo modal dropdown items (Change / Remove photo)
  document.querySelectorAll('.photo-modal-dropdown-item').forEach(function(item) {
    item.addEventListener('click', function() {
      if (item.getAttribute('data-action') === 'remove-photo') handleRemovePhoto();
      else handleChangePhoto();
    });
  });
}

// ── Page init ──
document.addEventListener('DOMContentLoaded', function() {
  initAvatarPreview();
  initCollapsibleSections();
  initPhotoModal();
  initPhotoDropdown();
  initInlineHandlers();

  initLoadingState('profileForm', 'saveProfileBtn', 'Saving...');
  initLoadingState('passwordForm', 'changePwBtn', 'Changing...');
  initLoadingState('passwordForm', 'staffChangePwBtn', 'Changing...');

  // Init password validation (patient or staff)
  if (document.getElementById('staffChangePwBtn')) {
    initStaffPwValidation();
  } else {
    initPatientPwValidation();
  }

  // Init course loading for patient profile
  var collegeEl = document.getElementById('id_college');
  if (collegeEl) {
    collegeEl.addEventListener('change', function() {
      var courseSelect = document.getElementById('id_course');
      if (courseSelect) courseSelect.setAttribute('data-saved-course', courseSelect.value);
      loadProfileCourses();
    });
    if (collegeEl.value) loadProfileCourses();
  }
});
