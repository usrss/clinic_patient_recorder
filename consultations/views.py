from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch, Q

from accounts.models import User
from notifications.utils import notify_role, notify_user
from django.core.exceptions import ValidationError

from accounts.decorators import (
frontdesk_required, doctor_required,
admin_required, clinical_staff_required, patient_required,
)
from inventory.models import Medicine, StockMovement
from patients.models import Patient, PatientProfile
from .models import Consultation, Triage, Prescription, PrescriptionItem, CommonDiagnosis, FollowUpRequest, \
FollowUpProgress, ACTIVE_STATUSES
from .forms import (
ConsultationSubmitForm, QueueAssignForm, TriageForm, TriageEditForm,
PrescriptionForm, PrescriptionItemFormSet, PrescriptionMedicineFormSet,
PatientConsultationForm, FollowUpProgressForm, CloseConsultationForm, ConsultationStatusUpdateForm,
DOSAGE_CHOICES, FREQUENCY_CHOICES, DURATION_CHOICES, INSTRUCTIONS_CHOICES,
)
from .utils import (
    assign_next_queue_number,
    ACTIVE_CONSULTATION_MESSAGE,
    ActiveConsultationExists,
    lock_patient_and_get_active_consultation,
)
from inventory.utils import deduct_medicine_stock


# ─── PRESCRIPTION EDIT HELPERS ─────────────────────────────────────────────────

def _split_choice_value(value, choices):
    """Map a stored free-text value back to (select_value, other_value).

    If the value matches one of the fixed choices, return it directly;
    otherwise return ('other', value) so the "Other…" free-text input is used.
    """
    if not value:
        return '', ''
    for choice_value, label in choices:
        if choice_value and (choice_value == value or label == value):
            return choice_value, ''
    return 'other', value


def _prescription_item_initial(item):
    """Build initial formset data for an existing PrescriptionItem so the
    edit form opens with each medicine row pre-filled."""
    data = {}
    if item.medicine:
        data['source'] = 'inventory'
        data['medicine'] = item.medicine_id
        data['quantity'] = item.quantity
        data['inv_dosage'], data['inv_dosage_other'] = _split_choice_value(item.dosage, DOSAGE_CHOICES)
        data['inv_frequency'], data['inv_frequency_other'] = _split_choice_value(item.frequency, FREQUENCY_CHOICES)
        data['inv_duration'], data['inv_duration_other'] = _split_choice_value(item.duration, DURATION_CHOICES)
        data['inv_instructions'], data['inv_instructions_other'] = _split_choice_value(item.instructions, INSTRUCTIONS_CHOICES)
    else:
        data['source'] = 'custom'
        data['medicine_name'] = item.medicine_name
        data['cus_dosage'], data['cus_dosage_other'] = _split_choice_value(item.dosage, DOSAGE_CHOICES)
        data['cus_frequency'], data['cus_frequency_other'] = _split_choice_value(item.frequency, FREQUENCY_CHOICES)
        data['cus_duration'], data['cus_duration_other'] = _split_choice_value(item.duration, DURATION_CHOICES)
        data['cus_instructions'], data['cus_instructions_other'] = _split_choice_value(item.instructions, INSTRUCTIONS_CHOICES)
    return data


def _prescription_snapshot(prescription):
    """Capture the current prescription content for the audit trail."""
    items = [
        {
            'name': item.get_display_name(),
            'dosage': item.dosage,
            'frequency': item.frequency,
            'duration': item.duration,
            'quantity': item.quantity,
            'instructions': item.instructions,
        }
        for item in prescription.items.all()
    ]
    return {
        'diagnosis': prescription.diagnosis,
        'treatment_plan': prescription.treatment_plan,
        'items': items,
    }
from certificates.models import MedicalCertificate, CertificateAuditLog
from audit_logs.services import log_create, log_change
from django.http import JsonResponse


# ─── SIDEBAR COUNTS API ───────────────────────────────────────────────────────

@login_required
def sidebar_counts(request):
    """Return per-sidebar-item counts as JSON.

    Each sidebar nav link that needs a badge gets its own count.
    When the count is 0, the badge shows a muted "0" so users can
    see at a glance that a section is empty.
    """
    user = request.user
    role = user.role
    counts = {}

    # Triage Queue (doctor): consultations queued/scheduled for triage
    if role == 'doctor':
        counts['triage_queue'] = Consultation.objects.filter(
            status__in=[Consultation.Status.QUEUED, Consultation.Status.SCHEDULED]
        ).count()

    # My Patients (doctor): triaged patients waiting for consultation
    if role == 'doctor':
        counts['my_patients'] = Consultation.objects.filter(
            status=Consultation.Status.TRIAGED
        ).count()

    # Queue (frontdesk + admin): pending consultations
    if role in ('frontdesk', 'admin'):
        counts['queue'] = Consultation.objects.filter(
            status=Consultation.Status.PENDING
        ).count()

    # Archived patients pending (admin)
    if role == 'admin':
        from patients.models import Patient
        counts['archives'] = Patient.objects.filter(
            archived_at__isnull=False
        ).count()

    # Unread notifications (all roles)
    import notifications.utils as notif_utils
    counts['notifications'] = notif_utils.get_unread_count(user)

    return JsonResponse(counts)


# ─── PATIENT VIEWS ────────────────────────────────────────────────────────────

def _base_template(user):
    """Return the correct base template for the current user's role."""
    if user.role == 'admin':
        return 'core/base_admin.html'
    return 'core/base_staff.html'





@login_required
def patient_home(request):
    """Patient's own consultation history."""
    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    consultations = Consultation.objects.filter(
        patient=patient
    ).order_by('-created_at')

    # Get active follow-up requests: consultation_id -> FollowUpRequest pk
    pending_follow_ups = {
        r.consultation_id: r.pk
        for r in FollowUpRequest.objects.filter(
            patient=patient,
            request_status__in=['pending', 'queued'],
        ).only('pk', 'consultation_id')
    }

    return render(request, 'consultations/patient_home.html', {
        'consultations': consultations,
        'patient': patient,
        'pending_follow_ups': pending_follow_ups,
    })


@login_required
@patient_required
def patient_submit(request):
    """
    Patient consultation page:
    - Shows active follow-up consultations (marked by doctor)
    - Option to create a new consultation
    """
    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    # Active follow-up consultations (doctor-marked only)
    active_follow_ups = Consultation.objects.filter(
        patient=patient,
        is_original_case=True,
        status=Consultation.Status.ACTIVE_FOLLOW_UP,
    ).order_by('-created_at')

    # Most recent active consultation — blocks new request submissions
    active_consultation = Consultation.objects.active_for_patient(patient).first()

    # New consultation form
    form = PatientConsultationForm(request.POST or None, patient=patient)

    consultation_fields = {
        'symptoms', 'medical_history',
        'severity_description', 'additional_notes',
    }
    is_new_consultation_post = (
        'submit_new' in request.POST
        or any(field in request.POST for field in consultation_fields)
    )

    if request.method == 'POST' and is_new_consultation_post:
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Serialize concurrent submissions for this patient, then
                    # re-check the rule under the row lock (source of truth).
                    if lock_patient_and_get_active_consultation(patient) is not None:
                        raise ActiveConsultationExists()

                    consultation = form.save(commit=False)
                    consultation.patient = patient
                    consultation.status = Consultation.Status.PENDING
                    consultation.is_original_case = True
                    consultation.save()
            except ActiveConsultationExists:
                messages.error(request, ACTIVE_CONSULTATION_MESSAGE)
                return render(request, 'consultations/patient_submit.html', {
                    'form': form,
                    'active_follow_ups': active_follow_ups,
                    'active_consultation': (
                        active_consultation
                        or Consultation.objects.active_for_patient(patient).first()
                    ),
                })

            notify_role('frontdesk',
                        'New Consultation Request',
                        f'{patient.get_full_name()} submitted a new consultation request.',
                        f'/consultations/queue/{consultation.pk}/')
            log_create(
                user=request.user,
                module='Consultations',
                description=f'Submitted new consultation request — {patient.get_full_name()}',
                object_model='consultations.Consultation',
                object_id=consultation.pk,
                object_repr=str(consultation),
                request=request,
            )
            messages.success(request, 'Your new consultation request has been submitted.')
            return redirect('consultations:patient_home')

    return render(request, 'consultations/patient_submit.html', {
        'form': form,
        'active_follow_ups': active_follow_ups,
        'active_consultation': active_consultation,
    })


@login_required
@patient_required
def request_follow_up(request, consultation_pk):
    """
    Patient requests a follow-up visit for an active consultation.
    Validates that the recommended follow-up date has arrived, then
    sets the consultation to PENDING status so it appears in the
    front desk queue for processing.
    """
    if request.method != 'POST':
        return redirect('consultations:patient_home')

    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    consultation = get_object_or_404(
        Consultation,
        pk=consultation_pk,
        patient=patient,
        is_original_case=True,
        status=Consultation.Status.ACTIVE_FOLLOW_UP,
    )

    from django.utils import timezone

    # Validate: patient can only follow up on or after the recommended date
    if consultation.recommended_follow_up_date:
        if timezone.localdate() < consultation.recommended_follow_up_date:
            messages.error(
                request,
                f'Your recommended follow-up date is '
                f'{consultation.recommended_follow_up_date.strftime("%B %d, %Y")}. '
                f'You may only request a follow-up on or after this date. '
                f'Please wait until the recommended date to submit your request.'
            )
            return redirect('consultations:patient_home')

    # Prevent duplicate pending requests
    existing_request = FollowUpRequest.objects.filter(
        consultation=consultation,
        patient=patient,
        request_status__in=['pending', 'queued'],
    ).first()
    if existing_request:
        messages.info(
            request,
            f'You already have a follow-up request pending for Consultation #{consultation_pk}. '
            f'Please wait for the front desk to process your request.'
        )
        return redirect('consultations:patient_home')

    with transaction.atomic():
        # Set consultation to PENDING so it appears in the front desk queue
        consultation.status = Consultation.Status.PENDING
        consultation.save(update_fields=['status'])

        # Create FollowUpRequest record for audit trail
        FollowUpRequest.objects.create(
            consultation=consultation,
            patient=patient,
            request_status='pending',
        )

    # Notify front desk to process the follow-up request
    notify_role(
        'frontdesk',
        'Follow-up Request Ready for Processing',
        f'{patient.get_full_name()} has requested a follow-up for Consultation #{consultation_pk}. '
        f'Please process in the queue.',
        f'/consultations/queue/{consultation.pk}/'
    )

    messages.success(
        request,
        f'Your follow-up visit request for Consultation #{consultation_pk} has been submitted. '
        f'Please proceed to the front desk for processing.'
    )
    return redirect('consultations:patient_home')





@login_required
@doctor_required
def consultation_complete(request, pk):
    """
    Doctor completes a consultation and decides whether follow-up is needed.
    """
    consultation = get_object_or_404(
        Consultation,
        pk=pk,
        status=Consultation.Status.TRIAGED,
    )

    if not consultation.prescriptions.exists():
        messages.error(request, 'Please complete the prescription first.')
        return redirect('consultations:prescribe', pk=pk)

    if request.method == 'POST':
        requires_follow_up = request.POST.get('requires_follow_up') == '1'
        recommended_date = request.POST.get('recommended_follow_up_date', '').strip()

        if requires_follow_up and not recommended_date:
            messages.error(request, 'Please set a recommended follow-up date.')
        else:
            if requires_follow_up:
                consultation.status = Consultation.Status.ACTIVE_FOLLOW_UP
                consultation.recommended_follow_up_date = recommended_date
            else:
                consultation.status = Consultation.Status.COMPLETED

            consultation.save(update_fields=['status', 'recommended_follow_up_date'])

            log_change(
                user=request.user,
                module='Consultations',
                description=f'Completed consultation #{pk} — {"follow-up recommended" if requires_follow_up else "no follow-up needed"}',
                object_model='consultations.Consultation',
                object_id=consultation.pk,
                object_repr=str(consultation),
                changes_after={'status': consultation.status},
                request=request,
            )

            patient_user = User.objects.filter(username=consultation.patient.patient_id).first()
            if patient_user:
                notify_user(
                    patient_user,
                    'Consultation Completed',
                    f'Consultation #{pk} has been completed. '
                    + ('A follow-up has been recommended.' if requires_follow_up else ''),
                    f'/consultations/my/{pk}/'
                )

            # Check if doctor requested to issue a certificate
            issue_certificate = request.POST.get('issue_certificate') == '1'

            messages.success(
                request,
                f'Consultation #{pk} completed.'
                + (' Follow-up recommended.' if requires_follow_up else '')
            )

            if issue_certificate:
                return redirect('certificates:wizard_type', consultation_pk=consultation.pk)
            return redirect('consultations:completion_summary', pk=consultation.pk)

    return render(request, 'consultations/consultation_complete.html', {
        'consultation': consultation,
        'base_template': _base_template(request.user),
        'today': date.today(),
    })


@login_required
@patient_required
def patient_detail(request, pk):
    """Patient views one of their own consultations."""
    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    consultation = get_object_or_404(Consultation, pk=pk, patient=patient)
    return render(request, 'consultations/patient_consultation_detail.html', {
        'consultation': consultation,
    })


@login_required
@patient_required
def cancel_follow_up_request(request, follow_up_pk):
    """Patient cancels a follow-up request that is pending or queued.

    Also resets the consultation back to ACTIVE_FOLLOW_UP status
    and removes its queue number.
    """
    if request.method != 'POST':
        return redirect('consultations:patient_home')

    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    follow_up_req = get_object_or_404(
        FollowUpRequest,
        pk=follow_up_pk,
        patient=patient,
        request_status__in=['pending', 'queued'],
    )

    with transaction.atomic():
        follow_up_req.request_status = 'cancelled'
        follow_up_req.save(update_fields=['request_status'])

        # Reset the consultation back to active follow-up and remove queue number
        consultation = follow_up_req.consultation
        consultation.status = Consultation.Status.ACTIVE_FOLLOW_UP
        consultation.queue_number = None
        consultation.save(update_fields=['status', 'queue_number'])

    messages.success(
        request,
        f'Follow-up request for Consultation #{follow_up_req.consultation_id} has been cancelled.'
    )

    # Notify front desk
    notify_role('frontdesk',
                'Follow-up Request Cancelled',
                f'Patient {patient.get_full_name()} cancelled their follow-up request for Consultation #{follow_up_req.consultation_id}.',
                link=f'/consultations/queue/')

    return redirect('consultations:patient_home')


@login_required
@patient_required
def patient_cancel(request, pk):
    """Patient cancels a pending consultation."""
    if request.method != 'POST':
        return redirect('consultations:patient_home')

    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    consultation = get_object_or_404(
        Consultation, pk=pk, patient=patient,
        status=Consultation.Status.PENDING,
    )
    consultation.status = Consultation.Status.CANCELLED
    consultation.save(update_fields=['status'])
    messages.success(request, f'Consultation #{pk} has been cancelled.')
    return redirect('consultations:patient_home')


# ─── FRONT DESK VIEWS ─────────────────────────────────────────────────────────

@login_required
@frontdesk_required
def queue(request):
    """List pending consultation requests and follow-up requests for front desk to process."""
    consultations = Consultation.objects.filter(
        status=Consultation.Status.PENDING
    ).select_related('patient', 'patient__college').order_by('created_at')

    # Identify which consultations are follow-up requests
    follow_up_consultation_ids = set(
        FollowUpRequest.objects.filter(
            consultation__in=consultations,
            request_status='pending',
        ).values_list('consultation_id', flat=True)
    )

    # Calculate queue positions for queued consultations (ordered by created_at)
    queue_positions = {}
    for idx, c in enumerate(consultations, start=1):
        queue_positions[c.pk] = idx

    return render(request, 'consultations/queue.html', {
        'consultations': consultations,
        'base_template': _base_template(request.user),
        'follow_up_consultation_ids': follow_up_consultation_ids,
        'queue_positions': queue_positions,
    })


@login_required
@frontdesk_required
def consultation_create(request):
    """Front desk creates a consultation on behalf of a walk-in patient.

    Supports walk-in patients who are not yet registered:
    - If the patient ID matches an existing Patient → use that record.
    - Otherwise → create a minimal Patient + PatientProfile + User account.
    """
    from patients.models import Patient, PatientProfile
    from accounts.utils import create_patient_user

    # ── One-time credentials from a successful creation (PRG pattern) ──────────
    new_patient_credentials = request.session.pop('new_patient_credentials', None)

    # Persist the last looked-up patient_id across POST requests
    looked_up_patient_id = request.session.get('looked_up_patient_id', '')
    looked_up_patient = None
    if looked_up_patient_id:
        looked_up_patient = Patient.objects.filter(
            patient_id=looked_up_patient_id
        ).first()

    form = ConsultationSubmitForm(request.POST or None)

    if request.method == 'POST':
        # ── Handle Lookup action ────────────────────────────────────────
        if 'lookup' in request.POST:
            pid = request.POST.get('patient_id', '').strip()
            existing = Patient.objects.filter(patient_id=pid).first()
            if existing:
                request.session['looked_up_patient_id'] = pid
                messages.success(
                    request,
                    f'Patient found: {existing.get_full_name()} ({existing.patient_id})'
                )
            else:
                request.session['looked_up_patient_id'] = ''
                if pid:
                    messages.info(
                        request,
                        'Patient not found. Complete the registration fields below.'
                    )

            # Re-render same page with POST data preserved — no redirect, no data loss
            form = ConsultationSubmitForm(request.POST)
            return render(request, 'consultations/consultation_create.html', {
                'form': form,
                'base_template': _base_template(request.user),
                'looked_up_patient': existing if existing else None,
                'looked_up_has_active': (
                    Consultation.objects.has_active_for_patient(existing)
                    if existing else False
                ),
            })

        # ── Handle Create Consultation action ───────────────────────────
        if form.is_valid():
            cd = form.cleaned_data
            patient = cd.get('_patient')  # existing Patient or None
            is_new_patient = patient is None
            temp_password = None

            try:
                with transaction.atomic():
                    if is_new_patient:
                        # A brand-new patient cannot have any prior consultation.
                        # Create minimal Patient record
                        patient = Patient.objects.create(
                            patient_id=cd['patient_id'],
                            first_name=cd['first_name'],
                            last_name=cd['last_name'],
                            sex=cd['sex'],
                            phone=cd.get('contact_number', ''),
                            is_active=True,
                        )
                        # Create PatientProfile with birthday
                        PatientProfile.objects.create(
                            patient=patient,
                            birthday=cd['birthdate'],
                        )
                        # Auto-create User account (no email — patient provides it during profile completion)
                        user, temp_password = create_patient_user(patient)
                    else:
                        # Existing patient — enforce the single-active-consultation
                        # rule atomically (row lock serializes concurrent creates).
                        if lock_patient_and_get_active_consultation(patient) is not None:
                            raise ActiveConsultationExists()

                    # Create Consultation
                    consultation = Consultation(
                        patient=patient,
                        symptoms=cd['symptoms'],
                        medical_history=cd.get('medical_history', ''),
                        severity_description=cd['severity_description'],
                        additional_notes=cd.get('additional_notes', ''),
                        status=Consultation.Status.PENDING,
                        is_original_case=True,
                    )
                    consultation.save()
            except ActiveConsultationExists:
                messages.error(request, ACTIVE_CONSULTATION_MESSAGE)
                return redirect('consultations:consultation_create')

            # Notify front desk
            log_create(
                user=request.user,
                module='Consultations',
                description=f'Created consultation for {"new patient" if is_new_patient else "existing"} — {patient.get_full_name()}',
                object_model='consultations.Consultation',
                object_id=consultation.pk,
                object_repr=str(consultation),
                request=request,
            )

            notify_role(
                'frontdesk',
                'New Consultation Request',
                f'{patient.get_full_name()} submitted a consultation request.',
                f'/consultations/queue/{consultation.pk}/'
            )

            # Clear session lookup
            request.session.pop('looked_up_patient_id', None)

            if is_new_patient and temp_password:
                # Store credentials in session (one-time) and redirect (PRG)
                request.session['new_patient_credentials'] = {
                    'username': patient.patient_id,
                    'password': temp_password,
                    'name': patient.get_full_name(),
                }
                messages.success(
                    request,
                    f'Consultation created for {patient.get_full_name()}. '
                    'Patient registered successfully.'
                )
                # Also include password in messages for recovery
                messages.info(
                    request,
                    f'Patient credentials — Username: {patient.patient_id} | '
                    f'Password: {temp_password}'
                )
                # Redirect to create page to show credentials box via session
                return redirect('consultations:consultation_create')
            else:
                messages.success(
                    request,
                    f'Consultation created for {patient.get_full_name()}.'
                )
                # PRG: Redirect to queue for existing patients
                return redirect('consultations:queue')

    return render(request, 'consultations/consultation_create.html', {
        'form': form,
        'base_template': _base_template(request.user),
        'looked_up_patient': looked_up_patient,
        'looked_up_has_active': (
            Consultation.objects.has_active_for_patient(looked_up_patient)
            if looked_up_patient else False
        ),
        'new_patient_credentials': new_patient_credentials,
    })


@login_required
@frontdesk_required
def queue_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)

    if consultation.status != Consultation.Status.PENDING:
        messages.info(
            request,
            f'Consultation #{consultation.pk} has already been processed '
            f'(status: {consultation.get_status_display()}).'
        )
        return redirect('consultations:queue')

    # Check if this is a follow-up request
    follow_up_request = FollowUpRequest.objects.filter(
        consultation=consultation,
        request_status='pending',
    ).first()

    form = QueueAssignForm(request.POST or None, instance=consultation)

    if request.method == 'POST':
        if follow_up_request and 'process_follow_up' in request.POST:
            # Auto-queue the follow-up — no form selection needed
            with transaction.atomic():
                queue_number = assign_next_queue_number()
                consultation.status = Consultation.Status.QUEUED
                consultation.queue_number = queue_number
                consultation.save(update_fields=['status', 'queue_number'])

                follow_up_request.request_status = 'queued'
                follow_up_request.queue_number = queue_number
                follow_up_request.save(update_fields=['request_status', 'queue_number'])

                notify_role(
                    'doctor',
                    'Follow-up Queued for Triage',
                    f'{consultation.patient.get_full_name()} (follow-up) is ready for triage.',
                    f'/consultations/triage/{consultation.pk}/'
                )

            messages.success(
                request,
                f'Follow-up request #{consultation.pk} processed. '
                f'Queue number: #{queue_number}. Patient routed to triage.'
            )
            return redirect('consultations:queue')

        if form.is_valid():
            instance = form.save(commit=False)
            if instance.status == Consultation.Status.QUEUED:
                with transaction.atomic():
                    instance.queue_number = assign_next_queue_number()
                    instance.save()
                    notify_role('doctor',
                                'Patient Queued for Triage',
                                f'{consultation.patient.get_full_name()} is ready for triage.',
                                f'/consultations/triage/{consultation.pk}/')
            else:
                instance.save()
            log_change(
                user=request.user,
                module='Consultations',
                description=f'Processed consultation #{consultation.pk} — queued for triage',
                object_model='consultations.Consultation',
                object_id=consultation.pk,
                object_repr=str(consultation),
                changes_after={'status': consultation.status, 'queue_number': getattr(instance, 'queue_number', None)},
                request=request,
            )

            messages.success(
                request,
                f'Consultation #{consultation.pk} updated. '
                + (f'Queue number: #{instance.queue_number}' if instance.queue_number else '')
            )
            return redirect('consultations:queue')

    return render(request, 'consultations/queue_detail.html', {
        'consultation': consultation,
        'form': form,
        'base_template': _base_template(request.user),
        'is_follow_up': follow_up_request is not None,
    })





@login_required
@frontdesk_required
def frontdesk_cancel(request, pk):
    if request.method != 'POST':
        return redirect('consultations:queue')

    consultation = get_object_or_404(Consultation, pk=pk)
    cancellable = [
        Consultation.Status.PENDING,
        Consultation.Status.QUEUED,
        Consultation.Status.SCHEDULED,
    ]
    if consultation.status not in cancellable:
        messages.error(
            request,
            f'Consultation #{pk} cannot be cancelled at this stage '
            f'({consultation.get_status_display()}).'
        )
        return redirect('consultations:queue')

    with transaction.atomic():
        # Also cancel any associated follow-up request
        FollowUpRequest.objects.filter(
            consultation=consultation,
            request_status__in=['pending', 'queued'],
        ).update(request_status='cancelled')
        consultation.status = Consultation.Status.CANCELLED
        consultation.save(update_fields=['status'])

    log_change(
        user=request.user,
        module='Consultations',
        description=f'Cancelled consultation #{pk} — {consultation.patient.get_full_name()}',
        object_model='consultations.Consultation',
        object_id=consultation.pk,
        object_repr=str(consultation),
        changes_after={'status': 'cancelled'},
        request=request,
    )

    messages.success(request, f'Consultation #{pk} has been cancelled.')
    return redirect('consultations:queue')


# ─── ADMIN REOPEN ─────────────────────────────────────────────────────────────

@login_required
@admin_required
def admin_reopen(request, pk):
    if request.method != 'POST':
        return redirect('accounts:dashboard')

    consultation = get_object_or_404(Consultation, pk=pk)
    if consultation.status != Consultation.Status.CANCELLED:
        messages.error(request, 'Only cancelled consultations can be reopened.')
        return redirect('consultations:queue')

    # Reopening flips this consultation back to PENDING (an active status).
    # Block it if the patient already has another active consultation, so the
    # single-active-consultation rule is never violated.
    other_active = Consultation.objects.filter(
        patient=consultation.patient,
        status__in=ACTIVE_STATUSES,
    ).exclude(pk=consultation.pk).exists()
    if other_active:
        messages.error(
            request,
            f'Cannot reopen Consultation #{pk}: {consultation.patient.get_full_name()} '
            'already has an active consultation. Complete or cancel the active '
            'consultation first.'
        )
        return redirect('consultations:queue')

    consultation.status = Consultation.Status.PENDING
    consultation.queue_number = None
    consultation.scheduled_at = None
    consultation.save(update_fields=['status', 'queue_number', 'scheduled_at'])
    log_change(
        user=request.user,
        module='Consultations',
        description=f'Reopened consultation #{pk} — {consultation.patient.get_full_name()}',
        object_model='consultations.Consultation',
        object_id=consultation.pk,
        object_repr=str(consultation),
        changes_after={'status': 'pending'},
        request=request,
    )
    messages.success(request, f'Consultation #{pk} has been reopened and returned to Pending.')
    return redirect('consultations:queue')


# ─── DOCTOR VIEWS (includes triage + consultations + prescribing) ─────────────

@login_required
@doctor_required
def triage_list(request):
    consultations = Consultation.objects.filter(
        status__in=[Consultation.Status.QUEUED, Consultation.Status.SCHEDULED]
    ).select_related('patient', 'patient__college').order_by(
        'queue_number', 'scheduled_at', 'created_at'
    )

    # Identify follow-up consultations for badge display
    follow_up_consultation_ids = set(
        FollowUpRequest.objects.filter(
            consultation__in=consultations,
            request_status='queued',
        ).values_list('consultation_id', flat=True)
    )

    # Calculate queue positions (consultations are already ordered by queue_number)
    queue_positions = {}
    for idx, c in enumerate(consultations, start=1):
        queue_positions[c.pk] = idx

    return render(request, 'consultations/triage_list.html', {
        'consultations': consultations,
        'base_template': _base_template(request.user),
        'follow_up_consultation_ids': follow_up_consultation_ids,
        'queue_positions': queue_positions,
    })


@login_required
@doctor_required
def triage_form(request, pk):
    consultation = get_object_or_404(
        Consultation, pk=pk,
        status__in=[Consultation.Status.QUEUED, Consultation.Status.SCHEDULED],
    )

    if consultation.triages.exists():
        # If this consultation already has a prescription, it's a follow-up case.
        # Redirect doctor to the follow-up creation form instead.
        if consultation.prescriptions.exists():
            messages.info(request, f'This is a follow-up visit. Recording follow-up progress.')
            return redirect('consultations:follow_up_create', consultation_pk=consultation.pk)
        # Already triaged but no prescription yet — let the doctor edit the triage
        messages.info(request, f'Consultation #{consultation.pk} has already been triaged. You can edit triage records below.')
        return redirect('consultations:triage_edit', pk=consultation.pk)

    # Get or create patient profile
    patient = consultation.patient
    profile, _ = PatientProfile.objects.get_or_create(patient=patient)

    # Pre-fill profile data as initial values
    initial_profile = {
        'hypertension': profile.hypertension,
        'diabetes': profile.diabetes,
        'asthma': profile.asthma,
        'cardiac_problems': profile.cardiac_problems,
        'arthritis': profile.arthritis,
        'other_conditions': profile.other_conditions,
        'bcg': profile.bcg,
        'dpt': profile.dpt,
        'opv': profile.opv,
        'hepatitis_b': profile.hepatitis_b,
        'measles': profile.measles,
        'tt': profile.tt,
        # Pre-fill the final chief complaint with the patient's own words so
        # the doctor can review and reword it during triage.
        'chief_complaint': consultation.symptoms,
    }

    form = TriageForm(request.POST or None, initial=initial_profile)

    if request.method == 'POST' and form.is_valid():
        triage = form.save(commit=False)
        triage.consultation = consultation
        triage.triaged_by = request.user
        triage.save()

        # Update patient profile from triage form
        profile.hypertension = form.cleaned_data['hypertension']
        profile.diabetes = form.cleaned_data['diabetes']
        profile.asthma = form.cleaned_data['asthma']
        profile.cardiac_problems = form.cleaned_data['cardiac_problems']
        profile.arthritis = form.cleaned_data['arthritis']
        profile.other_conditions = form.cleaned_data.get('other_conditions', '')
        profile.bcg = form.cleaned_data['bcg']
        profile.dpt = form.cleaned_data['dpt']
        profile.opv = form.cleaned_data['opv']
        profile.hepatitis_b = form.cleaned_data['hepatitis_b']
        profile.measles = form.cleaned_data['measles']
        profile.tt = form.cleaned_data['tt']
        profile.save()

        # Save the doctor-reviewed chief complaint. Blank → keep the
        # patient's own words so the official record always has a value.
        consultation.chief_complaint = (
            (form.cleaned_data.get('chief_complaint') or '').strip()
            or consultation.symptoms
        )
        consultation.status = Consultation.Status.TRIAGED
        consultation.save(update_fields=['status', 'chief_complaint'])

        log_change(
            user=request.user,
            module='Consultations',
            description=f'Triaged patient — {consultation.patient.get_full_name()} — {triage.get_urgency_display()} urgency',
            object_model='consultations.Consultation',
            object_id=consultation.pk,
            object_repr=str(consultation),
            changes_after={'status': 'triaged', 'urgency': triage.urgency},
            request=request,
        )

        notify_role('doctor',
                    'Patient Ready for Consultation',
                    f'{consultation.patient.get_full_name()} has been triaged and is ready.',
                    f'/consultations/prescribe/{consultation.pk}/')
        messages.success(request, f'Triage complete for Consultation #{consultation.pk}.')
        return redirect('consultations:prescribe', pk=consultation.pk)

    return render(request, 'consultations/triage_form.html', {
        'consultation': consultation,
        'form': form,
        'profile': profile,
        'base_template': _base_template(request.user),
    })


@login_required
@doctor_required
def triage_edit(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)

    if not consultation.triages.exists():
        messages.error(request, f'Consultation #{pk} has not been triaged yet.')
        return redirect('consultations:triage_list')

    if consultation.status == Consultation.Status.COMPLETED:
        messages.error(request, 'Triage records cannot be amended after a consultation is completed.')
        return redirect('consultations:triage_list')

    # Amendments are only allowed BEFORE a prescription is made — once the
    # doctor has prescribed, the triage record is locked.
    if consultation.prescriptions.exists():
        messages.error(request, 'Triage records cannot be amended after a prescription has been made.')
        return redirect('consultations:triage_list')

    triage = consultation.triages.first()

    # Snapshot before-values for the audit trail
    before_notes = triage.notes
    before_cc = consultation.chief_complaint

    form = TriageEditForm(
        request.POST or None,
        instance=triage,
        initial={
            'chief_complaint': consultation.chief_complaint or consultation.symptoms,
        },
    )

    if request.method == 'POST' and form.is_valid():
        amended = form.save(commit=False)
        reason = form.cleaned_data['amendment_reason']
        amended.notes = (
            f"{triage.notes}\n\n[Amended by {request.user.username}: {reason}]"
            if triage.notes else f"[Amended by {request.user.username}: {reason}]"
        )
        amended.save()

        # Allow amending the final chief complaint along with the triage record.
        new_cc = (
            (form.cleaned_data.get('chief_complaint') or '').strip()
            or consultation.symptoms
        )
        if new_cc != consultation.chief_complaint:
            consultation.chief_complaint = new_cc
            consultation.save(update_fields=['chief_complaint'])

        # Audit trail — record the amendment like every other change in the system
        log_change(
            user=request.user,
            module='Consultations',
            description=f'Amended triage for consultation #{pk} — {reason}',
            object_model='consultations.Consultation',
            object_id=consultation.pk,
            object_repr=str(consultation),
            changes_before=(
                {'notes': before_notes, 'chief_complaint': before_cc}
                if (before_notes or before_cc) else None
            ),
            changes_after={'notes': amended.notes, 'chief_complaint': new_cc},
            request=request,
        )

        messages.success(request, f'Triage record for Consultation #{pk} has been updated.')
        return redirect('consultations:triage_list')

    return render(request, 'consultations/triage_edit.html', {
        'consultation': consultation,
        'triage': triage,
        'form': form,
        'base_template': _base_template(request.user),
    })


@login_required
@doctor_required
def doctor_list(request):
    consultations = Consultation.objects.filter(
        status=Consultation.Status.TRIAGED
    ).select_related('patient', 'patient__college').prefetch_related('triages').order_by('created_at')
    return render(request, 'consultations/doctor_list.html', {
        'consultations': consultations,
        'base_template': _base_template(request.user),
    })


@login_required
@doctor_required
def prescribe(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk, status=Consultation.Status.TRIAGED)

    if consultation.prescriptions.exists():
        # The prescription already exists — send the doctor to the edit form
        # instead of the read-only print page, so "Back to Prescription"
        # actually lets them amend it.
        messages.info(request, f'Consultation #{consultation.pk} already has a prescription.')
        return redirect('consultations:prescription_edit', pk=consultation.pk)

    prescription_form = PrescriptionForm(request.POST or None)
    formset = PrescriptionMedicineFormSet(request.POST or None, prefix='meds')
    inventory_medicines = Medicine.objects.filter(quantity__gt=0).order_by('name')

    if request.method == 'POST':
        no_medicine = request.POST.get('no_medicine') == '1'

        if no_medicine or not inventory_medicines.exists():
            # ── Complete without any medicine ──────────────────────
            if prescription_form.is_valid():
                with transaction.atomic():
                    prescription = prescription_form.save(commit=False)
                    prescription.consultation = consultation
                    prescription.doctor = request.user
                    prescription.save()
                messages.success(request, f'Consultation #{consultation.pk} completed.')
                return redirect('consultations:consultation_complete', pk=consultation.pk)
            else:
                messages.error(request, 'Please enter a diagnosis.')

        else:
            # ── Complete with medicine ─────────────────────────────
            forms_valid   = prescription_form.is_valid()
            formset_valid = formset.is_valid()

            if forms_valid and formset_valid:
                item_rows = [f for f in formset if f.has_data()]

                # "Apply to All" shared instruction submitted via hidden field by JS.
                # Used as fallback when the doctor left per-row instructions blank.
                global_instructions = request.POST.get('apply_instructions', '').strip()

                try:
                    with transaction.atomic():
                        prescription = prescription_form.save(commit=False)
                        prescription.consultation = consultation
                        prescription.doctor = request.user
                        prescription.save()

                        for form in item_rows:
                            med           = form.cleaned_data.get('medicine')
                            medicine_name = form.cleaned_data.get('medicine_name', '').strip()
                            qty           = form.cleaned_data.get('quantity')

                            # Per-row instructions win; global is the fallback
                            row_instructions   = form.cleaned_data.get('instructions', '').strip()
                            final_instructions = row_instructions or global_instructions

                            PrescriptionItem.objects.create(
                                prescription=prescription,
                                medicine=med,
                                medicine_name=med.name if med else medicine_name,
                                dosage=form.cleaned_data.get('dosage', '').strip(),
                                frequency=form.cleaned_data.get('frequency', '').strip(),
                                duration=form.cleaned_data.get('duration', '').strip(),
                                instructions=final_instructions,
                                # Persist the dispensed quantity so a later edit
                                # can restore the correct amount of stock.
                                quantity=qty,
                            )

                            if med and qty:
                                deduct_medicine_stock(
                                    medicine_id=med.pk,
                                    quantity=qty,
                                    reason=(
                                        f'Consultation #{consultation.pk} — '
                                        f'{consultation.patient.get_full_name()}'
                                    ),
                                    user=request.user,
                                )

                    log_change(
                        user=request.user,
                        module='Consultations',
                        description=f'Completed prescription for consultation #{consultation.pk} — {prescription.diagnosis}',
                        object_model='consultations.Consultation',
                        object_id=consultation.pk,
                        object_repr=str(consultation),
                        changes_after={'diagnosis': prescription.diagnosis},
                        request=request,
                    )

                    messages.success(
                        request,
                        f'Prescription saved. Consultation #{consultation.pk} completed.',
                    )
                    return redirect('consultations:consultation_complete', pk=consultation.pk)

                except Exception as exc:
                    messages.error(
                        request,
                        f'An unexpected error occurred: {exc}. Please try again.',
                    )

    return render(request, 'consultations/prescribe.html', {
        'consultation': consultation,
        'prescription_form': prescription_form,
        'formset': formset,
        'inventory_medicines': inventory_medicines,
        'common_diagnoses': CommonDiagnosis.objects.all().order_by('name'),
        'base_template': _base_template(request.user),
    })


@login_required
@doctor_required
def prescription_edit(request, pk):
    """
    Doctor edits an existing prescription while the consultation is still
    open (TRIAGED — not yet completed/closed).

    Stock handling: every edit restores the previously dispensed inventory
    quantities and re-deducts for the final list, so removing or reducing a
    medicine returns stock to inventory. The whole change is atomic and is
    recorded in the audit trail with before/after snapshots.
    """
    consultation = get_object_or_404(Consultation, pk=pk)

    if consultation.status != Consultation.Status.TRIAGED:
        messages.error(
            request,
            'This consultation has already been completed. Prescriptions can '
            'only be edited before the consultation is completed.'
        )
        return redirect('consultations:clinical_detail', pk=pk)

    prescription = consultation.prescriptions.first()
    if prescription is None:
        messages.error(request, 'No prescription has been made for this consultation yet.')
        return redirect('consultations:prescribe', pk=pk)

    # Snapshot BEFORE any form validation mutates the in-memory instance.
    before = _prescription_snapshot(prescription)

    initial_items = [_prescription_item_initial(i) for i in prescription.items.all()]

    # Include medicines that are currently prescribed even if they have run
    # out of stock, so they are not silently dropped from the edit form.
    existing_medicine_ids = list(
        prescription.items.exclude(medicine__isnull=True).values_list('medicine_id', flat=True)
    )
    inventory_medicines = Medicine.objects.filter(
        Q(quantity__gt=0) | Q(pk__in=existing_medicine_ids)
    ).order_by('name')

    if request.method == 'POST':
        prescription_form = PrescriptionForm(request.POST, instance=prescription)
        formset = PrescriptionMedicineFormSet(request.POST, prefix='meds')

        if prescription_form.is_valid() and formset.is_valid():
            item_rows = [f for f in formset if f.has_data()]
            global_instructions = request.POST.get('apply_instructions', '').strip()

            try:
                with transaction.atomic():
                    # 1) Return stock for every inventory-linked line so the
                    #    new list is deducted fresh (removed/reduced meds return stock).
                    for item in prescription.items.select_related('medicine').all():
                        if item.medicine and item.quantity:
                            item.medicine.add_stock(item.quantity)
                            StockMovement.objects.create(
                                medicine=item.medicine,
                                movement_type=StockMovement.MovementType.IN,
                                quantity=item.quantity,
                                reason=(
                                    f'Prescription #{prescription.pk} edit — stock returned '
                                    f'(Consultation #{consultation.pk})'
                                ),
                                reference=f'Prescription #{prescription.pk} edit',
                                created_by=request.user.username,
                            )

                    # 2) Replace the medicine lines
                    prescription.items.all().delete()

                    # 3) Update the prescription itself
                    prescription.diagnosis = prescription_form.cleaned_data['diagnosis']
                    prescription.treatment_plan = prescription_form.cleaned_data.get('treatment_plan', '')
                    prescription.save(update_fields=['diagnosis', 'treatment_plan'])

                    # 4) Recreate lines from the formset
                    for form in item_rows:
                        med           = form.cleaned_data.get('medicine')
                        medicine_name = form.cleaned_data.get('medicine_name', '').strip()
                        qty           = form.cleaned_data.get('quantity')

                        row_instructions   = form.cleaned_data.get('instructions', '').strip()
                        final_instructions = row_instructions or global_instructions

                        PrescriptionItem.objects.create(
                            prescription=prescription,
                            medicine=med,
                            medicine_name=med.name if med else medicine_name,
                            dosage=form.cleaned_data.get('dosage', '').strip(),
                            frequency=form.cleaned_data.get('frequency', '').strip(),
                            duration=form.cleaned_data.get('duration', '').strip(),
                            instructions=final_instructions,
                            # Persist the dispensed quantity so a later edit
                            # can restore the correct amount of stock.
                            quantity=qty,
                        )

                        if med and qty:
                            deduct_medicine_stock(
                                medicine_id=med.pk,
                                quantity=qty,
                                reason=(
                                    f'Consultation #{consultation.pk} — '
                                    f'{consultation.patient.get_full_name()}'
                                ),
                                user=request.user,
                            )
            except Exception as exc:
                messages.error(
                    request,
                    f'An unexpected error occurred: {exc}. Please try again.',
                )
            else:
                log_change(
                    user=request.user,
                    module='Consultations',
                    description=(
                        f'Amended prescription for consultation #{consultation.pk} — '
                        f'{consultation.patient.get_full_name()}'
                    ),
                    object_model='consultations.Prescription',
                    object_id=prescription.pk,
                    object_repr=str(prescription),
                    changes_before=before,
                    changes_after=_prescription_snapshot(prescription),
                    request=request,
                )
                messages.success(
                    request,
                    f'Prescription for Consultation #{consultation.pk} has been updated.'
                )
                return redirect('consultations:consultation_complete', pk=consultation.pk)

        # Fall through on validation errors → re-render with errors
    else:
        prescription_form = PrescriptionForm(instance=prescription)
        formset = PrescriptionMedicineFormSet(prefix='meds', initial=initial_items)

    return render(request, 'consultations/prescribe.html', {
        'consultation': consultation,
        'prescription': prescription,
        'prescription_form': prescription_form,
        'formset': formset,
        'inventory_medicines': inventory_medicines,
        'common_diagnoses': CommonDiagnosis.objects.all().order_by('name'),
        'base_template': _base_template(request.user),
        'edit_mode': True,
    })


# ─── CLINICAL STAFF SHARED VIEWS ──────────────────────────────────────────────

@login_required
@clinical_staff_required
def clinical_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    back_url = request.GET.get('next') or reverse('consultations:doctor_list')
    return render(request, 'consultations/clinical_detail.html', {
        'consultation': consultation,
        'base_template': _base_template(request.user),
        'back_url': back_url,
    })


# ─── MEDICAL HISTORY (MODULE 3) ───────────────────────────────────────────────

@login_required
@clinical_staff_required
def patient_medical_history(request, patient_pk):
    """
    Full medical history of a patient, assembled from consultations and prescriptions.
    Available to doctors and admins. Frontdesk cannot access.
    """
    from patients.models import Patient
    from django.db.models import Count, Q
    from datetime import date

    patient = get_object_or_404(Patient, pk=patient_pk)

    # Base queryset — all consultations for this patient
    consultations_qs = (
        Consultation.objects
        .filter(patient=patient)
        .prefetch_related('triages', 'prescriptions')
        .prefetch_related('prescriptions__items')
        .order_by('-created_at')
    )

    # Date range filter
    date_from_str = request.GET.get('date_from', '')
    date_to_str   = request.GET.get('date_to', '')
    keyword       = request.GET.get('keyword', '').strip()

    if date_from_str:
        try:
            date_from = date.fromisoformat(date_from_str)
            consultations_qs = consultations_qs.filter(created_at__date__gte=date_from)
        except ValueError:
            pass

    if date_to_str:
        try:
            date_to = date.fromisoformat(date_to_str)
            consultations_qs = consultations_qs.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    if keyword:
        consultations_qs = consultations_qs.filter(
            Q(prescriptions__diagnosis__icontains=keyword) |
            Q(prescriptions__items__medicine_name__icontains=keyword)
        ).distinct()

    consultations = list(consultations_qs)

    # Summary — computed from ALL consultations (no date/keyword filter)
    all_consultations = Consultation.objects.filter(patient=patient)
    total_count = all_consultations.count()
    first_visit = all_consultations.order_by('created_at').values_list('created_at', flat=True).first()
    last_visit  = all_consultations.order_by('-created_at').values_list('created_at', flat=True).first()

    # Most frequent diagnosis
    top_diagnosis = (
        Prescription.objects
        .filter(consultation__patient=patient)
        .values('diagnosis')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')
        .first()
    )

    # Most frequently prescribed medicine
    top_medicine = (
        PrescriptionItem.objects
        .filter(prescription__consultation__patient=patient)
        .values('medicine_name')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')
        .first()
    )

    # Get patient profile
    try:
        patient_profile = patient.profile
    except PatientProfile.DoesNotExist:
        patient_profile = None

    return render(request, 'consultations/medical_history.html', {
        'patient': patient,
        'patient_profile': patient_profile,
        'consultations': consultations,
        'total_count': total_count,
        'first_visit': first_visit,
        'last_visit': last_visit,
        'top_diagnosis': top_diagnosis,
        'top_medicine': top_medicine,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'keyword': keyword,
        'base_template': _base_template(request.user),
    })


@login_required
@doctor_required
def patient_medical_history_pdf(request, patient_pk):
    """Export patient medical history as PDF."""
    from patients.models import Patient
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    import io
    import html
    from datetime import date

    patient = get_object_or_404(Patient, pk=patient_pk)

    consultations = (
        Consultation.objects
        .filter(patient=patient)
        .prefetch_related('triages', 'prescriptions__items')
        .order_by('-created_at')
    )

    # Build PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, spaceAfter=6)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, spaceAfter=4, spaceBefore=10)
    body_style = styles['Normal']
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=9,
                                  textColor=colors.grey, spaceAfter=2)

    story = []

    # Header
    story.append(Paragraph('PATIENT RECORD SYSTEM', title_style))
    story.append(Paragraph('Patient Medical History', styles['Heading2']))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.3*cm))

    # Patient info table
    all_c = Consultation.objects.filter(patient=patient)
    total = all_c.count()
    first_v = all_c.order_by('created_at').values_list('created_at', flat=True).first()
    last_v  = all_c.order_by('-created_at').values_list('created_at', flat=True).first()

    info_data = [
        ['Patient Name', patient.get_full_name(), 'Patient ID', patient.patient_id],
        ['Sex', patient.get_sex_display(), 'Age', str(patient.age or '—')],
        ['Phone', patient.phone or '—', 'Email', patient.email or '—'],
        ['College/Dept',
         patient.college.name if patient.college else (patient.department or '—'),
         'Total Visits', str(total)],
        ['First Visit', first_v.strftime('%B %d, %Y') if first_v else '—',
         'Last Visit', last_v.strftime('%B %d, %Y') if last_v else '—'],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3*cm, 4*cm])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.grey),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.3*cm))

    # Timeline
    story.append(Paragraph('Consultation Timeline', h2_style))

    if not consultations:
        story.append(Paragraph('No consultations on record.', body_style))
    else:
        for c in consultations:
            story.append(Spacer(1, 0.2*cm))
            status_txt = c.get_status_display()
            header_txt = (
                f'<b>Consultation #{c.pk}</b> — '
                f'{c.created_at.strftime("%B %d, %Y")} — {status_txt}'
            )
            story.append(Paragraph(header_txt, body_style))
            # Show the doctor-reviewed chief complaint (fall back to the
            # patient's own words). Escaped — raw patient text can contain
            # XML-special characters that would otherwise break ReportLab.
            cc = c.chief_complaint or c.symptoms
            story.append(Paragraph(f'<i>Chief Complaint:</i> {html.escape(cc)}', small_style))
            if c.severity_description:
                # Patient-entered free text — escape so & / < can't crash ReportLab.
                story.append(Paragraph(
                    f'<i>Severity:</i> {html.escape(c.severity_description)}',
                    small_style,
                ))

            t = c.triages.first()
            if t:
                story.append(Paragraph(
                    f'<i>Vitals:</i> BP {t.blood_pressure} | '
                    f'Temp {t.temperature}°C | Pulse {t.pulse_rate} bpm | '
                    f'Urgency: {t.get_urgency_display()}',
                    small_style
                ))

            rx = c.prescriptions.first()
            if rx:
                story.append(Paragraph(f'<i>Diagnosis:</i> {rx.diagnosis}', small_style))
                if rx.treatment_plan:
                    story.append(Paragraph(f'<i>Treatment Plan:</i> {rx.treatment_plan}', small_style))
                items = rx.items.all()
                if items:
                    for item in items:
                        line = f'• {item.get_display_name()}'
                        if item.dosage:
                            line += f' {item.dosage}'
                        if item.frequency:
                            line += f' — {item.frequency}'
                        if item.duration:
                            line += f' for {item.duration}'
                        if item.instructions:
                            line += f' ({item.instructions})'
                        story.append(Paragraph(line, small_style))

            story.append(HRFlowable(width='100%', thickness=0.3, color=colors.lightgrey, spaceAfter=2))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f'Generated: {date.today().strftime("%B %d, %Y")} | Patient Record System',
        small_style
    ))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    safe_name = patient.patient_id.replace('/', '_')
    response['Content-Disposition'] = (
        f'attachment; filename="medical_history_{safe_name}.pdf"'
    )
    return response


# ─── FOLLOW-UP / CONSULTATION CONTINUATION VIEWS ─────────────────────────────

@login_required
@doctor_required
def follow_up_create(request, consultation_pk):
    """
    Doctor records a follow-up visit for an existing consultation.
    This creates a FollowUpProgress entry linked to the original consultation.
    """
    original_consultation = get_object_or_404(
        Consultation,
        pk=consultation_pk,
        is_original_case=True,
    )

    # Determine next visit number
    last_visit = original_consultation.progress_entries.order_by(
        '-visit_number'
    ).first()
    next_visit_number = (last_visit.visit_number + 1) if last_visit else 1

    form = FollowUpProgressForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        progress = form.save(commit=False)
        progress.consultation = original_consultation
        progress.visit_number = next_visit_number
        progress.doctor = request.user
        progress.follow_up_status = 'completed'
        progress.save()

        # Update original consultation
        original_consultation.follow_up_count = next_visit_number
        original_consultation.last_follow_up_date = progress.created_at


        if form.cleaned_data.get('requires_follow_up'):
            original_consultation.status = Consultation.Status.ACTIVE_FOLLOW_UP
            original_consultation.recommended_follow_up_date = form.cleaned_data.get('recommended_follow_up_date')
        else:
            original_consultation.status = Consultation.Status.COMPLETED

        original_consultation.save(
            update_fields=[
                'follow_up_count', 'last_follow_up_date', 'status', 'recommended_follow_up_date'
            ]
        )

        messages.success(
            request,
            f'Follow-up visit #{next_visit_number} recorded for '
            f'Consultation #{consultation_pk}.'
        )
        return redirect(
            'consultations:consultation_timeline',
            pk=consultation_pk
        )

    return render(request, 'consultations/follow_up_form.html', {
        'form': form,
        'consultation': original_consultation,
        'visit_number': next_visit_number,
        'base_template': _base_template(request.user),
    })


@login_required
@clinical_staff_required
def consultation_timeline(request, pk):
    """
    Staff view: Full timeline of a consultation case including all follow-ups.
    """
    consultation = get_object_or_404(
        Consultation.objects.select_related(
            'patient', 'patient__college',
        ).prefetch_related(
            'progress_entries',
            'triages',
            'prescriptions',
        ),
        pk=pk,
    )

    # Get all progress entries ordered by visit number
    progress_entries = consultation.progress_entries.all().order_by('visit_number')

    return render(request, 'consultations/timeline.html', {
        'consultation': consultation,
        'progress_entries': progress_entries,
        'base_template': _base_template(request.user),
    })


@login_required
@doctor_required
def close_consultation(request, pk):
    """
    Doctor closes a consultation case — no more follow-ups allowed.
    """
    consultation = get_object_or_404(
        Consultation,
        pk=pk,
        is_original_case=True,
    )

    if consultation.status == Consultation.Status.CLOSED:
        messages.info(request, f'Consultation #{pk} is already closed.')
        return redirect('consultations:consultation_timeline', pk=pk)

    form = CloseConsultationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        consultation.status = Consultation.Status.CLOSED
        consultation.closure_notes = form.cleaned_data['closure_notes']
        from django.utils import timezone
        consultation.closed_at = timezone.now()
        consultation.save(
            update_fields=['status', 'closure_notes', 'closed_at']
        )
        log_change(
            user=request.user,
            module='Consultations',
            description=f'Closed consultation case #{pk} — {consultation.patient.get_full_name()}',
            object_model='consultations.Consultation',
            object_id=consultation.pk,
            object_repr=str(consultation),
            changes_after={'status': 'closed'},
            request=request,
        )
        messages.success(request, f'Consultation case #{pk} has been closed.')
        return redirect('consultations:consultation_timeline', pk=pk)

    return render(request, 'consultations/close_consultation.html', {
        'form': form,
        'consultation': consultation,
        'base_template': _base_template(request.user),
    })


@login_required
@doctor_required
def patient_active_cases(request, patient_pk):
    """
    List all active/open consultation cases for a specific patient.
    """
    from patients.models import Patient

    patient = get_object_or_404(Patient, pk=patient_pk)

    active_cases = Consultation.objects.filter(
        patient=patient,
        is_original_case=True,
        status__in=[
            Consultation.Status.ACTIVE_FOLLOW_UP,
            Consultation.Status.TRIAGED,
            Consultation.Status.COMPLETED,
        ]
    ).order_by('-created_at')

    return render(request, 'consultations/patient_active_cases.html', {
        'patient': patient,
        'active_cases': active_cases,
        'base_template': _base_template(request.user),
    })


# ─── COMPLETION SUMMARY ──────────────────────────────────────────────────────

@login_required
@doctor_required
def completion_summary(request, pk):
    """
    Post-completion hub showing all clinical documents generated from this consultation.
    """
    consultation = get_object_or_404(
        Consultation.objects.select_related(
            'patient', 'patient__college', 'patient__profile',
        ).prefetch_related(
            'prescriptions__items',
            'certificates',
        ),
        pk=pk,
    )

    prescription = consultation.prescriptions.first()
    issued_certificate = consultation.certificates.filter(
        status=MedicalCertificate.Status.ISSUED
    ).first()
    draft_certificate = consultation.certificates.filter(
        status=MedicalCertificate.Status.DRAFT
    ).first()

    return render(request, 'consultations/completion_summary.html', {
        'consultation': consultation,
        'prescription': prescription,
        'issued_certificate': issued_certificate,
        'draft_certificate': draft_certificate,
        'base_template': _base_template(request.user),
    })


# ─── PRINTABLE CONSULTATION ────────────────────────────────────────────────────

@login_required
@clinical_staff_required
def print_consultation(request, pk):
    """
    Printable/single-page view of a consultation with all vitals,
    diagnosis, prescriptions — optimised for printing.
    Also includes follow-up visit records when available.
    """
    progress_entries_prefetch = Prefetch(
        'progress_entries',
        queryset=FollowUpProgress.objects
            .select_related('doctor')
            .prefetch_related('triages')
            .order_by('visit_number'),
    )

    consultation = get_object_or_404(
        Consultation.objects.select_related(
            'patient', 'patient__college', 'patient__profile',
        ).prefetch_related(
            'triages',
            'prescriptions__items',
            progress_entries_prefetch,
        ),
        pk=pk,
    )

    back_url = request.GET.get('next') or reverse('consultations:clinical_detail', args=[pk])

    return render(request, 'consultations/print_consultation.html', {
        'consultation': consultation,
        'back_url': back_url,
    })
