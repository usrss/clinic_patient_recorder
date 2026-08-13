document.addEventListener('DOMContentLoaded', function() {
  const choiceYes = document.getElementById('choice-yes');
  const choiceNo = document.getElementById('choice-no');
  const dateRow = document.getElementById('date-row');
  const radioYes = choiceYes.querySelector('input');
  const radioNo = choiceNo.querySelector('input');

  function updateSelection() {
    if (radioYes.checked) {
      choiceYes.classList.add('selected');
      choiceNo.classList.remove('selected');
      dateRow.classList.add('visible');
    } else {
      choiceNo.classList.add('selected');
      choiceYes.classList.remove('selected');
      dateRow.classList.remove('visible');
    }
  }

  radioYes.addEventListener('change', updateSelection);
  radioNo.addEventListener('change', updateSelection);

  // Click on entire card
  choiceYes.addEventListener('click', function() { radioYes.checked = true; updateSelection(); });
  choiceNo.addEventListener('click', function() { radioNo.checked = true; updateSelection(); });

  // Initial state
  updateSelection();

  // ── Unsaved changes warning is handled by base.js via data-track-changes="true" ──

  // ── Loading state on submit ──
  var form = document.querySelector('.form-card form');
  if (form) {
    form.addEventListener('submit', function() {
      var btn = this.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Completing…'; }
    });
  }
});
