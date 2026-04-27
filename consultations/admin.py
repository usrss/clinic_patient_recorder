from django.contrib import admin
from .models import Consultation, Triage, Prescription, PrescriptionItem


class TriageInline(admin.StackedInline):
    model = Triage
    extra = 0
    readonly_fields = ('triaged_at',)
    can_delete = False


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0
    readonly_fields = ('medicine', 'quantity', 'instructions')
    can_delete = False


class PrescriptionInline(admin.StackedInline):
    model = Prescription
    extra = 0
    readonly_fields = ('prescribed_at',)
    can_delete = False


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'status', 'queue_number', 'scheduled_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name', 'symptoms')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TriageInline, PrescriptionInline]
    ordering = ('-created_at',)


@admin.register(Triage)
class TriageAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'nurse', 'urgency', 'temperature', 'pulse_rate', 'triaged_at')
    list_filter = ('urgency', 'triaged_at')
    readonly_fields = ('triaged_at',)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'doctor', 'prescribed_at')
    list_filter = ('prescribed_at',)
    readonly_fields = ('prescribed_at',)
    inlines = [PrescriptionItemInline]