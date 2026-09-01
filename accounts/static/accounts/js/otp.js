/* ═══════════════════════════════════════════
   Verify OTP — Digit boxes, countdown, resend
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  var digits = [];
  for (var i = 0; i < 6; i++) digits.push(document.getElementById('otp-' + i));

  function getOtp() {
    var val = '';
    for (var i = 0; i < 6; i++) val += digits[i].value;
    return val;
  }

  // ── Auto-advance & auto-submit ──
  for (var i = 0; i < 6; i++) {
    (function (idx) {
      digits[idx].addEventListener('input', function () {
        this.value = this.value.replace(/[^0-9]/g, '').slice(0, 1);
        if (this.value) {
          this.classList.add('filled');
          this.classList.remove('error');
          if (idx < 5) digits[idx + 1].focus();
          if (getOtp().length === 6) {
            document.getElementById('verifyOtpBtn').click();
          }
        } else {
          this.classList.remove('filled');
        }
        document.getElementById('otp-error').style.display = 'none';
      });

      digits[idx].addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !this.value && idx > 0) {
          digits[idx - 1].focus();
          digits[idx - 1].value = '';
          digits[idx - 1].classList.remove('filled');
        }
        if (e.key === 'ArrowLeft' && idx > 0) { digits[idx - 1].focus(); }
        if (e.key === 'ArrowRight' && idx < 5) { digits[idx + 1].focus(); }
        if (e.key === 'Enter') {
          e.preventDefault();
          document.getElementById('verifyOtpBtn').click();
        }
      });

      digits[idx].addEventListener('paste', function (e) {
        e.preventDefault();
        var paste = (e.clipboardData || window.clipboardData).getData('text').replace(/[^0-9]/g, '').slice(0, 6);
        for (var j = 0; j < paste.length; j++) {
          if (idx + j < 6) {
            digits[idx + j].value = paste[j];
            digits[idx + j].classList.add('filled');
            digits[idx + j].classList.remove('error');
          }
        }
        digits[Math.min(idx + paste.length, 5)].focus();
      });
    })(i);
  }

  // ── Countdown timer ──
  var totalSeconds = 180;
  var formEl = document.getElementById('verify-otp-form');
  if (formEl && formEl.getAttribute('data-remaining')) {
    totalSeconds = Math.max(0, parseInt(formEl.getAttribute('data-remaining'), 10) || 0);
  }
  var resendBtn = document.getElementById('resend-btn');
  var verifyBtn = document.getElementById('verifyOtpBtn');

  function updateCountdown() {
    var mins = Math.floor(totalSeconds / 60);
    var secs = totalSeconds % 60;
    var timeStr = String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
    resendBtn.textContent = 'Resend code (' + timeStr + ')';
    if (totalSeconds <= 0) {
      clearInterval(timer);
      resendBtn.disabled = false;
      resendBtn.textContent = 'Resend code';
      resendBtn.style.cursor = 'pointer';
      resendBtn.style.opacity = '1';
      verifyBtn.disabled = true;
      verifyBtn.style.opacity = '0.5';
      verifyBtn.style.cursor = 'not-allowed';
      for (var i = 0; i < 6; i++) {
        digits[i].disabled = true;
        digits[i].classList.add('error');
      }
      document.getElementById('otp-error').textContent = 'Code expired. Please request a new one.';
      document.getElementById('otp-error').style.display = 'block';
    } else {
      totalSeconds--;
    }
  }
  var timer = setInterval(updateCountdown, 1000);

  // ── Inline resend via fetch ──
  resendBtn.addEventListener('click', function () {
    var csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
    resendBtn.disabled = true;
    resendBtn.textContent = 'Sending...';

    fetch(window.location.href, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: new URLSearchParams({ resend_otp: '1', csrfmiddlewaretoken: csrf })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.success) {
        totalSeconds = 180;
        updateCountdown(); // Immediately show countdown on button
        resendBtn.disabled = true;
        verifyBtn.disabled = false;
        verifyBtn.style.opacity = '1';
        verifyBtn.style.cursor = 'pointer';
        for (var i = 0; i < 6; i++) {
          digits[i].disabled = false;
          digits[i].value = '';
          digits[i].classList.remove('filled', 'error');
        }
        digits[0].focus();
        document.getElementById('otp-error').style.display = 'none';
      } else {
        resendBtn.textContent = 'Resend code';
        resendBtn.disabled = false;
        document.getElementById('otp-error').textContent = data.error || 'Failed to resend.';
        document.getElementById('otp-error').style.display = 'block';
      }
    })
    .catch(function () {
      resendBtn.textContent = 'Resend code';
      resendBtn.disabled = false;
      document.getElementById('otp-error').textContent = 'Network error.';
      document.getElementById('otp-error').style.display = 'block';
    });
  });

  // ── Loading state on submit ──
  document.getElementById('verify-otp-form').addEventListener('submit', function (e) {
    var otpVal = getOtp();
    if (otpVal.length !== 6) {
      e.preventDefault();
      document.getElementById('otp-error').textContent = 'Please enter all 6 digits.';
      document.getElementById('otp-error').style.display = 'block';
      for (var i = 0; i < 6; i++) {
        if (!digits[i].value) digits[i].classList.add('error');
      }
      return;
    }
    document.getElementById('otp-hidden').value = otpVal;
    // Show success state (replaces button with checkmark)
    document.getElementById('otp-success').style.display = 'block';
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<ion-icon name="checkmark-circle" style="font-size:16px;"></ion-icon> Verified!';
    verifyBtn.style.background = '#10b981';
  });
})();
