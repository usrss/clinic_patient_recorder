/* ═══════════════════════════════════════════
   Auth — Shared JS for login / forgot password /
   reset password / change password pages
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Password strength calculator ──
  function getPwStrength(val) {
    var score = 0;
    if (val.length >= 8) score++;
    if (val.length >= 12) score++;
    if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
    if (/[0-9]/.test(val)) score++;
    if (/[^A-Za-z0-9]/.test(val)) score++;
    return score;
  }

  // ── Password visibility toggle ──
  function togglePw(btn, inputId) {
    var input = document.getElementById(inputId);
    if (!input || !btn) return;
    var eye = btn.querySelector('.icon-eye');
    var eyeOff = btn.querySelector('.icon-eye-off');
    var show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    if (eye) eye.style.display = show ? 'none' : '';
    if (eyeOff) eyeOff.style.display = show ? '' : 'none';
  }

  // ── Generic password toggle buttons (.pw-toggle / .pw-toggle-btn) ──
  // (The login page's #pwToggle is handled by its own dedicated handler below,
  // so it is skipped here to avoid double-toggling.)
  document.querySelectorAll('.pw-toggle, .pw-toggle-btn').forEach(function (btn) {
    if (btn.id === 'pwToggle') return;
    btn.addEventListener('click', function () {
      var wrap = btn.parentElement;
      var input = wrap ? wrap.querySelector('input') : null;
      if (input) togglePw(btn, input.id);
    });
  });

  // ── Login: password visibility toggle (SVG icon swap) ──
  var loginToggle = document.getElementById('pwToggle');
  if (loginToggle) {
    loginToggle.addEventListener('click', function () {
      var pwField = document.getElementById('id_password');
      var eye = document.getElementById('iconEye');
      var eyeOff = document.getElementById('iconEyeOff');
      if (!pwField) return;
      var show = pwField.type === 'password';
      pwField.type = show ? 'text' : 'password';
      if (eye) eye.style.display = show ? 'none' : '';
      if (eyeOff) eyeOff.style.display = show ? '' : 'none';
      loginToggle.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
  }

  // ── Login: loading state on submit ──
  var loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function () {
      var username = document.getElementById('id_username');
      var password = document.getElementById('id_password');
      if (!username || !password) return;
      if (!username.value.trim() || !password.value) return; // let the server handle it
      var btn = document.getElementById('loginBtn');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Signing in...';
      }
    });
  }

  // ── Forgot password: loading state on submit ──
  var fpForm = document.getElementById('forgot-pw-form');
  if (fpForm) {
    fpForm.addEventListener('submit', function (e) {
      var input = document.getElementById('id_patient_id');
      if (!input || !input.value.trim()) {
        e.preventDefault();
        return;
      }
      var btn = document.getElementById('sendOtpBtn');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Sending...';
      }
    });
  }

  // ── Strength meter + match indicator (reset & change password) ──
  function initPwStrengthUI(cfg) {
    var pw1 = document.getElementById(cfg.input1);
    if (!pw1) return;
    var pw2 = document.getElementById(cfg.input2);
    var wrap = document.getElementById(cfg.wrapId);
    var textEl = document.getElementById(cfg.textId);
    var matchEl = document.getElementById(cfg.matchId);

    function update() {
      var val = pw1.value;

      // Strength meter
      if (!val) {
        if (wrap) wrap.style.display = 'none';
      } else if (wrap && textEl) {
        wrap.style.display = 'block';
        var score = getPwStrength(val);
        var level = score <= 1 ? 1 : score <= 2 ? 2 : score <= 3 ? 3 : 4;
        var colors = ['', '#ef4444', '#f97316', '#eab308', '#10b981'];
        var labels = ['', 'Too weak', 'Weak', 'Good', 'Strong'];
        for (var i = 1; i <= 4; i++) {
          var bar = document.getElementById(cfg.barPrefix + i);
          if (bar) bar.style.background = i <= level ? colors[level] : '#e8ecf1';
        }
        textEl.textContent = labels[level];
        textEl.style.color = colors[level];
      }

      // Match indicator
      if (!pw2 || !matchEl) return;
      var v1 = pw1.value, v2 = pw2.value;
      if (v2.length === 0 && v1.length === 0) { matchEl.style.display = 'none'; return; }
      matchEl.style.display = 'flex';
      if (v1 && v2 && v1 === v2) {
        matchEl.innerHTML = '<ion-icon name="checkmark-circle" style="color:#10b981;font-size:14px;"></ion-icon><span style="color:#10b981;">Passwords match</span>';
      } else if (v2.length > 0) {
        matchEl.innerHTML = '<ion-icon name="close-circle" style="color:#ef4444;font-size:14px;"></ion-icon><span style="color:#ef4444;">Passwords do not match</span>';
      } else {
        matchEl.style.display = 'none';
      }
    }

    pw1.addEventListener('input', update);
    if (pw2) pw2.addEventListener('input', update);
  }

  // Reset password page
  initPwStrengthUI({
    input1: 'id_new_password1',
    input2: 'id_new_password2',
    wrapId: 'reset-strength-wrap',
    barPrefix: 'rsb',
    textId: 'reset-strength-text',
    matchId: 'reset-pw-match-indicator'
  });

  // Change password page
  initPwStrengthUI({
    input1: 'id_new_password1',
    input2: 'id_new_password2',
    wrapId: 'cp-strength-wrap',
    barPrefix: 'csb',
    textId: 'cp-strength-text',
    matchId: 'cp-pw-match-indicator'
  });
})();
