(function () {
  'use strict';

  /* ── Inventory medicine options (for dynamically added rows) ──
     Data is rendered by Django into #prescribe-inventory-data (JSON). */
  var INV_OPTIONS = ['<option value="">— Select —</option>'];
  var HAS_INVENTORY = false;
  var invDataEl = document.getElementById('prescribe-inventory-data');
  if (invDataEl) {
    try {
      var inventory = JSON.parse(invDataEl.textContent);
      HAS_INVENTORY = inventory.length > 0;
      inventory.forEach(function (med) {
        INV_OPTIONS.push('<option value="' + med.pk + '">' + med.name + ' (' + med.quantity + ' left)</option>');
      });
    } catch (e) { /* keep defaults */ }
  }
  INV_OPTIONS = INV_OPTIONS.join('');

  /* ── Select dropdown option HTML snippets ── */
  var DOSAGE_OPTS    = '<option value="">—</option><option>500mg</option><option>250mg</option><option>200mg</option><option>100mg</option><option>50mg</option><option>25mg</option><option>10mg</option><option>5mg</option><option>10ml</option><option>5ml</option><option>2.5ml</option><option value="other">Other…</option>';
  var FREQ_OPTS      = '<option value="">—</option><option>Once daily</option><option>2x a day</option><option>3x a day</option><option>4x a day</option><option>Every 4 hours</option><option>Every 6 hours</option><option>Every 8 hours</option><option>As needed</option><option value="other">Other…</option>';
  var DUR_OPTS       = '<option value="">—</option><option>1 day</option><option>3 days</option><option>5 days</option><option>7 days</option><option>10 days</option><option>14 days</option><option>1 month</option><option value="other">Other…</option>';
  var INSTR_OPTS     = '<option value="">—</option><option>Take after meals</option><option>Take before meals</option><option>Take on empty stomach</option><option>Take with food</option><option>Apply topically</option><option>As directed</option><option value="other">Other…</option>';

  var totalForms = document.getElementById('id_meds-TOTAL_FORMS');
  var container  = document.getElementById('medicine-rows');
  var PREFIX     = 'meds';

  /* ════════════════════════════════════════════════════════════
     1. "Other…" toggle — shows/hides the free-text sibling
     ════════════════════════════════════════════════════════════ */
  function wireOtherToggles(scope) {
    scope.querySelectorAll('select.med-select').forEach(function (sel) {
      var other = sel.nextElementSibling;
      if (!other || !other.classList.contains('other-input')) return;

      function sync() {
        if (sel.value === 'other') {
          other.classList.add('visible');
          other.style.display = '';
        } else {
          other.classList.remove('visible');
          other.style.display = 'none';
          other.value = '';
        }
      }
      sel.addEventListener('change', function () {
        sync();
        if (sel.value === 'other') other.focus();
      });
      sync(); // initial state (no focus steal)
    });
  }

  /* Also wire the Apply-to-All bar selects */
  wireOtherToggles(document.getElementById('apply-all-bar'));

  /* ════════════════════════════════════════════════════════════
     2. Mode toggle (inventory ↔ custom) per row
     ════════════════════════════════════════════════════════════ */
  function wireMode(row) {
    var radios   = row.querySelectorAll('.med-source-radio');
    var invDiv   = row.querySelector('.med-mode-inventory');
    var cusDiv   = row.querySelector('.med-mode-custom');
    var srcField = row.querySelector('.source-field');

    // Initial mode from the hidden source field (edit pre-fill).
    if (srcField && srcField.value === 'custom') {
      radios.forEach(function (r) { if (r.value === 'custom') r.checked = true; });
    }

    function update() {
      var active = row.querySelector('.med-source-radio:checked');
      var isCustom = active && active.value === 'custom';
      if (invDiv) invDiv.style.display = isCustom ? 'none' : '';
      if (cusDiv) cusDiv.style.display = isCustom ? ''     : 'none';
      if (srcField) srcField.value = isCustom ? 'custom' : 'inventory';
    }

    radios.forEach(function (r) { r.addEventListener('change', update); });
    update();
  }

  /* ════════════════════════════════════════════════════════════
     3. Remove row
     ════════════════════════════════════════════════════════════ */
  function removeRow(btn) {
    var row  = btn.closest('.medicine-row');
    var rows = container.querySelectorAll('.medicine-row');
    if (rows.length <= 1) {
      // Clear all fields instead of removing last row
      row.querySelectorAll('input:not([type=radio]):not([type=hidden]), select').forEach(function (el) { el.value = ''; });
      return;
    }
    row.remove();
    renumber();
  }

  /* ════════════════════════════════════════════════════════════
     4. Renumber all rows after add/remove
     ════════════════════════════════════════════════════════════ */
  function renumber() {
    container.querySelectorAll('.medicine-row').forEach(function (row, idx) {
      row.setAttribute('data-index', idx);
      row.querySelectorAll('[name^="meds-"]').forEach(function (el) {
        el.name = el.name.replace(/^meds-\d+-/, PREFIX + '-' + idx + '-');
        if (el.id) el.id = el.id.replace(/^id_meds-\d+-/, 'id_' + PREFIX + '-' + idx + '-');
      });
    });
    totalForms.value = container.querySelectorAll('.medicine-row').length;
  }

  /* ════════════════════════════════════════════════════════════
     5. Build a fresh row HTML for a given index
     ════════════════════════════════════════════════════════════ */
  function buildRowHTML(idx) {
    var p = PREFIX + '-' + idx + '-';
    return '' +
      '<button type="button" class="remove-row-btn" title="Remove row"><ion-icon name="close-outline" style="font-size:16px;"></ion-icon></button>' +
      '<input type="hidden" name="' + p + 'source" value="inventory" class="source-field">' +

      '<div style="margin-bottom:12px;">' +
        '<label class="mode-toggle-label"><input type="radio" name="med_source_' + idx + '" value="inventory" class="med-source-radio" checked> From Inventory</label>' +
        '<label class="mode-toggle-label"><input type="radio" name="med_source_' + idx + '" value="custom" class="med-source-radio"> Custom (not in inventory)</label>' +
      '</div>' +

      /* inventory */
      '<div class="med-mode-inventory">' +
        '<div class="inv-grid">' +
          '<div class="field-wrap"><label>Medicine</label><select name="' + p + 'medicine" class="reg-input">' + INV_OPTIONS + '</select></div>' +
          '<div class="field-wrap"><label>Dosage <span style="color:#ef4444;">*</span></label><select name="' + p + 'inv_dosage" class="reg-input med-select">' + DOSAGE_OPTS + '</select><input type="text" name="' + p + 'inv_dosage_other" class="reg-input other-input" placeholder="e.g. 750mg"></div>' +
          '<div class="field-wrap"><label>Frequency <span style="color:#ef4444;">*</span></label><select name="' + p + 'inv_frequency" class="reg-input med-select">' + FREQ_OPTS + '</select><input type="text" name="' + p + 'inv_frequency_other" class="reg-input other-input" placeholder="e.g. Every 12 hours"></div>' +
          '<div class="field-wrap"><label>Duration <span style="color:#ef4444;">*</span></label><select name="' + p + 'inv_duration" class="reg-input med-select">' + DUR_OPTS + '</select><input type="text" name="' + p + 'inv_duration_other" class="reg-input other-input" placeholder="e.g. 3 weeks"></div>' +
          '<div class="field-wrap"><label>Qty <span style="color:#ef4444;">*</span></label><input type="number" name="' + p + 'quantity" class="reg-input" min="1" placeholder="Units"></div>' +
          '<div class="field-wrap"><label>Instructions</label><select name="' + p + 'inv_instructions" class="reg-input med-select">' + INSTR_OPTS + '</select><input type="text" name="' + p + 'inv_instructions_other" class="reg-input other-input" placeholder="e.g. Dissolve in water"></div>' +
        '</div>' +
      '</div>' +

      /* custom */
      '<div class="med-mode-custom" style="display:none;">' +
        '<div class="cus-grid">' +
          '<div class="field-wrap"><label>Medicine Name <span style="color:#ef4444;">*</span></label><input type="text" name="' + p + 'medicine_name" class="reg-input" placeholder="e.g. Betadine Gargle" autocomplete="off"></div>' +
          '<div class="field-wrap"><label>Dosage <span style="color:#ef4444;">*</span></label><select name="' + p + 'cus_dosage" class="reg-input med-select">' + DOSAGE_OPTS + '</select><input type="text" name="' + p + 'cus_dosage_other" class="reg-input other-input" placeholder="e.g. 750mg"></div>' +
          '<div class="field-wrap"><label>Frequency <span style="color:#ef4444;">*</span></label><select name="' + p + 'cus_frequency" class="reg-input med-select">' + FREQ_OPTS + '</select><input type="text" name="' + p + 'cus_frequency_other" class="reg-input other-input" placeholder="e.g. Every 12 hours"></div>' +
          '<div class="field-wrap"><label>Duration <span style="color:#ef4444;">*</span></label><select name="' + p + 'cus_duration" class="reg-input med-select">' + DUR_OPTS + '</select><input type="text" name="' + p + 'cus_duration_other" class="reg-input other-input" placeholder="e.g. 3 weeks"></div>' +
          '<div class="field-wrap"><label>Instructions</label><select name="' + p + 'cus_instructions" class="reg-input med-select">' + INSTR_OPTS + '</select><input type="text" name="' + p + 'cus_instructions_other" class="reg-input other-input" placeholder="e.g. Dissolve in water"></div>' +
        '</div>' +
      '</div>';
  }

  /* ════════════════════════════════════════════════════════════
     6. Wire existing rows
     ════════════════════════════════════════════════════════════ */
  container.querySelectorAll('.medicine-row').forEach(function (row) {
    wireMode(row);
    wireOtherToggles(row);
    var btn = row.querySelector('.remove-row-btn');
    if (btn) btn.addEventListener('click', function () { removeRow(btn); });
  });

  /* ════════════════════════════════════════════════════════════
     7. Add medicine row button
     ════════════════════════════════════════════════════════════ */
  document.getElementById('add-medicine-btn').addEventListener('click', function () {
    var idx = parseInt(totalForms.value, 10);
    var row = document.createElement('div');
    row.className = 'medicine-row';
    row.setAttribute('data-index', idx);
    row.innerHTML = buildRowHTML(idx);
    container.appendChild(row);
    wireMode(row);
    wireOtherToggles(row);
    row.querySelector('.remove-row-btn').addEventListener('click', function () { removeRow(this); });
    totalForms.value = idx + 1;
  });

  /* ════════════════════════════════════════════════════════════
     8. Apply to All
     Resolves the "other" free-text value for each ATA field.
     Copies dosage/frequency/duration into each row's ACTIVE mode.
     Instructions: stored in one hidden field (not copied per-row)
     so the print view shows it only once.
     ════════════════════════════════════════════════════════════ */
  function ataValue(selectId, otherId) {
    var sel = document.getElementById(selectId);
    var oth = document.getElementById(otherId);
    if (!sel || !sel.value) return null;       // "— keep —"
    if (sel.value === 'other') return (oth && oth.value.trim()) || null;
    return sel.value;
  }

  document.getElementById('apply-all-btn').addEventListener('click', function () {
    var dosage       = ataValue('ata-dosage',       'ata-dosage-other');
    var frequency    = ataValue('ata-frequency',    'ata-frequency-other');
    var duration     = ataValue('ata-duration',     'ata-duration-other');
    var instructions = ataValue('ata-instructions', 'ata-instructions-other');

    // Store shared instructions into the hidden field (submitted once, used by view)
    if (instructions !== null) {
      document.getElementById('apply_instructions_hidden').value = instructions;
    }

    container.querySelectorAll('.medicine-row').forEach(function (row) {
      var sourceField = row.querySelector('.source-field');
      var mode = (sourceField && sourceField.value === 'custom') ? 'cus' : 'inv';

      function setSelect(nameSuffix, value) {
        if (value === null) return;
        var sel = row.querySelector('[name$="-' + nameSuffix + '"]');
        if (!sel) return;
        // Try to match existing option
        var matched = false;
        for (var i = 0; i < sel.options.length; i++) {
          if (sel.options[i].value === value || sel.options[i].text === value) {
            sel.value = sel.options[i].value;
            matched = true;
            break;
          }
        }
        if (!matched) {
          // Fall back to "Other…" + set text field
          sel.value = 'other';
          var other = sel.nextElementSibling;
          if (other && other.classList.contains('other-input')) {
            other.value = value;
            other.style.display = '';
            other.classList.add('visible');
          }
        } else {
          // Hide the other input if the match wasn't "other"
          var other = sel.nextElementSibling;
          if (other && other.classList.contains('other-input') && sel.value !== 'other') {
            other.style.display = 'none';
            other.classList.remove('visible');
            other.value = '';
          }
        }
        sel.dispatchEvent(new Event('change'));
      }

      setSelect(mode + '_dosage',    dosage);
      setSelect(mode + '_frequency', frequency);
      setSelect(mode + '_duration',  duration);
      // Instructions are NOT copied per-row (shared hidden field handles it)
      // But we clear the per-row instruction selects so there's no conflict
      if (instructions !== null) {
        ['inv_instructions', 'cus_instructions'].forEach(function (suffix) {
          var sel = row.querySelector('[name$="-' + suffix + '"]');
          if (sel) {
            sel.value = '';
            var other = sel.nextElementSibling;
            if (other && other.classList.contains('other-input')) {
              other.style.display = 'none';
              other.classList.remove('visible');
              other.value = '';
            }
          }
        });
      }
    });

    /* Visual feedback */
    var btn = document.getElementById('apply-all-btn');
    var origHTML = btn.innerHTML;
    btn.innerHTML = '<ion-icon name="checkmark-circle" style="font-size:14px;"></ion-icon> Applied!';
    btn.style.background = '#16a34a';
    setTimeout(function () { btn.innerHTML = origHTML; btn.style.background = ''; }, 1500);
  });

  /* ════════════════════════════════════════════════════════════
     9. Diagnosis auto-fill
     ════════════════════════════════════════════════════════════ */
  var diagSel = document.getElementById('diagnosis_select_field');
  if (diagSel) {
    diagSel.addEventListener('change', function () {
      if (this.value) {
        document.querySelector('[name="diagnosis"]').value =
          this.options[this.selectedIndex].text;
      }
    });
  }

  /* ════════════════════════════════════════════════════════════
     10. Form submit — loading state to prevent double-submission
     ════════════════════════════════════════════════════════════ */
  document.getElementById('prescription-form').addEventListener('submit', function () {
    var btn = this.querySelector('button[type="submit"]');
    if (btn) { btn.disabled = true; btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Saving…'; }
  });

})();
