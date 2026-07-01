from django.test import TestCase, override_settings
from django.urls import reverse

from patients.models import Patient, PatientProfile

from .models import User


# Test classes that render templates need a non-manifest static storage
# since the manifest (staticfiles.json) is only built during deploy.
_NO_MANIFEST_STORAGE = override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})


@_NO_MANIFEST_STORAGE
class UserEnumerationPreventionTest(TestCase):
    """
    Tests that login and forgot-password views do not reveal whether a username exists.
    """

    @classmethod
    def setUpTestData(cls):
        # Create a user that exists
        cls.existing_user = User.objects.create_user(
            username='EXISTING-001',
            password='correctpassword123',
            role=User.Role.PATIENT,
            email='existing@test.clinic',
            first_name='Existing',
            last_name='User',
        )

    def test_login_same_message_for_existing_and_nonexistent_user(self):
        """Login should show the same error message regardless of whether the user exists."""
        # Try with existing user but wrong password
        response_existing = self.client.post(reverse('accounts:login'), {
            'username': 'EXISTING-001',
            'password': 'wrongpassword',
        })
        # Try with non-existent user
        response_nonexistent = self.client.post(reverse('accounts:login'), {
            'username': 'NONEXISTENT-999',
            'password': 'anypassword',
        })

        # Both should have the same error message
        self.assertContains(response_existing, 'Invalid username or password.')
        self.assertContains(response_nonexistent, 'Invalid username or password.')

    def test_forgot_password_same_message_for_existing_and_nonexistent_user(self):
        """Forgot password should show the same generic message regardless of whether the user exists."""
        generic_message = 'If an account with that username exists'

        # Try with existing user — should redirect to verify_otp (success path)
        response_existing = self.client.post(reverse('accounts:forgot_password'), {
            'patient_id': 'EXISTING-001',
        })
        # Redirect indicates the OTP was sent (without revealing it was sent)
        self.assertEqual(response_existing.status_code, 302)

        # Try with non-existent user — should stay on same page with generic message
        response_nonexistent = self.client.post(reverse('accounts:forgot_password'), {
            'patient_id': 'NONEXISTENT-999',
        })
        self.assertEqual(response_nonexistent.status_code, 200)
        self.assertContains(response_nonexistent, generic_message)

    def test_forgot_password_no_distinct_error_for_user_without_email(self):
        """Forgot password should show generic message even if user has no email."""
        user_no_email = User.objects.create_user(
            username='NOEMAIL-001',
            password='testpass123',
            role=User.Role.PATIENT,
            # No email set
            first_name='No',
            last_name='Email',
        )
        generic_message = 'If an account with that username exists'

        response = self.client.post(reverse('accounts:forgot_password'), {
            'patient_id': 'NOEMAIL-001',
        }, follow=True)

        self.assertContains(response, generic_message)


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
