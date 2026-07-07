"""
Signal handlers for automatic cleanup of old notifications.

When a new notification is created, a post_save handler purges read
notifications older than a configurable number of days (default 90).
This prevents unbounded table growth without relying solely on the
management command or manual cleanup.
"""

from django.utils import timezone

from .models import Notification

# Number of days after which a read notification is eligible for auto-cleanup.
# Read notifications older than this will be deleted each time a new
# notification is created.
_AUTO_CLEANUP_READ_AFTER_DAYS = 90


def auto_cleanup_old_notifications(sender, instance, created, **kwargs):
    """Purge read notifications older than the cutoff when a new one is created.

    Only fires on CREATE (not UPDATE) to keep the overhead minimal.
    Runs synchronously inside the CREATE transaction, so the cleanup
    is atomic with the new notification creation.
    """
    if not created:
        return  # Only run on new notification creation

    cutoff = timezone.now() - timezone.timedelta(days=_AUTO_CLEANUP_READ_AFTER_DAYS)
    Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff,
    ).delete()
