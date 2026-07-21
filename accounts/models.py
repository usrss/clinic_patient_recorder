from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Clinic user. Staff roles control system access. Patients get the
    'patient' role and are linked 1-to-1 with a patients.Patient record
    via patient_id = username.
    """

    class Role(models.TextChoices):
        PATIENT  = 'patient',  'Patient'
        DOCTOR   = 'doctor',   'Doctor'
        FRONTDESK = 'frontdesk', 'Front Desk'
        ADMIN    = 'admin',    'Admin'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PATIENT,
    )

    phone = models.CharField(max_length=20, blank=True)

    # ── Override AbstractUser.email to enforce uniqueness ──────────────────
    # null=True allows blank emails to be stored as NULL, which SQLite handles
    # gracefully with unique constraints (multiple NULLs are permitted).
    email = models.EmailField(unique=True, blank=True, null=True)

    # ── Profile Picture ────────────────────────────────────────────────────
    profile_picture = models.ImageField(
        upload_to='staff/',
        null=True,
        blank=True,
        help_text='Optional profile picture (JPG, PNG, WebP)',
    )

    temp_password = models.CharField(
        max_length=10,
        blank=True,
        help_text='Temporary password in plaintext (cleared after user changes password).',
    )

    force_password_change = models.BooleanField(default=False)

    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    # FIX: Increased max_length from 6 to 255 to support hashed OTPs (make_password produces ~128+ chars)
    reset_otp = models.CharField(max_length=255, null=True, blank=True)
    reset_otp_expiry = models.DateTimeField(null=True, blank=True)

    # ── convenience properties ──────────────────────────────────────────
    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_frontdesk(self):
        return self.role == self.Role.FRONTDESK

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_clinical_staff(self):
        return self.role in (
            self.Role.DOCTOR,
            self.Role.FRONTDESK,
            self.Role.ADMIN,
        )

    def get_patient_record(self):
        """
        Return the linked patients.Patient record for a patient-role user.
        username == patient_id by convention.
        """
        if self.role != self.Role.PATIENT:
            return None
        from patients.models import Patient
        try:
            return Patient.objects.get(patient_id=self.username)
        except Patient.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role != self.Role.ADMIN:
            self.role = self.Role.ADMIN
        # Normalise empty email to NULL so MySQL's unique constraint allows
        # multiple users with no email (NULLs are distinct; empty strings are not).
        if not self.email:
            self.email = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['role', 'username']