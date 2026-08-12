import re
from datetime import date

import bleach
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


def strip_doctor_honorific(name):
    """
    Remove a leading 'Dr.' / 'Dr' / 'Dra.' honorific from a doctor's name so
    certificates display only the name (e.g. "Dr. Juan Dela Cruz" → "Juan Dela Cruz").
    """
    if not name:
        return name
    return re.sub(r'^\s*Dr[ra]?\.?\s+', '', name, flags=re.IGNORECASE).strip() or name


class MedicalCertificate(models.Model):
    """
    Medical certificate issued after a consultation.
    Supports a draft→issued→voided lifecycle.
    """

    class CertificateType(models.TextChoices):
        ABSENCES = 'absences', 'Medical Certificate — Absences (Classes/Work)'
        OJT = 'ojt', 'Medical Certificate — OJT'
        ACTIVITIES = 'activities', 'Medical Certificate — Activities/Training/Seminars'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ISSUED = 'issued', 'Issued'
        VOIDED = 'voided', 'Voided'

    class FitnessStatus(models.TextChoices):
        CLEARED = 'cleared', 'Cleared'
        NOT_CLEARED = 'not_cleared', 'Not Cleared'

    class WorkAssessment(models.TextChoices):
        FIT_TO_RETURN = 'fit_to_return', 'Physically fit to return to work'
        FIT_WITH_RESTRICTIONS = 'fit_with_restrictions', 'Fit with restrictions'

    # ── Relationships ─────────────────────────────────────────────────────
    consultation = models.ForeignKey(
        'consultations.Consultation',
        on_delete=models.CASCADE,
        related_name='certificates',
        help_text='The consultation this certificate belongs to',
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='certificates',
        null=True,
        blank=True,
        help_text='Direct patient reference (denormalized for history)',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certificates_issued',
    )

    # ── Identity ──────────────────────────────────────────────────────────
    certificate_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text='Format: MC-YYYY-XXXXXX (assigned on issue)',
    )
    certificate_type = models.CharField(
        max_length=20,
        choices=CertificateType.choices,
        default=CertificateType.ABSENCES,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    # ── Clinical content (working fields, editable while DRAFT) ───────────
    diagnosis = models.TextField(help_text='Diagnosis for the certificate')
    diagnosis_snapshot = models.TextField(
        blank=True,
        help_text='Frozen diagnosis at time of issuance (historical accuracy)',
    )
    rest_from = models.DateField(null=True, blank=True, help_text='Rest period start date')
    rest_to = models.DateField(null=True, blank=True, help_text='Rest period end date')
    remarks = models.TextField(blank=True, help_text='Additional remarks or restrictions')
    place = models.CharField(
        max_length=255,
        blank=True,
        default='Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines',
        help_text='Clinic location / place of issuance',
    )

    # ── Fit-to-Work specific ──────────────────────────────────────────────
    work_assessment = models.CharField(
        max_length=50,
        blank=True,
        choices=WorkAssessment.choices,
        help_text='Fit-to-Work assessment result',
    )
    return_date = models.DateField(null=True, blank=True, help_text='Fit-to-Work: recommended return date')
    restrictions = models.TextField(blank=True, help_text='Work restrictions if applicable')

    # ── Fit-to-Play specific ──────────────────────────────────────────────
    activity_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Fit-to-Play: name of the sports/activity',
    )
    fitness_status = models.CharField(
        max_length=20,
        blank=True,
        choices=FitnessStatus.choices,
        help_text='Fit-to-Play: clearance result',
    )

    # ── Rendered-text snapshot ────────────────────────────────────────────
    rendered_text_snapshot = models.JSONField(
        null=True, blank=True,
        help_text='Resolved body text at time of issuance (single string)',
    )

    # ── Audit ─────────────────────────────────────────────────────────────
    issued_at = models.DateTimeField(null=True, blank=True, help_text='When the certificate was issued')
    template_version = models.CharField(max_length=10, default='3.0', help_text='Print template version used')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Medical Certificate'
        verbose_name_plural = 'Medical Certificates'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['certificate_number']),
        ]

    def __str__(self):
        return f'{self.get_certificate_type_display()} #{self.certificate_number or self.pk} — {self.patient_name}'

    @property
    def patient_name(self):
        if self.patient:
            return self.patient.get_full_name()
        if self.consultation:
            return self.consultation.patient.get_full_name()
        return 'Unknown'

    def generate_certificate_number(self):
        """Generate the next sequential certificate number for the current year."""
        year = timezone.localtime(timezone.now()).year
        prefix = f'MC-{year}-'
        last_cert = MedicalCertificate.objects.filter(
            certificate_number__startswith=prefix,
        ).order_by('-certificate_number').first()
        if last_cert:
            last_num = int(last_cert.certificate_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f'{prefix}{new_num:06d}'

    def _resolve_placeholder(self, placeholder, field_value, default=''):
        """Resolve a single placeholder value."""
        if field_value is None or field_value == '':
            return default
        if isinstance(field_value, date):
            return field_value.strftime('%B %d, %Y')
        return str(field_value)

    def _build_placeholder_map(self):
        """Build the dict of {placeholder: value} for this certificate.

        Used by both CertificateTemplateText prose rendering and
        .docx template generation (docxtpl). Keys use {{ jinja }} style.
        """
        patient = self.consultation.patient
        profile = getattr(patient, 'profile', None)

        college_name = patient.college.name if patient.college else ''
        college_abbr = patient.college.abbreviation if patient.college else ''
        year_level = profile.year_level if profile and profile.year_level else ''
        course_name = patient.course.name if patient.course else ''

        # Build college_info: include course if available, otherwise year_level
        if college_name:
            academic_detail = course_name or year_level
            college_info = f'from {college_name}' + (f' — {academic_detail}, ' if academic_detail else ', ')
        else:
            college_info = ''

        position = getattr(patient, 'position', '') or ''
        department = getattr(patient, 'department', '') or ''
        position_info = f'{position} — {department}, ' if position or department else ''

        # ── Doctor info ────────────────────────────────────────────────
        # The honorific ("Dr."/"Dra.") is stripped so certificates show
        # only the doctor's name.
        if self.doctor:
            doctor_name = self.doctor.get_full_name() or self.doctor.username
        else:
            doctor_name = 'Attending Physician'
        doctor_name = strip_doctor_honorific(doctor_name)

        # ── Issue date parts ───────────────────────────────────────────
        issued = self.issued_at or self.created_at
        day_num = issued.day
        month_name = issued.strftime('%B')
        year_num = issued.year

        # ── Latest triage vital signs ──────────────────────────────────
        latest_triage = self.consultation.triages.order_by('-triaged_at').first()
        temperature = str(latest_triage.temperature) if latest_triage and latest_triage.temperature else ''
        blood_pressure = latest_triage.blood_pressure if latest_triage and latest_triage.blood_pressure else ''
        pulse_rate = str(latest_triage.pulse_rate) if latest_triage and latest_triage.pulse_rate else ''
        respiratory_rate = str(latest_triage.respiratory_rate) if latest_triage and latest_triage.respiratory_rate else ''

        return {
            'patient_name': patient.get_full_name().title(),
            'age': self._resolve_placeholder('age', patient.age, '—'),
            'sex': self._resolve_placeholder('sex', patient.get_sex_display().lower(), ''),
            'college_info': college_info,
            'college': college_name,
            'college_abbr': college_abbr,
            'year_level': year_level,
            'course': course_name,
            'position_info': position_info,
            'position': position,
            'department': department,
            'exam_date': self.consultation.created_at.strftime('%B %d, %Y'),
            # Patient's complaint for official documents: the doctor-reviewed
            # chief complaint, falling back to the patient's own words (symptoms)
            # when the doctor hasn't reworded it.
            'complaints': (self.consultation.chief_complaint or self.consultation.symptoms).strip(),
            'diagnosis': self.diagnosis,
            'rest_date': self._resolve_placeholder('rest_date', self.rest_from),
            'rest_from': self._resolve_placeholder('rest_from', self.rest_from),
            'rest_to': self._resolve_placeholder('rest_to', self.rest_to),
            'return_date': self._resolve_placeholder('return_date', self.return_date),
            'activity_name': self.activity_name or '',
            'fitness_status': self.get_fitness_status_display() or '',
            'work_assessment': self.get_work_assessment_display() or '',
            'restrictions': self.restrictions or '',
            'place': self.place or '',
            # ── New keys for .docx templates ───────────────────────────
            'remarks': self.remarks or '',
            'doctor_name': doctor_name,
            'day': str(day_num),
            'month': month_name,
            'year': str(year_num),
            'temperature': temperature,
            'blood_pressure': blood_pressure,
            'pulse_rate': pulse_rate,
            'respiratory_rate': respiratory_rate,
        }

    def _resolve_text(self, text):
        """Replace {placeholders} in text with actual values from this certificate."""
        mapping = self._build_placeholder_map()
        try:
            return text.format(**mapping)
        except KeyError:
            # Fallback: replace known tokens only, leave unknown ones as-is
            for key, val in mapping.items():
                text = text.replace(f'{{{key}}}', val)
            return text

    def _compute_rendered_snapshot(self):
        """Compute and return a single body string of resolved template text."""
        ct = self.certificate_type

        # Dental inherits absences' template text
        templates = CertificateTemplateText.objects.filter(
            certificate_type=ct,
        )
        # Get the body entry (there should be one per certificate type)
        body_template = templates.filter(slot_key='body').first()
        if body_template:
            return self._resolve_text(body_template.text)

        return ''

    def issue(self, user=None):
        """Finalize the certificate from DRAFT to ISSUED.

        Uses select_for_update() within a transaction to prevent race
        conditions where two drafts for the same consultation are issued
        simultaneously. Raises ValidationError if another issued cert
        already exists for the same consultation.
        """
        with transaction.atomic():
            # Lock all certs for this consultation and check for existing issued
            existing_issued = MedicalCertificate.objects.select_for_update().filter(
                consultation=self.consultation,
                status=MedicalCertificate.Status.ISSUED,
            ).exclude(pk=self.pk).exists()

            if existing_issued:
                raise ValidationError(
                    f'Another issued certificate already exists for '
                    f'consultation #{self.consultation_id}.'
                )

            self.status = self.Status.ISSUED
            self.certificate_number = self.generate_certificate_number()
            self.diagnosis_snapshot = self.diagnosis
            self.rendered_text_snapshot = self._compute_rendered_snapshot()
            self.issued_at = timezone.now()
            self.template_version = '3.0'
            self.save(update_fields=[
                'status', 'certificate_number', 'diagnosis_snapshot',
                'rendered_text_snapshot', 'issued_at', 'template_version',
            ])
            # Log the issue action
            CertificateAuditLog.objects.create(
                certificate=self,
                user=user,
                action='issued',
                details=f'Certificate {self.certificate_number} issued',
            )

    def void(self, user=None, reason=''):
        """Void an issued certificate.

        Uses select_for_update() within a transaction to prevent race
        conditions with simultaneous issue() calls on the same certificate.
        Raises ValidationError if the certificate is not in ISSUED status
        or is already voided.
        """
        with transaction.atomic():
            # Lock this specific certificate row and re-fetch within the lock
            locked = MedicalCertificate.objects.select_for_update().get(pk=self.pk)

            if locked.status == self.Status.VOIDED:
                raise ValidationError(
                    f'Certificate #{locked.certificate_number or locked.pk} is already voided.'
                )
            if locked.status != self.Status.ISSUED:
                raise ValidationError(
                    f'Only issued certificates can be voided (current status: {locked.status}).'
                )

            # Update local instance to match locked state
            self.status = self.Status.VOIDED
            self.save(update_fields=['status'])

            CertificateAuditLog.objects.create(
                certificate=self,
                user=user,
                action='voided',
                details=reason or 'Certificate voided',
            )


class CertificateAuditLog(models.Model):
    """Audit trail for certificate lifecycle events."""
    certificate = models.ForeignKey(
        MedicalCertificate,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=20, db_index=True,
        help_text='e.g. created, issued, printed, viewed, voided')
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Certificate Audit Log'
        verbose_name_plural = 'Certificate Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.action} — Cert #{self.certificate_id} at {self.timestamp:%Y-%m-%d %H:%M}'


class CertificateTemplateText(models.Model):
    """
    Editable prose text for certificate print templates.
    Staff can modify the wording of certificate sentences without touching HTML.
    """
    certificate_type = models.CharField(
        max_length=20,
        choices=MedicalCertificate.CertificateType.choices,
    )
    slot_key = models.CharField(
        max_length=50,
        help_text='Unique identifier for this prose slot (e.g. diagnosis_statement)',
    )
    text = models.TextField(
        help_text='Prose text with {placeholder} tokens for dynamic values',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Certificate Template Text'
        verbose_name_plural = 'Certificate Template Texts'
        unique_together = ('certificate_type', 'slot_key')

    def __str__(self):
        return f'{self.get_cert_type_label()} — {self.slot_key}'

    def get_cert_type_label(self):
        return dict(MedicalCertificate.CertificateType.choices).get(self.certificate_type, self.certificate_type)

    def clean(self):
        from django.core.exceptions import ValidationError
        self.text = bleach.clean(self.text, tags=[], strip=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CertificateTemplateChangeLog(models.Model):
    """Audit trail for template text edits."""
    slot = models.ForeignKey(
        CertificateTemplateText,
        on_delete=models.CASCADE,
        related_name='change_logs',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    old_text = models.TextField(blank=True)
    new_text = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Certificate Template Change Log'
        verbose_name_plural = 'Certificate Template Change Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.slot.slot_key} changed by {self.user} at {self.timestamp:%Y-%m-%d %H:%M}'