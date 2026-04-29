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


def get_notifications(user):
    """Get all notifications for a user."""
    from django.db.models import Q
    return Notification.objects.filter(
        Q(recipient=user) | Q(recipient_role=user.role),
    ).distinct().order_by('-created_at')[:20]