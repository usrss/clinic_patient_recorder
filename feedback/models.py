from django.db import models
from django.conf import settings


class ConsultationFeedback(models.Model):
    consultation = models.OneToOneField(
        'consultations.Consultation',
        on_delete=models.CASCADE,
        related_name='feedback',
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')],
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultation Feedback'
        verbose_name_plural = 'Consultation Feedbacks'

    def __str__(self):
        return f'Consultation #{self.consultation_id} — {self.rating}★'