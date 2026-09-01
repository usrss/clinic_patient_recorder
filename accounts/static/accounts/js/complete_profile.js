/* ═══════════════════════════════════════════
   Complete Profile — 2-step profile wizard
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  var formEl = document.getElementById('profile-form');
  var COURSES_URL = formEl ? formEl.getAttribute('data-courses-url') : '';

  // ── State ──────────────────────────────────────────────────────────
  let currentStep = parseInt(document.getElementById('current_step').value) || 1;

  // ── Step navigation ────────────────────────────────────────────────
  function showStep(n) {
    document.getElementById('current_step').value = n;
    document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('step-' + n).classList.add('active');

    for (let i = 1; i <= 2; i++) {
      const prog = document.getElementById('prog-' + i);
      prog.classList.remove('active', 'done');
      if (i < n) prog.classList.add('done');
      else if (i === n) prog.classList.add('active');
    }
    currentStep = n;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goNext(step) {
    if (step === 1) {
      var emailEl = document.getElementById('id_email');
      var emailError = document.getElementById('emailError');

      // If email has a visible server-side error (from a previous form submission), block
      if (emailError.classList.contains('visible')) {
        emailEl.classList.add('email-taken');
        emailEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        emailEl.focus();
        return;
      }

      // If the server previously flagged this email as taken (from a re-rendered form), block
      if (emailEl.getAttribute('data-server-error') === 'true') {
        emailEl.classList.add('email-taken');
        emailEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        emailEl.focus();
        return;
      }

      let valid = true;

      // Validate role is selected
      const roleEl = document.getElementById('id_role');
      if (roleEl && !roleEl.value) {
        roleEl.classList.add('error');
        valid = false;
      } else if (roleEl) {
        roleEl.classList.remove('error');
      }

      // Role-dependent validation
      const role = roleEl ? roleEl.value : '';
      if (role === 'student') {
        const collegeEl = document.getElementById('id_college');
        if (collegeEl && !collegeEl.value) {
          collegeEl.classList.add('error');
          valid = false;
        } else if (collegeEl) {
          collegeEl.classList.remove('error');
        }
        const courseEl = document.getElementById('id_course');
        if (courseEl && courseEl.offsetParent !== null && !courseEl.value) {
          courseEl.classList.add('error');
          valid = false;
        } else if (courseEl) {
          courseEl.classList.remove('error');
        }
        const yearEl = document.getElementById('id_year_level');
        if (yearEl && !yearEl.value) {
          yearEl.classList.add('error');
          valid = false;
        } else if (yearEl) {
          yearEl.classList.remove('error');
        }
      } else if (role === 'faculty') {
        // Faculty needs both college and department
        const collegeEl = document.getElementById('id_college');
        if (collegeEl && !collegeEl.value) {
          collegeEl.classList.add('error');
          valid = false;
        } else if (collegeEl) {
          collegeEl.classList.remove('error');
        }
        const deptEl = document.getElementById('id_department');
        if (deptEl && !deptEl.value.trim()) {
          deptEl.classList.add('error');
          valid = false;
        } else if (deptEl) {
          deptEl.classList.remove('error');
        }
      } else if (role === 'staff') {
        // Staff only needs department
        const deptEl = document.getElementById('id_department');
        if (deptEl && !deptEl.value.trim()) {
          deptEl.classList.add('error');
          valid = false;
        } else if (deptEl) {
          deptEl.classList.remove('error');
        }
      }

      if (valid) showStep(2);
    }
  }

  // ── Course stash for restoring on goBack ──
  let savedCourseIdCP = '';

  function goBack(step) {
    if (step === 2) {
      // Stash course value before switching steps (will be restored when going forward again)
      const courseEl = document.getElementById('id_course');
      if (courseEl) savedCourseIdCP = courseEl.value;
      showStep(1);
    }
  }

  // ── Role → show/hide college vs department ────────────────────────
  function updateRoleFields() {
    const role = document.getElementById('id_role').value;
    const isStudent = role === 'student';
    const isFaculty = role === 'faculty';
    const showCollege = isStudent || isFaculty;
    document.getElementById('field-college').style.display    = showCollege ? '' : 'none';
    document.getElementById('field-year').style.display       = isStudent ? '' : 'none';
    document.getElementById('field-department').style.display = isStudent ? 'none' : '';
    document.getElementById('field-position').style.display   = isStudent ? 'none' : '';
    const fieldCourse = document.getElementById('field-course');
    if (fieldCourse) fieldCourse.style.display = isStudent ? '' : 'none';
    if (showCollege) loadCourses();
  }

  function loadCourses() {
    const collegeId = document.getElementById('id_college').value;
    const courseSelect = document.getElementById('id_course');
    const fieldCourse = document.getElementById('field-course');
    if (!courseSelect) return Promise.resolve();
    courseSelect.innerHTML = '<option value="">Select Course</option>';
    var role = document.getElementById('id_role').value;
    if (!collegeId) { if (fieldCourse) fieldCourse.style.display = 'none'; return Promise.resolve(); }
    if (fieldCourse) fieldCourse.style.display = (role === 'student' && collegeId) ? '' : 'none';
    return fetch(COURSES_URL + '?college_id=' + collegeId)
      .then(r => r.json())
      .then(data => {
        (data.courses || []).forEach(c => {
          const opt = document.createElement('option');
          opt.value = c.id; opt.textContent = c.name;
          courseSelect.appendChild(opt);
        });
        // Restore stashed course value if it exists in the new list
        if (savedCourseIdCP) {
          for (var i = 0; i < courseSelect.options.length; i++) {
            if (courseSelect.options[i].value === savedCourseIdCP) {
              courseSelect.value = savedCourseIdCP;
              savedCourseIdCP = ''; // consumed
              break;
            }
          }
        }
      }).catch(() => {});
  }

  // ── Client-side file validation for profile picture ──
  document.addEventListener('DOMContentLoaded', function () {
    var picInput = document.getElementById('id_profile_picture');
    if (picInput) {
      picInput.addEventListener('change', function (e) {
        var file = e.target.files[0];
        if (!file) return;
        var maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
          alert('File size (' + Math.round(file.size / 1024) + ' KB) exceeds the maximum allowed size of 5 MB.');
          picInput.value = '';
          return;
        }
        var allowed = ['image/jpeg', 'image/png', 'image/webp'];
        if (allowed.indexOf(file.type) === -1) {
          alert('Unsupported file type. Allowed types: JPG, PNG, WebP.');
          picInput.value = '';
        }
      });
    }
  });

  // ── Clear server-side email error when user edits the field ──
  document.addEventListener('DOMContentLoaded', function () {
    var emailEl = document.getElementById('id_email');
    if (emailEl) {
      emailEl.addEventListener('input', function () {
        this.removeAttribute('data-server-error');
        this.classList.remove('email-taken');
        document.getElementById('emailError').classList.remove('visible');
      });
    }
  });

  // ── Form-level Enter key handling ──
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('profile-form');
    if (form) {
      form.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
          e.preventDefault();
          const step = parseInt(document.getElementById('current_step').value) || 1;
          if (step === 1) {
            goNext(1);
          } else {
            // Step 2 — submit the form
            form.requestSubmit();
          }
        }
      });
    }
  });

  // ── Loading state on form submit (step 2) ──
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('profile-form');
    if (form) {
      form.addEventListener('submit', function () {
        const btn = document.getElementById('completeProfileBtn');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Saving...';
        }
      });
    }
  });

  // ── Event bindings (previously inline onclick/onchange handlers) ──
  document.addEventListener('DOMContentLoaded', function () {
    // Step navigation buttons
    document.querySelectorAll('[data-step-next]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        goNext(parseInt(btn.getAttribute('data-step-next'), 10));
      });
    });
    document.querySelectorAll('[data-step-back]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        goBack(parseInt(btn.getAttribute('data-step-back'), 10));
      });
    });

    // Role select → show/hide role-dependent fields
    var roleEl = document.getElementById('id_role');
    if (roleEl) roleEl.addEventListener('change', updateRoleFields);

    // College select → load courses
    var collegeEl = document.getElementById('id_college');
    if (collegeEl) collegeEl.addEventListener('change', loadCourses);
  });

  // ── Restore step after failed POST ─────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    const stepVal = parseInt(document.getElementById('current_step').value);
    if (stepVal > 1) showStep(stepVal);
    updateRoleFields();

    // Pre-load courses if college is already selected (e.g. on form re-render)
    const collegeEl = document.getElementById('id_college');
    const courseEl = document.getElementById('id_course');
    if (collegeEl && collegeEl.value && courseEl) {
      loadCourses().then(() => {
        const savedCourse = courseEl.getAttribute('data-saved-course') || '';
        if (savedCourse) courseEl.value = savedCourse;
      });
    }

    // ── Stash course on college change so goBack retains it ──
    if (collegeEl) {
      collegeEl.addEventListener('change', function () {
        // Clear stash so a new college load doesn't restore from a previous college
        savedCourseIdCP = '';
        // Current course value is stashed before loadCourses clears it
        if (courseEl) savedCourseIdCP = courseEl.value;
      });
    }
  });
})();
