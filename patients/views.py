import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q

from accounts.decorators import clinical_staff_required, admin_required
from audit_logs.services import log_create, log_change, log_view
from accounts.models import User
from consultations.models import Consultation
from .models import Patient, PatientProfile, AcademicYearSettings
from .forms import (
    PatientSearchForm, PatientContactForm,
    AcademicYearSettingsForm,
)


def _base_template(user):
    """Return the correct base template for the current user's role."""
    if user.role == 'admin':
        return 'core/base_admin.html'
    return 'core/base_staff.html'


@login_required
@clinical_staff_required
def patient_list(request):
    form = PatientSearchForm(request.GET or None)

    # ── Determine show_archived from query params ──────────────────────────
    show_archived = request.GET.get('archived') == '1'

    patients = Patient.objects.select_related('college', 'profile').filter(
        is_active=True,
    )

    # By default, hide archived patients unless explicitly requested
    if not show_archived:
        patients = patients.filter(is_archived=False)

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

    # ── Pagination: 25 patients per page ─────────────────────────────────
    paginator = Paginator(patients, 25)
    page = request.GET.get('page', 1)
    try:
        patients_page = paginator.page(page)
    except PageNotAnInteger:
        patients_page = paginator.page(1)
    except EmptyPage:
        patients_page = paginator.page(paginator.num_pages)

    return render(request, 'patients/patient_list.html', {
        'patients': patients_page,
        'form': form,
        'query': query,
        'show_archived': show_archived,
        'is_paginated': patients_page.has_other_pages(),
        'page_obj': patients_page,
        'paginator': paginator,
        'base_template': _base_template(request.user),
    })


@login_required
@clinical_staff_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    profile = getattr(patient, 'profile', None)
    consultations = Consultation.objects.filter(
        patient=patient
    ).prefetch_related('triages', 'prescriptions').order_by('-created_at')

    # Log view of patient record
    log_view(
        user=request.user,
        module='Patients',
        description=f'Viewed patient record — {patient.get_full_name()} ({patient.patient_id})',
        object_model='patients.Patient',
        object_id=patient.pk,
        object_repr=str(patient),
        request=request,
    )

    return render(request, 'patients/patient_detail.html', {
        'patient': patient,
        'profile': profile,
        'consultations': consultations,
        'base_template': _base_template(request.user),
    })


@login_required
def patient_profile_setup(request, pk):
    """Staff updates patient profile."""
    user = request.user

    if user.role == User.Role.PATIENT:
        patient_record = user.get_patient_record()
        if patient_record is None or patient_record.pk != pk:
            messages.error(request, 'You do not have permission to access that page.')
            return redirect('accounts:dashboard')
        return redirect('accounts:profile_settings')

    elif not user.is_clinical_staff:
        messages.error(request, 'You do not have permission to access that page.')
        return redirect('accounts:dashboard')

    patient = get_object_or_404(Patient, pk=pk)
    profile, _ = PatientProfile.objects.get_or_create(patient=patient)

    # Capture before state for audit
    old_phone = patient.phone
    old_email = patient.email

    # Use the full profile edit form from accounts
    from accounts.forms import PatientProfileEditForm
    from accounts.utils import calculate_graduation_year
    form = PatientProfileEditForm(
        request.POST or None,
        request.FILES or None,
        instance=profile,
        patient=patient,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        patient.phone = form.cleaned_data.get('phone', '')
        patient.email = form.cleaned_data.get('email', '')
        patient.emergency_contact_name = form.cleaned_data.get('emergency_contact_name', '')
        patient.emergency_contact_phone = form.cleaned_data.get('emergency_contact_phone', '')
        # Recalculate expected_graduation_year if year_level changed
        new_year_level = form.cleaned_data.get('year_level', '')
        if new_year_level:
            patient.expected_graduation_year = calculate_graduation_year(new_year_level)
        else:
            patient.expected_graduation_year = None
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            patient.profile_picture = request.FILES['profile_picture']
        elif form.cleaned_data.get('remove_picture'):
            patient.profile_picture = None
        patient.save(update_fields=['phone', 'email', 'emergency_contact_name',
                                     'emergency_contact_phone', 'profile_picture',
                                     'expected_graduation_year'])

        log_change(
            user=request.user,
            module='Patients',
            description=f'Updated profile — {patient.get_full_name()} ({patient.patient_id})',
            object_model='patients.Patient',
            object_id=patient.pk,
            object_repr=str(patient),
            changes_before={'phone': old_phone, 'email': old_email},
            changes_after={'phone': patient.phone, 'email': patient.email},
            request=request,
        )

        messages.success(request, f'Profile updated for {patient.get_full_name()}.')
        return redirect('patients:patient_detail', pk=pk)

    return render(request, 'accounts/profile_settings_patient.html', {
        'info_form': form,
        'patient': patient,
        'is_staff_edit': True,
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
        old_phone = patient.phone
        form.save()
        log_change(
            user=request.user,
            module='Patients',
            description=f'Updated contact info — {patient.get_full_name()} ({patient.patient_id})',
            object_model='patients.Patient',
            object_id=patient.pk,
            object_repr=str(patient),
            changes_before={'phone': old_phone},
            changes_after={'phone': patient.phone},
            request=request,
        )
        messages.success(request, f'Contact information updated for {patient.get_full_name()}.')
        return redirect('patients:patient_detail', pk=pk)

    return render(request, 'patients/patient_contact_edit.html', {
        'patient': patient,
        'form': form,
    })


# ─── ACADEMIC YEAR & ARCHIVE ADMIN VIEWS ────────────────────────────────────


@login_required
@admin_required
def archive_settings(request):
    """
    Admin configures the academic year end date and archive-after-months threshold.
    """
    settings, _ = AcademicYearSettings.objects.get_or_create(
        defaults={
            'academic_year_end': datetime.date(datetime.date.today().year, 5, 31),
            'archive_after_months': 5,
        }
    )

    if request.method == 'POST':
        form = AcademicYearSettingsForm(request.POST)
        if form.is_valid():
            old_end = settings.academic_year_end
            old_months = settings.archive_after_months
            settings.academic_year_end = form.cleaned_data['academic_year_end']
            settings.archive_after_months = form.cleaned_data['archive_after_months']
            settings.updated_by = request.user
            settings.save()
            log_change(
                user=request.user,
                module='Settings',
                description=f'Updated academic year archive settings',
                object_model='patients.AcademicYearSettings',
                object_id=settings.pk,
                object_repr=str(settings),
                changes_before={'academic_year_end': str(old_end), 'archive_after_months': old_months},
                changes_after={'academic_year_end': str(settings.academic_year_end), 'archive_after_months': settings.archive_after_months},
                request=request,
            )
            messages.success(request, 'Academic year settings updated.')
            return redirect('patients:archive_settings')
    else:
        form = AcademicYearSettingsForm(initial={
            'academic_year_end': settings.academic_year_end,
            'archive_after_months': settings.archive_after_months,
        })

    return render(request, 'patients/archive_settings.html', {
        'form': form,
        'settings': settings,
        'base_template': _base_template(request.user),
    })


@login_required
@admin_required
def archive_browser(request):
    """
    Admin views/search archived patients by ID, name, college, or department.
    """
    query = request.GET.get('q', '').strip()

    archived_base = Patient.objects.filter(is_archived=True).select_related('college')
    total_archived = archived_base.count()  # Compute total BEFORE search filter

    archived_patients = archived_base
    if query:
        archived_patients = archived_patients.filter(
            Q(patient_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(college__name__icontains=query) |
            Q(college__abbreviation__icontains=query) |
            Q(department__icontains=query)
        )

    archived_patients = archived_patients.order_by('-archived_at', 'last_name', 'first_name')

    # ── Pagination: 25 patients per page ─────────────────────────────────
    paginator = Paginator(archived_patients, 25)
    page = request.GET.get('page', 1)
    try:
        patients_page = paginator.page(page)
    except PageNotAnInteger:
        patients_page = paginator.page(1)
    except EmptyPage:
        patients_page = paginator.page(paginator.num_pages)

    return render(request, 'patients/archive_browser.html', {
        'archived_patients': patients_page,
        'query': query,
        'total_archived': total_archived,
        'is_paginated': patients_page.has_other_pages(),
        'page_obj': patients_page,
        'paginator': paginator,
        'base_template': _base_template(request.user),
    })


@login_required
@admin_required
def unarchive_patient(request, pk):
    """
    Admin restores a patient from archive.
    """
    if request.method != 'POST':
        return redirect('patients:archive_browser')

    patient = get_object_or_404(Patient, pk=pk, is_archived=True)
    patient.is_archived = False
    patient.archived_at = None
    patient.archived_reason = ''
    patient.save(update_fields=['is_archived', 'archived_at', 'archived_reason'])

    log_change(
        user=request.user,
        module='Patients',
        description=f'Restored patient from archive — {patient.get_full_name()} ({patient.patient_id})',
        object_model='patients.Patient',
        object_id=patient.pk,
        object_repr=str(patient),
        changes_before={'is_archived': True},
        changes_after={'is_archived': False},
        request=request,
    )

    messages.success(
        request,
        f'{patient.get_full_name()} ({patient.patient_id}) has been restored from archive.'
    )
    return redirect('patients:archive_browser')