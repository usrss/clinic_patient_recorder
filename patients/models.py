import re
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_phone(value):
    """Accept Philippine mobile numbers and common formats."""
    cleaned = re.sub(r'[\s\-\(\)\+]', '', value)
    if not re.match(r'^\d{7,15}$', cleaned):
        raise ValidationError(
            'Enter a valid phone number (7–15 digits, spaces/dashes allowed).'
        )


class Patient(models.Model):
    """
    Unified patient model for all clinic patients — students, staff, instructors.
    Deliberately NOT tied to Django auth users; patients are independent identities.
    """

    class Sex(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'

    patient_id = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text='Student ID / Employee ID / Instructor ID',
    )
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=150)
    sex = models.CharField(max_length=1, choices=Sex.choices)

    # ── Contact information ──────────────────────────────────────────────────
    phone = models.CharField(
        max_length=30,
        blank=True,
        validators=[validate_phone],
        help_text='Primary contact number (e.g. 09171234567)',
    )
    email = models.EmailField(
        blank=True,
        help_text='Optional email address',
    )
    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Name of emergency contact',
    )
    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        validators=[validate_phone],
        help_text='Phone number of emergency contact',
    )

    # Only applicable for students
    college = models.ForeignKey(
        'colleges.College',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients',
    )

    # Optional — staff / instructor use
    department = models.CharField(max_length=150, blank=True)
    position = models.CharField(max_length=150, blank=True)

    is_active = models.BooleanField(default=True)

    # ── Login tracking ───────────────────────────────────────────────────────
    has_logged_in = models.BooleanField(
        default=False,
        db_index=True,
        help_text='True once the patient has successfully logged into the system at least once.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)

    @property
    def age(self):
        """Compute age from linked PatientProfile birthday. Returns None if not set."""
        try:
            birthday = self.profile.birthday
        except PatientProfile.DoesNotExist:
            return None
        if birthday is None:
            return None
        today = timezone.now().date()
        return (
            today.year - birthday.year
            - ((today.month, today.day) < (birthday.month, birthday.day))
        )

    @property
    def is_profile_complete(self):
        """Check if the patient has completed mandatory profile setup."""
        try:
            return self.profile.profile_completed
        except PatientProfile.DoesNotExist:
            return False

    def __str__(self):
        return f'{self.patient_id} — {self.get_full_name()}'

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['has_logged_in']),
        ]


class PatientProfile(models.Model):
    """
    User-managed profile data for a patient.
    Birthday is entered by the patient (not imported) and is used to compute age.
    profile_completed is set True once the patient finishes mandatory setup.
    """
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile',
    )
    birthday = models.DateField(null=True, blank=True)
    # Additional self-reported fields
    address = models.CharField(max_length=300, blank=True, help_text='Home address')
    blood_type = models.CharField(
        max_length=10,
        blank=True,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
            ('Unknown', 'Unknown'),
        ],
        help_text='Blood type'
    )
    known_allergies = models.TextField(
        blank=True,
        help_text='List any known allergies (medications, food, etc.)'
    )
    existing_conditions = models.TextField(
        blank=True,
        help_text='Existing medical conditions (e.g. diabetes, hypertension)'
    )

    # ── Demographics ───────────────────────────────────────────────────────
    religion = models.CharField(
        max_length=100,
        blank=True,
        help_text='Religious affiliation (e.g. Roman Catholic, Islam, etc.)'
    )
    civil_status = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('Single', 'Single'),
            ('Married', 'Married'),
            ('Widowed', 'Widowed'),
            ('Separated', 'Separated'),
            ('Divorced', 'Divorced'),
        ],
        help_text='Civil status'
    )
    year_level = models.CharField(
        max_length=20,
        blank=True,
        help_text='Year level (e.g. 1st Year, 2nd Year, 3rd Year, 4th Year)'
    )

    # ── Physical Info ──────────────────────────────────────────────────────
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Height in centimeters'
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Weight in kilograms'
    )

    # ── Family & Past Medical History (booleans + text) ────────────────────
    hypertension = models.BooleanField(
        default=False,
        help_text='Patient has hypertension'
    )
    diabetes = models.BooleanField(
        default=False,
        help_text='Patient has diabetes'
    )
    asthma = models.BooleanField(
        default=False,
        help_text='Patient has asthma'
    )
    cardiac_problems = models.BooleanField(
        default=False,
        help_text='Patient has cardiac problems'
    )
    arthritis = models.BooleanField(
        default=False,
        help_text='Patient has arthritis'
    )
    other_conditions = models.TextField(
        blank=True,
        help_text='Other medical conditions not listed above'
    )

    # ── Immunization Records (booleans + text) ────────────────────────────
    bcg = models.BooleanField(
        default=False,
        help_text='BCG vaccine received'
    )
    dpt = models.BooleanField(
        default=False,
        help_text='DPT vaccine received'
    )
    opv = models.BooleanField(
        default=False,
        help_text='Oral Polio Vaccine received'
    )
    hepatitis_b = models.BooleanField(
        default=False,
        help_text='Hepatitis B vaccine received'
    )
    measles = models.BooleanField(
        default=False,
        help_text='Measles vaccine received'
    )
    tt = models.BooleanField(
        default=False,
        help_text='Tetanus Toxoid vaccine received'
    )
    immunization_others = models.TextField(
        blank=True,
        help_text='Other immunization details (e.g. influenza, HPV, etc.)'
    )

    # ── Medical Background (text fields) ──────────────────────────────────
    current_medications = models.TextField(
        blank=True,
        help_text='List of current medications and dosages'
    )
    vices = models.TextField(
        blank=True,
        help_text='Smoking, alcohol intake, or other habits'
    )
    previous_illnesses = models.TextField(
        blank=True,
        help_text='Past illnesses (non‑chronic)'
    )
    previous_hospitalizations = models.TextField(
        blank=True,
        help_text='Past hospitalizations and dates if known'
    )

    profile_completed = models.BooleanField(
        default=False,
        help_text='True once the patient has completed the mandatory profile setup.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile — {self.patient.patient_id}'

    class Meta:
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'