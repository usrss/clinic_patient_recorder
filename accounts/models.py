from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Clinic staff user. Roles represent system access levels.
    Patients are a separate model (patients.Patient) — not auth users.
    """

    class Role(models.TextChoices):
        NURSE = 'nurse', 'Nurse'
        DOCTOR = 'doctor', 'Doctor'
        FRONTDESK = 'frontdesk', 'Front Desk'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.NURSE,
    )
    phone = models.CharField(max_length=20, blank=True)
    force_password_change = models.BooleanField(default=False)

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

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    class Meta:
        verbose_name = 'Staff User'
        verbose_name_plural = 'Staff Users'
        ordering = ['role', 'username']