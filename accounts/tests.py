from django.test import TestCase
from django.urls import reverse

from patients.models import Patient, PatientProfile

from .models import User


class ProfileSettingsTests(TestCase):
    def test_staff_profile_save_works_without_submit_button_name(self):
        user = User.objects.create_user(
            username='doctor1',
            password='secret12345',
            role=User.Role.DOCTOR,
            first_name='Old',
            last_name='Name',
            email='old@example.com',
            phone='111',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('accounts:profile_settings'), {
            'first_name': 'New',
            'last_name': 'Doctor',
            'email': 'new@example.com',
            'phone': '222',
        })

        self.assertRedirects(
            response,
            reverse('accounts:profile_settings'),
            fetch_redirect_response=False,
        )
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'Doctor')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.phone, '222')

    def test_patient_profile_save_works_without_submit_button_name(self):
        user = User.objects.create_user(
            username='P-001',
            password='secret12345',
            role=User.Role.PATIENT,
        )
        patient = Patient.objects.create(
            patient_id='P-001',
            first_name='Patient',
            last_name='One',
            sex=Patient.Sex.FEMALE,
        )
        profile = PatientProfile.objects.create(patient=patient, profile_completed=True)
        self.client.force_login(user)

        response = self.client.post(reverse('accounts:profile_settings'), {
            'phone': '09171234567',
            'email': 'patient@example.com',
            'emergency_contact_name': 'Contact One',
            'emergency_contact_phone': '09176543210',
            'address': 'Updated address',
            'religion': 'None',
            'civil_status': 'Single',
            'year_level': '2nd Year',
            'height_cm': '160.5',
            'weight_kg': '55.0',
            'hypertension': 'on',
            'other_conditions': 'None',
            'known_allergies': 'Dust',
            'immunization_others': '',
            'current_medications': '',
            'vices': '',
            'previous_illnesses': '',
            'previous_hospitalizations': '',
        })

        self.assertRedirects(
            response,
            reverse('accounts:profile_settings'),
            fetch_redirect_response=False,
        )
        patient.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual(patient.phone, '09171234567')
        self.assertEqual(patient.email, 'patient@example.com')
        self.assertEqual(patient.emergency_contact_name, 'Contact One')
        self.assertEqual(patient.emergency_contact_phone, '09176543210')
        self.assertEqual(profile.address, 'Updated address')
        self.assertEqual(profile.year_level, '2nd Year')
        self.assertTrue(profile.hypertension)
        self.assertEqual(profile.known_allergies, 'Dust')
