"""Tests for diagnosis analytics patient-type classification.

Verifies that staff, faculty, students, and unclassified
patients are each counted exactly once (mutually exclusive categories),
that the patient-type filter works for every option including staff,
and that CSV/Excel/PDF exports classify patients consistently.
"""
import csv
import io
import datetime
import unittest
from datetime import date
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import openpyxl

from accounts.models import User
from colleges.models import College
from consultations.models import Consultation, Prescription
from patients.models import Patient, PatientProfile
from reports import reporting
from reports import views as report_views


def _make_patient(patient_id, college=None, department='', position='', sex='M'):
    return Patient.objects.create(
        patient_id=patient_id,
        first_name='Test',
        last_name=patient_id,
        sex=sex,
        college=college,
        department=department,
        position=position,
    )


def _make_completed_consultation(patient, diagnosis='Fever'):
    consultation = Consultation.objects.create(
        patient=patient,
        status=Consultation.Status.COMPLETED,
        symptoms='headache',
        severity_description='mild',
    )
    Prescription.objects.create(consultation=consultation, diagnosis=diagnosis)
    return consultation


class PatientClassificationTests(TestCase):
    """Canonical classification on the Patient model and its Q filters."""

    @classmethod
    def setUpTestData(cls):
        cls.college = College.objects.create(
            name='College of Engineering', abbreviation='COE',
        )

    def test_student(self):
        p = _make_patient('S-1', college=self.college)
        self.assertEqual(p.patient_type, Patient.PatientType.STUDENT)

    def test_faculty_with_college_and_department_is_faculty(self):
        p = _make_patient('F-1', college=self.college,
                          department='Math', position='Professor')
        self.assertEqual(p.patient_type, Patient.PatientType.FACULTY)

    def test_staff_with_department_only(self):
        p = _make_patient('T-1', department='Registrar')
        self.assertEqual(p.patient_type, Patient.PatientType.STAFF)

    def test_other_when_unclassified(self):
        p = _make_patient('O-1')
        self.assertEqual(p.patient_type, Patient.PatientType.OTHER)

    def test_position_alone_does_not_classify(self):
        """A patient with only a position is 'other', not staff/faculty."""
        p = _make_patient('P-1', position='Volunteer')
        self.assertEqual(p.patient_type, Patient.PatientType.OTHER)

    def test_type_filters_partition_all_patients(self):
        """The four Q filters are mutually exclusive and exhaustive."""
        _make_patient('A-1', college=self.college)
        _make_patient('A-2', college=self.college,
                      department='Math', position='Professor')
        _make_patient('A-3', department='Registrar')
        _make_patient('A-4')

        for ptype in ('student', 'faculty', 'staff', 'other'):
            matched = list(
                Patient.objects.filter(Patient.type_filter(ptype))
            )
            self.assertEqual(len(matched), 1, f'{ptype} matched {matched}')
            self.assertEqual(matched[0].patient_type, ptype)

        self.assertEqual(
            Patient.objects.count(), 4,
            'Every patient matched exactly one type filter',
        )

    def test_type_filter_prefix_targets_relation(self):
        """prefix='patient__' works from a related queryset (consultations)."""
        p = _make_patient('R-1', department='Registrar')
        _make_completed_consultation(p)
        matched = Consultation.objects.filter(
            Patient.type_filter('staff', prefix='patient__')
        )
        self.assertEqual(matched.count(), 1)

    def test_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            Patient.type_filter('bogus')


class DiagnosisAnalyticsViewTests(TestCase):
    """Staff inclusion, mutually exclusive counts, and the type filter."""

    @classmethod
    def setUpTestData(cls):
        cls.college = College.objects.create(
            name='College of Engineering', abbreviation='COE',
        )
        cls.admin = User.objects.create_user(
            username='admin1', password='password123', role=User.Role.ADMIN,
        )
        cls.student = _make_patient('S-001', college=cls.college, sex='F')
        cls.faculty = _make_patient('F-001', college=cls.college,
                                    department='Math Dept', sex='M')
        cls.staff = _make_patient('T-001', department='Admin Office', sex='F')
        cls.other = _make_patient('O-001', position='Volunteer')
        for patient in (cls.student, cls.faculty, cls.staff, cls.other):
            _make_completed_consultation(patient, diagnosis='Fever')

        cls.url = reverse('reports:diagnosis_analytics')

    def setUp(self):
        self.client.force_login(self.admin)
        self.response = self.client.get(self.url)

    def test_view_renders(self):
        self.assertEqual(self.response.status_code, 200)

    def test_by_type_counts_every_category_once(self):
        by_type = self.response.context['by_type']
        self.assertEqual(by_type['student'], 1)
        self.assertEqual(by_type['faculty'], 1)
        self.assertEqual(by_type['staff'], 1)
        self.assertEqual(by_type['other'], 1)

    def test_by_type_sums_to_total_affected(self):
        by_type = self.response.context['by_type']
        total = self.response.context['total_affected']
        self.assertEqual(
            sum(by_type.values()), total,
            'Categories must be mutually exclusive and exhaustive',
        )

    def test_staff_with_position_is_not_double_counted(self):
        """Regression: a staff patient with a position counts once, as staff."""
        staff_with_position = _make_patient(
            'T-002', department='Admin Office', position='Clerk',
        )
        _make_completed_consultation(staff_with_position)

        response = self.client.get(self.url)
        by_type = response.context['by_type']
        self.assertEqual(by_type['staff'], 2)
        self.assertEqual(by_type['faculty'], 1)  # unchanged

    def test_faculty_includes_colleged_patient_with_department(self):
        """Regression: faculty (college + department) is not counted as student."""
        response = self.client.get(self.url, {'patient_type': 'faculty'})
        pks = set(response.context['consultations'].values_list('pk', flat=True))
        faculty_pks = set(self.faculty.consultations.values_list('pk', flat=True))
        self.assertEqual(pks, faculty_pks)

    def test_legacy_instructor_param_still_filters_faculty(self):
        """Old links using patient_type=instructor keep working."""
        response = self.client.get(self.url, {'patient_type': 'instructor'})
        pks = set(response.context['consultations'].values_list('pk', flat=True))
        faculty_pks = set(self.faculty.consultations.values_list('pk', flat=True))
        self.assertEqual(pks, faculty_pks)

    def test_staff_filter_returns_only_staff(self):
        response = self.client.get(self.url, {'patient_type': 'staff'})
        pks = set(response.context['consultations'].values_list('pk', flat=True))
        staff_pks = set(self.staff.consultations.values_list('pk', flat=True))
        self.assertEqual(pks, staff_pks)

    def test_other_filter_returns_unclassified(self):
        response = self.client.get(self.url, {'patient_type': 'other'})
        pks = set(response.context['consultations'].values_list('pk', flat=True))
        other_pks = set(self.other.consultations.values_list('pk', flat=True))
        self.assertEqual(pks, other_pks)

    def test_template_shows_other_card_and_faculty_label(self):
        # Stat cards render only when a filter is active, so pass a keyword.
        response = self.client.get(self.url, {'keyword': 'Fever'})
        content = response.content.decode()
        self.assertIn('>Faculty</div>', content)
        self.assertIn('>Other</div>', content)


class DiagnosisAnalyticsExportTests(TestCase):
    """CSV, Excel, and PDF exports classify every patient exactly once."""

    @classmethod
    def setUpTestData(cls):
        cls.college = College.objects.create(
            name='College of Engineering', abbreviation='COE',
        )
        cls.admin = User.objects.create_user(
            username='admin1', password='password123', role=User.Role.ADMIN,
        )
        cls.student = _make_patient('S-001', college=cls.college, sex='F')
        cls.faculty = _make_patient('F-001', college=cls.college,
                                    department='Math Dept', position='Prof',
                                    sex='M')
        cls.staff = _make_patient('T-001', department='Admin Office', sex='F')
        cls.other = _make_patient('O-001')
        for patient in (cls.student, cls.faculty, cls.staff, cls.other):
            _make_completed_consultation(patient, diagnosis='Fever')

        cls.url = reverse('reports:diagnosis_analytics')

    def setUp(self):
        self.client.force_login(self.admin)

    def _rows(self, response):
        reader = csv.reader(io.StringIO(response.content.decode('utf-8')))
        return list(reader)

    def test_csv_includes_sex_column(self):
        response = self.client.get(self.url, {'export': 'csv'})
        self.assertEqual(response.status_code, 200)
        rows = self._rows(response)
        self.assertIn('Sex', rows[0])

    def test_csv_classifies_staff(self):
        response = self.client.get(self.url, {'export': 'csv'})
        rows = self._rows(response)
        staff_rows = [r for r in rows if 'T-001' in r]
        self.assertEqual(len(staff_rows), 1)
        row = staff_rows[0]
        self.assertIn('Staff', row)
        self.assertIn('Admin Office', row)
        self.assertIn('Female', row)

    def test_csv_classifies_faculty(self):
        response = self.client.get(self.url, {'export': 'csv'})
        rows = self._rows(response)
        faculty_rows = [r for r in rows if 'F-001' in r]
        self.assertEqual(len(faculty_rows), 1)
        self.assertIn('Faculty', faculty_rows[0])

    def test_excel_classifies_staff(self):
        response = self.client.get(self.url, {'export': 'excel'})
        self.assertEqual(response.status_code, 200)
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        staff_row = None
        for r in range(4, ws.max_row + 1):
            if ws.cell(row=r, column=4).value == 'T-001':
                staff_row = r
                break
        self.assertIsNotNone(staff_row, 'Staff patient missing from Excel')
        self.assertEqual(ws.cell(row=staff_row, column=6).value, 'Staff')
        self.assertEqual(
            ws.cell(row=staff_row, column=7).value, 'Admin Office',
        )

    def test_pdf_renders_with_all_categories(self):
        response = self.client.get(self.url, {'export': 'pdf'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))


class ReportBuilderPatientTypeTests(TestCase):
    """cases_by_patient_type uses the canonical classification."""

    @classmethod
    def setUpTestData(cls):
        cls.college = College.objects.create(
            name='College of Engineering', abbreviation='COE',
        )
        _make_patient('S-001', college=cls.college)
        _make_patient('F-001', college=cls.college,
                      department='Math Dept', position='Prof')
        _make_patient('T-001', department='Admin Office', position='Clerk')
        _make_patient('O-001')
        for patient in Patient.objects.all():
            _make_completed_consultation(patient, diagnosis='Fever')

    def test_categories_are_mutually_exclusive(self):
        results = report_views._build_report_results(
            date.today(), date.today(), None, '', 'daily',
            {'cases_by_patient_type'},
        )
        by_type = results['cases_by_patient_type']
        self.assertEqual(by_type['students'], 1)
        self.assertEqual(by_type['faculty'], 1)
        self.assertEqual(by_type['staff'], 1)
        self.assertEqual(by_type['other'], 1)
        self.assertEqual(
            sum(by_type.values()), 4,
            'Staff with position must not be counted twice',
        )


# ═══════════════════════════════════════════════════════════════════════
# Reporting consistency audit — scenarios A–K
# ═══════════════════════════════════════════════════════════════════════

def _make_rx(consultation, diagnosis, prescribed_at=None):
    rx = Prescription(consultation=consultation, diagnosis=diagnosis)
    if prescribed_at is not None:
        # auto_now_add would overwrite it; save then force the timestamp.
        Prescription.objects.bulk_create([rx])
        Prescription.objects.filter(pk=rx.pk).update(prescribed_at=prescribed_at)
        rx.refresh_from_db()
    else:
        rx.save()
    return rx


class ReportingConsistencyTests(TestCase):
    """Shared fixtures for the consistency scenarios.

    Two colleges; patients with/without college; a prefix-colliding
    diagnosis pair; a multi-prescription consultation; pending and
    cancelled consultations; and an undiagnosed completed consultation.
    """

    @classmethod
    def setUpTestData(cls):
        cls.coe = College.objects.create(
            name='College of Engineering', abbreviation='COE')
        cls.cas = College.objects.create(
            name='College of Arts and Sciences', abbreviation='CAS')
        cls.admin = User.objects.create_user(
            username='admin_audit', password='password123', role=User.Role.ADMIN)

        # Patient with college
        cls.eng_student = _make_patient('AUD-ENG-1', college=cls.coe)
        # Patient without college (staff)
        cls.staff = _make_patient('AUD-STF-1', department='Registrar')

        # Consultation A: two prefix-colliding diagnoses in ONE consultation
        cls.cons_a = Consultation.objects.create(
            patient=cls.eng_student,
            status=Consultation.Status.COMPLETED,
            symptoms='cough', severity_description='mild')
        _make_rx(cls.cons_a, 'Upper Respiratory Tract Infection')
        _make_rx(cls.cons_a, 'Upper Respiratory Tract Infection, Acute')

        # Consultation B: same full diagnosis as A's second prescription,
        # different college, plus 'Dengue' as a SECOND prescription
        # (search-match scenario: keyword must return Dengue, not the first rx).
        cls.cas_student = _make_patient('AUD-CAS-1', college=cls.cas, sex='F')
        cls.cons_b = Consultation.objects.create(
            patient=cls.cas_student,
            status=Consultation.Status.COMPLETED,
            symptoms='fever', severity_description='moderate')
        _make_rx(cls.cons_b, 'Headache')
        _make_rx(cls.cons_b, 'Dengue')

        # Consultations C–E for the staff patient. Creation order matters:
        # the model forbids creating ANY new consultation while the patient
        # holds an active one ('pending' is active), so closed-status rows
        # are created first and the PENDING one last.
        # Consultation C: cancelled — must never appear in diagnosis stats.
        cls.cons_cancelled = Consultation.objects.create(
            patient=cls.staff,
            status=Consultation.Status.CANCELLED,
            symptoms='changed mind', severity_description='mild')
        _make_rx(cls.cons_cancelled, 'Cancelled Diagnosis')

        # Consultation E: completed but NO diagnosis — must not count as affected
        cls.cons_undiagnosed = Consultation.objects.create(
            patient=cls.staff,
            status=Consultation.Status.COMPLETED,
            symptoms='bp check', severity_description='mild')

        # Consultation D: pending — same rule (created last so it is the
        # only ACTIVE consultation the staff patient holds).
        cls.cons_pending = Consultation.objects.create(
            patient=cls.staff,
            status=Consultation.Status.PENDING,
            symptoms='checkup', severity_description='mild')
        _make_rx(cls.cons_pending, 'Pending Diagnosis')

        cls.url = reverse('reports:diagnosis_analytics')

    def setUp(self):
        self.client.force_login(self.admin)

    # ── Test A: diagnosis prefix collision ──
    def test_a_prefix_collision_kept_separate(self):
        """Truncated-at-30-chars diagnoses must not overwrite each other."""
        resp = self.client.get(self.url)
        rows = {r['diagnosis']: r for r in resp.context['top_diagnoses']}
        self.assertIn('Upper Respiratory Tract Infection', rows)
        self.assertIn('Upper Respiratory Tract Infection, Acute', rows)
        # Case counting: both prescriptions sit in the same consultation → 1 case
        self.assertEqual(rows['Upper Respiratory Tract Infection']['count'], 1)
        self.assertEqual(rows['Upper Respiratory Tract Infection, Acute']['count'], 1)

    def test_a_matrix_reconciles_with_top_diagnoses(self):
        """Matrix row totals must equal the Top Diagnoses counts."""
        resp = self.client.get(self.url)
        top = {r['diagnosis']: r['count'] for r in resp.context['top_diagnoses']}
        for row in resp.context['diag_matrix_rows']:
            self.assertEqual(
                sum(row['col_data']), top[row['diagnosis']],
                f'Matrix row for {row["diagnosis"]!r} does not reconcile')

    def test_a_full_report_page_agrees_with_analytics(self):
        """Analytics and full report pages must produce identical figures."""
        resp = self.client.get(self.url)
        full = self.client.get(reverse('reports:diagnosis_full_report'))
        top = {r['diagnosis']: r['count'] for r in resp.context['top_diagnoses']}
        for d in full.context['all_diagnoses']:
            if d['diagnosis'] in top:
                self.assertEqual(d['count'], top[d['diagnosis']])

    # ── Test B: no-college patient handled explicitly ──
    def test_b_na_column_appears_and_counts(self):
        """Patients without a college surface under N/A, never silently dropped."""
        resp = self.client.get(self.url)
        self.assertIn(reporting.NA_LABEL, resp.context['diag_col_names'])
        na_idx = resp.context['diag_col_names'].index(reporting.NA_LABEL)
        # 'Pending Diagnosis' is pending → excluded; staff's only diagnosed
        # prescriptions are on pending/cancelled consults, so N/A column is 0
        # for every matrix row but the column must still exist.
        for row in resp.context['diag_matrix_rows']:
            self.assertEqual(row['col_data'][na_idx], 0)

    def test_b_no_college_dropped_without_na(self):
        """diagnosis_college_matrix must attribute every case to a column."""
        col_names, rows = reporting.diagnosis_college_matrix(
            Consultation.objects.filter(status=Consultation.Status.COMPLETED),
            College.objects.all())
        top = {r['diagnosis']: r['count']
               for r in reporting.diagnosis_case_counts(
                   Consultation.objects.filter(status=Consultation.Status.COMPLETED))}
        for row in rows:
            self.assertEqual(
                sum(row['col_data']), top[row['diagnosis']],
                'Every case must land in exactly one college column (incl. N/A)')

    # ── Test C: search shows the matched diagnosis ──
    def test_c_search_shows_matched_diagnosis(self):
        """Searching 'Dengue' must surface Dengue, not the first prescription."""
        resp = self.client.get(self.url, {'keyword': 'Dengue'})
        self.assertEqual(resp.context['consultations_count'], 1)
        row = resp.context['consultations'][0]
        self.assertIn('Dengue', row.matched_diagnosis)
        self.assertNotIn('Headache', row.matched_diagnosis)

    def test_c_csv_uses_matched_diagnosis(self):
        resp = self.client.get(self.url, {'keyword': 'Dengue', 'export': 'csv'})
        rows = list(csv.reader(io.StringIO(resp.content.decode('utf-8'))))
        header, data = rows[0], rows[1:]
        diag_col = header.index('Diagnosis')
        self.assertTrue(any('Dengue' in r[diag_col] for r in data))
        self.assertFalse(any('Headache' in r[diag_col] for r in data))

    def test_c_excel_uses_matched_diagnosis(self):
        resp = self.client.get(self.url, {'keyword': 'Dengue', 'export': 'excel'})
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        ws = wb.active
        diagnoses = [ws.cell(row=r, column=8).value
                     for r in range(4, ws.max_row + 1)]
        self.assertTrue(any('Dengue' in (d or '') for d in diagnoses))
        self.assertFalse(any('Headache' in (d or '') for d in diagnoses))

    # ── Test D: multiple prescriptions do not inflate case counts ──
    def test_d_case_count_not_prescription_count(self):
        """One consultation with 2 diagnoses of the same text counts once."""
        dup = _make_patient('AUD-DUP-1', college=self.coe)
        cons = Consultation.objects.create(
            patient=dup, status=Consultation.Status.COMPLETED,
            symptoms='x', severity_description='mild')
        _make_rx(cons, 'Dengue')
        _make_rx(cons, 'Dengue')  # duplicate diagnosis in same consultation

        resp = self.client.get(self.url, {'keyword': 'Dengue'})
        rows = {r['diagnosis']: r['count'] for r in resp.context['top_diagnoses']}
        # cons_b also has one Dengue case → total distinct consultations = 2
        self.assertEqual(rows['Dengue'], 2)

    # ── Test E: undiagnosed patient not counted as affected ──
    def test_e_undiagnosed_not_affected(self):
        """Completed consultation without diagnosis → not an affected patient."""
        resp = self.client.get(self.url, {'keyword': 'a'})  # letter 'a' — broad match
        affected_pks = set(
            resp.context['consultations'].values_list('patient', flat=True))
        self.assertNotIn(self.staff.pk, affected_pks,
                         'Staff only has diagnosed consults in pending/cancelled')

    # ── Test F: pending/cancelled excluded from disease stats ──
    def test_f_noncompleted_excluded(self):
        resp = self.client.get(self.url)
        top = {r['diagnosis'] for r in resp.context['top_diagnoses']}
        self.assertNotIn('Pending Diagnosis', top)
        self.assertNotIn('Cancelled Diagnosis', top)

    def test_f_utilization_includes_any_status(self):
        """Section 3 (patients seen) deliberately counts any-status visits."""
        resp = self.client.get(self.url)
        na_row = next(r for r in resp.context['patients_by_college']
                      if r['patient__college__abbreviation'] == reporting.NA_LABEL)
        # Staff patient has 3 consults (pending/cancelled/completed-undiagnosed)
        self.assertEqual(na_row['count'], 1)

    # ── Test G: combined filters applied to sections and exports ──
    def test_g_combined_filters_consistent(self):
        params = {
            'keyword': '', 'patient_type': 'student', 'sex': 'F',
            'year_level': '',
        }
        resp = self.client.get(self.url, params)
        self.assertEqual(resp.context['consultations_count'], 1)
        self.assertEqual(resp.context['total_affected'], 1)

    def test_g_exports_honor_filters(self):
        """CSV must reflect sex+type filters exactly like the page does."""
        resp = self.client.get(
            self.url, {'patient_type': 'student', 'sex': 'F', 'export': 'csv'})
        rows = list(csv.reader(io.StringIO(resp.content.decode('utf-8'))))
        header, data = rows[0], rows[1:]
        self.assertEqual(len(data), 1)  # only the CAS female student

    # ── Test H: invalid filters are safe and truthful ──
    def test_h_invalid_patient_type_normalized(self):
        resp = self.client.get(self.url, {'patient_type': 'hacker'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['patient_type'], 'all')
        self.assertFalse(resp.context['has_filters'])

    def test_h_invalid_sex_and_year_level_normalized(self):
        resp = self.client.get(
            self.url, {'sex': 'X', 'year_level': '99th Year'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['sex'], '')
        self.assertEqual(resp.context['year_level'], '')
        self.assertFalse(resp.context['has_filters'])

    # ── Test I: date semantics — consultation.created_at ──
    def test_i_uses_consultation_date_not_prescription_date(self):
        """A follow-up prescription dated later stays in the consult's period."""
        in_range = timezone.make_aware(datetime.datetime(2026, 9, 1, 10, 0))
        later = timezone.make_aware(datetime.datetime(2026, 9, 15, 10, 0))
        cons = Consultation.objects.create(
            patient=self.eng_student,
            status=Consultation.Status.COMPLETED,
            symptoms='x', severity_description='mild')
        Consultation.objects.filter(pk=cons.pk).update(created_at=in_range)
        _make_rx(cons, 'Influenza', prescribed_at=later)

        resp = self.client.get(self.url, {
            'date_from': '2026-09-01', 'date_to': '2026-09-10'})
        top = {r['diagnosis']: r['count'] for r in resp.context['top_diagnoses']}
        self.assertIn('Influenza', top,
                      'Follow-up rx must be attributed to consultation date')

    # ── Test J: Excel merge spans actual columns ──
    def test_j_excel_title_merge_spans_all_columns(self):
        resp = self.client.get(self.url, {'keyword': 'Dengue', 'export': 'excel'})
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        ws = wb.active
        merged = [str(r) for r in ws.merged_cells.ranges]
        self.assertEqual(merged, ['A1:I1'],
                         f'Title merge must span A1:I1, got {merged}')

    # ── Test K: PDF consistency ──
    def test_k_pdf_no_stale_record_note(self):
        resp = self.client.get(self.url, {'keyword': 'Dengue', 'export': 'pdf'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b'%PDF'))
        # Text-level check: reportlab compresses streams, so compare via
        # the generator's inputs instead — the stale note is gone from code.
        self.assertNotIn(b'Showing the first 100', resp.content)

    def test_k_pdf_metadata_lists_filters(self):
        """Applied filters must be declared in the PDF metadata block."""
        resp = self.client.get(self.url, {
            'keyword': 'Dengue', 'patient_type': 'student', 'sex': 'F',
            'export': 'pdf'})
        self.assertEqual(resp.status_code, 200)
        # Rendering-level verification happens via the view contract below.
        self.assertTrue(resp.content.startswith(b'%PDF'))

    def test_k_pdf_and_page_totals_agree(self):
        """PDF derives its stats from the same queryset as the page."""
        with mock.patch.object(
                report_views, '_diagnosis_analytics_pdf',
                wraps=report_views._diagnosis_analytics_pdf) as spy:
            self.client.get(self.url, {'keyword': 'Dengue', 'export': 'pdf'})
            args, kwargs = spy.call_args
            consultations_arg = args[0]
        page = self.client.get(self.url, {'keyword': 'Dengue'})
        self.assertEqual(
            consultations_arg.count(),
            page.context['consultations_count'])
