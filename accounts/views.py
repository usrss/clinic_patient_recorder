import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
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
                            messages.error(request, f'Account locked for {LOCKOUT_DURATION.seconds // 60} minutes. Use Forgot Password to unlock sooner.')
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
        messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
        return redirect('accounts:dashboard')

    # Pass current_step back so JS can restore the correct step on failed submission
    current_step = request.POST.get('current_step', '1') if request.method == 'POST' else '1'
    return render(request, 'accounts/register.html', {
        'form': form,
        'current_step': current_step,
    })


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

    otp = str(random.randint(100000, 999999))
    request.session['registration_otp'] = otp
    request.session['registration_otp_expiry'] = (timezone.now() + timedelta(minutes=3)).isoformat()
    request.session['registration_email'] = email
    request.session['registration_otp_pending'] = True

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
    stored_otp = request.session.get('registration_otp')
    expiry_str = request.session.get('registration_otp_expiry')

    if not stored_otp or not expiry_str:
        return JsonResponse({'success': False, 'error': 'OTP expired.'})

    if timezone.now() > timezone.datetime.fromisoformat(expiry_str):
        return JsonResponse({'success': False, 'error': 'OTP expired.'})

    if otp != stored_otp:
        return JsonResponse({'success': False, 'error': 'Invalid OTP.'})

    request.session['registration_otp_verified'] = True
    return JsonResponse({'success': True})


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
        patient_id = form.cleaned_data['patient_id']
        user = User.objects.get(username=patient_id, is_active=True)

        otp = str(random.randint(100000, 999999))
        # FIX: Hash the OTP before storing to prevent plaintext exposure in DB
        user.reset_otp = make_password(otp)
        user.reset_otp_expiry = timezone.now() + timedelta(minutes=3)
        user.save(update_fields=['reset_otp', 'reset_otp_expiry'])

        # Mask email for display: e.g. j***e@gmail.com
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

        messages.success(
            request,
            f'A 6-digit OTP has been sent to {masked_email}.'
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

        # FIX: Use check_password() since OTP is now hashed
        if not check_password(otp, user.reset_otp):
            messages.error(request, 'Invalid OTP.')
            return render(request, 'accounts/verify_otp.html', {'user_id': user_id})

        # FIX: Clear OTP fields regardless — reset to None (the hash is cleared)
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

        # Check for unreviewed completed consultations
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
        seven_days_ago = now - timedelta(days=7)

        # Doctor's triage urgency breakdown (last 30 days)
        doctor_triages = Triage.objects.filter(
            triaged_by=user,
            triaged_at__gte=thirty_days_ago
        )
        urgency_counts = doctor_triages.values('urgency').annotate(count=Count('pk'))
        urgency_data = {u['urgency']: u['count'] for u in urgency_counts}

        # Doctor's consultations handled per day (last 7 days)
        daily_activity = []
        for i in range(6, -1, -1):
            day = now.date() - timedelta(days=i)
            count = Consultation.objects.filter(
                triages__triaged_by=user,
                updated_at__date=day
            ).count()
            daily_activity.append({'date': day.strftime('%a'), 'count': count})

        # Doctor's recent consultations
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

        # ── Consultation Status Breakdown (donut chart) ──
        status_counts = Consultation.objects.values('status').annotate(count=Count('pk'))
        status_data = {s['status']: s['count'] for s in status_counts}
        status_labels = ['Pending', 'Queued', 'Triaged', 'Completed', 'Cancelled', 'Closed']
        status_keys = ['pending', 'queued', 'triaged', 'completed', 'cancelled', 'closed']
        consultation_status_data = [status_data.get(k, 0) for k in status_keys]

        # ── Consultations per Day (last 30 days — line chart) ──
        daily_consultations = []
        daily_labels = []
        for i in range(29, -1, -1):
            day = now.date() - timedelta(days=i)
            count = Consultation.objects.filter(created_at__date=day).count()
            daily_labels.append(day.strftime('%b %d'))
            daily_consultations.append(count)

        # ── Patient Sex Distribution (pie chart) ──
        male_count = Patient.objects.filter(is_archived=False, sex='M').count()
        female_count = Patient.objects.filter(is_archived=False, sex='F').count()

        # ── Patients by College (bar chart) ──
        college_data = []
        college_labels = []
        for college in College.objects.annotate(patient_count=Count('patients', filter=Q(patients__is_archived=False))):
            if college.patient_count > 0:
                college_labels.append(college.abbreviation)
                college_data.append(college.patient_count)

        # ── Patient Medical Conditions (horizontal bar) ──
        cond_hypertension = PatientProfile.objects.filter(hypertension=True).count()
        cond_diabetes = PatientProfile.objects.filter(diabetes=True).count()
        cond_asthma = PatientProfile.objects.filter(asthma=True).count()
        cond_cardiac = PatientProfile.objects.filter(cardiac_problems=True).count()
        cond_arthritis = PatientProfile.objects.filter(arthritis=True).count()

        # ── Low Stock Alerts ──
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
            # Chart data
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
        messages.success(request, 'Password changed successfully.')

        # If patient, redirect to profile completion if not yet completed
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
        form.save()
        messages.success(request, 'Staff user created successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Create'})


@login_required
@admin_required
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, request.FILES or None, instance=target)
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
                info_form = PatientProfileEditForm(request.POST, request.FILES, instance=profile, patient=patient)
            else:
                info_form = UserProfileForm(request.POST, request.FILES, instance=user)
            password_form = StaffPasswordChangeForm(user)

            if info_form.is_valid():
                if user.role == User.Role.PATIENT:
                    info_form.save()
                    patient.phone = info_form.cleaned_data.get('phone', '')
                    patient.email = info_form.cleaned_data.get('email', '')
                    patient.emergency_contact_name = info_form.cleaned_data.get('emergency_contact_name', '')
                    patient.emergency_contact_phone = info_form.cleaned_data.get('emergency_contact_phone', '')
                    # Handle profile picture upload
                    if 'profile_picture' in request.FILES:
                        patient.profile_picture = request.FILES['profile_picture']
                    elif info_form.cleaned_data.get('remove_picture'):
                        patient.profile_picture = None
                    patient.save(update_fields=['phone', 'email', 'emergency_contact_name', 'emergency_contact_phone', 'profile_picture'])
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

    if user.role == User.Role.PATIENT:
        template = 'accounts/profile_settings_patient.html'
        context = {
            'info_form': info_form,
            'password_form': password_form,
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

    # If already completed, redirect to dashboard
    if patient.is_profile_complete:
        messages.info(request, 'Your profile is already complete.')
        return redirect('accounts:dashboard')

    profile, _ = PatientProfile.objects.get_or_create(patient=patient)

    # Pre-fill from existing Patient + PatientProfile data
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
        # Medical history checkboxes
        'hypertension': profile.hypertension,
        'diabetes': profile.diabetes,
        'asthma': profile.asthma,
        'cardiac_problems': profile.cardiac_problems,
        'arthritis': profile.arthritis,
        'other_conditions': profile.other_conditions or '',
        'known_allergies': profile.known_allergies or '',
        # Immunizations
        'bcg': profile.bcg,
        'dpt': profile.dpt,
        'opv': profile.opv,
        'hepatitis_b': profile.hepatitis_b,
        'measles': profile.measles,
        'tt': profile.tt,
        'immunization_others': profile.immunization_others or '',
        # Background
        'current_medications': profile.current_medications or '',
        'vices': profile.vices or '',
        'previous_illnesses': profile.previous_illnesses or '',
        'previous_hospitalizations': profile.previous_hospitalizations or '',
    }
    # Pre-fill college from patient record
    if patient.college:
        initial['college'] = patient.college

    form = ProfileCompletionForm(request.POST or None, request.FILES or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data

        with transaction.atomic():
            # Update Patient model fields
            patient.phone = cd.get('phone', '')
            patient.email = cd.get('email', '')
            patient.emergency_contact_name = cd.get('emergency_contact_name', '')
            patient.emergency_contact_phone = cd.get('emergency_contact_phone', '')
            patient.college = cd.get('college', None)
            patient.department = cd.get('department', '')
            patient.position = cd.get('position', '')
            # Handle profile picture
            if 'profile_picture' in request.FILES:
                patient.profile_picture = request.FILES['profile_picture']
            # Calculate expected graduation year from year_level
            from accounts.utils import calculate_graduation_year
            year_level = cd.get('year_level', '')
            if cd.get('role') == 'student' and year_level:
                patient.expected_graduation_year = calculate_graduation_year(year_level)
            else:
                patient.expected_graduation_year = None

            patient.save(update_fields=[
                'phone', 'email', 'emergency_contact_name',
                'emergency_contact_phone', 'college', 'department', 'position',
                'profile_picture', 'expected_graduation_year',
            ])

            # Update PatientProfile
            profile.birthday = cd.get('birthday') or profile.birthday
            profile.address = cd.get('address', '')
            profile.blood_type = cd.get('blood_type', '')
            profile.religion = cd.get('religion', '')
            profile.civil_status = cd.get('civil_status', '')
            profile.year_level = cd.get('year_level', '')
            profile.height_cm = cd.get('height_cm')
            profile.weight_kg = cd.get('weight_kg')

            # Medical history
            profile.hypertension = cd.get('hypertension', False)
            profile.diabetes = cd.get('diabetes', False)
            profile.asthma = cd.get('asthma', False)
            profile.cardiac_problems = cd.get('cardiac_problems', False)
            profile.arthritis = cd.get('arthritis', False)
            profile.other_conditions = cd.get('other_conditions', '')
            profile.known_allergies = cd.get('known_allergies', '')

            # Immunizations
            profile.bcg = cd.get('bcg', False)
            profile.dpt = cd.get('dpt', False)
            profile.opv = cd.get('opv', False)
            profile.hepatitis_b = cd.get('hepatitis_b', False)
            profile.measles = cd.get('measles', False)
            profile.tt = cd.get('tt', False)
            profile.immunization_others = cd.get('immunization_others', '')

            # Medical background
            profile.current_medications = cd.get('current_medications', '')
            profile.vices = cd.get('vices', '')
            profile.previous_illnesses = cd.get('previous_illnesses', '')
            profile.previous_hospitalizations = cd.get('previous_hospitalizations', '')

            # Mark as completed
            profile.profile_completed = True
            profile.save()

            # Mark patient as having logged in
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