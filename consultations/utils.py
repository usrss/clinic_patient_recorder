# ── Single-active-consultation rule ───────────────────────────────────────────
# A patient may only create a new consultation request when they have no
# existing consultation that is still active (pending, queued, scheduled,
# triaged, or an active follow-up).

ACTIVE_CONSULTATION_MESSAGE = (
    'You already have an active consultation request. '
    'You may submit another consultation request once your current '
    'consultation has been completed.'
)


class ActiveConsultationExists(Exception):
    """Raised when a new consultation is requested while the patient already
    has an active consultation. Used to roll back and report cleanly."""


def lock_patient_and_get_active_consultation(patient):
    """
    Atomically guard new-consultation creation for a patient.

    MUST be called inside transaction.atomic(). Locks the patient row so
    concurrent submissions for the same patient are serialized, then returns
    the most recent active consultation (or None if the patient is free to
    submit a new request).

    Returns:
        Consultation | None
    """
    from patients.models import Patient
    from .models import Consultation

    locked = Patient.objects.select_for_update().get(pk=patient.pk)
    return Consultation.objects.active_for_patient(locked).first()


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