document.addEventListener('DOMContentLoaded', function() {
  var printBtn = document.querySelector('.print-btn.no-print');
  if (printBtn) {
    printBtn.addEventListener('click', function() {
      window.print();
    });
  }
});
