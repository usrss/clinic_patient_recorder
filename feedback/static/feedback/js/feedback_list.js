/* ═══════════════════════════════════════════
   Feedback List — search, filters, export, modal
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('feedbackForm');
    var searchInput = document.getElementById('fbSearchInput');
    var ratingFilter = document.getElementById('fbRatingFilter');
    var exportBtn = document.getElementById('exportMenuBtn');
    var exportMenu = document.getElementById('exportMenu');
    var csvLink = document.getElementById('exportCSVLink');
    var pdfLink = document.getElementById('exportPDFLink');
    var modalCloseBtn = document.getElementById('modalCloseBtn');
    var reviewModal = document.getElementById('reviewModal');

    // ── Show skeleton on load (brief flash) ──
    var skeleton = document.getElementById('skeletonLoader');
    if (skeleton) {
      skeleton.style.display = 'block';
      setTimeout(function () { skeleton.style.display = 'none'; }, 400);
    }

    // ── Search debounce ──
    var debounceTimer;
    if (searchInput && form) {
      searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () { form.submit(); }, 400);
      });
    }

    // ── Rating filter auto-submit ──
    if (ratingFilter && form) {
      ratingFilter.addEventListener('change', function () { form.submit(); });
    }

    // ── Export dropdown ──
    if (exportBtn && exportMenu) {
      exportBtn.addEventListener('click', function () {
        exportMenu.classList.toggle('show');
      });
    }
    document.addEventListener('click', function (e) {
      if (exportMenu && !e.target.closest('.fb-btn-export-dropdown')) {
        exportMenu.classList.remove('show');
      }
    });

    // ── CSV Export ──
    if (csvLink) {
      csvLink.addEventListener('click', function (e) {
        e.preventDefault();
        var rows = [['Patient Name', 'Patient ID', 'Consultation #', 'Rating', 'Review', 'Date']];

        // Row data is rendered by Django into #feedbackExportData (JSON)
        var dataEl = document.getElementById('feedbackExportData');
        var exportRows = [];
        if (dataEl) {
          try {
            exportRows = JSON.parse(dataEl.textContent);
          } catch (err) {
            exportRows = [];
          }
        }
        exportRows.forEach(function (row) {
          rows.push([row.patient_name, row.patient_id, row.consultation, row.rating, row.comment, row.date]);
        });

        var csv = rows.map(function (r) { return r.join(','); }).join('\n');
        var blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'feedback_export_' + new Date().toISOString().split('T')[0] + '.csv';
        a.click();
        URL.revokeObjectURL(a.href);
        if (exportMenu) exportMenu.classList.remove('show');
        showToast('CSV exported successfully');
      });
    }

    // ── PDF Export toast ──
    if (pdfLink) {
      pdfLink.addEventListener('click', function () {
        showToast('Generating PDF…');
      });
    }

    // ── View full review links (data-attribute driven) ──
    document.querySelectorAll('.view-full-review').forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        document.getElementById('reviewModalName').textContent = this.dataset.name;
        document.getElementById('reviewModalMeta').textContent = this.dataset.pid + ' \u00b7 ' + this.dataset.rating + '/5 stars \u00b7 ' + this.dataset.date;
        document.getElementById('reviewModalContent').textContent = this.dataset.comment;
        if (reviewModal) reviewModal.classList.add('open');
      });
    });

    // ── Modal close ──
    if (modalCloseBtn && reviewModal) {
      modalCloseBtn.addEventListener('click', function () { reviewModal.classList.remove('open'); });
    }

    // ── Click outside modal to close ──
    if (reviewModal) {
      reviewModal.addEventListener('click', function (e) {
        if (e.target === this) this.classList.remove('open');
      });
    }
  });
})();
