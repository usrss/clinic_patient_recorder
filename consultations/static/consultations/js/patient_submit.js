document.addEventListener('DOMContentLoaded', function() {
  // ── Character counter on textareas ──
  document.querySelectorAll('textarea').forEach(function(ta) {
    var counter = document.createElement('div');
    counter.style.cssText = 'font-size:11px;color:#94a3b8;text-align:right;margin-top:3px;';
    ta.parentNode.appendChild(counter);
    var maxLen = ta.getAttribute('maxlength');
    function updateCounter() {
      var len = ta.value.length;
      if (maxLen) {
        counter.textContent = len + ' / ' + maxLen;
      } else {
        counter.textContent = len + ' characters';
      }
    }
    ta.addEventListener('input', updateCounter);
    updateCounter();
  });

  // ── Unsaved changes warning is handled by base.js via data-track-changes="true" ──

  // ── Loading state on submit ──
  var submitForm = document.querySelector('.form-card form');
  if (submitForm) {
    submitForm.addEventListener('submit', function() {
      var btn = this.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Submitting…'; }
    });
  }
});
