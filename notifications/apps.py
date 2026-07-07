from django.apps import AppConfig
from django.db.models.signals import post_save


class NotificationsConfig(AppConfig):
    name = 'notifications'

    def ready(self):
        # Connect auto-cleanup signal handler to Notification model
        from .models import Notification
        from .signals import auto_cleanup_old_notifications
        post_save.connect(
            auto_cleanup_old_notifications,
            sender=Notification,
            weak=False,
        )
