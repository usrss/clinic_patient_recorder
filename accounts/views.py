from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User
from .forms import LoginForm, UserCreateForm, UserEditForm, PatientBulkUploadForm, StaffPasswordChangeForm
from .decorators import admin_required
from .utils import import_patients_from_excel, PatientImportError


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # ── Patient: mark first-ever login ──────────────────────────────
            if user.role == User.Role.PATIENT:
                patient = user.get_patient_record()
                if patient is not None and not patient.has_logged_in:
                    patient.has_logged_in = True
                    patient.save(update_fields=['has_logged_in'])

            # ── Force password change (first login) ─────────────────────────
            if user.force_password_change:
                return redirect('accounts:change_password')

            messages.success(
                request,
                f'Welcome back, {user.first_name or user.username}!'
            )
            return redirect('accounts:dashboard')

        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method != 'POST':
        return redirect('accounts:dashboard')
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    user = request.user

    if user.force_password_change:
        return redirect('accounts:change_password')

    # ── Patient portal ────────────────────────────────────────────────
    if user.role == User.Role.PATIENT:
        patient = user.get_patient_record()

        if patient is None:
            messages.error(
                request,
                'Your patient record could not be found. Please contact the clinic.'
            )
            logout(request)
            return redirect('accounts:login')

        # Gate 1: Force profile setup (birthday + contact info)
        if not patient.is_profile_complete:
            messages.info(
                request,
                'Please complete your profile before continuing. All fields marked * are required.'
            )
            return redirect('patients:patient_full_profile_setup', pk=patient.pk)

        return render(request, 'patients/patient_dashboard.html', {
            'patient': patient
        })

    # ── Staff roles ───────────────────────────────────────────────────
    role_template_map = {
        User.Role.NURSE:     'accounts/dashboard_nurse.html',
        User.Role.DOCTOR:    'accounts/dashboard_doctor.html',
        User.Role.FRONTDESK: 'accounts/dashboard_frontdesk.html',
    }

    if user.role in role_template_map:
        return render(request, role_template_map[user.role], {'user': user})

    if user.role == User.Role.ADMIN:
        from patients.models import Patient
        from consultations.models import Consultation
        context = {
            'user': user,
            'total_staff': User.objects.exclude(role=User.Role.PATIENT).count(),
            'total_patients': Patient.objects.filter(is_active=True).count(),
            'nurses': User.objects.filter(role=User.Role.NURSE).count(),
            'doctors': User.objects.filter(role=User.Role.DOCTOR).count(),
            'pending_consultations': Consultation.objects.filter(
                status=Consultation.Status.PENDING
            ).count(),
        }
        return render(request, 'accounts/dashboard_admin.html', context)

    messages.error(request, 'Your account has an unrecognised role. Please contact an administrator.')
    logout(request)
    return redirect('accounts:login')


@login_required
def change_password(request):
    user = request.user
    form = StaffPasswordChangeForm(user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()

        user.force_password_change = False
        user.save(update_fields=['force_password_change'])

        update_session_auth_hash(request, user)

        # After password change, patient still needs profile setup if incomplete
        if user.role == User.Role.PATIENT:
            patient = user.get_patient_record()
            if patient and not patient.is_profile_complete:
                return redirect('patients:patient_full_profile_setup', pk=patient.pk)

        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:dashboard')

    return render(request, 'accounts/change_password.html', {
        'form': form,
        'forced': user.force_password_change,
    })


@login_required
@admin_required
def user_list(request):
    users = User.objects.exclude(role=User.Role.PATIENT).order_by('role', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@admin_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Staff user created successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Create'})


@login_required
@admin_required
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=target)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'User updated successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {
        'form': form, 'action': 'Edit', 'target': target,
    })


@login_required
@admin_required
def user_toggle_active(request, pk):
    if request.method != 'POST':
        return redirect('accounts:user_list')
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
    else:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} {status}.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def patient_import(request):
    """Bulk import Patient records from Excel (no birthday — creates auth user per patient)."""
    form = PatientBulkUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            results = import_patients_from_excel(request.FILES['file'])
            messages.success(
                request,
                f'✓ Import complete: {results["created"]} created, {results["skipped"]} skipped'
            )
            for warning in results['warnings']:
                messages.warning(request, warning)
            for error in results['errors']:
                messages.error(request, error)
            return redirect('accounts:patient_import')
        except PatientImportError as e:
            messages.error(request, f'Import failed: {str(e)}')
        except Exception as e:
            messages.error(request, f'Unexpected error: {str(e)}')
    return render(request, 'accounts/import_patients.html', {'form': form})