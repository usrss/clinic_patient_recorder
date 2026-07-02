"""
Reusable audit logging service for the CPR system.

Centralizes audit log creation so views and signals can log actions
with a single function call rather than duplicating logic.
"""

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)

# Lazy import for choices validation
# Imported inside functions to avoid circular import during app init
# These cached references are populated on first use.
_VALID_ACTIONS = None
_VALID_MODULES = None


def _get_valid_actions():
    """Return the set of valid action values, lazy-loaded from AuditLog.Action.choices."""
    global _VALID_ACTIONS
    if _VALID_ACTIONS is None:
        from .models import AuditLog
        _VALID_ACTIONS = {v for v, _ in AuditLog.Action.choices}
    return _VALID_ACTIONS


def _get_valid_modules():
    """Return the set of valid module values, lazy-loaded from AuditLog.Module.choices."""
    global _VALID_MODULES
    if _VALID_MODULES is None:
        from .models import AuditLog
        _VALID_MODULES = {v for v, _ in AuditLog.Module.choices}
    return _VALID_MODULES


def _get_client_ip(request):
    """Extract client IP address from the request."""
    if request is None:
        return None
    # Use middleware-cached IP if available (avoids duplicate extraction)
    audit_ip = getattr(request, 'audit_ip', None)
    if audit_ip:
        return audit_ip
    # Fallback: check common proxy headers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _validate_action(action):
    """Raise ``ValueError`` if *action* is not a valid AuditLog.Action value."""
    valid = _get_valid_actions()
    if action not in valid:
        raise ValueError(
            f"Invalid action '{action}'. Must be one of: {', '.join(sorted(valid))}"
        )


def _validate_module(module):
    """Raise ``ValueError`` if *module* is not a valid AuditLog.Module value."""
    valid = _get_valid_modules()
    if module not in valid:
        raise ValueError(
            f"Invalid module '{module}'. Must be one of: {', '.join(sorted(valid))}"
        )


def log_audit_entry(
    *,
    user,
    action,
    module,
    description='',
    object_model='',
    object_id='',
    object_repr='',
    changes_before=None,
    changes_after=None,
    status='SUCCESS',
    request=None,
    ip_address=None,
):
    """
    Create a single audit log entry.

    Parameters
    ----------
    user : User or None
        The user who performed the action.
    action : str
        One of AuditLog.Action enum values (CREATE, UPDATE, DELETE,
        VIEW, LOGIN, LOGOUT, DOWNLOAD, PRINT, EXPORT).
    module : str
        One of AuditLog.Module enum values.
    description : str
        Human-readable explanation.
    object_model : str
        Dotted model path, e.g. ``"patients.Patient"``.
    object_id : str
        Primary key or identifier of the affected record.
    object_repr : str
        String representation of the object.
    changes_before : dict or None
        Values before the change (e.g. ``{"diagnosis": "Common Cold"}``).
    changes_after : dict or None
        Values after the change (e.g. ``{"diagnosis": "ARI"}``).
    status : str
        ``"SUCCESS"`` or ``"FAILED"``.
    request : HttpRequest or None
        Optional Django request object for IP extraction.
    ip_address : str or None
        Direct IP address (used when request is unavailable, e.g. signals).

    Raises
    ------
    ValueError
        If *action* or *module* is not a valid choice value.
    """
    _validate_action(action)
    _validate_module(module)

    from .models import AuditLog

    # Resolve IP: explicit ip_address takes precedence, then request-derived
    resolved_ip = ip_address or _get_client_ip(request)

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        user_role=getattr(user, 'role', '') if user and user.is_authenticated else '',
        user_name=(
            user.get_full_name() or getattr(user, 'username', '')
        ) if user and user.is_authenticated else '',
        action=action,
        module=module,
        description=description,
        object_model=object_model,
        object_id=str(object_id) if object_id is not None else '',
        object_repr=str(object_repr)[:300] if object_repr else '',
        changes_before=changes_before,
        changes_after=changes_after,
        ip_address=resolved_ip,
        status=status,
    )


def log_change(
    *,
    user,
    module,
    description='',
    object_model='',
    object_id='',
    object_repr='',
    changes_before=None,
    changes_after=None,
    request=None,
    ip_address=None,
):
    """Shortcut to log an UPDATE action with before/after change tracking."""
    log_audit_entry(
        user=user,
        action='UPDATE',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        changes_before=changes_before,
        changes_after=changes_after,
        request=request,
        ip_address=ip_address,
    )


def log_create(
    *,
    user,
    module,
    description='',
    object_model='',
    object_id='',
    object_repr='',
    request=None,
    ip_address=None,
):
    """Shortcut to log a CREATE action."""
    log_audit_entry(
        user=user,
        action='CREATE',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        request=request,
        ip_address=ip_address,
    )


def log_delete(
    *,
    user,
    module,
    description='',
    object_model='',
    object_id='',
    object_repr='',
    changes_before=None,
    request=None,
    ip_address=None,
):
    """Shortcut to log a DELETE action."""
    log_audit_entry(
        user=user,
        action='DELETE',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        changes_before=changes_before,
        request=request,
        ip_address=ip_address,
    )


def log_view(
    *,
    user,
    module,
    description='',
    object_model='',
    object_id='',
    object_repr='',
    request=None,
    ip_address=None,
):
    """Shortcut to log a VIEW action (e.g. viewing sensitive patient records)."""
    log_audit_entry(
        user=user,
        action='VIEW',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        request=request,
        ip_address=ip_address,
    )


def log_auth_event(
    *,
    user,
    action,
    description='',
    status='SUCCESS',
    request=None,
    ip_address=None,
):
    """Shortcut to log an authentication event (LOGIN, LOGOUT, etc.)."""
    log_audit_entry(
        user=user,
        action=action,
        module='Authentication',
        description=description,
        status=status,
        request=request,
        ip_address=ip_address,
    )


def log_export(
    *,
    user,
    module,
    description='',
    object_model='',
    object_id='',
    object_repr='',
    request=None,
    ip_address=None,
):
    """Shortcut to log an EXPORT / DOWNLOAD / PRINT action."""
    log_audit_entry(
        user=user,
        action='EXPORT',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        request=request,
        ip_address=ip_address,
    )


def get_changes_from_model(instance, changed_fields):
    """
    Build ``changes_after`` dict by reading the model instance's current
    field values for the specified changed fields.

    .. note::

       This function can only capture the **current** (after) values.
       The ``changes_before`` dict will always be empty because old values
       are no longer available on the instance after the change has been
       applied.

       To capture both before and after values, callers should stash the
       old field values in a pre-save signal (``pre_save``), then pass
       them to a logging shortcut like :func:`log_change`.

    Parameters
    ----------
    instance : Model
        The model instance (after the change has been applied).
    changed_fields : list of str
        Field names that were modified.

    Returns
    -------
    tuple
        ``(changes_before, changes_after)`` where ``changes_before`` is
        always ``None`` (old values are not available after the fact),
        and ``changes_after`` is a dict of field → current value, or
        ``None`` if no fields were provided.
    """
    if not changed_fields:
        return None, None

    after = {}
    for field in changed_fields:
        value = _serialize_value(getattr(instance, field, None))
        after[field] = value

    return (None, after if after else None)


def _serialize_value(value):
    """Convert a model field value to a JSON-serializable form."""
    if value is None:
        return None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if hasattr(value, 'pk'):
        return str(value)
    return str(value)
