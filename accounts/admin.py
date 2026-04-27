from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect

from .models import User
from .forms import PatientBulkUploadForm
from .utils import import_patients_from_excel, PatientImportError


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name', 'role', 'is_active',
                    'email', 'force_password_change')
    list_filter = ('role', 'is_active', 'force_password_change', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = (
        ('Account Info', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'force_password_change')
        }),
        ('Dates', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('role', 'username')

    def get_full_name(self, obj):
        return obj.get_full_name() or '—'
    get_full_name.short_description = 'Full Name'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-patients/', self.admin_site.admin_view(self.import_patients_view),
                 name='accounts_user_import_patients'),
        ]
        return custom_urls + urls

    def import_patients_view(self, request):
        if request.method == 'POST':
            form = PatientBulkUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    results = import_patients_from_excel(request.FILES['file'])
                    messages.success(
                        request,
                        f'✓ Import complete: {results["created"]} created, {results["skipped"]} skipped'
                    )
                    for w in results['warnings']:
                        messages.warning(request, w)
                    for e in results['errors']:
                        messages.error(request, e)
                    return HttpResponseRedirect(request.path)
                except PatientImportError as e:
                    messages.error(request, f'Import failed: {str(e)}')
                except Exception as e:
                    messages.error(request, f'Unexpected error: {str(e)}')
        else:
            form = PatientBulkUploadForm()

        context = {
            'form': form,
            'title': 'Import Patients from Excel',
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/accounts/import_patients.html', context)