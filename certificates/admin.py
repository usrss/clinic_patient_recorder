from django.contrib import admin
from .models import MedicalCertificate, CertificateAuditLog


class CertificateAuditLogInline(admin.TabularInline):
    model = CertificateAuditLog
    extra = 0
    readonly_fields = ['user', 'action', 'details', 'timestamp']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MedicalCertificate)
class MedicalCertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'patient_name', 'certificate_type', 'status', 'doctor', 'issued_at']
    list_filter = ['status', 'certificate_type', 'issued_at']
    search_fields = ['certificate_number', 'consultation__patient__first_name', 'consultation__patient__last_name']
    readonly_fields = ['certificate_number', 'diagnosis_snapshot', 'issued_at', 'created_at', 'updated_at']
    inlines = [CertificateAuditLogInline]

    def patient_name(self, obj):
        return obj.patient_name
    patient_name.short_description = 'Patient'


@admin.register(CertificateAuditLog)
class CertificateAuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'certificate', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['certificate', 'user', 'action', 'details', 'timestamp']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
