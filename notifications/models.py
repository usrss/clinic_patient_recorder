from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Role-based notification system.
    Notifications are created for specific roles or users.
    """

    class RecipientRole(models.TextChoices):
        FRONTDESK = 'frontdesk', 'Front Desk'
        NURSE = 'nurse', 'Nurse'
        DOCTOR = 'doctor', 'Doctor'
        ADMIN = 'admin', 'Admin'
        PATIENT = 'patient', 'Patient'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Specific user recipient (null = role-based)',
    )
    recipient_role = models.CharField(
        max_length=20,
        choices=RecipientRole.choices,
        null=True,
        blank=True,
        help_text='Role to notify (null = specific user only)',
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(
        max_length=300,
        blank=True,
        help_text='URL to redirect when clicked',
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient_role', '-created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        target = self.recipient.username if self.recipient else self.get_recipient_role_display()
        return f'[{target}] {self.title}'