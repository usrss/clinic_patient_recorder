function checkAll(val) {
  document.querySelectorAll('input[name="metrics"]').forEach(cb => cb.checked = val);
}

document.addEventListener('DOMContentLoaded', function () {
  const cols = document.querySelectorAll('#builder-trend .trend-bar-col');
  if (!cols.length) return;
  const counts = Array.from(cols).map(col => {
    const t = col.getAttribute('title') || '';
    const m = t.match(/:\s*(\d+)/);
    return m ? parseInt(m[1]) : 0;
  });
  const max = Math.max(...counts, 1);
  cols.forEach((col, i) => {
    const bar = col.querySelector('.trend-bar');
    if (bar) {
      const pct = Math.max((counts[i] / max) * 100, counts[i] > 0 ? 4 : 2);
      bar.style.height = pct + '%';
      bar.style.flex   = 'none';
    }
  });
});