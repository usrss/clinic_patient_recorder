from django.db import models
from django.conf import settings


class Consultation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        QUEUED = 'queued', 'Queued'
        SCHEDULED = 'scheduled', 'Scheduled'
        TRIAGED = 'triaged', 'Triaged'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='consultations',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    symptoms = models.TextField()
    medical_history = models.TextField(blank=True)
    severity_description = models.TextField(
        help_text='Self-reported severity description by the patient'
    )
    additional_notes = models.TextField(blank=True)
    queue_number = models.PositiveIntegerField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f'Consultation #{self.pk} — {self.patient.get_full_name()} '
            f'({self.get_status_display()})'
        )

    class Meta:
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['patient', '-created_at']),
        ]


class Triage(models.Model):
    class Urgency(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name='triage',
    )
    nurse = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='triages_performed',
    )
    blood_pressure = models.CharField(max_length=20, help_text='e.g. 120/80')
    temperature = models.DecimalField(
        max_digits=5, decimal_places=2, help_text='Degrees Celsius'
    )
    pulse_rate = models.PositiveIntegerField(help_text='BPM')
    urgency = models.CharField(max_length=10, choices=Urgency.choices)
    notes = models.TextField(blank=True)
    triaged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Triage #{self.pk} — Consultation #{self.consultation_id}'

    class Meta:
        verbose_name = 'Triage'
        verbose_name_plural = 'Triages'


class Prescription(models.Model):
    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name='prescription',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prescriptions_made',
    )
    diagnosis = models.TextField()
    treatment_plan = models.TextField(blank=True)
    prescribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Prescription #{self.pk} — Consultation #{self.consultation_id}'

    class Meta:
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'


class PrescriptionItem(models.Model):
    """
    A single medicine line in a prescription.

    Supports two modes:
      1. Inventory-linked: medicine FK is set, quantity is set (existing flow).
      2. Free-text: medicine_name text field is used with dosage/frequency/duration.

    Both modes store instructions (optional).
    Dosage, frequency, and duration are available in both modes.
    """
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items',
    )
    # Inventory link (existing flow — nullable to support free-text mode)
    medicine = models.ForeignKey(
        'inventory.Medicine',
        on_delete=models.PROTECT,
        related_name='prescription_items',
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(null=True, blank=True)

    # Free-text medicine name (used when not linked to inventory)
    medicine_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Free-text medicine name',
    )

    # Clinical dosing fields
    dosage = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g. 500mg, 10ml',
    )
    frequency = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g. 3x a day, once daily',
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g. 7 days, until finished',
    )
    instructions = models.CharField(
        max_length=200,
        blank=True,
        help_text='e.g. Take after meals',
    )

    def get_display_name(self):
        """Return the medicine name for display, regardless of mode."""
        if self.medicine:
            return self.medicine.name
        return self.medicine_name or '—'

    def __str__(self):
        return f'{self.get_display_name()} (Prescription #{self.prescription_id})'

    class Meta:
        verbose_name = 'Prescription Item'
        verbose_name_plural = 'Prescription Items'