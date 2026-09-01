// ── Toggle visibility of new patient fields ──
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('consultation-form');
  const patientFound = form ? form.getAttribute('data-patient-found') === 'true' : false;

  document.querySelectorAll('.new-patient-fields').forEach(function (el) {
    if (patientFound) {
      el.classList.remove('visible');
    } else {
      el.classList.add('visible');
    }
  });

  // ── Unsaved changes warning is handled by base.js via data-track-changes="true" ──

  // ── Disable "Create Consultation" while the patient has an active consultation ──
  const hasActive = form ? form.getAttribute('data-has-active') === 'true' : false;
  const createBtn = document.getElementById('create-consultation-btn');
  if (createBtn && hasActive) {
    createBtn.disabled = true;
    createBtn.style.opacity = '0.5';
    createBtn.style.cursor = 'not-allowed';
  }
});
