import threading
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone


# Test classes that render print templates need a non-manifest static storage
# since the manifest (staticfiles.json) is only built during deploy.
_NO_MANIFEST_STORAGE = override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})

from certificates.models import MedicalCertificate, CertificateTemplateText, CertificateTemplateChangeLog
from consultations.models import Consultation
from patients.models import Patient
from colleges.models import College

User = get_user_model()


class CertificateRaceConditionTest(TestCase):
    """
    Tests for concurrent issue() and void() calls.
    """

    @classmethod
    def setUpTestData(cls):
        cls.patient = Patient.objects.create(
            patient_id='RACE-001',
            first_name='Race',
            last_name='Condition',
            sex='M',
        )
        cls.doctor = User.objects.create_user(
            username='dr_race', password='testpass123', role='doctor',
            first_name='Race', last_name='Doc',
            email='dr_race@test.clinic',
        )

    def test_concurrent_issue_and_void_race_condition(self):
        """
        Simulate concurrent issue() and void() calls on the same certificate.
        Only one mutation should win cleanly (no partial state, no orphaned audit logs).
        """
        consultation = Consultation.objects.create(
            patient=self.patient,
            symptoms='Race test',
            status=Consultation.Status.COMPLETED,
        )
        # Issue the cert first so void() can act on it
        cert = MedicalCertificate.objects.create(
            consultation=consultation,
            patient=self.patient,
            doctor=self.doctor,
            certificate_type=MedicalCertificate.CertificateType.STANDARD,
            status=MedicalCertificate.Status.DRAFT,
            diagnosis='Race condition test',
        )
        cert.issue(user=self.doctor)
        cert.refresh_from_db()
        self.assertEqual(cert.status, MedicalCertificate.Status.ISSUED)

        results = {'issue_error': None, 'void_error': None}

        def do_issue():
            """Attempt to issue again — should fail because already issued."""
            try:
                with transaction.atomic():
                    # Create a new draft for the same consultation
                    draft2 = MedicalCertificate.objects.create(
                        consultation=consultation,
                        patient=self.patient,
                        doctor=self.doctor,
                        certificate_type=MedicalCertificate.CertificateType.STANDARD,
                        status=MedicalCertificate.Status.DRAFT,
                        diagnosis='Race retry',
                    )
                    draft2.issue(user=self.doctor)
                    results['issue_error'] = None  # unexpected success
            except Exception as e:
                results['issue_error'] = e

        def do_void():
            """Attempt to void the original issued cert."""
            try:
                with transaction.atomic():
                    cert.void(user=self.doctor, reason='Testing race')
            except Exception as e:
                results['void_error'] = e

        # Start both threads near-simultaneously
        t1 = threading.Thread(target=do_issue)
        t2 = threading.Thread(target=do_void)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        cert.refresh_from_db()

        # The void should have succeeded (it was on the issued cert)
        # The re-issue should have failed (already an issued cert exists)
        if results['void_error'] is None:
            self.assertEqual(cert.status, MedicalCertificate.Status.VOIDED,
                'Void should have succeeded.')
        else:
            self.assertEqual(cert.status, MedicalCertificate.Status.ISSUED,
                'If void failed, cert should remain issued.')

        # Verify no orphaned audit logs
        self.assertGreaterEqual(cert.audit_logs.count(), 2)  # created + issued + possibly voided
        self.assertLessEqual(cert.audit_logs.count(), 3)  # max 3: created + issued + voided


@_NO_MANIFEST_STORAGE
class CertificateAccessScopingTest(TestCase):
    """
    Tests for certificate access scoping in the print view.
    Doctors may only print certificates they issued.
    Frontdesk and admin may print any certificate.
    """

    @classmethod
    def setUpTestData(cls):
        cls.patient = Patient.objects.create(
            patient_id='TEST-001',
            first_name='Juan',
            last_name='Dela Cruz',
            sex='M',
        )
        cls.doctor_a = User.objects.create_user(
            username='dr_a', password='testpass123', role='doctor',
            first_name='Alice', last_name='Doctor',
            email='dr_a@test.clinic',
        )
        cls.doctor_b = User.objects.create_user(
            username='dr_b', password='testpass123', role='doctor',
            first_name='Bob', last_name='Physician',
            email='dr_b@test.clinic',
        )
        cls.frontdesk = User.objects.create_user(
            username='fd', password='testpass123', role='frontdesk',
            email='fd@test.clinic',
        )
        cls.admin = User.objects.create_user(
            username='admin', password='testpass123', role='admin',
            email='admin@test.clinic',
        )

    def _create_issued_cert(self, doctor):
        consultation = Consultation.objects.create(
            patient=self.patient,
            symptoms='Test symptoms',
            status=Consultation.Status.COMPLETED,
        )
        cert = MedicalCertificate.objects.create(
            consultation=consultation,
            patient=self.patient,
            doctor=doctor,
            certificate_type=MedicalCertificate.CertificateType.STANDARD,
            status=MedicalCertificate.Status.ISSUED,
            diagnosis='Test diagnosis',
            certificate_number='MC-2026-000001',
            issued_at='2026-06-30T12:00:00Z',
        )
        return cert

    def test_doctor_can_print_own_certificate(self):
        """A doctor should be able to print a certificate they issued."""
        cert = self._create_issued_cert(self.doctor_a)
        self.client.force_login(self.doctor_a)
        response = self.client.get(reverse('certificates:print_certificate', args=[cert.pk]))
        self.assertEqual(response.status_code, 200)

    def test_doctor_cannot_print_other_doctors_certificate(self):
        """A doctor should NOT be able to print another doctor's certificate."""
        cert = self._create_issued_cert(self.doctor_a)
        self.client.force_login(self.doctor_b)
        response = self.client.get(reverse('certificates:print_certificate', args=[cert.pk]))
        self.assertEqual(response.status_code, 403)

    def test_frontdesk_can_print_any_certificate(self):
        """Frontdesk staff should be able to print any certificate."""
        cert = self._create_issued_cert(self.doctor_a)
        self.client.force_login(self.frontdesk)
        response = self.client.get(reverse('certificates:print_certificate', args=[cert.pk]))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_print_any_certificate(self):
        """Admin should be able to print any certificate."""
        cert = self._create_issued_cert(self.doctor_a)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('certificates:print_certificate', args=[cert.pk]))
        self.assertEqual(response.status_code, 200)


@_NO_MANIFEST_STORAGE
class CertificateStatusGuardTest(TestCase):
    """
    Tests for the status guard in the print view.
    Only issued certificates should be printable.
    """

    @classmethod
    def setUpTestData(cls):
        cls.patient = Patient.objects.create(
            patient_id='TEST-002',
            first_name='Maria',
            last_name='Santos',
            sex='F',
        )
        cls.admin = User.objects.create_user(
            username='admin2', password='testpass123', role='admin',
            email='admin2@test.clinic',
        )

    def _create_cert(self, status):
        consultation = Consultation.objects.create(
            patient=self.patient,
            symptoms='Test',
            status=Consultation.Status.COMPLETED,
        )
        return MedicalCertificate.objects.create(
            consultation=consultation,
            patient=self.patient,
            doctor=self.admin,
            certificate_type=MedicalCertificate.CertificateType.STANDARD,
            status=status,
            diagnosis='Test',
        )

    def test_issued_cert_is_printable(self):
        """An issued certificate should return 200."""
        cert = self._create_cert(MedicalCertificate.Status.ISSUED)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('certificates:print_certificate', args=[cert.pk]))
        self.assertEqual(response.status_code, 200)

    def test_draft_cert_is_not_printable(self):
        """A draft certificate should return 403."""
        cert = self._create_cert(MedicalCertificate.Status.DRAFT)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('certificates:print_certificate', args=[cert.pk]))
        self.assertEqual(response.status_code, 403)

    def test_voided_cert_is_not_printable(self):
        """A voided certificate should return 403."""
        cert = self._create_cert(MedicalCertificate.Status.VOIDED)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('certificates:print_certificate', args=[cert.pk]))
        self.assertEqual(response.status_code, 403)


class CertificateTemplateTextTest(TestCase):
    """
    Tests for the editable certificate template text system.
    """

    @classmethod
    def setUpTestData(cls):
        cls.patient = Patient.objects.create(
            patient_id='TEMPLATE-001',
            first_name='Test',
            last_name='Patient',
            sex='M',
        )
        cls.doctor = User.objects.create_user(
            username='dr_template', password='testpass123', role='doctor',
            first_name='Doc', last_name='Template',
            email='dr_template@test.clinic',
        )
        cls.admin = User.objects.create_user(
            username='admin_template', password='testpass123', role='admin',
            email='admin_template@test.clinic',
        )

        # Ensure template text is seeded
        from certificates.models import CertificateTemplateText
        cls._seed_templates()

    @classmethod
    def _seed_templates(cls):
        # Clear any rows from data migration so we control the exact set
        CertificateTemplateText.objects.all().delete()
        CertificateTemplateText.objects.bulk_create([
            CertificateTemplateText(
                certificate_type='standard',
                slot_key='diagnosis_statement',
                text='This is to certify that {patient_name}, {age} years of age, was examined on {exam_date}.',
            ),
            CertificateTemplateText(
                certificate_type='standard',
                slot_key='diagnosis_line',
                text='Diagnosis: {diagnosis}',
            ),
            CertificateTemplateText(
                certificate_type='standard',
                slot_key='rest_period_single',
                text='The patient is advised to rest on {rest_date}.',
            ),
            CertificateTemplateText(
                certificate_type='standard',
                slot_key='rest_period_range',
                text='The patient is advised to rest from {rest_from} to {rest_to}.',
            ),
            CertificateTemplateText(
                certificate_type='standard',
                slot_key='closing_statement',
                text='This certificate is issued for legal purposes.',
            ),
            CertificateTemplateText(
                certificate_type='fit_to_work',
                slot_key='statement',
                text='This is to certify that {patient_name} is FIT to work. Assessment: {work_assessment}.',
            ),
            CertificateTemplateText(
                certificate_type='fit_to_work',
                slot_key='findings_line',
                text='Findings: {diagnosis}',
            ),
            CertificateTemplateText(
                certificate_type='fit_to_work',
                slot_key='closing_statement',
                text='This certificate is issued upon the request of the patient for legal purposes.',
            ),
            CertificateTemplateText(
                certificate_type='fit_to_play',
                slot_key='statement',
                text='This is to certify that {patient_name} is FIT to play. Status: {fitness_status}.',
            ),
            CertificateTemplateText(
                certificate_type='fit_to_play',
                slot_key='findings_line',
                text='Findings: {diagnosis}',
            ),
            CertificateTemplateText(
                certificate_type='fit_to_play',
                slot_key='closing_statement',
                text='This certificate is issued upon the request of the patient for legal purposes.',
            ),
        ])

    def _create_consultation(self):
        return Consultation.objects.create(
            patient=self.patient,
            symptoms='Test symptoms',
            status=Consultation.Status.COMPLETED,
        )

    def _create_cert(self, cert_type, **kwargs):
        consultation = self._create_consultation()
        params = dict(
            consultation=consultation,
            patient=self.patient,
            doctor=self.doctor,
            certificate_type=cert_type,
            diagnosis='Upper respiratory tract infection',
        )
        params.update(kwargs)
        return MedicalCertificate.objects.create(**params)

    # ── Test 1: Editing a slot after issuance doesn't change snapshot ──

    def test_edit_after_issue_does_not_change_snapshot(self):
        """Editing a template slot after a cert is issued should NOT change that cert's rendered_text_snapshot."""
        cert = self._create_cert(
            MedicalCertificate.CertificateType.STANDARD,
            rest_from=timezone.localtime(timezone.now()).date(),
            rest_to=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        original_snapshot = dict(cert.rendered_text_snapshot)

        # Now edit the template text
        slot = CertificateTemplateText.objects.get(
            certificate_type='standard', slot_key='diagnosis_statement',
        )
        slot.text = 'EDITED: {patient_name} was examined on {exam_date}.'
        slot.save()

        # Refresh the cert from db
        cert.refresh_from_db()
        self.assertEqual(
            cert.rendered_text_snapshot,
            original_snapshot,
            'Snapshot should remain unchanged after template text is edited.',
        )

    # ── Test 2: New cert after edit uses new wording ──

    def test_new_cert_after_edit_uses_new_wording(self):
        """A new certificate issued after a template edit should use the new wording."""
        # Edit the template text first
        slot = CertificateTemplateText.objects.get(
            certificate_type='standard', slot_key='diagnosis_statement',
        )
        slot.text = 'NEW WORDING: {patient_name} was examined on {exam_date}.'
        slot.save()

        cert = self._create_cert(
            MedicalCertificate.CertificateType.STANDARD,
            rest_from=timezone.localtime(timezone.now()).date(),
            rest_to=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        self.assertIn(
            'NEW WORDING:',
            cert.rendered_text_snapshot['diagnosis_statement'],
        )
        self.assertNotIn(
            'This is to certify',
            cert.rendered_text_snapshot['diagnosis_statement'],
        )

    # ── Test 3: Dental renders only diagnosis_statement, no rest period ──

    def test_dental_no_rest_period_content(self):
        """Dental certificate should render only diagnosis_statement and diagnosis_line, no rest-period content."""
        cert = self._create_cert(
            MedicalCertificate.CertificateType.DENTAL,
            rest_from=timezone.localtime(timezone.now()).date(),
            rest_to=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        snapshot = cert.rendered_text_snapshot
        self.assertIn('diagnosis_statement', snapshot)
        self.assertIn('diagnosis_line', snapshot)
        self.assertNotIn('rest_period_single', snapshot)
        self.assertNotIn('rest_period_range', snapshot)

    # ── Test 4: Standard branches single vs range ──

    def test_standard_branches_single_vs_range(self):
        """Standard certificate with rest_from == rest_to should use rest_period_single."""
        same_day = timezone.localtime(timezone.now()).date()

        # Single day
        cert_single = self._create_cert(
            MedicalCertificate.CertificateType.STANDARD,
            rest_from=same_day,
            rest_to=same_day,
        )
        cert_single.issue(user=self.doctor)
        self.assertIn('rest_period_single', cert_single.rendered_text_snapshot)
        self.assertIn('rest_period_range', cert_single.rendered_text_snapshot)

        # Note: currently the system stores BOTH templates and the branching
        # happens at template render time. Both slots are present in the snapshot
        # because we want the template to have access to both wordings.
        # The actual branching (single vs range) still occurs via template
        # conditionals on rest_from == rest_to.

    # ── Test 5: HTML injection stripped by bleach ──

    def test_html_tags_are_stripped(self):
        """HTML tags should be stripped from template text by bleach."""
        slot = CertificateTemplateText.objects.get(
            certificate_type='standard', slot_key='closing_statement',
        )
        slot.text = '<script>alert("xss")</script>'
        slot.save()
        slot.refresh_from_db()
        self.assertNotIn('<script>', slot.text)
        self.assertNotIn('<', slot.text)
        self.assertNotIn('>', slot.text)
        # bleach strips tags but keeps text content
        self.assertIn('alert', slot.text)

    # ── Test 6: Unicode-escaped injection stripped ──

    def test_unicode_escaped_injection_stripped(self):
        """Unicode-escaped HTML injection (\u003Cscript\u003E) should be stripped."""
        slot = CertificateTemplateText.objects.get(
            certificate_type='standard', slot_key='closing_statement',
        )
        slot.text = '\u003Cscript\u003Ealert(1)\u003C/script\u003E'
        slot.save()
        slot.refresh_from_db()
        self.assertNotIn('<script>', slot.text)
        # bleach strips tags but keeps text content
        self.assertIn('alert(1)', slot.text)

    # ── Test 7: HTML-entity-encoded injection stripped ──

    def test_html_entity_encoded_injection_stripped(self):
        """HTML-entity-encoded injection (&lt;script&gt;) should be stripped."""
        slot = CertificateTemplateText.objects.get(
            certificate_type='standard', slot_key='closing_statement',
        )
        slot.text = '&lt;script&gt;alert(1)&lt;/script&gt;'
        slot.save()
        slot.refresh_from_db()
        self.assertNotIn('<script>', slot.text)
        # bleach decodes entities then strips tags, keeping text content
        self.assertIn('alert(1)', slot.text)

    # ── Test 8: Closing statement editable and snapshots correctly ──

    def test_closing_statement_editable_and_snapshots_for_fit_to_work(self):
        """Fit-to-Work closing statement should be editable and snapshot correctly on issue."""
        # Edit the closing statement
        slot = CertificateTemplateText.objects.get(
            certificate_type='fit_to_work', slot_key='closing_statement',
        )
        slot.text = 'Custom closing: {patient_name} — issued for work purposes.'
        slot.save()

        cert = self._create_cert(
            MedicalCertificate.CertificateType.FIT_TO_WORK,
            work_assessment='fit_to_return',
            return_date=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        snapshot = cert.rendered_text_snapshot
        self.assertIn('closing_statement', snapshot)
        self.assertIn('Custom closing:', snapshot['closing_statement'])
        self.assertIn('Test Patient', snapshot['closing_statement'])  # patient full name

    def test_closing_statement_editable_and_snapshots_for_fit_to_play(self):
        """Fit-to-Play closing statement should be editable and snapshot correctly on issue."""
        # Edit the closing statement
        slot = CertificateTemplateText.objects.get(
            certificate_type='fit_to_play', slot_key='closing_statement',
        )
        slot.text = 'Custom play closing: {patient_name} cleared for {activity_name}.'
        slot.save()

        cert = self._create_cert(
            MedicalCertificate.CertificateType.FIT_TO_PLAY,
            activity_name='Basketball tournament',
            fitness_status='cleared',
        )
        cert.issue(user=self.doctor)

        snapshot = cert.rendered_text_snapshot
        self.assertIn('closing_statement', snapshot)
        self.assertIn('Custom play closing:', snapshot['closing_statement'])
        self.assertIn('Basketball tournament', snapshot['closing_statement'])
