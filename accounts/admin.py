from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect

from .models import User, StudentProfile
from .forms import StudentBulkUploadForm
from .utils import import_students_from_excel, StudentImportError


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name', 'role', 'is_active', 'email', 'force_password_change')
    list_filter = ('role', 'is_active', 'force_password_change', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = (
        ('Account Info', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'force_password_change')}),
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
            path('import-students/', self.admin_site.admin_view(self.import_students_view),
                 name='accounts_user_import_students'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_url'] = '/admin/accounts/user/import-students/'
        return super().changelist_view(request, extra_context)

    def import_students_view(self, request):
        if request.method == 'POST':
            form = StudentBulkUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    results = import_students_from_excel(request.FILES['file'])
                    messages.success(
                        request,
                        f'✓ Import complete: {results["created"]} created, {results["skipped"]} skipped'
                    )
                    for warning in results['warnings']:
                        messages.warning(request, warning)
                    for error in results['errors']:
                        messages.error(request, error)
                    return HttpResponseRedirect(request.path)
                except StudentImportError as e:
                    messages.error(request, f'Import failed: {str(e)}')
                except Exception as e:
                    messages.error(request, f'Unexpected error: {str(e)}')
        else:
            form = StudentBulkUploadForm()

        context = {
            'form': form,
            'title': 'Import Students from Excel',
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/accounts/import_students.html', context)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_user_name', 'age', 'gender', 'college', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Link', {'fields': ('user', 'student_id')}),
        ('Personal Info', {'fields': ('middle_name', 'age', 'gender', 'college')}),
        ('Dates', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ('student_id',)

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_user_name.short_description = 'User'