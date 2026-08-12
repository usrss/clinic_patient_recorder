/* ═══════════════════════════════════════════
   Doctor Dashboard — Chart.js initialization
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  function getChartData(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  document.addEventListener('DOMContentLoaded', function () {
    // ── 1. Urgency breakdown (bar) ──
    var urgencyData = getChartData('chart-data-urgency');
    var ctx1 = document.getElementById('chart-urgency');
    if (ctx1 && urgencyData) {
      new Chart(ctx1, {
        type: 'bar',
        data: {
          labels: Object.keys(urgencyData),
          datasets: [{
            label: 'Triages',
            data: Object.values(urgencyData),
            backgroundColor: ['#10b981', '#f97316', '#ef4444'],
            borderRadius: 4,
            borderSkipped: false,
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { font: { size: 11 } }, grid: { display: false } },
            y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } }, grid: { color: '#f0f0f0' } }
          }
        }
      });
    }

    // ── 2. Daily activity (line) ──
    var activityData = getChartData('chart-data-activity');
    var ctx2 = document.getElementById('chart-activity');
    if (ctx2 && activityData) {
      new Chart(ctx2, {
        type: 'line',
        data: {
          labels: activityData.map(d => d.date),
          datasets: [{
            label: 'Consultations',
            data: activityData.map(d => d.count),
            borderColor: '#7c3aed',
            backgroundColor: 'rgba(124,58,237,0.08)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#7c3aed',
            borderWidth: 2,
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { font: { size: 10 } }, grid: { display: false } },
            y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } }, grid: { color: '#f0f0f0' } }
          }
        }
      });
    }
  });
})();
