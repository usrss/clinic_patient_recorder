def assign_next_queue_number():
    """
    Auto-generate the next queue number for today.
    Resets to 1 each calendar day. Called inside transaction.atomic().
    """
    from .models import Consultation

    numbers = list(Consultation.objects.today_queue_numbers())
    last = max(numbers) if numbers else 0
    return last + 1