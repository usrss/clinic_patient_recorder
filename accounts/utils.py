import random
import string

from .models import User


def generate_temp_password(length=8):
    """
    Return a random string of letters and digits of the given length.
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


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


def create_patient_user(patient):
    """
    Create a User account for a Patient record that was created by the
    front desk (walk-in).  The User is set up with:

        * username = patient.patient_id
        * random temporary password
        * role = PATIENT

    Returns a tuple of (user, temp_password).

    The user account is marked with ``force_password_change = True`` so
    the patient must change their password on first login.
    """
    temp_password = generate_temp_password()
    user = User.objects.create_user(
        username=patient.patient_id,
        password=temp_password,
        first_name=patient.first_name,
        last_name=patient.last_name,
        role=User.Role.PATIENT,
    )
    user.force_password_change = True
    user.save(update_fields=['force_password_change'])
    return user, temp_password
