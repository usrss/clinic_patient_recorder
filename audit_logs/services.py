"""
Reusable audit logging service for the CPR system.

Centralizes audit log creation so views and signals can log actions
with a single function call rather than duplicating logic.
"""

from django.utils import timezone


def _get_client_ip(request):
    """Extract client IP address from the request."""
    if request is None:
        return None
    # Check common proxy headers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


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
):
    """
    Create a single audit log entry.

    Parameters
    ----------
    user : User or None
        The user who performed the action.
    action : str
        One of AuditLog.Action enum values.
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
    """
    from .models import AuditLog

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
        ip_address=_get_client_ip(request),
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
):
    """
    Shortcut to log an UPDATE action with before/after change tracking.
    """
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
):
    """
    Shortcut to log a CREATE action.
    """
    log_audit_entry(
        user=user,
        action='CREATE',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        request=request,
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
):
    """
    Shortcut to log a DELETE action.
    """
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
):
    """
    Shortcut to log a VIEW action (e.g. viewing sensitive patient records).
    """
    log_audit_entry(
        user=user,
        action='VIEW',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        request=request,
    )


def log_auth_event(
    *,
    user,
    action,
    description='',
    status='SUCCESS',
    request=None,
):
    """
    Shortcut to log an authentication event (LOGIN, LOGOUT, etc.).
    """
    log_audit_entry(
        user=user,
        action=action,
        module='Authentication',
        description=description,
        status=status,
        request=request,
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
):
    """
    Shortcut to log an EXPORT / DOWNLOAD / PRINT action.
    """
    log_audit_entry(
        user=user,
        action='EXPORT',
        module=module,
        description=description,
        object_model=object_model,
        object_id=object_id,
        object_repr=object_repr,
        request=request,
    )


def get_changes_from_model(instance, changed_fields):
    """
    Build ``changes_before`` and ``changes_after`` dicts by reading
    the model instance's current field values.

    Parameters
    ----------
    instance : Model
        The model instance (after the change has been applied).
    changed_fields : list of str
        Field names that were modified.

    Returns
    -------
    (changes_before, changes_after) tuple of dicts or None.
    """
    if not changed_fields:
        return None, None

    before = {}
    after = {}
    for field in changed_fields:
        # The "old" value is no longer available unless we've stored it
        # beforehand via a signal.  We return the current value as "after"
        # and leave "before" empty — callers should populate before if
        # they captured it.
        value = _serialize_value(getattr(instance, field, None))
        after[field] = value

    return (before if before else None, after if after else None)


def _serialize_value(value):
    """Convert a model field value to a JSON-serializable form."""
    if value is None:
        return None
    if hasattr(value, 'strftime'):
        return value.isoformat()
    if hasattr(value, 'pk'):
        return str(value)
    if hasattr(value, '__str__'):
        return str(value)
    return value
