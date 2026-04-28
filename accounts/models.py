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
        NURSE    = 'nurse',    'Nurse'
        DOCTOR   = 'doctor',   'Doctor'
        FRONTDESK = 'frontdesk', 'Front Desk'
        ADMIN    = 'admin',    'Admin'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.NURSE,
    )
    phone = models.CharField(max_length=20, blank=True)
    force_password_change = models.BooleanField(default=False)

    # ── convenience properties ──────────────────────────────────────────
    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_nurse(self):
        return self.role == self.Role.NURSE

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
            self.Role.NURSE,
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

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['role', 'username']