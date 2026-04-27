from django.contrib import admin
from .models import Patient, PatientProfile


class PatientProfileInline(admin.StackedInline):
    model = PatientProfile
    extra = 0
    can_delete = False
    readonly_fields = ('updated_at',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'get_full_name', 'sex', 'college', 'department',
                    'position', 'is_active', 'created_at')
    list_filter = ('sex', 'is_active', 'college', 'created_at')
    search_fields = ('patient_id', 'first_name', 'last_name', 'middle_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PatientProfileInline]
    ordering = ('last_name', 'first_name')

    fieldsets = (
        ('Identity', {'fields': ('patient_id', 'first_name', 'middle_name', 'last_name', 'sex')}),
        ('Classification', {'fields': ('college', 'department', 'position')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'