/* ═══════════════════════════════════════════
   Wizard Step 3 — PDF preview loading state
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  var frame = document.getElementById('pdfFrame');
  if (frame) {
    // Hide the loading overlay once the PDF iframe finishes loading
    frame.addEventListener('load', function () {
      var loading = document.getElementById('pdfLoading');
      if (loading) loading.classList.add('hidden');
    });
  }

  // Fallback: hide loading spinner after 15 seconds in case iframe load never fires
  setTimeout(function () {
    var loading = document.getElementById('pdfLoading');
    if (loading && !loading.classList.contains('hidden')) {
      loading.classList.add('hidden');
    }
  }, 15000);
})();
