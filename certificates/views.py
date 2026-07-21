from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from consultations.models import Consultation
from .models import MedicalCertificate, CertificateAuditLog, CertificateTemplateText, CertificateTemplateChangeLog
from .forms import CertificateTypeForm, CertificateDetailsForm, CertificateVoidForm, CertificateTemplateTextForm
from accounts.decorators import doctor_required, clinical_staff_required, admin_required
from audit_logs.services import log_create, log_audit_entry


def _base_template(user):
    """Return the correct base template for the current user's role."""
    if user.role == 'admin':
        return 'core/base_admin.html'
    return 'core/base_staff.html'
from certificates.services.docx_export import generate_certificate_docx_bytes, CertificateDocxError
from certificates.services.pdf_export import convert_docx_bytes_to_pdf, CertificatePdfError


# ─── HELPER ────────────────────────────────────────────────────────────────

def _log_audit(certificate, user, action, details=''):
    """Create an audit log entry for a certificate event."""
    CertificateAuditLog.objects.create(
        certificate=certificate,
        user=user,
        action=action,
        details=details,
    )


def _prefill_diagnosis(consultation):
    """
    Pre-fill diagnosis from the consultation's prescriptions.
    Returns (first_diagnosis, all_diagnoses_list).
    """
    prescriptions = consultation.prescriptions.all()
    all_diagnoses = [rx.diagnosis for rx in prescriptions if rx.diagnosis]
    first = all_diagnoses[0] if all_diagnoses else ''
    return first, all_diagnoses


def _get_issued_certificate(consultation):
    """Get the currently active (issued) certificate, if any."""
    return consultation.certificates.filter(
        status=MedicalCertificate.Status.ISSUED
    ).first()


# ─── STEP 1: CERTIFICATE TYPE SELECTION ────────────────────────────────────

@login_required
@doctor_required
def wizard_type(request, consultation_pk):
    """Step 1: Select certificate type."""
    consultation = get_object_or_404(Consultation, pk=consultation_pk)

    # Check if an issued certificate already exists
    existing = _get_issued_certificate(consultation)
    if existing:
        messages.info(request, 'An issued certificate already exists for this consultation.')
        return redirect('certificates:print_certificate', pk=existing.pk)

    # Check prescription exists
    if not consultation.prescriptions.exists():
        messages.error(request, 'The consultation must have a prescription before issuing a certificate.')
        return redirect('consultations:clinical_detail', pk=consultation.pk)

    form = CertificateTypeForm(request.POST or None)
    diagnoses, diagnosis_list = _prefill_diagnosis(consultation)

    if request.method == 'POST' and form.is_valid():
        cert_type = form.cleaned_data['certificate_type']

        # If multiple diagnoses exist, use the user's selection from the dropdown
        selected_diagnosis = request.POST.get('selected_diagnosis', '').strip()
        if not selected_diagnosis:
            selected_diagnosis = diagnoses  # fallback to pre-fill

        # Create DRAFT certificate within a transaction so that the audit
        # log is rolled back if certificate creation fails (and vice versa).
        with transaction.atomic():
            certificate = MedicalCertificate.objects.create(
                consultation=consultation,
                patient=consultation.patient,
                doctor=request.user,
                certificate_type=cert_type,
                status=MedicalCertificate.Status.DRAFT,
                diagnosis=selected_diagnosis,
            )
            _log_audit(certificate, request.user, 'created',
                       f'Draft created (type: {cert_type})')
            log_create(
                user=request.user,
                module='Medical Certificates',
                description=f'Created draft {cert_type} certificate — {consultation.patient.get_full_name()}',
                object_model='certificates.MedicalCertificate',
                object_id=certificate.pk,
                object_repr=str(certificate),
                request=request,
            )

        return redirect('certificates:wizard_details', pk=certificate.pk)

    return render(request, 'certificates/wizard_step1.html', {
        'consultation': consultation,
        'form': form,
        'diagnosis_list': diagnosis_list,
        'base_template': _base_template(request.user),
    })


# ─── STEP 2: CERTIFICATE DETAILS ───────────────────────────────────────────

@login_required
@doctor_required
def wizard_details(request, pk):
    """Step 2: Fill in certificate details (type-specific form)."""
    certificate = get_object_or_404(
        MedicalCertificate,
        pk=pk,
        doctor=request.user,
        status=MedicalCertificate.Status.DRAFT,
    )
    consultation = certificate.consultation

    form = CertificateDetailsForm(
        request.POST or None,
        instance=certificate,
        cert_type=certificate.certificate_type,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        _log_audit(certificate, request.user, 'updated', 'Details saved')
        return redirect('certificates:wizard_preview', pk=certificate.pk)

    return render(request, 'certificates/wizard_step2.html', {
        'certificate': certificate,
        'consultation': consultation,
        'form': form,
        'base_template': _base_template(request.user),
    })


# ─── STEP 3: PREVIEW + CONFIRM ─────────────────────────────────────────────

@login_required
@doctor_required
def wizard_preview(request, pk):
    """Step 3: Preview the certificate and confirm issuance."""
    certificate = get_object_or_404(
        MedicalCertificate.objects.select_related(
            'consultation__patient', 'consultation__patient__college',
            'consultation__patient__profile',
            'doctor',
        ),
        pk=pk,
        doctor=request.user,
        status=MedicalCertificate.Status.DRAFT,
    )

    if request.method == 'POST':
        try:
            with transaction.atomic():
                certificate.issue(user=request.user)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('consultations:completion_summary', pk=certificate.consultation_id)
        messages.success(
            request,
            f'{certificate.get_certificate_type_display()} '
            f'#{certificate.certificate_number} issued successfully.'
        )
        return redirect('certificates:print_certificate', pk=certificate.pk)

    return render(request, 'certificates/wizard_step3.html', {
        'certificate': certificate,
        'base_template': _base_template(request.user),
    })


# ─── PRINT / REPRINT ────────────────────────────────────────────────────────

@login_required
@clinical_staff_required
def print_certificate(request, pk):
    """Printable medical certificate — PDF-preview wrapper page.

    Only ISSUED certificates are printable. Drafts and voided certs
    return HTTP 403. Access is further scoped by user role (see
    clinic/institution check).

    Serves a thin HTML page with an embedded PDF preview and
    a "Download Word" button, replacing the old HTML-only print templates.
    """
    certificate = get_object_or_404(
        MedicalCertificate.objects.select_related(
            'consultation__patient', 'consultation__patient__college',
            'consultation__patient__profile',
            'doctor',
        ),
        pk=pk,
    )

    # ── Status guard: only issued certs are printable ────────────────
    if certificate.status != MedicalCertificate.Status.ISSUED:
        return HttpResponseForbidden('Only issued certificates can be printed.')

    # ── Clinic/institution access scoping ────────────────────────────
    if request.user.role == 'doctor' and certificate.doctor != request.user:
        return HttpResponseForbidden(
            'You can only print certificates you issued.'
        )

    # ── Audit logging: view vs print ─────────────────────────────────
    viewed_exists = certificate.audit_logs.filter(
        action='viewed', user=request.user
    ).exists()

    if viewed_exists:
        _log_audit(certificate, request.user, 'printed',
                   f'Printed by {request.user.get_full_name() or request.user.username}')
    else:
        _log_audit(certificate, request.user, 'viewed',
                   f'Viewed by {request.user.get_full_name() or request.user.username}')

    # ── Render the PDF-preview wrapper page ──────────────────────────
    return render(request, 'certificates/certificate_preview.html', {
        'certificate': certificate,
        'base_template': _base_template(request.user),
    })


# ─── CERTIFICATE PDF PREVIEW (raw PDF for iframe) ─────────────────────────

@login_required
@clinical_staff_required
@xframe_options_exempt
def certificate_pdf_preview(request, pk):
    """Return the raw PDF bytes for a certificate, embedded in an iframe.

    Generates a .docx from the template, converts it to PDF via
    LibreOffice, and serves the PDF inline.
    The @xframe_options_exempt decorator allows this to load in
    an iframe on the certificate preview page.
    """
    certificate = get_object_or_404(MedicalCertificate, pk=pk)

    # Allow DRAFT preview for the owning doctor (wizard step 3)
    if certificate.status == MedicalCertificate.Status.DRAFT:
        if request.user.role != 'doctor' or certificate.doctor != request.user:
            return HttpResponse('You can only preview your own draft certificates.', status=403)
    elif certificate.status == MedicalCertificate.Status.ISSUED:
        if request.user.role == 'doctor' and certificate.doctor != request.user:
            return HttpResponse('You can only preview certificates you issued.', status=403)
    else:
        return HttpResponse('Certificate cannot be previewed in its current state.', status=403)

    try:
        docx_bytes = generate_certificate_docx_bytes(certificate)
        pdf_bytes = convert_docx_bytes_to_pdf(docx_bytes)
    except (CertificateDocxError, CertificatePdfError):
        return HttpResponse('Certificate preview could not be generated.', status=500)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="certificate_{certificate.pk}_preview.pdf"'
    return response


# ─── DOWNLOAD .DOCX ────────────────────────────────────────────────────────

@login_required
@clinical_staff_required
def download_certificate_docx(request, pk):
    """Download the certificate as an editable .docx file."""
    certificate = get_object_or_404(MedicalCertificate, pk=pk)

    if certificate.status != MedicalCertificate.Status.ISSUED:
        return HttpResponse('Only issued certificates can be downloaded.', status=403)

    if request.user.role == 'doctor' and certificate.doctor != request.user:
        return HttpResponse('You can only download certificates you issued.', status=403)

    try:
        docx_bytes = generate_certificate_docx_bytes(certificate)
    except CertificateDocxError:
        return HttpResponse('Certificate could not be generated as a Word document.', status=500)

    # Log the download action
    _log_audit(certificate, request.user, 'downloaded_docx',
               f'Downloaded .docx by {request.user.get_full_name() or request.user.username}')

    filename = f'{certificate.certificate_number or certificate.pk}.docx'
    response = HttpResponse(
        docx_bytes,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─── DISCARD DRAFT ──────────────────────────────────────────────────────────

@login_required
@doctor_required
def discard_draft(request, pk):
    """Discard a draft certificate (voids it so the user can start over)."""
    certificate = get_object_or_404(
        MedicalCertificate,
        pk=pk,
        doctor=request.user,
        status=MedicalCertificate.Status.DRAFT,
    )

    if request.method == 'POST':
        certificate.status = MedicalCertificate.Status.VOIDED
        certificate.save(update_fields=['status'])
        _log_audit(certificate, request.user, 'voided', 'Discarded by user to start over')
        log_audit_entry(
            user=request.user,
            action='DELETE',
            module='Medical Certificates',
            description=f'Discarded draft certificate — {certificate.patient_name}',
            object_model='certificates.MedicalCertificate',
            object_id=certificate.pk,
            object_repr=str(certificate),
            request=request,
        )
        messages.info(request, 'Draft discarded. You can now issue a new certificate.')
        return redirect('certificates:wizard_type', consultation_pk=certificate.consultation_id)

    return redirect('consultations:completion_summary', pk=certificate.consultation_id)


# ─── VOID CERTIFICATE ───────────────────────────────────────────────────────

@login_required
@doctor_required
def void_certificate(request, pk):
    """Void an issued certificate."""
    certificate = get_object_or_404(
        MedicalCertificate,
        pk=pk,
        status=MedicalCertificate.Status.ISSUED,
    )

    if request.method == 'POST':
        form = CertificateVoidForm(request.POST)
        if form.is_valid():
            certificate.void(user=request.user, reason=form.cleaned_data['reason'])
            log_audit_entry(
                user=request.user,
                action='DELETE',
                module='Medical Certificates',
                description=f'Voided certificate #{certificate.certificate_number} — {certificate.patient_name}',
                object_model='certificates.MedicalCertificate',
                object_id=certificate.pk,
                object_repr=str(certificate),
                request=request,
            )
            messages.success(request, f'Certificate #{certificate.certificate_number} has been voided.')
            return redirect('consultations:completion_summary', pk=certificate.consultation_id)
    else:
        form = CertificateVoidForm()

    return render(request, 'certificates/certificate_void.html', {
        'certificate': certificate,
        'form': form,
        'base_template': _base_template(request.user),
    })


# ─── TEMPLATE TEXT EDITOR ───────────────────────────────────────────────────

@login_required
@admin_required
def template_text_list(request):
    """List all editable template text slots, grouped by certificate type."""
    order = ['standard', 'fit_to_work', 'fit_to_play']
    grouped = {}
    for ct in order:
        rows = CertificateTemplateText.objects.filter(certificate_type=ct)
        if rows.exists():
            grouped[ct] = rows

    return render(request, 'certificates/template_text_list.html', {
        'grouped': grouped,
    })


@login_required
@admin_required
def template_text_edit(request, pk):
    """Edit a single template text slot."""
    slot = get_object_or_404(CertificateTemplateText, pk=pk)

    if request.method == 'POST':
        form = CertificateTemplateTextForm(request.POST, instance=slot)
        if form.is_valid():
            old_text = slot.text
            new_text = form.cleaned_data['text']

            slot.text = new_text
            slot.updated_by = request.user
            slot.save()  # save() calls full_clean() which rejects HTML

            # Log the change
            CertificateTemplateChangeLog.objects.create(
                slot=slot,
                user=request.user,
                old_text=old_text,
                new_text=new_text,
            )

            messages.success(request, f'"{slot.slot_key}" updated successfully.')
            return redirect('certificates:template_text_list')
    else:
        form = CertificateTemplateTextForm(instance=slot)

    return render(request, 'certificates/template_text_edit.html', {
        'slot': slot,
        'form': form,
    })