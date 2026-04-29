from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from consultations.models import Consultation
from .models import MedicalCertificate
from .forms import MedicalCertificateForm
from accounts.decorators import doctor_required, clinical_staff_required


@login_required
@doctor_required
def create_certificate(request, consultation_pk):
    """Create a medical certificate for a completed consultation."""
    consultation = get_object_or_404(Consultation, pk=consultation_pk)

    if hasattr(consultation, 'certificate'):
        return redirect('certificates:print_certificate', pk=consultation.certificate.pk)

    if not hasattr(consultation, 'prescription'):
        messages.error(request, 'The consultation must have a prescription before issuing a certificate.')
        return redirect('consultations:clinical_detail', pk=consultation.pk)

    # Pre-fill diagnosis from prescription
    initial = {
        'diagnosis': consultation.prescription.diagnosis,
    }

    form = MedicalCertificateForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        certificate = form.save(commit=False)
        certificate.consultation = consultation
        certificate.doctor = request.user
        certificate.save()
        messages.success(request, f'{certificate.get_certificate_type_display()} issued successfully.')
        return redirect('certificates:print_certificate', pk=certificate.pk)

    return render(request, 'certificates/certificate_form.html', {
        'consultation': consultation,
        'form': form,
    })


@login_required
@clinical_staff_required
def print_certificate(request, pk):
    """Printable medical certificate."""
    certificate = get_object_or_404(
        MedicalCertificate.objects.select_related(
            'consultation__patient', 'consultation__patient__college',
            'consultation__prescription', 'doctor',
        ),
        pk=pk,
    )

    # Select template based on certificate type
    template_map = {
        MedicalCertificate.CertificateType.STANDARD: 'certificates/certificate_standard.html',
        MedicalCertificate.CertificateType.FIT_TO_PLAY: 'certificates/certificate_fit_to_play.html',
        MedicalCertificate.CertificateType.FIT_TO_WORK: 'certificates/certificate_fit_to_work.html',
        MedicalCertificate.CertificateType.DENTAL: 'certificates/certificate_dental.html',
    }

    template_name = template_map.get(certificate.certificate_type, 'certificates/certificate_standard.html')

    return render(request, template_name, {
        'certificate': certificate,
    })