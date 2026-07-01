function checkAll(val) {
  document.querySelectorAll('input[name="metrics"]').forEach(cb => cb.checked = val);
}
