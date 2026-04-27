from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.decorators import (
    student_required, frontdesk_required, nurse_required, doctor_required,
    admin_required, clinical_staff_required,
)
from .models import Consultation, Triage, Prescription, PrescriptionItem
from .forms import (
    ConsultationSubmitForm, QueueAssignForm, TriageForm, TriageEditForm,
    PrescriptionForm, PrescriptionItemFormSet,
)
from .utils import assign_next_queue_number
from inventory.utils import deduct_medicine_stock


# ─── STUDENT VIEWS ────────────────────────────────────────────────────────────

@login_required
@student_required
def student_home(request):
    consultations = Consultation.objects.filter(patient=request.user)
    return render(request, 'consultations/student_home.html', {
        'consultations': consultations,
    })


@login_required
@student_required
def student_submit(request):
    active_statuses = [
        Consultation.Status.PENDING,
        Consultation.Status.QUEUED,
        Consultation.Status.SCHEDULED,
        Consultation.Status.TRIAGED,
    ]
    if Consultation.objects.filter(patient=request.user, status__in=active_statuses).exists():
        messages.warning(
            request,
            'You already have an active consultation in progress. '
            'Please wait for it to be completed before submitting a new one.'
        )
        return redirect('consultations:student_home')

    form = ConsultationSubmitForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        consultation = form.save(commit=False)
        consultation.patient = request.user
        consultation.status = Consultation.Status.PENDING
        consultation.save()
        messages.success(request, 'Your consultation request has been submitted successfully.')
        return redirect('consultations:student_home')
    return render(request, 'consultations/student_submit.html', {'form': form})


@login_required
@student_required
def student_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk, patient=request.user)
    return render(request, 'consultations/student_detail.html', {
        'consultation': consultation,
    })


@login_required
@student_required
def student_cancel(request, pk):
    """
    FIX GAP 6: Students can cancel their own PENDING consultation.
    Only PENDING is allowed — once queued, the front desk owns it.
    POST-only to prevent accidental cancellation via GET.
    """
    consultation = get_object_or_404(Consultation, pk=pk, patient=request.user)

    if request.method != 'POST':
        return redirect('consultations:student_detail', pk=pk)

    if consultation.status != Consultation.Status.PENDING:
        messages.error(
            request,
            'Only pending consultations can be cancelled. '
            'Please contact the front desk if you need to cancel a queued or scheduled appointment.'
        )
        return redirect('consultations:student_detail', pk=pk)

    consultation.status = Consultation.Status.CANCELLED
    consultation.save(update_fields=['status'])
    messages.success(request, f'Consultation #{consultation.pk} has been cancelled.')
    return redirect('consultations:student_home')


# ─── FRONT DESK VIEWS ─────────────────────────────────────────────────────────

@login_required
@frontdesk_required
def queue(request):
    consultations = Consultation.objects.filter(
        status=Consultation.Status.PENDING
    ).select_related('patient', 'patient__student_profile').order_by('created_at')
    return render(request, 'consultations/queue.html', {
        'consultations': consultations,
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

    form = QueueAssignForm(request.POST or None, instance=consultation)
    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        # FIX GAP 1: Auto-assign queue number — no manual input, no duplicates
        if instance.status == Consultation.Status.QUEUED:
            with transaction.atomic():
                instance.queue_number = assign_next_queue_number()
                instance.save()
        else:
            instance.save()
        messages.success(
            request,
            f'Consultation #{consultation.pk} updated. '
            + (f'Queue number: #{instance.queue_number}' if instance.queue_number else '')
        )
        return redirect('consultations:queue')

    return render(request, 'consultations/queue_detail.html', {
        'consultation': consultation,
        'form': form,
    })


@login_required
@frontdesk_required
def frontdesk_cancel(request, pk):
    """
    FIX GAP 4 (partial): Front desk can cancel PENDING or QUEUED/SCHEDULED
    consultations. POST-only with a required reason.
    """
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

    consultation.status = Consultation.Status.CANCELLED
    consultation.save(update_fields=['status'])
    messages.success(request, f'Consultation #{pk} has been cancelled.')
    return redirect('consultations:queue')


# ─── ADMIN REOPEN VIEW ────────────────────────────────────────────────────────

@login_required
@admin_required
def admin_reopen(request, pk):
    """
    FIX GAP 4: Admin can reopen a CANCELLED consultation back to PENDING.
    POST-only. This is the escape hatch for accidental cancellations.
    """
    if request.method != 'POST':
        return redirect('accounts:dashboard')

    consultation = get_object_or_404(Consultation, pk=pk)
    if consultation.status != Consultation.Status.CANCELLED:
        messages.error(request, 'Only cancelled consultations can be reopened.')
        return redirect('consultations:queue')

    consultation.status = Consultation.Status.PENDING
    consultation.queue_number = None
    consultation.scheduled_at = None
    consultation.save(update_fields=['status', 'queue_number', 'scheduled_at'])
    messages.success(
        request,
        f'Consultation #{pk} has been reopened and returned to Pending.'
    )
    return redirect('consultations:queue')


# ─── NURSE VIEWS ──────────────────────────────────────────────────────────────

@login_required
@nurse_required
def triage_list(request):
    consultations = Consultation.objects.filter(
        status__in=[Consultation.Status.QUEUED, Consultation.Status.SCHEDULED]
    ).select_related('patient', 'patient__student_profile').order_by(
        'queue_number', 'scheduled_at', 'created_at'
    )
    return render(request, 'consultations/triage_list.html', {
        'consultations': consultations,
    })


@login_required
@nurse_required
def triage_form(request, pk):
    consultation = get_object_or_404(
        Consultation, pk=pk,
        status__in=[Consultation.Status.QUEUED, Consultation.Status.SCHEDULED],
    )

    if hasattr(consultation, 'triage'):
        messages.info(
            request,
            f'Consultation #{consultation.pk} has already been triaged. '
            f'Use the edit option to amend the record.'
        )
        return redirect('consultations:triage_list')

    form = TriageForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        triage = form.save(commit=False)
        triage.consultation = consultation
        triage.nurse = request.user
        triage.save()
        consultation.status = Consultation.Status.TRIAGED
        consultation.save(update_fields=['status'])
        messages.success(request, f'Triage complete for Consultation #{consultation.pk}.')
        return redirect('consultations:triage_list')

    return render(request, 'consultations/triage_form.html', {
        'consultation': consultation,
        'form': form,
    })


@login_required
@nurse_required
def triage_edit(request, pk):
    """
    FIX GAP 3: Allow nurse/admin to amend a triage record after the fact.
    Requires a mandatory amendment reason for accountability.
    The original nurse and triaged_at timestamp are preserved.
    """
    consultation = get_object_or_404(Consultation, pk=pk)

    if not hasattr(consultation, 'triage'):
        messages.error(request, f'Consultation #{pk} has not been triaged yet.')
        return redirect('consultations:triage_list')

    # Only allow amendment if consultation hasn't been completed
    if consultation.status == Consultation.Status.COMPLETED:
        messages.error(
            request,
            'Triage records cannot be amended after a consultation is completed.'
        )
        return redirect('consultations:triage_list')

    triage = consultation.triage
    form = TriageEditForm(request.POST or None, instance=triage)

    if request.method == 'POST' and form.is_valid():
        amended_triage = form.save(commit=False)
        # Append amendment reason to notes for audit trail
        reason = form.cleaned_data['amendment_reason']
        amended_triage.notes = (
            f"{triage.notes}\n\n[Amended by {request.user.username}: {reason}]"
            if triage.notes else f"[Amended by {request.user.username}: {reason}]"
        )
        amended_triage.save()
        messages.success(request, f'Triage record for Consultation #{pk} has been updated.')
        return redirect('consultations:triage_list')

    return render(request, 'consultations/triage_edit.html', {
        'consultation': consultation,
        'triage': triage,
        'form': form,
    })


# ─── DOCTOR VIEWS ─────────────────────────────────────────────────────────────

@login_required
@doctor_required
def doctor_list(request):
    consultations = Consultation.objects.filter(
        status=Consultation.Status.TRIAGED
    ).select_related('patient', 'triage', 'patient__student_profile').order_by('created_at')
    return render(request, 'consultations/doctor_list.html', {
        'consultations': consultations,
    })


@login_required
@doctor_required
def prescribe(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk, status=Consultation.Status.TRIAGED)

    if hasattr(consultation, 'prescription'):
        messages.info(
            request,
            f'Consultation #{consultation.pk} already has a prescription.'
        )
        return redirect('consultations:doctor_list')

    prescription_form = PrescriptionForm(request.POST or None)
    formset = PrescriptionItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST':
        forms_valid = prescription_form.is_valid()
        formset_valid = formset.is_valid()

        if forms_valid and formset_valid:
            try:
                with transaction.atomic():
                    item_rows = [f for f in formset if f.has_data()]

                    prescription = prescription_form.save(commit=False)
                    prescription.consultation = consultation
                    prescription.doctor = request.user
                    prescription.save()

                    for form in item_rows:
                        medicine = form.cleaned_data['medicine']
                        quantity = form.cleaned_data['quantity']
                        instructions = form.cleaned_data['instructions']

                        PrescriptionItem.objects.create(
                            prescription=prescription,
                            medicine=medicine,
                            quantity=quantity,
                            instructions=instructions,
                        )

                        deduct_medicine_stock(
                            medicine_id=medicine.pk,
                            quantity=quantity,
                            reason=f'Consultation #{consultation.pk}',
                            user=request.user,
                        )

                    consultation.status = Consultation.Status.COMPLETED
                    consultation.save(update_fields=['status'])

                    messages.success(
                        request,
                        f'Prescription saved. Consultation #{consultation.pk} is now completed.'
                    )
                    return redirect('consultations:doctor_list')

            except ValidationError as e:
                err = e.message if hasattr(e, 'message') else '; '.join(e.messages)
                messages.error(request, f'Stock error — prescription not saved: {err}')
            except Exception:
                messages.error(
                    request,
                    'An unexpected error occurred. Please try again or contact an administrator.'
                )

    return render(request, 'consultations/prescribe.html', {
        'consultation': consultation,
        'prescription_form': prescription_form,
        'formset': formset,
    })


# ─── CLINICAL STAFF — SHARED DETAIL VIEW ──────────────────────────────────────

@login_required
@clinical_staff_required
def clinical_detail(request, pk):
    """
    FIX GAP (bonus): Full consultation detail for clinical staff.
    Nurses and doctors can view any consultation's full history —
    triage vitals, prescription, medicines dispensed.
    """
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/clinical_detail.html', {
        'consultation': consultation,
    })