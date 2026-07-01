from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable, append-only audit trail for all important actions
    performed inside the CPR system.

    Once written, records must never be updated or deleted.
    Override save() / delete() to enforce this at the model level.
    """

    # ── Action choices ─────────────────────────────────────────────────
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'CREATE'
        UPDATE = 'UPDATE', 'UPDATE'
        DELETE = 'DELETE', 'DELETE'
        VIEW = 'VIEW', 'VIEW'
        LOGIN = 'LOGIN', 'LOGIN'
        LOGOUT = 'LOGOUT', 'LOGOUT'
        DOWNLOAD = 'DOWNLOAD', 'DOWNLOAD'
        PRINT = 'PRINT', 'PRINT'
        EXPORT = 'EXPORT', 'EXPORT'

    # ── Module choices ────────────────────────────────────────────────
    class Module(models.TextChoices):
        AUTHENTICATION = 'Authentication', 'Authentication'
        PATIENTS = 'Patients', 'Patients'
        APPOINTMENTS = 'Appointments', 'Appointments'
        CONSULTATIONS = 'Consultations', 'Consultations'
        MEDICAL_CERTIFICATES = 'Medical Certificates', 'Medical Certificates'
        DENTAL_CERTIFICATES = 'Dental Certificates', 'Dental Certificates'
        REPORTS = 'Reports', 'Reports'
        USER_MANAGEMENT = 'User Management', 'User Management'
        SETTINGS = 'Settings', 'Settings'
        CERTIFICATE_TEMPLATES = 'Certificate Templates', 'Certificate Templates'
        INVENTORY = 'Inventory', 'Inventory'
        FEEDBACK = 'Feedback', 'Feedback'

    # ── Status choices ────────────────────────────────────────────────
    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'SUCCESS'
        FAILED = 'FAILED', 'FAILED'

    # ── Fields ────────────────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='The user who performed the action',
    )
    user_role = models.CharField(
        max_length=20,
        blank=True,
        help_text='User role at the time of the action (stored for historical accuracy)',
    )
    user_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="User's full name at the time of the action",
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        db_index=True,
    )
    module = models.CharField(
        max_length=30,
        choices=Module.choices,
        db_index=True,
    )
    description = models.TextField(
        blank=True,
        help_text='Human-readable explanation of the activity',
    )

    # ── Object reference ──────────────────────────────────────────────
    object_model = models.CharField(
        max_length=100,
        blank=True,
        help_text='Dotted model path (e.g. "patients.Patient")',
    )
    object_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='Primary key / identifier of the affected record',
    )
    object_repr = models.CharField(
        max_length=300,
        blank=True,
        help_text='String representation of the affected object',
    )

    # ── Change tracking (JSON stores dict of field_name: old/new) ─────
    changes_before = models.JSONField(
        null=True, blank=True,
        help_text='Snapshot of values BEFORE the change (dict)',
    )
    changes_after = models.JSONField(
        null=True, blank=True,
        help_text='Snapshot of values AFTER the change (dict)',
    )

    # ── Meta ──────────────────────────────────────────────────────────
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        help_text='Request IP address when available',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS,
        db_index=True,
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='When the action occurred',
    )

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        # Prevent Django admin from showing a "Save" button — we override delete
        # to prevent removals.
        managed = True

        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['user_role', '-timestamp']),
            models.Index(fields=['action', 'module']),
            models.Index(fields=['module', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
            models.Index(fields=['object_model', 'object_id']),
        ]

    def __str__(self):
        return (
            f'{self.get_action_display()} — {self.get_module_display()} '
            f'({self.timestamp:%Y-%m-%d %H:%M})'
        )

    # ── Append-only enforcement ───────────────────────────────────────
    def save(self, *args, **kwargs):
        """Prevent updates to existing audit log entries."""
        if self.pk is not None:
            raise RuntimeError(
                'AuditLog entries are append-only and cannot be modified.'
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of audit log entries."""
        raise RuntimeError(
            'AuditLog entries are append-only and cannot be deleted.'
        )

    @classmethod
    def bulk_create_immutable(cls, objs, **kwargs):
        """
        Safely bulk-create audit log entries.
        Disallows creation if any object already has a pk set.
        """
        for obj in objs:
            if obj.pk is not None:
                raise RuntimeError(
                    'Cannot bulk-create AuditLog entries with existing PKs.'
                )
        return cls.objects.bulk_create(objs, **kwargs)
