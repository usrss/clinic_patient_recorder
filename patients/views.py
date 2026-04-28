from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

from accounts.decorators import clinical_staff_required
from accounts.models import User
from consultations.models import Consultation
from .models import Patient, PatientProfile
from .forms import (
    PatientFullProfileSetupForm, PatientProfileSetupForm,
    PatientSearchForm, PatientContactForm,
)


def _require_profile_complete(user, patient):
    """
    Return a redirect if the patient's profile is not yet complete,
    None otherwise. Use this as a guard in patient-role views.
    """
    if not patient.is_profile_complete:
        return redirect('patients:patient_full_profile_setup', pk=patient.pk)
    return None


@login_required
@clinical_staff_required
def patient_list(request):
    form = PatientSearchForm(request.GET or None)

    # ── Only show patients who have logged in at least once ────────────────
    patients = Patient.objects.select_related('college', 'profile').filter(
        is_active=True,
        has_logged_in=True,
    )

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

    # Count for info banner — all registered vs active+logged-in
    total_registered = Patient.objects.filter(is_active=True).count()

    return render(request, 'patients/patient_list.html', {
        'patients': patients,
        'form': form,
        'query': query,
        'total_registered': total_registered,
        'showing_active': patients.count(),
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
def patient_full_profile_setup(request, pk):
    """
    FORCED profile setup for patients on first login.
    Collects: birthday, phone, email, emergency contact, blood type,
    known allergies, existing conditions, and home address.
    Cannot be skipped until all required fields are filled.
    """
    user = request.user

    # Access control: patients can only access their own profile
    if user.role == User.Role.PATIENT:
        patient_record = user.get_patient_record()
        if patient_record is None or patient_record.pk != pk:
            messages.error(request, 'You do not have permission to access that page.')
            return redirect('accounts:dashboard')
    elif not user.is_clinical_staff:
        messages.error(request, 'You do not have permission to access that page.')
        return redirect('accounts:dashboard')

    patient = get_object_or_404(Patient, pk=pk)
    profile, _ = PatientProfile.objects.get_or_create(patient=patient)

    # Pre-populate contact fields from Patient model
    patient_initial = {
        'phone': patient.phone,
        'email': patient.email,
        'emergency_contact_name': patient.emergency_contact_name,
        'emergency_contact_phone': patient.emergency_contact_phone,
    }

    if request.method == 'POST':
        form = PatientFullProfileSetupForm(request.POST, instance=profile)
        if form.is_valid():
            with transaction.atomic():
                profile_instance = form.save(commit=False)
                profile_instance.profile_completed = True
                profile_instance.save()

                # Update contact fields on Patient model
                patient.phone = form.cleaned_data['phone']
                patient.email = form.cleaned_data.get('email', '')
                patient.emergency_contact_name = form.cleaned_data['emergency_contact_name']
                patient.emergency_contact_phone = form.cleaned_data['emergency_contact_phone']
                patient.save(update_fields=[
                    'phone', 'email',
                    'emergency_contact_name', 'emergency_contact_phone',
                ])

            messages.success(request, 'Profile setup complete. Welcome to the Clinic!')
            if user.role == User.Role.PATIENT:
                return redirect('accounts:dashboard')
            return redirect('patients:patient_detail', pk=pk)
    else:
        form = PatientFullProfileSetupForm(instance=profile, initial=patient_initial)

    is_patient_role = user.role == User.Role.PATIENT
    is_forced = is_patient_role and not patient.is_profile_complete

    return render(request, 'patients/patient_full_profile_setup.html', {
        'patient': patient,
        'form': form,
        'is_forced': is_forced,
    })


@login_required
def patient_profile_setup(request, pk):
    """
    Lightweight birthday-only form — used by staff to update birthday.
    """
    user = request.user

    if user.role == User.Role.PATIENT:
        patient_record = user.get_patient_record()
        if patient_record is None or patient_record.pk != pk:
            messages.error(request, 'You do not have permission to access that page.')
            return redirect('accounts:dashboard')
        # Patients must go through the full setup
        return redirect('patients:patient_full_profile_setup', pk=pk)

    elif not user.is_clinical_staff:
        messages.error(request, 'You do not have permission to access that page.')
        return redirect('accounts:dashboard')

    patient = get_object_or_404(Patient, pk=pk)
    profile, _ = PatientProfile.objects.get_or_create(patient=patient)
    form = PatientProfileSetupForm(request.POST or None, instance=profile)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Profile updated for {patient.get_full_name()}.')
        return redirect('patients:patient_detail', pk=pk)

    return render(request, 'patients/patient_profile_setup.html', {
        'patient': patient,
        'form': form,
    })


@login_required
def patient_contact_edit(request, pk):
    """Edit patient contact information. Admin and frontdesk only."""
    user = request.user

    if user.role not in (User.Role.ADMIN, User.Role.FRONTDESK):
        messages.error(request, 'You do not have permission to edit contact information.')
        return redirect('accounts:dashboard')

    patient = get_object_or_404(Patient, pk=pk)
    form = PatientContactForm(request.POST or None, instance=patient)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Contact information updated for {patient.get_full_name()}.')
        return redirect('patients:patient_detail', pk=pk)

    return render(request, 'patients/patient_contact_edit.html', {
        'patient': patient,
        'form': form,
    })