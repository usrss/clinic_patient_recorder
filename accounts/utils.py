import random
import string

from .models import User


def generate_temp_password(length=4):
    """
    Return a random string of digits of the given length.
    """
    return ''.join(random.choices(string.digits, k=length))


def calculate_graduation_year(year_level):
    """
    Map year level string to expected graduation year.

    Year Level 1 → current_year + 4
    Year Level 2 → current_year + 3
    Year Level 3 → current_year + 2
    Year Level 4 → current_year + 1

    Returns None if the year level is not recognised or empty.
    """
    import datetime
    year_map = {
        '1st Year': 4,
        '2nd Year': 3,
        '3rd Year': 2,
        '4th Year': 1,
    }
    offset = year_map.get(year_level, 0)
    return datetime.date.today().year + offset if offset else None


def create_patient_user(patient, email=''):
    """
    Create a User account for a Patient record that was created by the
    front desk (walk-in).  The User is set up with:

        * username = patient.patient_id
        * random temporary password
        * role = PATIENT
        * email (if provided — required so the patient can use
          "Forgot Password" to reset their own password)

    Returns a tuple of (user, temp_password).

    The user account is marked with ``force_password_change = True`` so
    the patient must change their password on first login.
    The temp password is stored in plaintext on ``patient.temp_password``
    so the front desk can retrieve it later.
    """
    temp_password = generate_temp_password(length=4)
    user = User.objects.create_user(
        username=patient.patient_id,
        password=temp_password,
        first_name=patient.first_name,
        last_name=patient.last_name,
        email=email or None,
        role=User.Role.PATIENT,
    )
    user.force_password_change = True
    user.save(update_fields=['force_password_change'])
    # Store plaintext temp password for front-desk retrieval
    patient.temp_password = temp_password
    patient.save(update_fields=['temp_password'])
    return user, temp_password
