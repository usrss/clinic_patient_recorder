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
