document.addEventListener('DOMContentLoaded', function() {
  var printBtn = document.querySelector('.print-btn.no-print');
  if (printBtn) {
    printBtn.addEventListener('click', function() {
      window.print();
    });
  }

  // ── Auto-size performer name to fit on one line ──
  document.querySelectorAll('.sig-name').forEach(function(el) {
    var defaultSize = 10;       // default pt size from CSS
    var minSize     = 6;        // never go smaller than this
    var containerW  = el.parentElement.clientWidth; // sig-block width
    if (!containerW) return;

    el.style.fontSize = defaultSize + 'pt';
    if (el.scrollWidth <= containerW) return; // already fits

    // Binary-search for the largest size that fits
    var lo = minSize, hi = defaultSize;
    while (hi - lo > 0.25) {
      var mid = (lo + hi) / 2;
      el.style.fontSize = mid + 'pt';
      if (el.scrollWidth <= containerW) lo = mid; else hi = mid;
    }
    el.style.fontSize = lo + 'pt';
  });
});
