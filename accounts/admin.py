from django.contrib import admin
from .models import User


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