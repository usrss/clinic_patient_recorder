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

    # ── Contact information (Module 1) ──────────────────────────────────────
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

    def __str__(self):
        return f'{self.patient_id} — {self.get_full_name()}'

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['last_name', 'first_name']),
        ]


class PatientProfile(models.Model):
    """
    User-managed profile data for a patient.
    Birthday is entered by the patient (not imported) and is used to compute age.
    """
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile',
    )
    birthday = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile — {self.patient.patient_id}'

    class Meta:
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'