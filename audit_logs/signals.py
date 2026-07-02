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

Signals are connected to specific sender models in ``apps.py`` so that
only whitelisted models trigger these handlers — not every model save
in the project.
"""

import logging

from .services import log_audit_entry
from .middleware import get_current_user, get_current_ip

logger = logging.getLogger(__name__)


# ── Signals are connected via AppConfig.ready() in apps.py ────────────
# See audit_logs.apps.AuditLogsConfig.ready() for registration.
# Individual model signal handlers are registered below as needed.
# We use a whitelist approach — only explicitly listed models are tracked.

# Mapping of model label → module for auto-logging
# Add models here to enable signal-based automatic audit logging.
# Note: View-level logging (using audit_logs.services) provides richer
# context (IP address, user descriptions). These signals are a safety
# net for operations outside views (admin, management commands).
MODEL_MODULE_MAP = {
    'patients.Patient': 'Patients',
    'consultations.Consultation': 'Consultations',
    'consultations.Prescription': 'Consultations',
    'certificates.MedicalCertificate': 'Medical Certificates',
    'accounts.User': 'User Management',
}

# Model-specific field exclusions for sensitive data.
# Fields listed here are stripped from audit log snapshots.
_SENSITIVE_FIELD_NAMES = {
    # User model
    'password', 'last_login', 'is_superuser', 'is_staff',
    'user_permissions', 'groups', 'reset_otp', 'reset_otp_expiry',
    'failed_login_attempts', 'locked_until', 'profile_picture',
    # Patient model
    'email', 'phone', 'emergency_contact_name', 'emergency_contact_number',
    'profile_picture',
    # Generic file/image fields
    'picture', 'avatar', 'photo', 'file', 'attachment',
}


def _get_model_label(instance):
    """Return the dotted app_label.ModelName for an instance."""
    meta = instance._meta
    return f'{meta.app_label}.{meta.model_name}'


def audit_log_post_save(sender, instance, created, **kwargs):
    """Log model CREATE / UPDATE events for whitelisted models."""
    model_label = _get_model_label(instance)
    module = MODEL_MODULE_MAP.get(model_label)
    if module is None:
        return  # Not a whitelisted model — skip

    action = 'CREATE' if created else 'UPDATE'
    changes = _extract_model_data(instance)
    current_user = get_current_user()

    log_audit_entry(
        user=current_user,  # Best-effort from thread-local; None outside request context
        action=action,
        module=module,
        description=f'{action} {model_label} #{instance.pk}',
        object_model=model_label,
        object_id=str(instance.pk),
        object_repr=str(instance),
        changes_after=changes if action == 'CREATE' else None,
        ip_address=get_current_ip(),
    )


def audit_log_post_delete(sender, instance, **kwargs):
    """Log model DELETE events for whitelisted models."""
    model_label = _get_model_label(instance)
    module = MODEL_MODULE_MAP.get(model_label)
    if module is None:
        return

    changes = _extract_model_data(instance)
    current_user = get_current_user()

    log_audit_entry(
        user=current_user,
        action='DELETE',
        module=module,
        description=f'DELETE {model_label} #{instance.pk}',
        object_model=model_label,
        object_id=str(instance.pk),
        object_repr=str(instance),
        changes_before=changes,
        ip_address=get_current_ip(),
    )


def _extract_model_data(instance):
    """
    Extract field values from a model instance as a JSON-safe dict.

    Excludes sensitive fields (passwords, tokens, file uploads, etc.)
    as defined in ``_SENSITIVE_FIELD_NAMES``.

    Returns a dict of field_name → serialized value.
    """
    data = {}
    try:
        for field in instance._meta.fields:
            name = field.attname
            # Skip sensitive / internal fields
            if name in _SENSITIVE_FIELD_NAMES:
                continue
            if name.endswith('_ptr_id'):  # Skip multi-table inheritance link
                continue

            value = getattr(instance, name, None)
            if value is None:
                continue

            # Serialize dates / datetimes
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            elif hasattr(value, 'pk'):
                value = str(value)
            else:
                value = str(value)[:500] if not isinstance(value, (bool, int, float)) else value

            data[name] = value
    except Exception as exc:
        logger.warning(
            'Failed to extract model data for audit log (%s #%s): %s',
            instance._meta.label, instance.pk, exc,
        )
    return data
