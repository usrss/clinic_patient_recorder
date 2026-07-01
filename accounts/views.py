import datetime
import time as _time
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from audit_logs.services import log_auth_event
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
import random
from .models import User
from .forms import (
    LoginForm, UserCreateForm, UserEditForm,
    StaffPasswordChangeForm, PatientProfileEditForm, UserProfileForm,
    PasswordResetRequestForm, PasswordResetForm, RegistrationForm,
    ProfileCompletionForm,
)
from django.db.models import Count, Q, F
from consultations.models import Consultation, Triage
from .decorators import admin_required
from colleges.models import College
from patients.models import Patient, PatientProfile
from inventory.models import Medicine

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=2)


def _base_template(user):
    """Return the correct base template for the current user's role."""
    if user.role == 'admin':
        return 'core/base_admin.html'
    return 'core/base_staff.html'


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

            log_auth_event(
                user=user,
                action='LOGIN',
                description=f'Successful login — {user.get_full_name() or user.username}',
                status='SUCCESS',
                request=request,
            )

            login(request, user)

            if user.role == User.Role.PATIENT:
                patient = user.get_patient_record()
                if patient is not None and not patient.has_logged_in:
                    patient.has_logged_in = True
                    patient.save(update_fields=['has_logged_in'])

            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:dashboard')

        else:
            # Track failed attempts without revealing whether the user exists
            # (prevents user enumeration)
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
                            messages.error(request, f'Account locked for {LOCKOUT_DURATION.seconds // 60} minutes. Use Forgot Password to unlock sooner.')
                        else:
                            messages.error(request, 'Invalid username or password.')
                        user.save(update_fields=['failed_login_attempts', 'locked_until'])
                        log_auth_event(
                            user=user,
                            action='LOGIN',
                            description=f'Failed login attempt — {username}',
                            status='FAILED',
                            request=request,
                        )
                except User.DoesNotExist:
                    # Generic message — don't reveal whether the user exists
                    messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


# ── REGISTRATION ──────────────────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        password = form.cleaned_data['password1']
        data = form.cleaned_data

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
                expected_graduation_year=data.get('_expected_graduation_year'),
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

        login(request, user)
        _clear_registration_session(request)
        messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
        return redirect('accounts:dashboard')

    current_step = request.POST.get('current_step', '1') if request.method == 'POST' else '1'
    return render(request, 'accounts/register.html', {
        'form': form,
        'current_step': current_step,
    })


REGISTRATION_OTP_COOLDOWN_SECONDS = 60  # Minimum seconds between OTP sends


def send_registration_otp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request.'})

    email = request.POST.get('email', '').strip()
    patient_id = request.POST.get('patient_id', '').strip()

    if not email or not patient_id:
        return JsonResponse({'success': False, 'error': 'Email and ID are required.'})

    if User.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'error': 'Email already registered.'})

    if User.objects.filter(username=patient_id).exists():
        return JsonResponse({'success': False, 'error': 'ID already registered.'})

    # Rate limit: prevent OTP spam
    last_sent_str = request.session.get('registration_otp_sent_at')
    if last_sent_str:
        try:
            elapsed = (timezone.now() - timezone.datetime.fromisoformat(last_sent_str)).total_seconds()
            if elapsed < REGISTRATION_OTP_COOLDOWN_SECONDS:
                wait = int(REGISTRATION_OTP_COOLDOWN_SECONDS - elapsed)
                return JsonResponse({'success': False, 'error': f'Please wait {wait} second(s) before requesting another OTP.'})
        except (ValueError, TypeError):
            pass

    otp = str(random.randint(100000, 999999))
    request.session['registration_otp'] = make_password(otp)
    request.session['registration_otp_expiry'] = (timezone.now() + timedelta(minutes=3)).isoformat()
    request.session['registration_email'] = email
    request.session['registration_otp_pending'] = True
    request.session['registration_otp_sent_at'] = timezone.now().isoformat()

    send_mail(
        'Registration OTP — Patient Record System',
        f'Your OTP is: {otp}\n\nExpires in 3 minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    return JsonResponse({'success': True})


def verify_registration_otp(request):
    if request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Already logged in.'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request.'})

    otp = request.POST.get('otp', '').strip()
    stored_otp_hash = request.session.get('registration_otp')
    expiry_str = request.session.get('registration_otp_expiry')

    if not stored_otp_hash or not expiry_str:
        return JsonResponse({'success': False, 'error': 'OTP expired.'})

    if timezone.now() > timezone.datetime.fromisoformat(expiry_str):
        return JsonResponse({'success': False, 'error': 'OTP expired.'})

    if not check_password(otp, stored_otp_hash):
        return JsonResponse({'success': False, 'error': 'Invalid OTP.'})

    request.session['registration_otp_verified'] = True
    return JsonResponse({'success': True})


def _clear_registration_session(request):
    keys = [
        'registration_data', 'registration_password', 'registration_email',
        'registration_otp', 'registration_otp_expiry', 'registration_otp_pending',
        'registration_otp_verified', 'registration_otp_sent_at',
    ]
    for key in keys:
        request.session.pop(key, None)


# ── FORGOT / RESET PASSWORD ───────────────────────────────────────────

FORGOT_PASSWORD_OTP_COOLDOWN_SECONDS = 60  # Minimum seconds between OTP sends


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    GENERIC_MESSAGE = (
        'If an account with that username exists, you\'ll receive further instructions.'
    )

    form = PasswordResetRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        patient_id = form.cleaned_data['patient_id']

        try:
            user = User.objects.get(username=patient_id, is_active=True)
        except User.DoesNotExist:
            # Don't reveal whether the user exists — use a generic message
            # Sleep briefly to avoid timing-based enumeration
            _time.sleep(0.5)
            messages.success(request, GENERIC_MESSAGE)
            return render(request, 'accounts/forgot_password.html', {'form': form})

        if not user.email:
            # User has no email — still show generic message to avoid enumeration
            _time.sleep(0.5)
            messages.success(request, GENERIC_MESSAGE)
            return render(request, 'accounts/forgot_password.html', {'form': form})

        # Rate limit: prevent OTP spam (only applies to valid users with email)
        last_sent_str = request.session.get('forgot_password_otp_sent_at')
        if last_sent_str:
            try:
                elapsed = (timezone.now() - timezone.datetime.fromisoformat(last_sent_str)).total_seconds()
                if elapsed < FORGOT_PASSWORD_OTP_COOLDOWN_SECONDS:
                    wait = int(FORGOT_PASSWORD_OTP_COOLDOWN_SECONDS - elapsed)
                    messages.error(request, f'Please wait {wait} second(s) before requesting another OTP.')
                    return render(request, 'accounts/forgot_password.html', {'form': form})
            except (ValueError, TypeError):
                pass

        otp = str(random.randint(100000, 999999))
        user.reset_otp = make_password(otp)
        user.reset_otp_expiry = timezone.now() + timedelta(minutes=3)
        user.save(update_fields=['reset_otp', 'reset_otp_expiry'])

        email = user.email
        local, domain = email.split('@')
        masked_email = local[0] + ('*' * (len(local) - 2)) + local[-1] + '@' + domain

        send_mail(
            'Password Reset OTP — Patient Record System',
            f'Your OTP for password reset is: {otp}\n\nThis OTP expires in 3 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        request.session['forgot_password_otp_sent_at'] = timezone.now().isoformat()

        messages.success(
            request,
            f'A 6-digit OTP has been sent to {masked_email}. '
            f'If you did not receive it, check your spam folder or contact the clinic.'
        )
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

        if not check_password(otp, user.reset_otp):
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
    user = request.user
    log_auth_event(
        user=user,
        action='LOGOUT',
        description=f'Logout — {user.get_full_name() or user.username}',
        status='SUCCESS',
        request=request,
    )
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

        unreviewed = Consultation.objects.filter(
            patient=patient,
            status=Consultation.Status.COMPLETED,
        ).exclude(feedback__isnull=False).first()

        return render(request, 'patients/patient_dashboard.html', {
            'patient': patient,
            'unreviewed_consultation': unreviewed,
        })

    if user.role == User.Role.DOCTOR:
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        doctor_triages = Triage.objects.filter(
            triaged_by=user,
            triaged_at__gte=thirty_days_ago
        )
        urgency_counts = doctor_triages.values('urgency').annotate(count=Count('pk'))
        urgency_data = {u['urgency']: u['count'] for u in urgency_counts}

        daily_activity = []
        for i in range(6, -1, -1):
            day = now.date() - timedelta(days=i)
            count = Consultation.objects.filter(
                triages__triaged_by=user,
                updated_at__date=day
            ).count()
            daily_activity.append({'date': day.strftime('%a'), 'count': count})

        recent_consults = Consultation.objects.filter(
            triages__triaged_by=user
        ).select_related('patient').order_by('-updated_at')[:5]

        context = {
            'user': user,
            'urgency_data_json': {
                'Low': urgency_data.get('low', 0),
                'Medium': urgency_data.get('medium', 0),
                'High': urgency_data.get('high', 0),
            },
            'daily_activity_json': daily_activity,
            'recent_consults': recent_consults,
        }
        return render(request, 'accounts/dashboard_doctor.html', context)

    if user.role == User.Role.FRONTDESK:
        return render(request, 'accounts/dashboard_frontdesk.html', {'user': user})

    if user.role == User.Role.ADMIN:
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        status_counts = Consultation.objects.values('status').annotate(count=Count('pk'))
        status_data = {s['status']: s['count'] for s in status_counts}
        status_labels = ['Pending', 'Queued', 'Triaged', 'Completed', 'Cancelled', 'Closed']
        status_keys = ['pending', 'queued', 'triaged', 'completed', 'cancelled', 'closed']
        consultation_status_data = [status_data.get(k, 0) for k in status_keys]

        daily_consultations = []
        daily_labels = []
        for i in range(29, -1, -1):
            day = now.date() - timedelta(days=i)
            count = Consultation.objects.filter(created_at__date=day).count()
            daily_labels.append(day.strftime('%b %d'))
            daily_consultations.append(count)

        male_count = Patient.objects.filter(is_archived=False, sex='M').count()
        female_count = Patient.objects.filter(is_archived=False, sex='F').count()

        college_data = []
        college_labels = []
        for college in College.objects.annotate(patient_count=Count('patients', filter=Q(patients__is_archived=False))):
            if college.patient_count > 0:
                college_labels.append(college.abbreviation)
                college_data.append(college.patient_count)

        cond_hypertension = PatientProfile.objects.filter(hypertension=True).count()
        cond_diabetes = PatientProfile.objects.filter(diabetes=True).count()
        cond_asthma = PatientProfile.objects.filter(asthma=True).count()
        cond_cardiac = PatientProfile.objects.filter(cardiac_problems=True).count()
        cond_arthritis = PatientProfile.objects.filter(arthritis=True).count()

        low_stock_medicines = Medicine.objects.filter(quantity__lte=F('low_stock_threshold')).order_by('quantity')

        staff_count = User.objects.exclude(role=User.Role.PATIENT).count()
        doctor_count = User.objects.filter(role=User.Role.DOCTOR).count()
        context = {
            'user': user,
            'total_staff': staff_count,
            'total_patients': Patient.objects.filter(is_active=True, is_archived=False).count(),
            'doctors': doctor_count,
            'front_desk_count': max(staff_count - 1 - doctor_count, 0),
            'pending_consultations': Consultation.objects.filter(status=Consultation.Status.PENDING).count(),
            'consultation_status_labels': status_labels,
            'consultation_status_data': consultation_status_data,
            'daily_labels': daily_labels,
            'daily_consultations': daily_consultations,
            'male_count': male_count,
            'female_count': female_count,
            'college_labels': college_labels,
            'college_data': college_data,
            'cond_hypertension': cond_hypertension,
            'cond_diabetes': cond_diabetes,
            'cond_asthma': cond_asthma,
            'cond_cardiac': cond_cardiac,
            'cond_arthritis': cond_arthritis,
            'low_stock_medicines': low_stock_medicines,
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
        log_auth_event(
            user=user,
            action='UPDATE',
            description=f'Password changed — {user.get_full_name() or user.username}',
            status='SUCCESS',
            request=request,
        )
        messages.success(request, 'Password changed successfully.')

        if user.role == User.Role.PATIENT:
            patient = user.get_patient_record()
            if patient and not patient.is_profile_complete:
                return redirect('accounts:complete_profile')

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
        new_user = form.save()
        from audit_logs.services import log_create
        log_create(
            user=request.user,
            module='User Management',
            description=f'Created staff account — {new_user.get_full_name() or new_user.username} ({new_user.role})',
            object_model='accounts.User',
            object_id=new_user.pk,
            object_repr=str(new_user),
            request=request,
        )
        messages.success(request, 'Staff user created successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Create'})


@login_required
@admin_required
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, request.FILES or None, instance=target)
    if request.method == 'POST' and form.is_valid():
        # Capture before values
        old_role = target.role
        old_active = target.is_active
        form.save()
        from audit_logs.services import log_change
        changes = {}
        if old_role != target.role:
            changes['role'] = f'{old_role} → {target.role}'
        if old_active != target.is_active:
            changes['is_active'] = f'{old_active} → {target.is_active}'
        log_change(
            user=request.user,
            module='User Management',
            description=f'Updated staff account — {target.get_full_name() or target.username}',
            object_model='accounts.User',
            object_id=target.pk,
            object_repr=str(target),
            changes_before={'role': old_role, 'is_active': old_active},
            changes_after={'role': target.role, 'is_active': target.is_active},
            request=request,
        )
        messages.success(request, 'User updated successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Edit', 'target': target})


@login_required
@admin_required
def user_toggle_active(request, pk):
    if request.method != 'POST':
        return redirect('accounts:user_list')
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
    else:
        was_active = target_user.is_active
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=['is_active'])
        status = 'activated' if target_user.is_active else 'deactivated'
        from audit_logs.services import log_change
        log_change(
            user=request.user,
            module='User Management',
            description=f'{status.capitalize()} account — {target_user.get_full_name() or target_user.username}',
            object_model='accounts.User',
            object_id=target_user.pk,
            object_repr=str(target_user),
            changes_before={'is_active': was_active},
            changes_after={'is_active': target_user.is_active},
            request=request,
        )
        messages.success(request, f'User {target_user.username} {status}.')
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

    # ── Initialize forms for GET (overridden on POST below) ──
    if user.role == User.Role.PATIENT:
        info_form = PatientProfileEditForm(instance=profile, patient=patient)
    else:
        info_form = UserProfileForm(instance=user)
    password_form = StaffPasswordChangeForm(user)

    if request.method == 'POST':
        password_fields = {'old_password', 'new_password1', 'new_password2'}
        is_password_post = (
            'save_password' in request.POST
            or any(field in request.POST for field in password_fields)
        )
        is_info_post = 'save_info' in request.POST or not is_password_post

        # ── Save Profile Info ──────────────────────────────────────────
        if is_info_post:
            if user.role == User.Role.PATIENT:
                info_form = PatientProfileEditForm(
                    request.POST, request.FILES, instance=profile, patient=patient
                )
            else:
                info_form = UserProfileForm(request.POST, request.FILES, instance=user)

            password_form = StaffPasswordChangeForm(user)

            if info_form.is_valid():
                if user.role == User.Role.PATIENT:
                    # Save PatientProfile model fields (all Meta.fields)
                    info_form.save()

                    # Manually propagate extra form fields onto the Patient record
                    patient.phone = info_form.cleaned_data.get('phone', '')
                    patient.email = info_form.cleaned_data.get('email', '')
                    patient.emergency_contact_name = info_form.cleaned_data.get('emergency_contact_name', '')
                    patient.emergency_contact_phone = info_form.cleaned_data.get('emergency_contact_phone', '')

                    update_fields = [
                        'phone', 'email',
                        'emergency_contact_name', 'emergency_contact_phone',
                    ]

                    # FIX: use cleaned_data for image (not raw request.FILES) so
                    # validators have already run and the value is normalised.
                    picture = info_form.cleaned_data.get('profile_picture')
                    if picture:
                        # A new file was uploaded and validated
                        patient.profile_picture = picture
                        update_fields.append('profile_picture')
                    elif info_form.cleaned_data.get('remove_picture'):
                        # Explicit removal requested
                        patient.profile_picture = None
                        update_fields.append('profile_picture')

                    patient.save(update_fields=update_fields)

                else:
                    # ── Staff branch ─────────────────────────────────────
                    # FIX: profile_picture is removed from UserProfileForm.Meta.fields
                    # so we handle it here explicitly — prevents info_form.save()
                    # racing with the remove_picture logic.
                    info_form.save()  # saves first_name, last_name, email, phone

                    picture = info_form.cleaned_data.get('profile_picture')
                    if picture:
                        user.profile_picture = picture
                        user.save(update_fields=['profile_picture'])
                    elif info_form.cleaned_data.get('remove_picture'):
                        user.profile_picture = None
                        user.save(update_fields=['profile_picture'])

                messages.success(request, 'Profile updated successfully.')
                return redirect('accounts:profile_settings')

        # ── Change Password ────────────────────────────────────────────
        elif is_password_post:
            if user.role == User.Role.PATIENT:
                info_form = PatientProfileEditForm(instance=profile, patient=patient)
            else:
                info_form = UserProfileForm(instance=user)

            password_form = StaffPasswordChangeForm(user, request.POST)

            if password_form.is_valid():
                updated_user = password_form.save()
                updated_user.force_password_change = False
                updated_user.save(update_fields=['force_password_change'])
                update_session_auth_hash(request, updated_user)
                messages.success(request, 'Password changed successfully.')
                return redirect('accounts:profile_settings')

    if user.role == User.Role.PATIENT:
        template = 'accounts/profile_settings_patient.html'
        context = {
            'info_form': info_form,
            'password_form': password_form,
            'patient': patient,
            'profile': profile,
        }
    else:
        template = 'accounts/profile_settings_staff.html'
        context = {
            'info_form': info_form,
            'password_form': password_form,
            'base_template': _base_template(request.user),
        }

    return render(request, template, context)


# ── PROFILE COMPLETION (Walk-in patient first login) ────────────────────

@login_required
def complete_profile(request):
    """
    Forces a walk-in patient to complete their full profile on first login.
    Pre-fills name, sex, birthday from existing Patient record.
    Has 2 steps: Personal & Academic Info → Medical Profile.
    """
    from patients.models import Patient, PatientProfile
    from django.db import transaction

    user = request.user
    if user.role != User.Role.PATIENT:
        messages.error(request, 'Only patients can access profile completion.')
        return redirect('accounts:dashboard')

    patient = user.get_patient_record()
    if patient is None:
        messages.error(request, 'Patient record not found.')
        return redirect('accounts:dashboard')

    if patient.is_profile_complete:
        messages.info(request, 'Your profile is already complete.')
        return redirect('accounts:dashboard')

    profile, _ = PatientProfile.objects.get_or_create(patient=patient)

    initial = {
        'first_name': patient.first_name,
        'middle_name': patient.middle_name,
        'last_name': patient.last_name,
        'sex': patient.sex,
        'birthday': profile.birthday,
        'phone': patient.phone or '',
        'email': patient.email or '',
        'address': profile.address or '',
        'blood_type': profile.blood_type or '',
        'religion': profile.religion or '',
        'civil_status': profile.civil_status or '',
        'height_cm': profile.height_cm,
        'weight_kg': profile.weight_kg,
        'year_level': profile.year_level or '',
        'emergency_contact_name': patient.emergency_contact_name or '',
        'emergency_contact_phone': patient.emergency_contact_phone or '',
        'hypertension': profile.hypertension,
        'diabetes': profile.diabetes,
        'asthma': profile.asthma,
        'cardiac_problems': profile.cardiac_problems,
        'arthritis': profile.arthritis,
        'other_conditions': profile.other_conditions or '',
        'known_allergies': profile.known_allergies or '',
        'bcg': profile.bcg,
        'dpt': profile.dpt,
        'opv': profile.opv,
        'hepatitis_b': profile.hepatitis_b,
        'measles': profile.measles,
        'tt': profile.tt,
        'immunization_others': profile.immunization_others or '',
        'current_medications': profile.current_medications or '',
        'vices': profile.vices or '',
        'previous_illnesses': profile.previous_illnesses or '',
        'previous_hospitalizations': profile.previous_hospitalizations or '',
    }
    if patient.college:
        initial['college'] = patient.college

    form = ProfileCompletionForm(request.POST or None, request.FILES or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data

        with transaction.atomic():
            patient.phone = cd.get('phone', '')
            patient.email = cd.get('email', '')
            patient.emergency_contact_name = cd.get('emergency_contact_name', '')
            patient.emergency_contact_phone = cd.get('emergency_contact_phone', '')
            patient.college = cd.get('college', None)
            patient.department = cd.get('department', '')
            patient.position = cd.get('position', '')

            # FIX: use cleaned_data for image
            picture = cd.get('profile_picture')
            if picture:
                patient.profile_picture = picture

            from accounts.utils import calculate_graduation_year
            year_level = cd.get('year_level', '')
            if cd.get('role') == 'student' and year_level:
                patient.expected_graduation_year = calculate_graduation_year(year_level)
            else:
                patient.expected_graduation_year = None

            update_fields = [
                'phone', 'email', 'emergency_contact_name',
                'emergency_contact_phone', 'college', 'department', 'position',
                'expected_graduation_year',
            ]
            if picture:
                update_fields.append('profile_picture')

            patient.save(update_fields=update_fields)

            profile.birthday = cd.get('birthday') or profile.birthday
            profile.address = cd.get('address', '')
            profile.blood_type = cd.get('blood_type', '')
            profile.religion = cd.get('religion', '')
            profile.civil_status = cd.get('civil_status', '')
            profile.year_level = cd.get('year_level', '')
            profile.height_cm = cd.get('height_cm')
            profile.weight_kg = cd.get('weight_kg')

            profile.hypertension = cd.get('hypertension', False)
            profile.diabetes = cd.get('diabetes', False)
            profile.asthma = cd.get('asthma', False)
            profile.cardiac_problems = cd.get('cardiac_problems', False)
            profile.arthritis = cd.get('arthritis', False)
            profile.other_conditions = cd.get('other_conditions', '')
            profile.known_allergies = cd.get('known_allergies', '')

            profile.bcg = cd.get('bcg', False)
            profile.dpt = cd.get('dpt', False)
            profile.opv = cd.get('opv', False)
            profile.hepatitis_b = cd.get('hepatitis_b', False)
            profile.measles = cd.get('measles', False)
            profile.tt = cd.get('tt', False)
            profile.immunization_others = cd.get('immunization_others', '')

            profile.current_medications = cd.get('current_medications', '')
            profile.vices = cd.get('vices', '')
            profile.previous_illnesses = cd.get('previous_illnesses', '')
            profile.previous_hospitalizations = cd.get('previous_hospitalizations', '')

            profile.profile_completed = True
            profile.save()

            patient.has_logged_in = True
            patient.save(update_fields=['has_logged_in'])

        messages.success(
            request,
            f'Profile completed successfully! Welcome, {patient.get_full_name()}.'
        )
        return redirect('accounts:dashboard')

    current_step = request.POST.get('current_step', '1') if request.method == 'POST' else '1'
    return render(request, 'accounts/complete_profile.html', {
        'form': form,
        'patient': patient,
        'profile': profile,
        'current_step': current_step,
    })
