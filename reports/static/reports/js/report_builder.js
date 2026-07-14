function checkAll(val) {
  document.querySelectorAll('input[name="metrics"]').forEach(cb => cb.checked = val);
}

document.addEventListener('DOMContentLoaded', function () {
  const cols = document.querySelectorAll('#trend-chart .bar-col');
  if (!cols.length) return;
  const counts = Array.from(cols).map(c => parseInt(c.dataset.count) || 0);
  const max = Math.max(...counts, 1);
  cols.forEach(col => {
    const bar   = col.querySelector('.bar-fill');
    const count = parseInt(col.dataset.count) || 0;
    if (bar) {
      const pct = count > 0 ? Math.max((count / max) * 100, 4) : 2;
      bar.style.height = pct + '%';
      bar.style.flex   = 'none';
      if (count === 0) bar.style.opacity = '0.15';
    }
  });
});
