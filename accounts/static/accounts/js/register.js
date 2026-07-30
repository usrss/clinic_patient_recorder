// ── State ──────────────────────────────────────────────────────────────
let currentStep = 1;
let otpTimerInterval = null;
let otpSecondsLeft = 180; // 3 minutes

// ── Registration form persistence via sessionStorage ────────────────────
const REG_STORAGE_KEY = 'reg_form_data';

function saveFormState() {
  var fields = document.querySelectorAll('#reg-form input, #reg-form select, #reg-form textarea');
  var data = {};
  fields.forEach(function(el) {
    if (el.type === 'checkbox') {
      data[el.name] = el.checked ? 'on' : '';
    } else if (el.type === 'radio') {
      if (el.checked) data[el.name] = el.value;
    } else if (el.name && el.type !== 'hidden') {
      data[el.name] = el.value;
    }
  });
  data['_step'] = currentStep;
  try { sessionStorage.setItem(REG_STORAGE_KEY, JSON.stringify(data)); } catch(e) {}
}

function restoreSavedData() {
  try {
    var raw = sessionStorage.getItem(REG_STORAGE_KEY);
    if (!raw) return false;
    var data = JSON.parse(raw);
    var restored = false;
    for (var key in data) {
      if (key === '_step') continue;
      var el = document.querySelector('[name="' + key + '"]');
      if (!el) continue;
      if (el.type === 'checkbox') {
        el.checked = data[key] === 'on';
      } else {
        el.value = data[key];
      }
      restored = true;
    }
    if (restored && data['_step'] && parseInt(data['_step']) > 1) {
      return parseInt(data['_step']);
    }
    return restored ? data['_step'] || 1 : false;
  } catch(e) { return false; }
}

function clearSavedData() {
  try { sessionStorage.removeItem(REG_STORAGE_KEY); } catch(e) {}
}

function shouldRestoreData() {
  try {
    var raw = sessionStorage.getItem(REG_STORAGE_KEY);
    if (!raw) return false;
    var data = JSON.parse(raw);
    // Check if any field has a value
    for (var key in data) {
      if (key !== '_step' && data[key]) return true;
    }
    return false;
  } catch(e) { return false; }
}

// ── Auto-save form data on any input change ────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('reg-form');
  if (form) {
    form.addEventListener('input', saveFormState);
    form.addEventListener('change', function() { setTimeout(saveFormState, 0); });
  }
});

// ── Prevent Enter key from submitting the form (causes fields to disappear) ─
document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('reg-form');
  if (form) {
    form.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        // Allow Enter in textareas (step 4 medical fields)
        if (e.target.tagName === 'TEXTAREA') return;
        e.preventDefault();
        if (currentStep === 1) goNext(1);
        else if (currentStep === 3) goNext(3);
      }
    });
  }
});

// ── Password strength calculator (reusable) ────────────────────────────
function getPasswordStrength(val) {
  var score = 0;
  if (val.length >= 8) score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  return score;
}

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
    var emailVal = email.value.trim();
    var emailOk = validateEmail(emailVal);
    if (!emailOk) {
      showErr('email', true); email.classList.add('error');
      document.getElementById('err-email').textContent = 'Please enter a valid email address (e.g. name@domain.com).';
      valid = false;
    } else {
      showErr('email', false); email.classList.remove('error');
      // Reset to default message — server errors shown on re-render
      document.getElementById('err-email').textContent = 'Please enter a valid email address.';
    }

    const pw1 = document.getElementById('id_password1');
    var pwStrength = getPasswordStrength(pw1.value);
    if (pwStrength < 3) {
      showErr('password1', true); pw1.classList.add('error');
      document.getElementById('err-password1').textContent = 'Password is too weak. Use at least 8 characters with uppercase, lowercase, numbers, and special characters.';
      valid = false;
    } else {
      showErr('password1', false); pw1.classList.remove('error');
      document.getElementById('err-password1').textContent = 'Password must be at least 8 characters.';
    }

    const pw2 = document.getElementById('id_password2');
    if (pw2.value !== pw1.value || !pw2.value) {
      document.getElementById('err-password2').textContent = pw2.value ? 'Passwords do not match.' : 'Please confirm your password.';
      showErr('password2', true); pw2.classList.add('error'); valid = false;
    } else { showErr('password2', false); pw2.classList.remove('error');
      document.getElementById('err-password2').textContent = 'Passwords do not match.';
    }

    if (valid) {
      var formData = new FormData();
      formData.append('email', email.value.trim());
      formData.append('patient_id', id.value.trim());

      var btn = document.querySelector('#step-1 .btn-next');
      btn.disabled = true;
      btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Sending OTP…';

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
          document.getElementById('otp-error').textContent = data.error || 'Failed to send OTP. Please try again.';
          document.getElementById('otp-error').style.display = 'block';
        }
      })
      .catch(() => {
        btn.disabled = false;
        btn.innerHTML = 'Send OTP &amp; Continue <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>';
        document.getElementById('otp-error').textContent = 'Network error. Please try again.';
        document.getElementById('otp-error').style.display = 'block';
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

    // Validate phone format (Philippine number)
    const phone = document.getElementById('id_phone');
    if (phone.value.trim()) {
      var phoneClean = phone.value.trim().replace(/[\s\-\(\)\+]/g, '');
      if (!/^\d{7,15}$/.test(phoneClean)) {
        showErr('phone', true); phone.classList.add('error');
        document.getElementById('err-phone').textContent = 'Enter a valid phone number (7-15 digits).';
        valid = false;
      } else {
        document.getElementById('err-phone').textContent = 'Please enter a valid phone number.';
      }
    }

    const role = document.getElementById('id_role').value;
    if (role === 'student') {
      const col = document.getElementById('id_college');
      if (!col.value) { showErr('college', true); col.classList.add('error'); valid = false; }
      else { showErr('college', false); col.classList.remove('error'); }
      const course = document.getElementById('id_course');
      if (course && course.offsetParent !== null && !course.value) { showErr('course', true); course.classList.add('error'); valid = false; }
      else if (course) { showErr('course', false); course.classList.remove('error'); }
      // Validate year level for students
      const yearEl = document.getElementById('id_year_level');
      if (!yearEl.value) { showErr('year_level', true); yearEl.classList.add('error'); valid = false; }
      else { showErr('year_level', false); yearEl.classList.remove('error'); }
    } else if (role === 'faculty') {
      // Faculty needs both college and department
      const col = document.getElementById('id_college');
      if (!col.value) { showErr('college', true); col.classList.add('error'); valid = false; }
      else { showErr('college', false); col.classList.remove('error'); }
      const dept = document.getElementById('id_department');
      if (!dept.value.trim()) { showErr('department', true); dept.classList.add('error'); valid = false; }
      else { showErr('department', false); dept.classList.remove('error'); }
      // Clear course and year errors if switching from student
      showErr('course', false);
      showErr('year_level', false);
    } else {
      // Staff only needs department
      const dept = document.getElementById('id_department');
      if (!dept.value.trim()) { showErr('department', true); dept.classList.add('error'); valid = false; }
      else { showErr('department', false); dept.classList.remove('error'); }
      // Clear course and year errors if switching from student
      showErr('course', false);
      showErr('year_level', false);
    }

    if (valid) showStep(4);
  }
}

function goBack(step) {
  if (step === 2) { clearInterval(otpTimerInterval); showStep(1); }
  else if (step === 3) showStep(2);
  else if (step === 4) showStep(3);
}

// ── Email validator (strict) ───────────────────────────────────────────
function validateEmail(email) {
  // Strict RFC 5322-ish pattern
  return /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$/.test(email);
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
}  // ── Password strength & match ───────────────────────────────────────────
function updatePasswordUI() {
  const pw1 = document.getElementById('id_password1');
  const pw2 = document.getElementById('id_password2');
  if (!pw1) return;

  // ── Hide requirements hint when user starts typing ──
  const reqEl = document.getElementById('pw-requirements');
  if (reqEl) reqEl.style.display = pw1.value.length > 0 ? 'none' : '';

  // ── Strength meter ──
  const val = pw1.value;
  const wrap = document.getElementById('strength-wrap');
  if (!val) { wrap.style.display = 'none'; } else {
    wrap.style.display = 'block';
    var score = getPasswordStrength(val);
    var level = score <= 1 ? 1 : score <= 2 ? 2 : score <= 3 ? 3 : 4;
    var colors = ['', '#ef4444', '#f97316', '#eab308', '#10b981'];
    var labels = ['', 'Too weak', 'Weak', 'Good', 'Strong'];
    for (var i = 1; i <= 4; i++) {
      document.getElementById('sb' + i).style.background = i <= level ? colors[level] : '#e8ecf1';
    }
    document.getElementById('strength-text').textContent = labels[level];
    document.getElementById('strength-text').style.color = colors[level];
  }

  // ── Password match indicator ──
  var matchEl = document.getElementById('pw-match-indicator');
  if (!pw2 || !matchEl) return;
  var v1 = pw1.value, v2 = pw2.value;
  if (v2.length === 0 && v1.length === 0) { matchEl.style.display = 'none'; return; }
  matchEl.style.display = 'flex';
  if (v1 && v2 && v1 === v2) {
    matchEl.innerHTML = '<ion-icon name="checkmark-circle" style="color:#10b981;font-size:14px;"></ion-icon><span style="color:#10b981;">Passwords match</span>';
  } else if (v2.length > 0) {
    matchEl.innerHTML = '<ion-icon name="close-circle" style="color:#ef4444;font-size:14px;"></ion-icon><span style="color:#ef4444;">Passwords do not match</span>';
  } else { matchEl.style.display = 'none'; }
}

document.getElementById('id_password1').addEventListener('input', updatePasswordUI);
document.getElementById('id_password2').addEventListener('input', updatePasswordUI);

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
  const resend = document.getElementById('resend-btn');
  const verifyBtn = document.getElementById('verifyOtpBtnReg');
  if (otpSecondsLeft <= 0) {
    clearInterval(otpTimerInterval);
    resend.disabled = false;
    resend.innerHTML = 'Resend code';
    if (verifyBtn) verifyBtn.disabled = true;
    return;
  }
  const m = Math.floor(otpSecondsLeft / 60).toString().padStart(2, '0');
  const s = (otpSecondsLeft % 60).toString().padStart(2, '0');
  resend.innerHTML = 'Resend code (' + m + ':' + s + ')';
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
  const isFaculty = role === 'faculty';
  const showCollege = isStudent || isFaculty;
  document.getElementById('field-college').style.display    = showCollege ? '' : 'none';
  document.getElementById('field-year').style.display       = isStudent ? '' : 'none';
  document.getElementById('field-department').style.display = isStudent ? 'none' : '';
  document.getElementById('field-position').style.display   = isStudent ? 'none' : '';
  const fieldCourse = document.getElementById('field-course');
  if (fieldCourse) fieldCourse.style.display = isStudent ? '' : 'none';

  document.getElementById('id_college').required    = showCollege;
  document.getElementById('id_department').required = !isStudent;
  if (showCollege) loadCourses();
}

// ── Load courses dynamically when college changes ──────────────────────
function loadCourses() {
  const collegeId = document.getElementById('id_college').value;
  const courseSelect = document.getElementById('id_course');
  const fieldCourse = document.getElementById('field-course');
  if (!courseSelect) return;

  courseSelect.innerHTML = '<option value="">Select Course</option>';

  var role = document.getElementById('id_role').value;
  if (!collegeId) {
    if (fieldCourse) fieldCourse.style.display = 'none';
    return;
  }
  if (fieldCourse) fieldCourse.style.display = (role === 'student' && collegeId) ? '' : 'none';

  fetch(REGISTER_COURSES_URL + '?college_id=' + collegeId)
    .then(r => r.json())
    .then(data => {
      (data.courses || []).forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        courseSelect.appendChild(opt);
      });
      // ── Restore selected course from server-side form data (re-render) ──
      var selectedVal = courseSelect.getAttribute('data-selected');
      if (selectedVal && courseSelect.querySelector('option[value="' + selectedVal + '"]')) {
        courseSelect.value = selectedVal;
      }
    })
    .catch(() => {});
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

  // ── Check for saved registration data to restore ──
  var banner = document.getElementById('reg-restore-banner');
  if (shouldRestoreData() && step === 1) {
    restoreSavedData();
    // Re-run role field visibility after restoring, since the saved role
    // may differ from the default HTML value ('student')
    updateRoleFields();
    if (banner) banner.style.display = '';
  } else {
    if (banner) banner.style.display = 'none';
  }
});

// ── Clear saved data when form is successfully submitted ──
document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('reg-form');
  if (form) {
    form.addEventListener('submit', function() {
      // Only clear on step 4 submit (actual registration, not OTP step)
      clearSavedData();
    });
  }
});

updateRoleFields();