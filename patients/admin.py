from django.contrib import admin
from .models import Patient, PatientProfile, AcademicYearSettings


class PatientProfileInline(admin.StackedInline):
    model = PatientProfile
    extra = 0
    can_delete = False
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'birthday', 'address', 'blood_type',
                'known_allergies', 'existing_conditions',
            )
        }),
        ('Demographics', {
            'fields': (
                'religion', 'civil_status', 'year_level',
            )
        }),
        ('Physical Information', {
            'fields': (
                'height_cm', 'weight_kg',
            )
        }),
        ('Family & Past Medical History', {
            'fields': (
                'hypertension', 'diabetes', 'asthma',
                'cardiac_problems', 'arthritis', 'other_conditions',
            )
        }),
        ('Immunization Records', {
            'fields': (
                'bcg', 'dpt', 'opv', 'hepatitis_b',
                'measles', 'tt', 'immunization_others',
            )
        }),
        ('Medical Background', {
            'fields': (
                'current_medications', 'vices',
                'previous_illnesses', 'previous_hospitalizations',
            )
        }),
        ('Profile Status', {
            'fields': (
                'profile_completed', 'updated_at',
            )
        }),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'get_full_name', 'sex', 'college', 'department',
                    'position', 'is_active', 'is_archived', 'expected_graduation_year', 'created_at')
    list_filter = ('sex', 'is_active', 'is_archived', 'college', 'created_at')
    search_fields = ('patient_id', 'first_name', 'last_name', 'middle_name')
    readonly_fields = ('created_at', 'updated_at', 'archived_at')
    inlines = [PatientProfileInline]
    ordering = ('last_name', 'first_name')

    fieldsets = (
        ('Identity', {'fields': ('patient_id', 'first_name', 'middle_name', 'last_name', 'sex')}),
        ('Classification', {'fields': ('college', 'department', 'position')}),
        ('Academic', {'fields': ('expected_graduation_year',)}),
        ('Archiving', {'fields': ('is_archived', 'archived_at', 'archived_reason'), 'classes': ('collapse',)}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(AcademicYearSettings)
class AcademicYearSettingsAdmin(admin.ModelAdmin):
    list_display = ('academic_year_end', 'archive_after_months', 'updated_by', 'updated_at')
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        # Enforce singleton — only allow add if no rows exist
        return not AcademicYearSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent accidental deletion of the singleton