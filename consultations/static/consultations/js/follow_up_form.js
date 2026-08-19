document.addEventListener('DOMContentLoaded', function() {
  // Show/hide recommended follow-up date based on checkbox
  const requiresCheckbox = document.querySelector('input[name="requires_follow_up"]');
  const dateRow = document.getElementById('follow-up-date-row');

  function toggleDateRow() {
    dateRow.style.display = requiresCheckbox.checked ? 'flex' : 'none';
  }

  if (requiresCheckbox) {
    requiresCheckbox.addEventListener('change', toggleDateRow);
    toggleDateRow(); // initial state
  }
});
