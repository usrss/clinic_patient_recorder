from django.db import models


class SiteSettings(models.Model):
    """Global site-wide settings displayed across pages."""

    site_name = models.CharField(
        max_length=100,
        default="Clinic Recorder",
        help_text="Brand name shown in the navbar and footer.",
    )
    site_title = models.CharField(
        max_length=200,
        default="Clinic Recorder — NORSU Medical Dental Clinic",
        help_text="Browser tab title for the home page.",
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Enforce singleton — only one row allowed
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ── Hero ──────────────────────────────────────────────────────────────────────

class HeroContent(models.Model):
    """Controls every piece of text and CTA in the hero section."""

    badge_text = models.CharField(
        max_length=120,
        default="NORSU — Medical Dental Clinic",
        help_text="Small badge above the headline (e.g. 'NORSU — Medical Dental Clinic').",
    )
    headline_plain = models.CharField(
        max_length=120,
        default="Your Health,",
        help_text="First line of the hero headline (plain colour).",
    )
    headline_accent = models.CharField(
        max_length=120,
        default="Digitally Managed",
        help_text="Second line of the hero headline (gradient colour).",
    )
    description = models.TextField(
        default=(
            "A seamless consultation management system for students, staff, and faculty. "
            "From triage to prescription — all in one place."
        ),
        help_text="Short paragraph below the headline.",
    )
    cta_primary_label = models.CharField(
        max_length=60,
        default="Sign In",
        help_text="Label for the primary CTA button (links to login).",
    )
    cta_secondary_label = models.CharField(
        max_length=60,
        default="Explore Features",
        help_text="Label for the secondary CTA button (scrolls to #features).",
    )

    class Meta:
        verbose_name = "Hero Content"
        verbose_name_plural = "Hero Content"

    def __str__(self):
        return f"{self.headline_plain} {self.headline_accent}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HeroStat(models.Model):
    """Individual stat items shown in the hero section (e.g. '10k+ Records')."""

    value = models.CharField(max_length=20, help_text="e.g. '10k+', '24/7', '4+'")
    label = models.CharField(max_length=60, help_text="e.g. 'Records', 'Access', 'Clinics'")
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order (ascending).")

    class Meta:
        verbose_name = "Hero Stat"
        verbose_name_plural = "Hero Stats"
        ordering = ["order"]

    def __str__(self):
        return f"{self.value} — {self.label}"


# ── Features ──────────────────────────────────────────────────────────────────

class FeatureCard(models.Model):
    """A card in the Features section."""

    title = models.CharField(max_length=80)
    description = models.TextField(help_text="Short description shown on the card.")
    tag = models.CharField(
        max_length=40,
        default="Core",
        help_text="Small pill tag (e.g. 'Records', 'Workflow', 'Analytics').",
    )
    icon = models.CharField(
        max_length=60,
        default="fa-circle",
        help_text="Font Awesome class without 'fa-' prefix is fine, but store full class e.g. 'fa-users'.",
    )
    icon_bg = models.CharField(
        max_length=30,
        default="#eff6ff",
        help_text="Icon background colour (hex or CSS colour).",
    )
    icon_color = models.CharField(
        max_length=30,
        default="#2563eb",
        help_text="Icon foreground colour (hex or CSS colour).",
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Feature Card"
        verbose_name_plural = "Feature Cards"
        ordering = ["order"]

    def __str__(self):
        return self.title


# ── Stats Strip ───────────────────────────────────────────────────────────────

class StatStrip(models.Model):
    """Full-width coloured stats band between Features and About."""

    value = models.CharField(max_length=20, help_text="e.g. '10k+', '50+'")
    label = models.CharField(max_length=60, help_text="e.g. 'Patient Records'")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Stats Strip Item"
        verbose_name_plural = "Stats Strip"
        ordering = ["order"]

    def __str__(self):
        return f"{self.value} — {self.label}"


# ── About ─────────────────────────────────────────────────────────────────────

class AboutContent(models.Model):
    """Controls the text block in the About section."""

    badge_text = models.CharField(max_length=80, default="About")
    headline = models.CharField(max_length=140, default="NORSU Medical Dental Clinic")
    description_1 = models.TextField(
        default=(
            "Committed to providing quality, accessible healthcare services to the "
            "entire university community — students, faculty, staff, and dependents."
        )
    )
    description_2 = models.TextField(
        default=(
            "Our digital system streamlines the patient experience — from registration "
            "and triage to doctor consultation, prescription dispensing, and follow-up care."
        )
    )

    class Meta:
        verbose_name = "About Content"
        verbose_name_plural = "About Content"

    def __str__(self):
        return self.headline

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AboutPill(models.Model):
    """Small pill tags in the About section."""

    label = models.CharField(max_length=60)
    icon = models.CharField(max_length=60, default="fa-check", help_text="Font Awesome class e.g. 'fa-shield-halved'")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "About Pill"
        verbose_name_plural = "About Pills"
        ordering = ["order"]

    def __str__(self):
        return self.label


class AboutCard(models.Model):
    """Grid cards on the right side of the About section."""

    title = models.CharField(max_length=80, help_text="e.g. 'Students'")
    subtitle = models.CharField(max_length=120, help_text="e.g. 'Primary health care'")
    icon = models.CharField(max_length=60, default="fa-user", help_text="Font Awesome class.")
    icon_color = models.CharField(max_length=30, default="#2563eb")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "About Card"
        verbose_name_plural = "About Cards"
        ordering = ["order"]

    def __str__(self):
        return self.title


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactContent(models.Model):
    """Badge / headline / subtext for the Contact section."""

    badge_text = models.CharField(max_length=80, default="Contact")
    headline = models.CharField(max_length=140, default="Get in Touch")
    subtext = models.CharField(
        max_length=220,
        default="Have questions or need assistance? Reach out to the NORSU Medical Dental Clinic.",
    )

    class Meta:
        verbose_name = "Contact Section Header"
        verbose_name_plural = "Contact Section Header"

    def __str__(self):
        return self.headline

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ContactItem(models.Model):
    """Individual contact info cards."""

    title = models.CharField(max_length=80, help_text="e.g. 'Location', 'Hours', 'Email'")
    detail = models.TextField(help_text="Contact detail text shown on the card.")
    icon = models.CharField(max_length=60, default="fa-map-marker-alt", help_text="Font Awesome class.")
    icon_bg = models.CharField(max_length=30, default="#eff6ff")
    icon_color = models.CharField(max_length=30, default="#2563eb")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Contact Item"
        verbose_name_plural = "Contact Items"
        ordering = ["order"]

    def __str__(self):
        return self.title


# ── Features section header ───────────────────────────────────────────────────

class FeaturesContent(models.Model):
    """Badge / headline / subtext for the Features section."""

    badge_text = models.CharField(max_length=80, default="Features")
    headline = models.CharField(max_length=140, default="Everything You Need")
    subtext = models.CharField(
        max_length=220,
        default="Powerful tools to streamline your clinic operations from registration to discharge.",
    )

    class Meta:
        verbose_name = "Features Section Header"
        verbose_name_plural = "Features Section Header"

    def __str__(self):
        return self.headline

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj