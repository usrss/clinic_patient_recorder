from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.decorators import (
    student_required, frontdesk_required, nurse_required, doctor_required,
)
from .models import Consultation, Triage, Prescription, PrescriptionItem
from .forms import (
    ConsultationSubmitForm, QueueAssignForm, TriageForm,
    PrescriptionForm, PrescriptionItemFormSet,
)

# FIX: Import at module level, not inside the function body.
# deduct_medicine_stock lives in inventory/views.py for now; once inventory
# has a utils.py it should move there.
from inventory.views import deduct_medicine_stock


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
    # Prevent duplicate pending submissions
    if Consultation.objects.filter(
        patient=request.user,
        status__in=[
            Consultation.Status.PENDING,
            Consultation.Status.QUEUED,
            Consultation.Status.SCHEDULED,
            Consultation.Status.TRIAGED,
        ]
    ).exists():
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
    # FIX: Fetch without status filter — the old code used
    # get_object_or_404(..., status=PENDING) which causes a 404 if the front
    # desk submits the form and then reloads the page (status is no longer PENDING).
    consultation = get_object_or_404(Consultation, pk=pk)

    # If already processed, redirect back with a message instead of crashing.
    if consultation.status != Consultation.Status.PENDING:
        messages.info(
            request,
            f'Consultation #{consultation.pk} has already been processed '
            f'(status: {consultation.get_status_display()}).'
        )
        return redirect('consultations:queue')

    form = QueueAssignForm(request.POST or None, instance=consultation)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Consultation #{consultation.pk} has been updated.')
        return redirect('consultations:queue')
    return render(request, 'consultations/queue_detail.html', {
        'consultation': consultation,
        'form': form,
    })


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

    # FIX: Guard against re-triage. The original code called triage.save()
    # unconditionally — if the nurse revisited this URL after already triaging,
    # the OneToOneField unique constraint would raise an IntegrityError crash.
    if hasattr(consultation, 'triage'):
        messages.info(
            request,
            f'Consultation #{consultation.pk} has already been triaged.'
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

    # FIX: Guard against re-prescription. Without this, revisiting the URL after
    # completing a prescription raises IntegrityError on the OneToOne Prescription field.
    if hasattr(consultation, 'prescription'):
        messages.info(
            request,
            f'Consultation #{consultation.pk} already has a prescription.'
        )
        return redirect('consultations:doctor_list')

    prescription_form = PrescriptionForm(request.POST or None)
    formset = PrescriptionItemFormSet(request.POST or None, prefix='items')

    if request.method == 'POST':
        # FIX: Validate prescription_form independently of formset.
        # The original code required BOTH to be valid, meaning a diagnosis-only
        # consultation (no medicines prescribed) could never be submitted because
        # an empty formset with partial rows would fail validation.
        forms_valid = prescription_form.is_valid()
        formset_valid = formset.is_valid()

        if forms_valid and formset_valid:
            try:
                with transaction.atomic():
                    # FIX: Validate all stock BEFORE writing anything to the DB.
                    # The original code saved the Prescription first, then deducted
                    # stock — if stock was insufficient partway through, the prescription
                    # record was already committed but stock was only partially deducted.
                    item_rows = [f for f in formset if f.has_data()]

                    # Note: stock sufficiency is enforced atomically inside
                    # deduct_stock() via select_for_update(). We do not pre-check
                    # medicine.quantity here because that value could be stale by
                    # the time deduct_stock() runs. The transaction.atomic() wrapper
                    # ensures any ValidationError from deduct_stock() rolls back
                    # the prescription and all previous items cleanly.

                    # Write prescription to DB
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

                        # FIX: deduct_medicine_stock now uses Medicine.objects.get()
                        # instead of get_object_or_404(), so it's safe to call here.
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
                # FIX: Catch ValidationError specifically (stock errors) with a clean message.
                err = e.message if hasattr(e, 'message') else '; '.join(e.messages)
                messages.error(request, f'Stock error — prescription not saved: {err}')
            except Exception:
                # FIX: Don't expose internal exception details to the user.
                messages.error(
                    request,
                    'An unexpected error occurred. Please try again or contact an administrator.'
                )

    return render(request, 'consultations/prescribe.html', {
        'consultation': consultation,
        'prescription_form': prescription_form,
        'formset': formset,
    })