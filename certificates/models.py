from django.db import models
from django.conf import settings


class MedicalCertificate(models.Model):
    """Medical certificate issued after a consultation."""

    class CertificateType(models.TextChoices):
        STANDARD = 'standard', 'Medical Certificate'
        FIT_TO_PLAY = 'fit_to_play', 'Fit-to-Play Certificate'
        FIT_TO_WORK = 'fit_to_work', 'Fit-to-Work Certificate'
        DENTAL = 'dental', 'Dental Certificate'

    consultation = models.OneToOneField(
        'consultations.Consultation',
        on_delete=models.CASCADE,
        related_name='certificate',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certificates_issued',
    )
    certificate_type = models.CharField(
        max_length=20,
        choices=CertificateType.choices,
        default=CertificateType.STANDARD,
    )
    diagnosis = models.TextField(help_text='Diagnosis for the certificate')
    rest_from = models.DateField(null=True, blank=True, help_text='Rest period start date')
    rest_to = models.DateField(null=True, blank=True, help_text='Rest period end date')
    remarks = models.TextField(blank=True, help_text='Additional remarks or restrictions')
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']
        verbose_name = 'Medical Certificate'
        verbose_name_plural = 'Medical Certificates'

    def __str__(self):
        return f'{self.get_certificate_type_display()} #{self.pk} — {self.consultation.patient.get_full_name()}'