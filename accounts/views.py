from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import random

from patients.models import PatientProfile
from .models import User
from .forms import (
    LoginForm, UserCreateForm, UserEditForm, PatientBulkUploadForm,
    StaffPasswordChangeForm, PatientProfileEditForm, UserProfileForm,
    PasswordResetRequestForm, PasswordResetForm,
)
from .decorators import admin_required
from .utils import import_patients_from_excel, PatientImportError

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()

            # Check if account is locked
            if user.locked_until and timezone.now() < user.locked_until:
                remaining = (user.locked_until - timezone.now()).seconds // 60
                messages.error(request, f'Account locked. Try again in {remaining} minutes or reset your password.')
                return render(request, 'accounts/login.html', {'form': form})

            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until'])

            login(request, user)

            if user.role == User.Role.PATIENT:
                patient = user.get_patient_record()
                if patient is not None and not patient.has_logged_in:
                    patient.has_logged_in = True
                    patient.save(update_fields=['has_logged_in'])

            if user.force_password_change:
                return redirect('accounts:change_password')

            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:dashboard')

        else:
            username = request.POST.get('username', '')
            if username:
                try:
                    user = User.objects.get(username=username)
                    if user.locked_until and timezone.now() < user.locked_until:
                        remaining = (user.locked_until - timezone.now()).seconds // 60
                        messages.error(request, f'Account locked. Try again in {remaining} minutes or reset your password.')
                    else:
                        user.failed_login_attempts += 1
                        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                            user.locked_until = timezone.now() + LOCKOUT_DURATION
                        user.save(update_fields=['failed_login_attempts', 'locked_until'])

                        remaining = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
                        if remaining > 0:
                            messages.error(request, f'Invalid password. {remaining} attempts remaining.')
                        else:
                            messages.error(request, 'Account locked for 15 minutes. Use Forgot Password to unlock sooner.')
                except User.DoesNotExist:
                    messages.error(request, 'Invalid username or password.')
            else:
                messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'form': form})


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = PasswordResetRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        user = User.objects.get(email=email, is_active=True)

        otp = str(random.randint(100000, 999999))
        user.reset_otp = otp
        user.reset_otp_expiry = timezone.now() + timedelta(minutes=10)
        user.save(update_fields=['reset_otp', 'reset_otp_expiry'])

        print(f'OTP for {email}: {otp}')  # Debug — remove in production

        send_mail(
            'Password Reset OTP — Clinic Recorder',
            f'Your OTP for password reset is: {otp}\n\n'
            f'This OTP expires in 10 minutes.\n\n'
            f'If you did not request this, please ignore this email.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        messages.success(request, 'A 6-digit OTP has been sent to your email.')
        return redirect('accounts:verify_otp', user_id=user.pk)

    return render(request, 'accounts/forgot_password.html', {'form': form})


def verify_otp(request, user_id):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    user = get_object_or_404(User, pk=user_id, is_active=True)

    if request.method == 'POST':
        user.refresh_from_db(fields=['reset_otp', 'reset_otp_expiry'])
        otp = request.POST.get('otp', '').strip()

        print(f'Entered OTP: [{otp}], Stored OTP: [{user.reset_otp}]')  # Debug

        if not user.reset_otp or not user.reset_otp_expiry:
            messages.error(request, 'No OTP was requested. Please try again.')
            return redirect('accounts:forgot_password')

        if timezone.now() > user.reset_otp_expiry:
            messages.error(request, 'OTP has expired. Please request a new one.')
            return redirect('accounts:forgot_password')

        if otp != user.reset_otp:
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(request, 'accounts/verify_otp.html', {'user_id': user_id})

        user.reset_otp = None
        user.reset_otp_expiry = None
        user.save(update_fields=['reset_otp', 'reset_otp_expiry'])

        request.session['reset_user_id'] = user.pk
        return redirect('accounts:reset_password')

    return render(request, 'accounts/verify_otp.html', {'user_id': user_id})


def reset_password(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'Please verify your OTP first.')
        return redirect('accounts:forgot_password')

    user = get_object_or_404(User, pk=user_id, is_active=True)

    form = PasswordResetForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['new_password1'])
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()

        del request.session['reset_user_id']

        messages.success(request, 'Password reset successful. You may now log in.')
        return redirect('accounts:login')

    return render(request, 'accounts/reset_password.html', {'form': form})


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

    if user.role == User.Role.PATIENT:
        patient = user.get_patient_record()

        if patient is None:
            messages.error(request, 'Your patient record could not be found. Please contact the clinic.')
            logout(request)
            return redirect('accounts:login')

        if not patient.is_profile_complete:
            messages.info(request, 'Please complete your profile before continuing.')
            return redirect('patients:patient_full_profile_setup', pk=patient.pk)

        return render(request, 'patients/patient_dashboard.html', {'patient': patient})

    role_template_map = {
        User.Role.NURSE: 'accounts/dashboard_nurse.html',
        User.Role.DOCTOR: 'accounts/dashboard_doctor.html',
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
            'pending_consultations': Consultation.objects.filter(status=Consultation.Status.PENDING).count(),
        }
        return render(request, 'accounts/dashboard_admin.html', context)

    messages.error(request, 'Your account has an unrecognised role.')
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
    form = PatientBulkUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            results = import_patients_from_excel(request.FILES['file'])
            messages.success(request, f'✓ Import complete: {results["created"]} created, {results["skipped"]} skipped')
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


@login_required
def profile_settings(request):
    user = request.user

    if user.role == User.Role.PATIENT:
        patient = user.get_patient_record()
        profile, _ = PatientProfile.objects.get_or_create(patient=patient)
    else:
        profile = None
        patient = None

    if request.method == 'POST':
        if 'save_info' in request.POST:
            if user.role == User.Role.PATIENT:
                info_form = PatientProfileEditForm(request.POST, instance=profile, patient=patient)
            else:
                info_form = UserProfileForm(request.POST, instance=user)
            password_form = StaffPasswordChangeForm(user)

            if info_form.is_valid():
                if user.role == User.Role.PATIENT:
                    info_form.save()
                    patient.phone = info_form.cleaned_data.get('phone', '')
                    patient.email = info_form.cleaned_data.get('email', '')
                    patient.emergency_contact_name = info_form.cleaned_data.get('emergency_contact_name', '')
                    patient.emergency_contact_phone = info_form.cleaned_data.get('emergency_contact_phone', '')
                    patient.save(update_fields=['phone', 'email', 'emergency_contact_name', 'emergency_contact_phone'])
                else:
                    info_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('accounts:profile_settings')

        elif 'save_password' in request.POST:
            info_form = PatientProfileEditForm(instance=profile, patient=patient) if user.role == User.Role.PATIENT else UserProfileForm(instance=user)
            password_form = StaffPasswordChangeForm(user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                user.force_password_change = False
                user.save(update_fields=['force_password_change'])
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
                return redirect('accounts:profile_settings')
    else:
        # GET request
        if user.role == User.Role.PATIENT:
            info_form = PatientProfileEditForm(instance=profile, patient=patient)
        else:
            info_form = UserProfileForm(instance=user)
        password_form = StaffPasswordChangeForm(user)

    return render(request, 'accounts/profile_settings.html', {
        'info_form': info_form,
        'password_form': password_form,
    })