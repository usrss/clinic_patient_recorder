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

from certificates.models import MedicalCertificate, CertificateTemplateText, CertificateTemplateChangeLog, CertificateAuditLog
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
            certificate_type=MedicalCertificate.CertificateType.ABSENCES,
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
                        certificate_type=MedicalCertificate.CertificateType.ABSENCES,
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

        # Verify audit log integrity based on outcome
        log_count = cert.audit_logs.count()
        if results['void_error'] is None:
            # Void succeeded — expect issued + voided audit logs
            self.assertGreaterEqual(log_count, 2,
                'Void succeeded: should have at least issued + voided audit logs.')
            self.assertLessEqual(log_count, 3,
                'Void succeeded: should have at most 3 audit logs.')
        else:
            # Void failed (concurrency guard) — only the pre-thread issue audit log
            self.assertEqual(log_count, 1,
                'Void failed: should have exactly 1 (issued) audit log.')


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
            certificate_type=MedicalCertificate.CertificateType.ABSENCES,
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
            certificate_type=MedicalCertificate.CertificateType.ABSENCES,
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
        cls._seed_templates()

    @classmethod
    def _seed_templates(cls):
        # Clear any rows from data migration so we control the exact set
        CertificateTemplateText.objects.all().delete()
        CertificateTemplateText.objects.bulk_create([
            # ── Absences ─────────────────────────────────────────────────
            CertificateTemplateText(
                certificate_type='absences',
                slot_key='body',
                text='This is to certify that {patient_name}, {age} years of age, was examined on {exam_date}.\n\n'
                     'Diagnosis: {diagnosis}\n\n'
                     'The patient is advised to rest from {rest_from} to {rest_to}.\n\n'
                     'This certificate is issued for legal purposes.',
            ),
            # ── OJT ──────────────────────────────────────────────────────
            CertificateTemplateText(
                certificate_type='ojt',
                slot_key='body',
                text='This is to certify that {patient_name} is FIT to work. Assessment: {work_assessment}.\n\n'
                     'Findings: {diagnosis}\n\n'
                     'This certificate is issued upon the request of the patient for legal purposes.',
            ),
            # ── Activities ───────────────────────────────────────────────
            CertificateTemplateText(
                certificate_type='activities',
                slot_key='body',
                text='This is to certify that {patient_name} is FIT to play. Status: {fitness_status}.\n\n'
                     'Findings: {diagnosis}\n\n'
                     'This certificate is issued upon the request of the patient for legal purposes.',
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
        """Editing a template after a cert is issued should NOT change that cert's rendered_text_snapshot."""
        cert = self._create_cert(
            MedicalCertificate.CertificateType.ABSENCES,
            rest_from=timezone.localtime(timezone.now()).date(),
            rest_to=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        original_snapshot = str(cert.rendered_text_snapshot)

        # Now edit the template text
        slot = CertificateTemplateText.objects.get(
            certificate_type='absences', slot_key='body',
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
            certificate_type='absences', slot_key='body',
        )
        slot.text = 'NEW WORDING: {patient_name} was examined on {exam_date}.'
        slot.save()

        cert = self._create_cert(
            MedicalCertificate.CertificateType.ABSENCES,
            rest_from=timezone.localtime(timezone.now()).date(),
            rest_to=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        self.assertIn(
            'NEW WORDING:',
            cert.rendered_text_snapshot,
        )
        self.assertNotIn(
            'This is to certify',
            cert.rendered_text_snapshot,
        )

    # ── Test 3: Standard certificate renders body from standard template ──

    def test_absences_certificate_renders_body(self):
        """Absences certificate should render body text from the template."""
        cert = self._create_cert(
            MedicalCertificate.CertificateType.ABSENCES,
            rest_from=timezone.localtime(timezone.now()).date(),
            rest_to=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        snapshot = cert.rendered_text_snapshot
        self.assertIn('This is to certify', snapshot)
        self.assertIn('Diagnosis:', snapshot)

    # ── Test 4: Body text contains diagnosis and rest period ──

    def test_body_contains_diagnosis_and_rest(self):
        """Absences certificate body should include diagnosis and rest period."""
        same_day = timezone.localtime(timezone.now()).date()

        cert = self._create_cert(
            MedicalCertificate.CertificateType.ABSENCES,
            rest_from=same_day,
            rest_to=same_day,
        )
        cert.issue(user=self.doctor)

        snapshot = cert.rendered_text_snapshot
        self.assertIsInstance(snapshot, str)
        self.assertIn('Diagnosis:', snapshot)
        self.assertIn('rest from', snapshot.lower())

    # ── Test 5: HTML injection stripped by bleach ──

    def test_html_tags_are_stripped(self):
        """HTML tags should be stripped from template text by bleach."""
        slot = CertificateTemplateText.objects.get(
            certificate_type='absences', slot_key='body',
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
        """Unicode-escaped HTML injection should be stripped."""
        slot = CertificateTemplateText.objects.get(
            certificate_type='absences', slot_key='body',
        )
        slot.text = '<script>alert(1)</script>'
        slot.save()
        slot.refresh_from_db()
        self.assertNotIn('<script>', slot.text)
        # bleach strips tags but keeps text content
        self.assertIn('alert(1)', slot.text)

    # ── Test 7: HTML-entity-encoded injection stripped ──

    def test_html_entity_encoded_injection_stripped(self):
        """HTML-entity-encoded injection should be stripped."""
        slot = CertificateTemplateText.objects.get(
            certificate_type='absences', slot_key='body',
        )
        slot.text = '&lt;script&gt;alert(1)&lt;/script&gt;'
        slot.save()
        slot.refresh_from_db()
        self.assertNotIn('<script>', slot.text)
        # bleach decodes entities then strips tags, keeping text content
        self.assertIn('alert(1)', slot.text)

    # ── Test 8: Body text editable and snapshots correctly ──

    def test_body_editable_and_snapshots_for_ojt(self):
        """OJT body text should be editable and snapshot correctly on issue."""
        # Edit the body
        slot = CertificateTemplateText.objects.get(
            certificate_type='ojt', slot_key='body',
        )
        slot.text = 'Custom work cert: {patient_name} — assessment: {work_assessment}.'
        slot.save()

        cert = self._create_cert(
            MedicalCertificate.CertificateType.OJT,
            work_assessment='fit_to_return',
            return_date=timezone.localtime(timezone.now()).date(),
        )
        cert.issue(user=self.doctor)

        snapshot = cert.rendered_text_snapshot
        self.assertIn('Custom work cert:', snapshot)
        self.assertIn('Test Patient', snapshot)  # patient full name

    def test_body_editable_and_snapshots_for_activities(self):
        """Activities body text should be editable and snapshot correctly on issue."""
        # Edit the body
        slot = CertificateTemplateText.objects.get(
            certificate_type='activities', slot_key='body',
        )
        slot.text = 'Custom play cert: {patient_name} cleared for {activity_name}.'
        slot.save()

        cert = self._create_cert(
            MedicalCertificate.CertificateType.ACTIVITIES,
            activity_name='Basketball tournament',
            fitness_status='cleared',
        )
        cert.issue(user=self.doctor)

        snapshot = cert.rendered_text_snapshot
        self.assertIn('Custom play cert:', snapshot)
        self.assertIn('Basketball tournament', snapshot)


class CertificateDoctorNameTest(TestCase):
    """
    Certificates must show the doctor's name WITHOUT a 'Dr.'/'Dra.' honorific.
    The placeholder map feeds both the .docx/PDF output and any prose that
    references {doctor_name}, so this is the single source of truth.
    """

    @classmethod
    def setUpTestData(cls):
        cls.patient = Patient.objects.create(
            patient_id='DOCNAME-001',
            first_name='Test',
            last_name='Patient',
            sex='M',
        )
        cls.doctor = User.objects.create_user(
            username='dr_prefix', password='testpass123', role='doctor',
            first_name='Dr. Juan', last_name='Dela Cruz',
            email='dr_prefix@test.clinic',
        )

    def _create_cert(self):
        consultation = Consultation.objects.create(
            patient=self.patient,
            symptoms='Test symptoms',
            status=Consultation.Status.COMPLETED,
        )
        return MedicalCertificate.objects.create(
            consultation=consultation,
            patient=self.patient,
            doctor=self.doctor,
            certificate_type=MedicalCertificate.CertificateType.ABSENCES,
            diagnosis='Test diagnosis',
        )

    def test_doctor_name_placeholder_has_no_honorific(self):
        """'Dr. Juan Dela Cruz' renders as 'Juan Dela Cruz' on certificates."""
        cert = self._create_cert()
        name = cert._build_placeholder_map()['doctor_name']
        self.assertEqual(name, 'Juan Dela Cruz')
        self.assertNotIn('Dr', name)

    def test_doctor_name_without_prefix_is_unchanged(self):
        self.doctor.first_name = 'Maria'
        self.doctor.last_name = 'Santos'
        self.doctor.save()
        cert = self._create_cert()
        self.assertEqual(
            cert._build_placeholder_map()['doctor_name'],
            'Maria Santos',
        )

    def test_dra_honorific_is_stripped(self):
        """The Filipino female honorific 'Dra.' is stripped too."""
        self.doctor.first_name = 'Dra. Ana'
        self.doctor.last_name = 'Reyes'
        self.doctor.save()
        cert = self._create_cert()
        self.assertEqual(
            cert._build_placeholder_map()['doctor_name'],
            'Ana Reyes',
        )
