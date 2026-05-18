from .models import Notification


def create_notification(title, message, link='', recipient=None, recipient_role=None):
    """
    Create a notification for a specific user OR a role.
    """
    Notification.objects.create(
        recipient=recipient,
        recipient_role=recipient_role,
        title=title,
        message=message,
        link=link,
    )


def notify_role(role, title, message, link=''):
    """Notify all users with a specific role."""
    create_notification(
        title=title,
        message=message,
        link=link,
        recipient_role=role,
    )


def notify_user(user, title, message, link=''):
    """Notify a specific user."""
    create_notification(
        title=title,
        message=message,
        link=link,
        recipient=user,
    )


def get_unread_count(user):
    """Get unread notification count for a user."""
    from django.db.models import Q
    return Notification.objects.filter(
        Q(recipient=user) | Q(recipient_role=user.role),
        is_read=False,
    ).distinct().count()


def get_notifications(user, filter_by='all', page=1, per_page=20):
    """
    Get notifications for a user with optional filtering and pagination.

    Args:
        user: The user to get notifications for.
        filter_by: 'all' or 'unread'.
        page: Page number (1-based).
        per_page: Notifications per page.

    Returns:
        dict with 'notifications', 'page', 'total_pages', 'total_count', 'unread_count'
    """
    from django.db.models import Q

    base_qs = Notification.objects.filter(
        Q(recipient=user) | Q(recipient_role=user.role),
    ).distinct()

    if filter_by == 'unread':
        base_qs = base_qs.filter(is_read=False)

    total_count = base_qs.count()
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    offset = (page - 1) * per_page
    notifications = list(base_qs.order_by('-created_at')[offset:offset + per_page])

    unread_count = Notification.objects.filter(
        Q(recipient=user) | Q(recipient_role=user.role),
        is_read=False,
    ).distinct().count()

    return {
        'notifications': notifications,
        'page': page,
        'total_pages': total_pages,
        'total_count': total_count,
        'unread_count': unread_count,
    }