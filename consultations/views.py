from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.decorators import (
    frontdesk_required, nurse_required, doctor_required,
    admin_required, clinical_staff_required, patient_required,
)
from .models import Consultation, Triage, Prescription, PrescriptionItem
from .forms import (
    ConsultationSubmitForm, QueueAssignForm, TriageForm, TriageEditForm,
    PrescriptionForm, PrescriptionItemFormSet, PatientConsultationForm,
)
from .utils import assign_next_queue_number
from inventory.utils import deduct_medicine_stock


# ─── PATIENT VIEWS ────────────────────────────────────────────────────────────

@login_required
@patient_required
def patient_home(request):
    """Patient's own consultation history."""
    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    consultations = Consultation.objects.filter(
        patient=patient
    ).order_by('-created_at')

    return render(request, 'consultations/patient_home.html', {
        'consultations': consultations,
        'patient': patient,
    })


@login_required
@patient_required
def patient_submit(request):
    """Patient submits a new consultation request."""
    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    form = PatientConsultationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        consultation = form.save(commit=False)
        consultation.patient = patient
        consultation.status = Consultation.Status.PENDING
        consultation.save()
        messages.success(request, 'Your consultation request has been submitted.')
        return redirect('consultations:patient_home')

    return render(request, 'consultations/patient_submit.html', {'form': form})


@login_required
@patient_required
def patient_detail(request, pk):
    """Patient views one of their own consultations."""
    patient = request.user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    consultation = get_object_or_404(Consultation, pk=pk, patient=patient)
    return render(request, 'consultations/patient_detail.html', {
        'consultation': consultation,
    })


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
    """List pending consultation requests for front desk to process."""
    consultations = Consultation.objects.filter(
        status=Consultation.Status.PENDING
    ).select_related('patient', 'patient__college').order_by('created_at')
    return render(request, 'consultations/queue.html', {
        'consultations': consultations,
    })


@login_required
@frontdesk_required
def consultation_create(request):
    """Front desk creates a consultation on behalf of a walk-in patient."""
    form = ConsultationSubmitForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        consultation = form.save(commit=False)
        consultation.status = Consultation.Status.PENDING
        consultation.save()
        messages.success(
            request,
            f'Consultation created for {consultation.patient.get_full_name()}.'
        )
        return redirect('consultations:queue')
    return render(request, 'consultations/consultation_create.html', {'form': form})


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

    consultation.status = Consultation.Status.PENDING
    consultation.queue_number = None
    consultation.scheduled_at = None
    consultation.save(update_fields=['status', 'queue_number', 'scheduled_at'])
    messages.success(request, f'Consultation #{pk} has been reopened and returned to Pending.')
    return redirect('consultations:queue')


# ─── NURSE VIEWS ──────────────────────────────────────────────────────────────

@login_required
@nurse_required
def triage_list(request):
    consultations = Consultation.objects.filter(
        status__in=[Consultation.Status.QUEUED, Consultation.Status.SCHEDULED]
    ).select_related('patient', 'patient__college').order_by(
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
        messages.info(request, f'Consultation #{consultation.pk} has already been triaged.')
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
    consultation = get_object_or_404(Consultation, pk=pk)

    if not hasattr(consultation, 'triage'):
        messages.error(request, f'Consultation #{pk} has not been triaged yet.')
        return redirect('consultations:triage_list')

    if consultation.status == Consultation.Status.COMPLETED:
        messages.error(request, 'Triage records cannot be amended after a consultation is completed.')
        return redirect('consultations:triage_list')

    triage = consultation.triage
    form = TriageEditForm(request.POST or None, instance=triage)

    if request.method == 'POST' and form.is_valid():
        amended = form.save(commit=False)
        reason = form.cleaned_data['amendment_reason']
        amended.notes = (
            f"{triage.notes}\n\n[Amended by {request.user.username}: {reason}]"
            if triage.notes else f"[Amended by {request.user.username}: {reason}]"
        )
        amended.save()
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
    ).select_related('patient', 'triage', 'patient__college').order_by('created_at')
    return render(request, 'consultations/doctor_list.html', {
        'consultations': consultations,
    })


@login_required
@doctor_required
def prescribe(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk, status=Consultation.Status.TRIAGED)

    if hasattr(consultation, 'prescription'):
        messages.info(request, f'Consultation #{consultation.pk} already has a prescription.')
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
                        medicine     = form.cleaned_data['medicine']
                        quantity     = form.cleaned_data['quantity']
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
                messages.error(request, 'An unexpected error occurred. Please try again.')

    return render(request, 'consultations/prescribe.html', {
        'consultation': consultation,
        'prescription_form': prescription_form,
        'formset': formset,
    })


# ─── CLINICAL STAFF SHARED VIEWS ──────────────────────────────────────────────

@login_required
@clinical_staff_required
def clinical_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/clinical_detail.html', {
        'consultation': consultation,
    })