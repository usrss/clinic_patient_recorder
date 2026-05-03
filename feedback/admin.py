from django.contrib import admin
from .models import ConsultationFeedback


@admin.register(ConsultationFeedback)
class ConsultationFeedbackAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'rating', 'created_at')
    search_fields = ('consultation__patient__first_name', 'consultation__patient__last_name')
    list_filter = ('rating', 'created_at')