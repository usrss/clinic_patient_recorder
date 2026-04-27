from django.contrib import admin
from django.utils.html import format_html
from .models import Medicine, StockMovement


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'stock_display', 'unit', 'low_stock_indicator', 'supplier',
                    'expiry_display')
    list_filter = ('unit', 'created_at', 'updated_at')
    search_fields = ('name', 'generic_name', 'supplier')
    readonly_fields = ('created_at', 'updated_at', 'get_stock_status')

    fieldsets = (
        ('Medicine Info', {'fields': ('name', 'generic_name', 'description')}),
        ('Stock Management', {
            'fields': ('quantity', 'unit', 'low_stock_threshold', 'get_stock_status')
        }),
        ('Details', {
            'fields': ('batch_number', 'expiry_date', 'supplier', 'cost_per_unit'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def stock_display(self, obj):
        return f"{obj.quantity} {obj.get_unit_display()}"

    stock_display.short_description = 'Stock'

    def low_stock_indicator(self, obj):
        if obj.is_low_stock():
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ LOW</span>'
            )
        return format_html(
            '<span style="color: green;">✓ OK</span>'
        )

    low_stock_indicator.short_description = 'Status'

    def expiry_display(self, obj):
        if obj.expiry_date:
            from datetime import date
            if obj.expiry_date < date.today():
                return format_html(
                    '<span style="color: red; font-weight: bold;">EXPIRED: {}</span>',
                    obj.expiry_date
                )
            return str(obj.expiry_date)
        return '—'

    expiry_display.short_description = 'Expiry Date'

    def get_stock_status(self, obj):
        status = '✓ Adequate Stock'
        if obj.is_low_stock():
            status = f'⚠ LOW STOCK (below threshold: {obj.low_stock_threshold})'
        return status

    get_stock_status.short_description = 'Stock Status'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'get_movement_color', 'quantity', 'reason', 'created_by', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('medicine__name', 'reason', 'reference', 'created_by')
    readonly_fields = ('medicine', 'movement_type', 'quantity', 'reason', 'reference', 'created_at', 'created_by')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Movement Info', {
            'fields': ('medicine', 'movement_type', 'quantity', 'reason')
        }),
        ('Reference', {
            'fields': ('reference', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Date', {
            'fields': ('created_at',),
        }),
    )

    def get_movement_color(self, obj):
        if obj.movement_type == StockMovement.MovementType.IN:
            color = 'green'
            symbol = '📥'
        elif obj.movement_type == StockMovement.MovementType.OUT:
            color = 'blue'
            symbol = '📤'
        elif obj.movement_type == StockMovement.MovementType.EXPIRED:
            color = 'red'
            symbol = '❌'
        else:
            color = 'orange'
            symbol = '⚙️'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            symbol,
            obj.get_movement_type_display()
        )

    get_movement_color.short_description = 'Type'

    def has_add_permission(self, request):
        # Prevent manual creation (should only be created by system)
        return False

    def has_delete_permission(self, request, obj=None):
        # Audit trail should be immutable
        return False