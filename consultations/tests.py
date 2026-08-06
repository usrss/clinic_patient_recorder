from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from patients.models import Patient, PatientProfile

from .models import Consultation


class PatientConsultationSubmitTests(TestCase):
    def test_patient_can_submit_new_consultation_without_submit_button_name(self):
        user = User.objects.create_user(
            username='P-002',
            password='secret12345',
            role=User.Role.PATIENT,
        )
        patient = Patient.objects.create(
            patient_id='P-002',
            first_name='Patient',
            last_name='Two',
            sex=Patient.Sex.MALE,
        )
        PatientProfile.objects.create(patient=patient, profile_completed=True)
        self.client.force_login(user)

        response = self.client.post(reverse('consultations:patient_submit'), {
            'symptoms': 'Fever and sore throat',
            'severity_description': 'Moderate fever since last night',
            'medical_history': '',
            'additional_notes': 'No other notes',
        })

        self.assertRedirects(
            response,
            reverse('consultations:patient_home'),
            fetch_redirect_response=False,
        )
        consultation = Consultation.objects.get(patient=patient)
        self.assertEqual(consultation.symptoms, 'Fever and sore throat')
        self.assertEqual(
            consultation.severity_description,
            'Moderate fever since last night',
        )
        self.assertEqual(consultation.status, Consultation.Status.PENDING)
        self.assertTrue(consultation.is_original_case)


class TriageChiefComplaintTests(TestCase):
    """
    Doctor-review step for the chief complaint during triage.
    The field is required and prefilled with the patient's own words, so the
    doctor must explicitly confirm/reword it. The saved value is what appears
    on official documents (print form, medical history).
    """

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doc1',
            password='secret12345',
            role=User.Role.DOCTOR,
        )
        self.patient = Patient.objects.create(
            patient_id='P-003',
            first_name='Jane',
            last_name='Doe',
            sex=Patient.Sex.FEMALE,
        )
        self.consultation = Consultation.objects.create(
            patient=self.patient,
            symptoms='sakit ako tiyan po',
            severity_description='Since last night',
            status=Consultation.Status.QUEUED,
            is_original_case=True,
        )
        self.client.force_login(self.doctor)

    def _post_triage(self, chief_complaint):
        return self.client.post(
            reverse('consultations:triage_form', args=[self.consultation.pk]),
            {
                'chief_complaint': chief_complaint,
                'blood_pressure': '120/80',
                'temperature': '36.5',
                'pulse_rate': '72',
                'urgency': 'low',
                'hypertension': 'on',
                'diabetes': '',
                'asthma': '',
                'cardiac_problems': '',
                'arthritis': '',
                'other_conditions': '',
                'bcg': '',
                'dpt': '',
                'opv': '',
                'hepatitis_b': '',
                'measles': '',
                'tt': '',
            },
        )

    def test_triage_saves_doctors_reviewed_chief_complaint(self):
        response = self._post_triage('abdominal pain for 2 days')
        self.assertRedirects(
            response,
            reverse('consultations:prescribe', args=[self.consultation.pk]),
            fetch_redirect_response=False,
        )
        self.consultation.refresh_from_db()
        self.assertEqual(
            self.consultation.chief_complaint,
            'abdominal pain for 2 days',
        )
        self.assertEqual(self.consultation.status, Consultation.Status.TRIAGED)

    def test_triage_requires_chief_complaint(self):
        """The doctor must explicitly confirm/reword the chief complaint —
        a blank value blocks the triage from being saved."""
        response = self._post_triage('')
        self.assertEqual(response.status_code, 200)  # re-renders with errors
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, Consultation.Status.QUEUED)
        self.assertFalse(self.consultation.triages.exists())
        self.assertFormError(
            response.context['form'],
            'chief_complaint',
            'This field is required.',
        )

    def test_triage_form_prefills_patient_words(self):
        response = self.client.get(
            reverse('consultations:triage_form', args=[self.consultation.pk])
        )
        form = response.context['form']
        self.assertEqual(form.initial['chief_complaint'], 'sakit ako tiyan po')

    def test_triage_edit_blocked_after_prescription(self):
        """Once a prescription exists, the triage record can no longer be
        amended — amendment is only allowed BEFORE prescribing."""
        from .models import Prescription, Triage

        self.consultation.status = Consultation.Status.TRIAGED
        self.consultation.save(update_fields=['status'])
        Triage.objects.create(
            consultation=self.consultation,
            blood_pressure='120/80',
            temperature=36.5,
            pulse_rate=72,
            urgency='low',
        )
        Prescription.objects.create(
            consultation=self.consultation,
            doctor=self.doctor,
            diagnosis='Abdominal pain',
        )

        response = self.client.get(
            reverse('consultations:triage_edit', args=[self.consultation.pk])
        )
        self.assertRedirects(
            response,
            reverse('consultations:triage_list'),
            fetch_redirect_response=False,
        )

    def test_triage_amendment_is_audit_logged(self):
        """Amending a triage must create an audit log entry (UPDATE action)
        so the change is traceable in the audit trail."""
        from .models import Triage
        from audit_logs.models import AuditLog

        self.consultation.status = Consultation.Status.TRIAGED
        self.consultation.save(update_fields=['status'])
        Triage.objects.create(
            consultation=self.consultation,
            blood_pressure='120/80',
            temperature=36.5,
            pulse_rate=72,
            urgency='low',
        )

        response = self.client.post(
            reverse('consultations:triage_edit', args=[self.consultation.pk]),
            {
                'blood_pressure': '130/85',
                'temperature': '36.6',
                'pulse_rate': '74',
                'urgency': 'low',
                'notes': '',
                'chief_complaint': 'abdominal pain',
                'amendment_reason': 'Re-measured blood pressure',
            },
        )
        self.assertRedirects(
            response,
            reverse('consultations:triage_list'),
            fetch_redirect_response=False,
        )

        entry = AuditLog.objects.filter(
            action='UPDATE',
            module='Consultations',
            object_id=str(self.consultation.pk),
        ).order_by('-id').first()
        self.assertIsNotNone(entry)
        self.assertIn('Amended triage', entry.description)
        self.assertEqual(entry.changes_after['chief_complaint'], 'abdominal pain')
