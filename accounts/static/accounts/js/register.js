// ── State ──────────────────────────────────────────────────────────────
let currentStep = 1;
let otpTimerInterval = null;
let otpSecondsLeft = 180; // 3 minutes

// ── Step navigation ────────────────────────────────────────────────────
function showStep(n) {
  var stepInput = document.getElementById('current_step');
  if (stepInput) stepInput.value = n;

  document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('step-' + n).classList.add('active');

  for (let i = 1; i <= 4; i++) {
    const prog = document.getElementById('prog-' + i);
    prog.classList.remove('active', 'done');
    if (i < n) prog.classList.add('done');
    else if (i === n) prog.classList.add('active');
  }
  currentStep = n;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Step 1 → 2: Send OTP via AJAX ────────────────────────────────────
function goNext(step) {
  if (step === 1) {
    let valid = true;

    const id = document.getElementById('id_patient_id');
    if (!id.value.trim()) { showErr('patient_id', true); id.classList.add('error'); valid = false; }
    else { showErr('patient_id', false); id.classList.remove('error'); }

    const email = document.getElementById('id_email');
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim());
    if (!emailOk) { showErr('email', true); email.classList.add('error'); valid = false; }
    else { showErr('email', false); email.classList.remove('error'); }

    const pw1 = document.getElementById('id_password1');
    if (pw1.value.length < 8) { showErr('password1', true); pw1.classList.add('error'); valid = false; }
    else { showErr('password1', false); pw1.classList.remove('error'); }

    const pw2 = document.getElementById('id_password2');
    if (pw2.value !== pw1.value || !pw2.value) {
      document.getElementById('err-password2').textContent = pw2.value ? 'Passwords do not match.' : 'Please confirm your password.';
      showErr('password2', true); pw2.classList.add('error'); valid = false;
    } else { showErr('password2', false); pw2.classList.remove('error'); }

    if (valid) {
      var formData = new FormData();
      formData.append('email', email.value.trim());
      formData.append('patient_id', id.value.trim());

      var btn = document.querySelector('#step-1 .btn-next');
      btn.disabled = true;
      btn.textContent = 'Sending OTP\u2026';

      fetch(REGISTER_SEND_OTP_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        btn.disabled = false;
        btn.innerHTML = 'Send OTP &amp; Continue <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>';
        if (data.success) {
          document.getElementById('otp-email-display').textContent = email.value.trim();
          startOtpTimer();
          showStep(2);
        } else {
          alert(data.error || 'Failed to send OTP. Please try again.');
        }
      })
      .catch(() => {
        btn.disabled = false;
        btn.innerHTML = 'Send OTP &amp; Continue <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>';
        alert('Network error. Please try again.');
      });
    }
  } else if (step === 3) {
    let valid = true;
    const required3 = ['first_name', 'last_name', 'sex', 'birthday', 'phone', 'emergency_contact_name', 'emergency_contact_phone'];

    required3.forEach(f => {
      const el = document.getElementById('id_' + f);
      if (!el || !el.value.trim()) {
        showErr(f, true); if (el) el.classList.add('error'); valid = false;
      } else {
        showErr(f, false); el.classList.remove('error');
      }
    });

    const role = document.getElementById('id_role').value;
    if (role === 'student') {
      const col = document.getElementById('id_college');
      if (!col.value) { showErr('college', true); col.classList.add('error'); valid = false; }
      else { showErr('college', false); col.classList.remove('error'); }
    } else {
      const dept = document.getElementById('id_department');
      if (!dept.value.trim()) { showErr('department', true); dept.classList.add('error'); valid = false; }
      else { showErr('department', false); dept.classList.remove('error'); }
    }

    if (valid) showStep(4);
  }
}

function goBack(step) {
  if (step === 2) { clearInterval(otpTimerInterval); showStep(1); }
  else if (step === 3) showStep(2);
  else if (step === 4) showStep(3);
}

// ── Show/hide field errors ─────────────────────────────────────────────
function showErr(field, show) {
  const el = document.getElementById('err-' + field);
  if (el) el.classList.toggle('show', show);
}

// ── Password show/hide ─────────────────────────────────────────────────
function togglePw(inputId, btn) {
  const input = document.getElementById(inputId);
  const num = inputId === 'id_password1' ? 'pw1' : 'pw2';
  const isHidden = input.type === 'password';

  input.type = isHidden ? 'text' : 'password';
  document.getElementById('eye-' + num + '-show').style.display = isHidden ? 'none' : '';
  document.getElementById('eye-' + num + '-hide').style.display = isHidden ? '' : 'none';
  btn.style.color = isHidden ? '#0078d4' : '#94a3b8';
}

// ── Password strength ──────────────────────────────────────────────────
document.getElementById('id_password1').addEventListener('input', function () {
  const val = this.value;
  const wrap = document.getElementById('strength-wrap');

  if (!val) { wrap.style.display = 'none'; return; }
  wrap.style.display = 'block';

  let score = 0;
  if (val.length >= 8) score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;

  const level = score <= 1 ? 1 : score <= 2 ? 2 : score <= 3 ? 3 : 4;
  const colors = ['', '#ef4444', '#f97316', '#eab308', '#10b981'];
  const labels = ['', 'Too weak', 'Weak', 'Good', 'Strong'];

  for (let i = 1; i <= 4; i++) {
    const bar = document.getElementById('sb' + i);
    bar.style.background = i <= level ? colors[level] : '#e8ecf1';
  }
  const txt = document.getElementById('strength-text');
  txt.textContent = labels[level];
  txt.style.color = colors[level];
});

// ── OTP boxes auto-advance ─────────────────────────────────────────────
const otpBoxes = document.querySelectorAll('.otp-box');
otpBoxes.forEach((box, idx) => {
  box.addEventListener('input', function () {
    this.value = this.value.replace(/[^0-9]/g, '');
    if (this.value && idx < 5) otpBoxes[idx + 1].focus();
    this.classList.toggle('filled', !!this.value);
    this.classList.remove('error-otp');
    document.getElementById('otp-error').textContent = '';
    let code = '';
    otpBoxes.forEach(b => code += b.value);
    document.getElementById('otp-hidden').value = code;
  });

  box.addEventListener('keydown', function (e) {
    // Prevent Enter from submitting the form; trigger verify instead
    if (e.key === 'Enter') {
      e.preventDefault();
      verifyOtp();
      return;
    }
    if (e.key === 'Backspace' && !this.value && idx > 0) {
      otpBoxes[idx - 1].focus();
      otpBoxes[idx - 1].value = '';
      otpBoxes[idx - 1].classList.remove('filled');
    }
  });

  box.addEventListener('paste', function (e) {
    e.preventDefault();
    const data = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '').slice(0, 6);
    data.split('').forEach((ch, i) => {
      if (otpBoxes[i]) { otpBoxes[i].value = ch; otpBoxes[i].classList.add('filled'); }
    });
    let code = '';
    otpBoxes.forEach(b => code += b.value);
    document.getElementById('otp-hidden').value = code;
    if (otpBoxes[Math.min(data.length, 5)]) otpBoxes[Math.min(data.length, 5)].focus();
  });
});

// ── OTP timer ─────────────────────────────────────────────────────────
function startOtpTimer() {
  otpSecondsLeft = 180;
  clearInterval(otpTimerInterval);
  document.getElementById('resend-btn').disabled = true;
  tickTimer();
  otpTimerInterval = setInterval(tickTimer, 1000);
}

function tickTimer() {
  const el = document.getElementById('otp-countdown');
  const resend = document.getElementById('resend-btn');
  if (otpSecondsLeft <= 0) {
    clearInterval(otpTimerInterval);
    el.textContent = 'expired';
    el.classList.add('expired');
    resend.disabled = false;
    return;
  }
  const m = Math.floor(otpSecondsLeft / 60).toString().padStart(2, '0');
  const s = (otpSecondsLeft % 60).toString().padStart(2, '0');
  el.textContent = m + ':' + s;
  el.classList.remove('expired');
  otpSecondsLeft--;
}

function resendOtp() {
  const email = document.getElementById('id_email').value.trim();
  const patientId = document.getElementById('id_patient_id').value.trim();

  document.getElementById('otp-error').textContent = '';
  otpBoxes.forEach(b => { b.value = ''; b.classList.remove('filled', 'error-otp'); });
  document.getElementById('otp-hidden').value = '';
  otpBoxes[0].focus();

  var formData = new FormData();
  formData.append('email', email);
  formData.append('patient_id', patientId);

  fetch(REGISTER_SEND_OTP_URL, {
    method: 'POST',
    headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      startOtpTimer();
    } else {
      document.getElementById('otp-error').textContent = data.error || 'Failed to resend OTP.';
    }
  });
}

// ── OTP verify ────────────────────────────────────────────────────────
function verifyOtp() {
  var code = document.getElementById('otp-hidden').value;
  if (code.length < 6) {
    otpBoxes.forEach(b => b.classList.add('error-otp'));
    document.getElementById('otp-error').textContent = 'Please enter all 6 digits.';
    return;
  }

  var formData = new FormData();
  formData.append('otp', code);

  fetch(REGISTER_VERIFY_OTP_URL, {
    method: 'POST',
    headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showStep(3);
    } else {
      document.getElementById('otp-error').textContent = data.error;
      otpBoxes.forEach(b => b.classList.add('error-otp'));
    }
  });
}

// ── Role → show/hide college vs department ────────────────────────────
function updateRoleFields() {
  const role = document.getElementById('id_role').value;
  const isStudent = role === 'student';
  document.getElementById('field-college').style.display    = isStudent ? '' : 'none';
  document.getElementById('field-year').style.display       = isStudent ? '' : 'none';
  document.getElementById('field-department').style.display = isStudent ? 'none' : '';
  document.getElementById('field-position').style.display   = isStudent ? 'none' : '';

  document.getElementById('id_college').required    = isStudent;
  document.getElementById('id_department').required = !isStudent;
}

// ── Restore step after server-side validation failure ─────────────────
// The hidden input is seeded server-side via {{ current_step|default:'1' }},
// so on a failed POST the page re-renders already showing the correct step value.
document.addEventListener('DOMContentLoaded', function () {
  var stepInput = document.getElementById('current_step');
  var step = stepInput ? parseInt(stepInput.value) : 1;
  if (step > 1) {
    showStep(step);
  }
});

updateRoleFields();