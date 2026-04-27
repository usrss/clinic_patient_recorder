from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        NURSE = 'nurse', 'Nurse'
        DOCTOR = 'doctor', 'Doctor'
        FRONTDESK = 'frontdesk', 'Front Desk'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    phone = models.CharField(max_length=20, blank=True)
    force_password_change = models.BooleanField(default=False)

    # FIX: Converted to @property so Django templates can access them correctly
    # without the ambiguity of calling them as methods vs. properties.
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

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
        """Nurse, doctor, frontdesk, or admin."""
        return self.role in (
            self.Role.NURSE,
            self.Role.DOCTOR,
            self.Role.FRONTDESK,
            self.Role.ADMIN,
        )

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['role', 'username']


class StudentProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=20, unique=True, db_index=True)
    middle_name = models.CharField(max_length=50, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        blank=True,
    )
    college = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        parts = [self.user.first_name, self.middle_name, self.user.last_name]
        return ' '.join(p for p in parts if p)

    def __str__(self):
        return f'{self.student_id} - {self.user.get_full_name()}'

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        ordering = ['student_id']