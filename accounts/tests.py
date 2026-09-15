from django.test import TestCase, override_settings
from django.urls import reverse

from core.validators import normalize_phone, validate_phone
from patients.models import Patient, PatientProfile

from colleges.models import Course
from .forms import RegistrationForm
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
            phone='+639171234567',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('accounts:profile_settings'), {
            'first_name': 'New',
            'last_name': 'Doctor',
            'email': 'new@example.com',
            'phone': '0917 123-4567',
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
        self.assertEqual(user.phone, '+639171234567')  # normalized from 0917 123-4567

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
        self.assertEqual(patient.phone, '+639171234567')  # normalized
        self.assertEqual(patient.email, 'patient@example.com')
        self.assertEqual(patient.emergency_contact_name, 'Contact One')
        self.assertEqual(patient.emergency_contact_phone, '+639176543210')  # normalized
        self.assertEqual(profile.address, 'Updated address')
        self.assertEqual(profile.year_level, '2nd Year')
        self.assertTrue(profile.hypertension)
        self.assertEqual(profile.known_allergies, 'Dust')


class PhilippinePhoneValidatorTests(TestCase):
    """Unit tests for the shared PH mobile validator and +63 normalizer."""

    def test_valid_formats_pass(self):
        for value in ('09171234567', '+639171234567', '9171234567',
                      '0917 123-4567', '+63 (917) 123-4567',
                      '0917.123.4567'):
            with self.subTest(value=value):
                self.assertEqual(normalize_phone(value), '+639171234567')

    def test_invalid_values_rejected(self):
        for value in ('12345', 'abc-!!!', '08171234567',  # landline prefix 8
                      '0917123456',                        # 9 digits after 0
                      '091712345678',                      # too long
                      '+6391712345678',                    # too long intl
                      '639171234567',                      # no +, no leading 0
                      '+63-917-abc-def',
                      '0917+1234567',                      # stray +
                      ''):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    normalize_phone(value)

    def test_validate_phone_model_validator(self):
        validate_phone('09171234567')  # must not raise
        with self.assertRaises(Exception):
            validate_phone('not-a-phone')


class RegistrationFormPhoneTests(TestCase):
    """RegistrationForm rejects non-PH phone values and normalizes valid ones."""

    @classmethod
    def setUpTestData(cls):
        from colleges.models import College, Course
        cls.college = College.objects.create(name='Test College', abbreviation='TC')
        cls.course = Course.objects.create(name='Test Course', college=cls.college)

    def _base_data(self, **overrides):
        data = {
            'role': 'student',
            'patient_id': '20250001',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'sex': 'M',
            'email': 'juan@test.clinic',
            'password1': 'Str0ng!Pass9',
            'password2': 'Str0ng!Pass9',
            'birthday': '2005-05-10',
            'college': str(self.college.pk),
            'course': str(self.course.pk),
            'year_level': '1st Year',
            'phone': '09171234567',
            'emergency_contact_name': 'Maria Dela Cruz',
            'emergency_contact_phone': '09181234567',
            'current_step': '4',
        }
        data.update(overrides)
        return data

    def test_valid_phones_normalized(self):
        form = RegistrationForm(self._base_data())
        # The register view re-scopes the course queryset from the POSTed
        # college before validation — replicate that here.
        form.fields['course'].queryset = Course.objects.filter(college=self.college)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone'], '+639171234567')
        self.assertEqual(form.cleaned_data['emergency_contact_phone'], '+639181234567')

    def test_letters_rejected(self):
        form = RegistrationForm(self._base_data(phone='0917abc4567'))
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_special_characters_rejected(self):
        form = RegistrationForm(self._base_data(phone='0917@#$4567'))
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_non_ph_digits_rejected(self):
        form = RegistrationForm(self._base_data(phone='1234567890'))
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_emergency_phone_letters_rejected(self):
        form = RegistrationForm(self._base_data(emergency_contact_phone='hello'))
        self.assertFalse(form.is_valid())
        self.assertIn('emergency_contact_phone', form.errors)

    def test_future_birthday_rejected(self):
        from datetime import date, timedelta
        future = (date.today() + timedelta(days=30)).isoformat()
        form = RegistrationForm(self._base_data(birthday=future))
        self.assertFalse(form.is_valid())
        self.assertIn('birthday', form.errors)


class RegistrationOtpEnforcementTests(TestCase):
    """Final registration POST must come from an OTP-verified session with
    the same email that was verified."""

    @classmethod
    def setUpTestData(cls):
        from colleges.models import College, Course
        cls.college = College.objects.create(name='OTP College', abbreviation='OC')
        cls.course = Course.objects.create(name='OTP Course', college=cls.college)

    def _post_registration(self, email='otp@test.clinic'):
        return self.client.post(reverse('accounts:register'), {
            'role': 'student',
            'patient_id': '20250002',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'sex': 'M',
            'email': email,
            'password1': 'Str0ng!Pass9',
            'password2': 'Str0ng!Pass9',
            'birthday': '2005-05-10',
            'college': str(self.college.pk),
            'course': str(self.course.pk),
            'year_level': '1st Year',
            'phone': '09171234567',
            'emergency_contact_name': 'Maria Dela Cruz',
            'emergency_contact_phone': '09181234567',
            'current_step': '4',
        })

    def test_rejected_without_otp_verification(self):
        response = self._post_registration()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'verify your email with the OTP code')
        self.assertFalse(User.objects.filter(username='20250002').exists())

    def test_rejected_when_email_differs_from_verified(self):
        session = self.client.session
        session['registration_otp_verified'] = True
        session['registration_email'] = 'other@test.clinic'
        session.save()

        response = self._post_registration(email='otp@test.clinic')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'does not match the one you verified')
        self.assertFalse(User.objects.filter(username='20250002').exists())

    def test_verify_endpoint_limits_guesses(self):
        from datetime import timedelta

        from django.contrib.auth.hashers import make_password
        from django.utils import timezone

        session = self.client.session
        session['registration_otp'] = make_password('123456')
        session['registration_otp_expiry'] = (timezone.now() + timedelta(minutes=3)).isoformat()
        session.save()

        response = None
        for _ in range(5):
            response = self.client.post(reverse('accounts:verify_registration_otp'), {'otp': '000000'})
            self.assertFalse(response.json()['success'])

        # 5 wrong attempts → OTP invalidated, message asks for a new code
        self.assertIn('Too many incorrect attempts', response.json()['error'])

    def test_successful_verify_sets_flag_and_matches_email(self):
        from django.contrib.auth.hashers import make_password
        from django.utils import timezone
        session = self.client.session
        session['registration_otp'] = make_password('654321')
        session['registration_otp_expiry'] = (timezone.now() + timezone.timedelta(minutes=3)).isoformat()
        session['registration_email'] = 'otp@test.clinic'
        session.save()

        response = self.client.post(reverse('accounts:verify_registration_otp'), {'otp': '654321'})
        self.assertTrue(response.json()['success'])

        # Verified session + matching email → registration succeeds
        response = self._post_registration()
        self.assertRedirects(response, reverse('accounts:dashboard'), fetch_redirect_response=False)
        user = User.objects.get(username='20250002')
        self.assertEqual(user.phone, '+639171234567')
