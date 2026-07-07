from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Patient
from accounts.models import User


@receiver(post_delete, sender=Patient)
def delete_orphaned_user(sender, instance, **kwargs):
    """When a Patient record is hard-deleted, also remove the orphaned User account.

    This allows the same patient_id to be re-registered in the future.
    The signal fires for both single-object deletes (Django Admin change page)
    and bulk deletes (\"Delete selected\" action).

    Archived patients (is_archived=True) are NOT affected — their User
    account remains active so they can still log in.
    """
    User.objects.filter(username=instance.patient_id).delete()
