"""Tests for diagnosis analytics patient-type classification.

Verifies that staff, faculty, students, and unclassified
patients are each counted exactly once (mutually exclusive categories),
that the patient-type filter works for every option including staff,
and that CSV/Excel/PDF exports classify patients consistently.
"""
import csv
import io
from datetime import date

from django.test import TestCase
from django.urls import reverse

import openpyxl

from accounts.models import User
from colleges.models import College
from consultations.models import Consultation, Prescription
from patients.models import Patient
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
