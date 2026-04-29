from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from notifications.utils import notify_role, notify_user
from django.core.exceptions import ValidationError

from accounts.decorators import (
    frontdesk_required, nurse_required, doctor_required,
    admin_required, clinical_staff_required, patient_required,
)
from inventory.models import Medicine
from patients.models import PatientProfile
from .models import Consultation, Triage, Prescription, PrescriptionItem
from .forms import (
    ConsultationSubmitForm, QueueAssignForm, TriageForm, TriageEditForm,
    PrescriptionForm, PrescriptionItemFormSet, PrescriptionMedicineFormSet,
    PatientConsultationForm,
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
        notify_role('frontdesk',
                    'New Consultation Request',
                    f'{patient.get_full_name()} submitted a consultation request.',
                    f'/consultations/queue/{consultation.pk}/')
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
        notify_role('frontdesk',
                    'New Consultation Request',
                    f'{consultation.patient.get_full_name()} submitted a consultation request.'
                    f'/consultations/queue/{consultation.pk}/')
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
                notify_role('nurse',
                            'Patient Queued for Triage',
                            f'{consultation.patient.get_full_name()} is ready for triage.',
                            f'/consultations/triage/{consultation.pk}/')
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
        notify_role('doctor',
                    'Patient Ready for Consultation',
                    f'{consultation.patient.get_full_name()} has been triaged and is ready.',
                    f'/consultations/prescribe/{consultation.pk}/')
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
    """
    Doctor creates a prescription using free-text medicine rows.
    Each row must have medicine name, dosage, frequency, duration (instructions optional).
    At least one medicine row must be filled. Saving is atomic.
    """
    consultation = get_object_or_404(Consultation, pk=pk, status=Consultation.Status.TRIAGED)

    if hasattr(consultation, 'prescription'):
        messages.info(request, f'Consultation #{consultation.pk} already has a prescription.')
        return redirect('consultations:print_consultation', pk=consultation.pk)

    prescription_form = PrescriptionForm(request.POST or None)
    formset = PrescriptionMedicineFormSet(request.POST or None, prefix='meds')

    if request.method == 'POST':
        forms_valid = prescription_form.is_valid()
        formset_valid = formset.is_valid()

        if forms_valid and formset_valid:
            # Collect rows that actually have data
            item_rows = [f for f in formset if f.has_data()]

            if not item_rows:
                messages.error(
                    request,
                    'At least one medicine must be added to the prescription.'
                )
            else:
                try:
                    with transaction.atomic():
                        prescription = prescription_form.save(commit=False)
                        prescription.consultation = consultation
                        prescription.doctor = request.user
                        prescription.save()

                        for form in item_rows:
                            med = form.cleaned_data.get('medicine')
                            med_name = form.cleaned_data.get('medicine_name', '').strip()
                            qty = form.cleaned_data.get('quantity')

                            # Determine medicine name: inventory name or custom text
                            display_name = med.name if med else med_name

                            PrescriptionItem.objects.create(
                                prescription=prescription,
                                medicine=med,  # FK to inventory (null if custom)
                                medicine_name=display_name,
                                dosage=form.cleaned_data.get('dosage', '').strip(),
                                frequency=form.cleaned_data.get('frequency', '').strip(),
                                duration=form.cleaned_data.get('duration', '').strip(),
                                instructions=form.cleaned_data.get('instructions', '').strip(),
                            )

                            # Auto-deduct from inventory if inventory medicine selected
                            if med and qty:
                                deduct_medicine_stock(
                                    medicine_id=med.pk,
                                    quantity=qty,
                                    reason=f'Consultation #{consultation.pk} — {consultation.patient.get_full_name()}',
                                    user=request.user,
                                )

                        consultation.status = Consultation.Status.COMPLETED
                        consultation.save(update_fields=['status'])

                    messages.success(
                        request,
                        f'Prescription saved. Consultation #{consultation.pk} is now completed.'
                    )
                    return redirect('consultations:print_consultation', pk=consultation.pk)

                except Exception:
                    messages.error(request, 'An unexpected error occurred. Please try again.')

    return render(request, 'consultations/prescribe.html', {
        'consultation': consultation,
        'prescription_form': prescription_form,
        'formset': formset,
        'inventory_medicines': Medicine.objects.filter(quantity__gt=0).order_by('name'),
    })


# ─── CLINICAL STAFF SHARED VIEWS ──────────────────────────────────────────────

@login_required
@clinical_staff_required
def clinical_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'consultations/clinical_detail.html', {
        'consultation': consultation,
    })


# ─── MEDICAL HISTORY (MODULE 3) ───────────────────────────────────────────────

@login_required
@doctor_required
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
        .select_related('triage', 'prescription')
        .prefetch_related('prescription__items')
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
            Q(prescription__diagnosis__icontains=keyword) |
            Q(prescription__items__medicine_name__icontains=keyword)
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
    from datetime import date

    patient = get_object_or_404(Patient, pk=patient_pk)

    consultations = (
        Consultation.objects
        .filter(patient=patient)
        .select_related('triage', 'prescription')
        .prefetch_related('prescription__items')
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
    story.append(Paragraph('CLINIC RECORDER', title_style))
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
         patient.college.abbreviation if patient.college else (patient.department or '—'),
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
            # Entry header
            status_txt = c.get_status_display()
            header_txt = (
                f'<b>Consultation #{c.pk}</b> — '
                f'{c.created_at.strftime("%B %d, %Y")} — {status_txt}'
            )
            story.append(Paragraph(header_txt, body_style))
            story.append(Paragraph(f'<i>Symptoms:</i> {c.symptoms}', small_style))
            if c.severity_description:
                story.append(Paragraph(f'<i>Severity:</i> {c.severity_description}', small_style))

            if hasattr(c, 'triage') and c.triage:
                t = c.triage
                story.append(Paragraph(
                    f'<i>Vitals:</i> BP {t.blood_pressure} | '
                    f'Temp {t.temperature}°C | Pulse {t.pulse_rate} bpm | '
                    f'Urgency: {t.get_urgency_display()}',
                    small_style
                ))

            if hasattr(c, 'prescription') and c.prescription:
                rx = c.prescription
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
        f'Generated: {date.today().strftime("%B %d, %Y")} | Clinic Recorder',
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

# ─── PRINTABLE CONSULTATION ────────────────────────────────────────────────────

@login_required
@clinical_staff_required
def print_consultation(request, pk):
    """
    Printable/single-page view of a consultation with all vitals,
    diagnosis, prescriptions — optimised for printing.
    """
    consultation = get_object_or_404(
        Consultation.objects.select_related(
            'patient', 'patient__college', 'patient__profile',
            'triage', 'prescription',
        ).prefetch_related('prescription__items'),
        pk=pk,
    )

    return render(request, 'consultations/print_consultation.html', {
        'consultation': consultation,
    })