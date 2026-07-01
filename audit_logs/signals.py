"""
Signal handlers for automatic audit logging of model-level events.

Currently, the primary audit-logging strategy is *explicit calls* from
views (via ``audit_logs.services``) because view-level logging captures
richer context (IP address, description, request metadata).

These signals provide a safety net for CREATE / UPDATE / DELETE actions
that may be performed outside of views (e.g. via the Django admin,
management commands, or the shell).

For full-context logging (IP address, descriptions), use the service
functions directly in your views.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import AuditLog
from .services import log_audit_entry


# ── Signals are connected via AppConfig.ready() in apps.py ────────────
# Individual model signals are registered below as needed.
# We use a whitelist approach — only explicitly listed models are tracked.
#
# To add a model, register a signal handler below with the model's
# dotted path and a suitable module mapping.

# Mapping of model label → module for auto-logging
# Add models here to enable signal-based automatic audit logging.
# Note: View-level logging (using audit_logs.services) provides richer
# context (IP address, user descriptions). These signals are a safety
# net for operations outside views (admin, management commands).
_MODEL_MODULE_MAP = {
    'patients.Patient': 'Patients',
    'consultations.Consultation': 'Consultations',
    'consultations.Prescription': 'Consultations',
    'certificates.MedicalCertificate': 'Medical Certificates',
    'accounts.User': 'User Management',
}


def _get_model_label(instance):
    """Return the dotted app_label.ModelName for an instance."""
    meta = instance._meta
    return f'{meta.app_label}.{meta.model_name}'


# ── Generic catch-all signal (only fires for whitelisted models) ─────

@receiver(post_save)
def audit_log_post_save(sender, instance, created, **kwargs):
    """Log model CREATE / UPDATE events for whitelisted models."""
    model_label = _get_model_label(instance)
    module = _MODEL_MODULE_MAP.get(model_label)
    if module is None:
        return  # Not a whitelisted model — skip

    action = 'CREATE' if created else 'UPDATE'
    changes = _extract_model_data(instance)

    log_audit_entry(
        user=None,  # No request context — view-level logging is preferred
        action=action,
        module=module,
        description=f'{action} {model_label} #{instance.pk}',
        object_model=model_label,
        object_id=str(instance.pk),
        object_repr=str(instance),
        changes_after=changes if action == 'CREATE' else None,
    )


@receiver(post_delete)
def audit_log_post_delete(sender, instance, **kwargs):
    """Log model DELETE events for whitelisted models."""
    model_label = _get_model_label(instance)
    module = _MODEL_MODULE_MAP.get(model_label)
    if module is None:
        return

    changes = _extract_model_data(instance)
    log_audit_entry(
        user=None,
        action='DELETE',
        module=module,
        description=f'DELETE {model_label} #{instance.pk}',
        object_model=model_label,
        object_id=str(instance.pk),
        object_repr=str(instance),
        changes_before=changes,
    )


def _extract_model_data(instance):
    """Extract field values from a model instance as a JSON-safe dict."""
    data = {}
    try:
        for field in instance._meta.fields:
            name = field.attname
            value = getattr(instance, name, None)
            if value is not None:
                # Serialize dates / datetimes
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                elif hasattr(value, 'pk'):
                    value = str(value)
                data[name] = str(value)[:500] if not isinstance(value, (bool, int, float)) else value
    except Exception:
        pass
    return data
