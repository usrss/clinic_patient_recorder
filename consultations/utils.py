from django.utils import timezone


def assign_next_queue_number():
    """
    Auto-generate the next queue number for today.
    Resets to 1 each calendar day. Called inside transaction.atomic().
    """
    from .models import Consultation

    today = timezone.localdate()
    last = (
        Consultation.objects
        .filter(queue_number__isnull=False, created_at__date=today)
        .order_by('-queue_number')
        .values_list('queue_number', flat=True)
        .first()
    )
    return (last or 0) + 1