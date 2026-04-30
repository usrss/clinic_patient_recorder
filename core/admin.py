from django.contrib import admin
from django.utils.html import format_html

from .models import (
    SiteSettings,
    HeroContent,
    HeroStat,
    FeaturesContent,
    FeatureCard,
    StatStrip,
    AboutContent,
    AboutPill,
    AboutCard,
    ContactContent,
    ContactItem,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def color_swatch(hex_color):
    """Render a small colour swatch next to a hex value."""
    return format_html(
        '<span style="display:inline-flex;align-items:center;gap:6px;">'
        '<span style="width:16px;height:16px;border-radius:4px;'
        'background:{0};border:1px solid rgba(0,0,0,.12);display:inline-block;"></span>'
        '{0}</span>',
        hex_color,
    )


# ── Site Settings ─────────────────────────────────────────────────────────────

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Branding", {
            "fields": ("site_name", "site_title"),
            "description": (
                "Global branding shown in the navbar, footer, and browser tab. "
                "Only one row is allowed — saving always updates the same record."
            ),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ── Hero ──────────────────────────────────────────────────────────────────────

@admin.register(HeroContent)
class HeroContentAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Badge", {"fields": ("badge_text",)}),
        ("Headline", {
            "fields": ("headline_plain", "headline_accent"),
            "description": "The two lines of the main headline. The accent line renders in a gradient.",
        }),
        ("Body & CTA", {
            "fields": ("description", "cta_primary_label", "cta_secondary_label"),
        }),
    )

    def has_add_permission(self, request):
        return not HeroContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeroStat)
class HeroStatAdmin(admin.ModelAdmin):
    list_display = ("value", "label", "order")
    list_editable = ("label", "order")
    ordering = ("order",)


# ── Features ──────────────────────────────────────────────────────────────────

@admin.register(FeaturesContent)
class FeaturesContentAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Section Header", {
            "fields": ("badge_text", "headline", "subtext"),
            "description": "Text shown above the feature cards grid.",
        }),
    )

    def has_add_permission(self, request):
        return not FeaturesContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FeatureCard)
class FeatureCardAdmin(admin.ModelAdmin):
    list_display = ("title", "tag", "icon_preview", "icon_color_swatch", "icon_bg_swatch", "order", "is_active")
    list_editable = ("tag", "order", "is_active")
    list_filter = ("is_active",)
    ordering = ("order",)
    fieldsets = (
        ("Content", {"fields": ("title", "description", "tag", "order", "is_active")}),
        ("Icon & Colours", {
            "fields": ("icon", "icon_color", "icon_bg"),
            "description": (
                "Enter a Font Awesome class (e.g. <code>fa-users</code>). "
                "Use hex colour values for icon_color and icon_bg."
            ),
        }),
    )

    @admin.display(description="Icon")
    def icon_preview(self, obj):
        return format_html(
            '<span style="display:inline-flex;align-items:center;justify-content:center;'
            'width:32px;height:32px;border-radius:8px;background:{};color:{};">'
            '<i class="fas {}"></i></span>',
            obj.icon_bg, obj.icon_color, obj.icon,
        )

    @admin.display(description="Icon Colour")
    def icon_color_swatch(self, obj):
        return color_swatch(obj.icon_color)

    @admin.display(description="BG Colour")
    def icon_bg_swatch(self, obj):
        return color_swatch(obj.icon_bg)


# ── Stats Strip ───────────────────────────────────────────────────────────────

@admin.register(StatStrip)
class StatStripAdmin(admin.ModelAdmin):
    list_display = ("value", "label", "order")
    list_editable = ("label", "order")
    ordering = ("order",)


# ── About ─────────────────────────────────────────────────────────────────────

@admin.register(AboutContent)
class AboutContentAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Badge & Headline", {"fields": ("badge_text", "headline")}),
        ("Body Copy", {"fields": ("description_1", "description_2")}),
    )

    def has_add_permission(self, request):
        return not AboutContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AboutPill)
class AboutPillAdmin(admin.ModelAdmin):
    list_display = ("label", "icon", "order")
    list_editable = ("icon", "order")
    ordering = ("order",)


@admin.register(AboutCard)
class AboutCardAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle", "icon", "icon_color_swatch", "order")
    list_editable = ("subtitle", "icon", "order")
    ordering = ("order",)

    @admin.display(description="Colour")
    def icon_color_swatch(self, obj):
        return color_swatch(obj.icon_color)


# ── Contact ───────────────────────────────────────────────────────────────────

@admin.register(ContactContent)
class ContactContentAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Section Header", {"fields": ("badge_text", "headline", "subtext")}),
    )

    def has_add_permission(self, request):
        return not ContactContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContactItem)
class ContactItemAdmin(admin.ModelAdmin):
    list_display = ("title", "detail_short", "icon", "icon_color_swatch", "icon_bg_swatch", "order")
    list_editable = ("icon", "order")
    ordering = ("order",)
    fieldsets = (
        ("Content", {"fields": ("title", "detail", "order")}),
        ("Icon & Colours", {"fields": ("icon", "icon_color", "icon_bg")}),
    )

    @admin.display(description="Detail")
    def detail_short(self, obj):
        return obj.detail[:60] + ("…" if len(obj.detail) > 60 else "")

    @admin.display(description="Icon Colour")
    def icon_color_swatch(self, obj):
        return color_swatch(obj.icon_color)

    @admin.display(description="BG Colour")
    def icon_bg_swatch(self, obj):
        return color_swatch(obj.icon_bg)