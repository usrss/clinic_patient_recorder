/* ═══════════════════════════════════════════
   Admin Dashboard — Chart.js initialization
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  function getChartData(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  document.addEventListener('DOMContentLoaded', function () {
    // ── Patients by College (doughnut) ──
    var collegeLabels = getChartData('chart-data-college-labels');
    var collegeValues = getChartData('chart-data-college-values');
    var ctx1 = document.getElementById('chart-college');
    if (ctx1 && collegeLabels && collegeValues) {
      new Chart(ctx1, {
        type: 'doughnut',
        data: {
          labels: collegeLabels,
          datasets: [{
            data: collegeValues,
            backgroundColor: ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#14b8a6', '#f97316'],
            borderWidth: 2,
            borderColor: '#ffffff',
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          cutout: '55%',
          plugins: {
            legend: {
              display: true,
              position: 'right',
              labels: {
                font: { size: 10, weight: '500' },
                boxWidth: 14,
                boxHeight: 14,
                padding: 10,
                usePointStyle: true,
                pointStyle: 'rectRounded',
                color: '#374151',
              },
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  var total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                  var val = context.parsed;
                  var pct = ((val / total) * 100).toFixed(1);
                  return context.label + ': ' + val + ' patients (' + pct + '%)';
                }
              }
            }
          },
        }
      });
    }

    // ── Diagnosis Analytics: Top Diagnoses (bar) ──
    var topDiagLabels = getChartData('chart-data-top-diag-labels');
    var topDiagValues = getChartData('chart-data-top-diag-values');
    var ctx4 = document.getElementById('chart-dash-top-diag');
    if (ctx4 && topDiagLabels && topDiagValues) {
      new Chart(ctx4, {
        type: 'bar',
        data: {
          labels: topDiagLabels,
          datasets: [{
            label: 'Cases',
            data: topDiagValues,
            backgroundColor: '#ef4444',
            borderRadius: 4,
            borderSkipped: false,
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'right',
              labels: {
                font: { size: 10, weight: '500' },
                boxWidth: 14,
                boxHeight: 14,
                padding: 10,
                usePointStyle: true,
                pointStyle: 'rectRounded',
                color: '#374151',
              },
            },
          },
          scales: {
            x: { ticks: { font: { size: 9 } }, grid: { display: false } },
            y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 9 } }, grid: { color: '#f0f0f0' } }
          }
        }
      });
    }

    // ── Diagnosis Analytics: Diagnosis Distribution by College (stacked bar) ──
    var diagCollegeLabels = getChartData('chart-data-diag-college-labels');
    var diagCollegeDatasets = getChartData('chart-data-diag-college-datasets');
    var ctx5 = document.getElementById('chart-dash-diag-college');
    if (ctx5 && diagCollegeLabels && diagCollegeDatasets) {
      new Chart(ctx5, {
        type: 'bar',
        data: {
          labels: diagCollegeLabels,
          datasets: diagCollegeDatasets,
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'right',
              labels: {
                font: { size: 10, weight: '500' },
                boxWidth: 14,
                boxHeight: 14,
                padding: 10,
                usePointStyle: true,
                pointStyle: 'rectRounded',
                color: '#374151',
              },
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  return context.dataset.label + ': ' + context.parsed.y + ' cases';
                }
              }
            }
          },
          scales: {
            x: { stacked: true, ticks: { font: { size: 9 } }, grid: { display: false } },
            y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1, font: { size: 9 } }, grid: { color: '#f0f0f0' } },
          }
        }
      });
    }
  });
})();
