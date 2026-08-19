from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError


# ── Status groups for the single-active-consultation rule ─────────────────────
# A patient may only create a NEW consultation when none of their existing
# consultations is in an ACTIVE_STATUSES state. Kept as plain module-level
# constants (rather than enum members) so they can be referenced from the
# model's Meta.constraints.
ACTIVE_STATUSES = (
    'pending',
    'queued',
    'scheduled',
    'triaged',
    'active_follow_up',
)
CLOSED_STATUSES = ('completed', 'cancelled', 'closed')


class ConsultationManager(models.Manager):
    """
    Reusable query methods for the Consultation model.
    Centralizes common filters so views don't duplicate query logic.
    """

    def active_queue(self):
        """Pending consultations awaiting front desk processing."""
        return self.filter(
            status=Consultation.Status.PENDING
        ).select_related('patient', 'patient__college').order_by('created_at')

    def for_triage(self):
        """Consultations queued or scheduled, ready for doctor triage."""
        return self.filter(
            status__in=[Consultation.Status.QUEUED, Consultation.Status.SCHEDULED]
        ).select_related('patient', 'patient__college').order_by(
            'queue_number', 'scheduled_at', 'created_at'
        )

    def triaged_ready(self):
        """Consultations triaged and awaiting doctor consultation/prescription."""
        return self.filter(
            status=Consultation.Status.TRIAGED
        ).select_related('patient', 'patient__college').prefetch_related('triages').order_by('created_at')

    def for_patient(self, patient):
        """All consultations for a given patient, ordered by most recent first."""
        return self.filter(patient=patient).order_by('-created_at')

    def patient_history(self, patient):
        """Full patient history with related triages and prescriptions prefetched."""
        return self.filter(patient=patient).prefetch_related(
            'triages', 'prescriptions__items'
        ).order_by('-created_at')

    def active_follow_ups(self, patient):
        """Active follow-up consultations for a patient (doctor-marked only)."""
        return self.filter(
            patient=patient,
            is_original_case=True,
            status=Consultation.Status.ACTIVE_FOLLOW_UP,
        ).order_by('-created_at')

    def active_cases(self, patient):
        """All open/active consultation cases for a patient."""
        return self.filter(
            patient=patient,
            is_original_case=True,
            status__in=[
                Consultation.Status.ACTIVE_FOLLOW_UP,
                Consultation.Status.TRIAGED,
                Consultation.Status.COMPLETED,
            ]
        ).order_by('-created_at')

    def active_for_patient(self, patient):
        """
        Consultations that are still active for a patient — i.e. NOT in a
        closed state (completed / cancelled / closed). Ordered most recent first.
        """
        return self.filter(
            patient=patient,
            status__in=ACTIVE_STATUSES,
        ).order_by('-created_at')

    def has_active_for_patient(self, patient):
        """True if the patient has at least one active consultation."""
        return self.active_for_patient(patient).exists()


class Consultation(models.Model):
    objects = ConsultationManager()
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        QUEUED = 'queued', 'Queued'
        SCHEDULED = 'scheduled', 'Scheduled'
        TRIAGED = 'triaged', 'Triaged'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        ACTIVE_FOLLOW_UP = 'active_follow_up', 'Active - Follow-up'
        CLOSED = 'closed', 'Closed'

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
    chief_complaint = models.TextField(
        blank=True,
        help_text='Doctor-reviewed final chief complaint. When empty, the patient\'s '
                  'own words (symptoms) are shown on official documents.',
    )
    medical_history = models.TextField(blank=True)
    severity_description = models.TextField(
        help_text='Self-reported severity description by the patient'
    )
    additional_notes = models.TextField(blank=True)
    queue_number = models.PositiveIntegerField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Follow-up / closure fields
    parent_consultation = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='follow_up_visits',
        help_text='Link to the original consultation if this is a follow-up'
    )
    is_original_case = models.BooleanField(
        default=True,
        help_text='True if this is the initial consultation (case file)'
    )
    follow_up_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of follow-up visits for this case'
    )
    last_follow_up_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date of the most recent follow-up'
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the consultation case was closed'
    )
    closure_notes = models.TextField(
        blank=True,
        help_text='Reason/notes for closing the consultation case'
    )
    recommended_follow_up_date = models.DateField(
        null=True,
        blank=True,
        help_text='Recommended date for the next follow-up visit'
    )

    # ── MySQL-compatible single-active-consultation backstop ──────────────────
    # MySQL cannot create conditional (partial) unique constraints, so the
    # conditional constraint in Meta below is silently skipped on MySQL. This
    # generated column is 1 while the consultation is active and NULL once it
    # reaches a closed status. The unique index on (patient, active_flag) then
    # allows at most one active consultation per patient on EVERY database
    # (MySQL, SQLite, PostgreSQL all permit multiple NULLs in a unique index,
    # so closed consultations never conflict).
    active_flag = models.GeneratedField(
        expression=models.Case(
            models.When(status__in=ACTIVE_STATUSES, then=models.Value(1)),
            default=None,
            output_field=models.IntegerField(),
        ),
        output_field=models.IntegerField(null=True, blank=True),
        db_persist=True,
    )

    def __str__(self):
        return (
            f'Consultation #{self.pk} — {self.patient.get_full_name()} '
            f'({self.get_status_display()})'
        )

    # ── Single-active-consultation rule ───────────────────────────────────────

    def validate_no_active_consultation(self):
        """
        Raise a ValidationError if this patient already has an active
        consultation. Enforced on creation via clean()/save() so the rule
        holds for every code path (views, admin, future API, shell).
        """
        if self.patient_id is None:
            return
        if Consultation.objects.filter(
            patient_id=self.patient_id,
            status__in=ACTIVE_STATUSES,
        ).exists():
            raise ValidationError(
                'This patient already has an active consultation. '
                'A new consultation cannot be created until the current '
                'one has been completed.'
            )

    def clean(self):
        if self.pk is None:
            self.validate_no_active_consultation()

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.validate_no_active_consultation()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['patient', '-created_at']),
        ]
        constraints = [
            # Database-level guarantee: a patient can never hold more than one
            # active consultation at the same time, even under concurrent
            # requests that race past the application-level checks.
            #
            # The conditional constraint below works on PostgreSQL but is a
            # no-op on MySQL (unsupported). The (patient, active_flag) unique
            # constraint covers MySQL/SQLite/PostgreSQL alike — see the
            # active_flag generated column above.
            models.UniqueConstraint(
                fields=['patient'],
                condition=Q(status__in=ACTIVE_STATUSES),
                name='unique_active_consultation_per_patient',
            ),
            models.UniqueConstraint(
                fields=['patient', 'active_flag'],
                name='unique_active_consultation_per_patient_mysql',
            ),
        ]

class FollowUpProgress(models.Model):
    """
    Stores each follow-up visit's clinical data, linked to the original consultation.
    This avoids duplicating entire consultation records.
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='progress_entries',
        help_text='The original consultation case this follow-up belongs to'
    )
    visit_number = models.PositiveIntegerField(
        help_text='Sequential number of this follow-up visit (1, 2, 3...)'
    )
    # Clinical data for this follow-up visit
    symptoms = models.TextField(
        help_text='Current symptoms reported during this follow-up'
    )
    assessment = models.TextField(
        blank=True,
        help_text='Doctor assessment for this visit'
    )
    treatment_notes = models.TextField(
        blank=True,
        help_text='Treatment administered or adjusted during this visit'
    )
    recommendations = models.TextField(
        blank=True,
        help_text='Recommendations for the patient after this visit'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes specific to this follow-up visit'
    )
    # Doctor who conducted this follow-up
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='follow_up_visits_conducted'
    )
    # Status of this specific follow-up
    FOLLOW_UP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    follow_up_status = models.CharField(
        max_length=20,
        choices=FOLLOW_UP_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    requires_follow_up = models.BooleanField(
        default=False,
        help_text='Whether another follow-up is needed after this visit'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Follow-up Progress Entry'
        verbose_name_plural = 'Follow-up Progress Entries'
        ordering = ['consultation', '-visit_number']
        unique_together = ['consultation', 'visit_number']
        indexes = [
            models.Index(fields=['consultation', '-visit_number']),
            models.Index(fields=['follow_up_status', '-created_at']),
        ]

    def __str__(self):
        return f'Follow-up #{self.visit_number} — Consultation #{self.consultation_id}'


class Triage(models.Model):
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='triages',
    )

    follow_up_progress = models.ForeignKey(
        FollowUpProgress,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='triages',
        help_text='Link to specific follow-up visit if applicable'
    )
    triaged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='triages_performed',
        verbose_name='Triaged by',
    )
    blood_pressure = models.CharField(max_length=20, help_text='e.g. 120/80')
    temperature = models.DecimalField(
        max_digits=5, decimal_places=2, help_text='Degrees Celsius'
    )
    pulse_rate = models.PositiveIntegerField(help_text='BPM')
    respiratory_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Respiratory rate (breaths per minute)'
    )
    oxygen_saturation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Oxygen saturation (SpO2) percentage (e.g. 98.50)'
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Weight in kilograms (e.g. 65.50)'
    )
    notes = models.TextField(blank=True)
    triaged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Triage #{self.pk} — Consultation #{self.consultation_id}'

    class Meta:
        verbose_name = 'Triage'
        verbose_name_plural = 'Triages'


class FollowUpRequest(models.Model):
    """
    A queue entry created when a patient requests a follow-up visit
    for a consultation marked as ACTIVE_FOLLOW_UP by the doctor.
    This is processed by front desk like a regular consultation queue entry.
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='follow_up_requests',
        help_text='The original consultation case this follow-up request belongs to'
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='follow_up_requests',
    )
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    request_status = models.CharField(
        max_length=20,
        choices=REQUEST_STATUS_CHOICES,
        default='pending',
        db_index=True,
    )
    queue_number = models.PositiveIntegerField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Follow-up Request'
        verbose_name_plural = 'Follow-up Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_status', '-created_at']),
            models.Index(fields=['consultation', '-created_at']),
        ]

    def __str__(self):
        return f'Follow-up Request #{self.pk} — Consultation #{self.consultation_id}'

class Prescription(models.Model):
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='prescriptions',
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

    follow_up_progress = models.ForeignKey(
        FollowUpProgress,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prescriptions',
        help_text='Link to specific follow-up visit if applicable'
    )

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


class CommonDiagnosis(models.Model):
    """Predefined list of common diagnoses for the clinic."""
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=100, blank=True, help_text='e.g. Respiratory, Musculoskeletal, etc.')

    class Meta:
        verbose_name = 'Common Diagnosis'
        verbose_name_plural = 'Common Diagnoses'
        ordering = ['name']

    def __str__(self):
        return self.name

