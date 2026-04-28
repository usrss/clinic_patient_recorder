from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from accounts.decorators import clinical_staff_required
from accounts.models import User
from consultations.models import Consultation
from .models import Patient, PatientProfile
from .forms import PatientProfileSetupForm, PatientSearchForm


@login_required
@clinical_staff_required
def patient_list(request):
    form = PatientSearchForm(request.GET or None)
    patients = Patient.objects.select_related('college', 'profile').filter(is_active=True)

    query = ''
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        if query:
            patients = patients.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(middle_name__icontains=query) |
                Q(patient_id__icontains=query) |
                Q(college__name__icontains=query) |
                Q(college__abbreviation__icontains=query) |
                Q(department__icontains=query)
            )

    patients = patients.order_by('last_name', 'first_name')

    return render(request, 'patients/patient_list.html', {
        'patients': patients,
        'form': form,
        'query': query,
    })


@login_required
@clinical_staff_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    profile = getattr(patient, 'profile', None)
    consultations = Consultation.objects.filter(
        patient=patient
    ).select_related('triage', 'prescription').order_by('-created_at')

    return render(request, 'patients/patient_detail.html', {
        'patient': patient,
        'profile': profile,
        'consultations': consultations,
    })


@login_required
def patient_profile_setup(request, pk):
    user = request.user

    # Patients can only access their own profile setup
    if user.role == User.Role.PATIENT:
        patient_record = user.get_patient_record()
        if patient_record is None or patient_record.pk != pk:
            messages.error(request, 'You do not have permission to access that page.')
            return redirect('accounts:dashboard')
    elif not user.is_clinical_staff:
        # Any other non-staff role is rejected
        messages.error(request, 'You do not have permission to access that page.')
        return redirect('accounts:dashboard')

    patient = get_object_or_404(Patient, pk=pk)
    profile, _ = PatientProfile.objects.get_or_create(patient=patient)
    form = PatientProfileSetupForm(request.POST or None, instance=profile)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Profile updated for {patient.get_full_name()}.')
        # Patients go back to dashboard; staff go to patient detail
        if user.role == User.Role.PATIENT:
            return redirect('accounts:dashboard')
        return redirect('patients:patient_detail', pk=pk)

    return render(request, 'patients/patient_profile_setup.html', {
        'patient': patient,
        'form': form,
    })