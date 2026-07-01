from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only admin for viewing audit logs."""

    list_display = [
        'timestamp', 'user_name', 'user_role', 'action',
        'module', 'description_short', 'status',
    ]
    list_filter = [
        'action', 'module', 'user_role', 'status', 'timestamp',
    ]
    search_fields = [
        'user_name', 'description', 'object_repr', 'object_id',
        'user__username', 'user__first_name', 'user__last_name',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    # ── Read-only ───────────────────────────────────────────────────
    readonly_fields = [
        'user', 'user_role', 'user_name', 'action', 'module',
        'description', 'object_model', 'object_id', 'object_repr',
        'changes_before', 'changes_after', 'ip_address', 'status',
        'timestamp',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def description_short(self, obj):
        return obj.description[:80] + '…' if len(obj.description) > 80 else obj.description
    description_short.short_description = 'Description'
