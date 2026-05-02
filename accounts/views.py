from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import random

from patients.models import Patient, PatientProfile
from .models import User
from .forms import (
    LoginForm, UserCreateForm, UserEditForm,
    StaffPasswordChangeForm, PatientProfileEditForm, UserProfileForm,
    PasswordResetRequestForm, PasswordResetForm, RegistrationForm,
)
from .decorators import admin_required

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()

            if user.locked_until and timezone.now() < user.locked_until:
                remaining = (user.locked_until - timezone.now()).seconds // 60
                messages.error(request, f'Account locked. Try again in {remaining} minutes or reset your password.')
                return render(request, 'accounts/login.html', {'form': form})

            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until'])

            login(request, user)

            if user.role == User.Role.PATIENT:
                patient = user.get_patient_record()
                if patient is not None and not patient.has_logged_in:
                    patient.has_logged_in = True
                    patient.save(update_fields=['has_logged_in'])

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


# ── REGISTRATION ──────────────────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Store form data in session for OTP verification
        request.session['registration_data'] = {
            k: v for k, v in form.cleaned_data.items()
            if k not in ('password1', 'password2')
        }
        request.session['registration_password'] = form.cleaned_data['password1']
        request.session['registration_email'] = form.cleaned_data['email']

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        request.session['registration_otp'] = otp
        request.session['registration_otp_expiry'] = (timezone.now() + timedelta(minutes=10)).isoformat()

        send_mail(
            'Registration OTP — Clinic Recorder',
            f'Your OTP to complete registration is: {otp}\n\nThis OTP expires in 10 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [form.cleaned_data['email']],
            fail_silently=False,
        )

        print(f'Registration OTP for {form.cleaned_data["email"]}: {otp}')  # Debug

        messages.success(request, 'A 6-digit OTP has been sent to your email.')
        return redirect('accounts:verify_registration_otp')

    return render(request, 'accounts/register.html', {'form': form})


def verify_registration_otp(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if 'registration_data' not in request.session:
        messages.error(request, 'No registration in progress.')
        return redirect('accounts:register')

    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        stored_otp = request.session.get('registration_otp')
        expiry_str = request.session.get('registration_otp_expiry')

        if not stored_otp or not expiry_str:
            messages.error(request, 'OTP expired. Please register again.')
            return redirect('accounts:register')

        if timezone.now() > timezone.datetime.fromisoformat(expiry_str):
            _clear_registration_session(request)
            messages.error(request, 'OTP expired. Please register again.')
            return redirect('accounts:register')

        if otp != stored_otp:
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(request, 'accounts/verify_registration_otp.html')

        # OTP verified — create the account
        data = request.session['registration_data']
        password = request.session['registration_password']

        with transaction.atomic():
            user = User.objects.create_user(
                username=data['patient_id'],
                password=password,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                role=User.Role.PATIENT,
                phone=data['phone'],
                force_password_change=False,
            )

            patient = Patient.objects.create(
                patient_id=data['patient_id'],
                first_name=data['first_name'],
                middle_name=data.get('middle_name', ''),
                last_name=data['last_name'],
                sex=data['sex'],
                college=data.get('college'),
                phone=data['phone'],
                email=data['email'],
                emergency_contact_name=data['emergency_contact_name'],
                emergency_contact_phone=data['emergency_contact_phone'],
                has_logged_in=False,
            )

            PatientProfile.objects.create(
                patient=patient,
                birthday=data.get('birthday'),
                address=data.get('address', ''),
                blood_type=data.get('blood_type', ''),
                religion=data.get('religion', ''),
                civil_status=data.get('civil_status', ''),
                year_level=data.get('year_level', ''),
                height_cm=data.get('height_cm'),
                weight_kg=data.get('weight_kg'),
                hypertension=data.get('hypertension', False),
                diabetes=data.get('diabetes', False),
                asthma=data.get('asthma', False),
                cardiac_problems=data.get('cardiac_problems', False),
                arthritis=data.get('arthritis', False),
                other_conditions=data.get('other_conditions', ''),
                known_allergies=data.get('known_allergies', ''),
                bcg=data.get('bcg', False),
                dpt=data.get('dpt', False),
                opv=data.get('opv', False),
                hepatitis_b=data.get('hepatitis_b', False),
                measles=data.get('measles', False),
                tt=data.get('tt', False),
                immunization_others=data.get('immunization_others', ''),
                current_medications=data.get('current_medications', ''),
                vices=data.get('vices', ''),
                previous_illnesses=data.get('previous_illnesses', ''),
                previous_hospitalizations=data.get('previous_hospitalizations', ''),
                profile_completed=True,
            )

        _clear_registration_session(request)
        messages.success(request, 'Registration successful! You may now log in.')
        return redirect('accounts:login')

    return render(request, 'accounts/verify_registration_otp.html')


def _clear_registration_session(request):
    keys = ['registration_data', 'registration_password', 'registration_email',
            'registration_otp', 'registration_otp_expiry']
    for key in keys:
        request.session.pop(key, None)


# ── FORGOT / RESET PASSWORD ───────────────────────────────────────────

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

        print(f'OTP for {email}: {otp}')

        send_mail(
            'Password Reset OTP — Clinic Recorder',
            f'Your OTP for password reset is: {otp}\n\nThis OTP expires in 10 minutes.',
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

        if not user.reset_otp or not user.reset_otp_expiry:
            messages.error(request, 'No OTP was requested.')
            return redirect('accounts:forgot_password')

        if timezone.now() > user.reset_otp_expiry:
            messages.error(request, 'OTP expired.')
            return redirect('accounts:forgot_password')

        if otp != user.reset_otp:
            messages.error(request, 'Invalid OTP.')
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
    return redirect('accounts:login')


@login_required
def dashboard(request):
    user = request.user

    if user.role == User.Role.PATIENT:
        patient = user.get_patient_record()
        if patient is None:
            messages.error(request, 'Patient record not found.')
            logout(request)
            return redirect('accounts:login')
        return render(request, 'patients/patient_dashboard.html', {'patient': patient})

    role_template_map = {
        User.Role.NURSE: 'accounts/dashboard_nurse.html',
        User.Role.DOCTOR: 'accounts/dashboard_doctor.html',
        User.Role.FRONTDESK: 'accounts/dashboard_frontdesk.html',
    }

    if user.role in role_template_map:
        return render(request, role_template_map[user.role], {'user': user})

    if user.role == User.Role.ADMIN:
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

    messages.error(request, 'Account has an unrecognised role.')
    logout(request)
    return redirect('accounts:login')


@login_required
def change_password(request):
    user = request.user
    form = StaffPasswordChangeForm(user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        user.force_password_change = False
        user.save()
        update_session_auth_hash(request, user)
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
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Edit', 'target': target})


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
                messages.success(request, 'Profile updated.')
                return redirect('accounts:profile_settings')

        elif 'save_password' in request.POST:
            info_form = PatientProfileEditForm(instance=profile, patient=patient) if user.role == User.Role.PATIENT else UserProfileForm(instance=user)
            password_form = StaffPasswordChangeForm(user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                user.force_password_change = False
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed.')
                return redirect('accounts:profile_settings')
    else:
        if user.role == User.Role.PATIENT:
            info_form = PatientProfileEditForm(instance=profile, patient=patient)
        else:
            info_form = UserProfileForm(instance=user)
        password_form = StaffPasswordChangeForm(user)

    return render(request, 'accounts/profile_settings.html', {
        'info_form': info_form,
        'password_form': password_form,
    })