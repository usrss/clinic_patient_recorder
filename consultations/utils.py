def assign_next_queue_number():
    """
    Auto-generate the next queue number for today.
    Resets to 1 each calendar day. Called inside transaction.atomic().
    Checks queue numbers from both Consultations and FollowUpRequests.
    """
    from .models import Consultation, FollowUpRequest
    from django.utils import timezone

    today = timezone.localdate()

    # Queue numbers assigned today from consultations
    # Use updated_at rather than created_at so re-queued consultations
    # (e.g. reopened from cancelled) get counted correctly.
    consultation_nums = Consultation.objects.filter(
        queue_number__isnull=False,
        updated_at__date=today,
    ).values_list('queue_number', flat=True)

    # Queue numbers assigned today from follow-up requests
    followup_nums = FollowUpRequest.objects.filter(
        queue_number__isnull=False,
        updated_at__date=today,
    ).values_list('queue_number', flat=True)

    numbers = list(consultation_nums) + list(followup_nums)
    last = max(numbers) if numbers else 0
    return last + 1