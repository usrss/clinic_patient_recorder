import datetime
import logging
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
from .email_utils import otp_email, temp_password_email, welcome_email
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
import random
from .models import User

logger = logging.getLogger(__name__)

from .forms import (
    LoginForm, UserCreateForm, UserEditForm,
    StaffPasswordChangeForm, ForcePasswordChangeForm,
    PatientProfileEditForm, UserProfileForm,
    PasswordResetRequestForm, PasswordResetForm, RegistrationForm,
    ProfileCompletionForm,
)
import json
from collections import defaultdict
from django.db.models import Count, Q, F
from consultations.models import Consultation, Triage, Prescription
from .decorators import admin_required, frontdesk_required
from .throttle import check_ip_rate_limit
from colleges.models import College, Course
from patients.models import Patient, PatientProfile
from inventory.models import Medicine
from audit_logs.services import log_create, log_change
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.sessions.models import Session as DjangoSession
from django.urls import reverse
from notifications.utils import notify_role
from notifications.models import Notification
from django.core.cache import cache


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

    # Show logout success banner if redirected from logout, then strip param
    if request.GET.get('logged_out'):
        messages.success(request, 'You have been logged out successfully.')
        return redirect('accounts:login')

    form = LoginForm(request, data=request.POST or None)

    failed_attempts_remaining = None

    if request.method == 'POST':
        # ── IP-based rate limiting: max 10 login POSTs per minute per IP ──
        is_limited, retry_after = check_ip_rate_limit(request, 'login', max_requests=10, window_seconds=60)
        if is_limited:
            messages.error(request, f'Too many login attempts from this IP. Please try again in {retry_after} second(s).')
            return render(request, 'accounts/login.html', {'form': form})

        if form.is_valid():
            user = form.get_user()

            if user.locked_until and timezone.now() < user.locked_until:
                remaining = (user.locked_until - timezone.now()).seconds // 60
                messages.error(request, f'Account locked. Try again in {remaining} minutes or reset your password.')
                return render(request, 'accounts/login.html', {'form': form, 'failed_attempts_remaining': failed_attempts_remaining})

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

            # ── Remember me: checked = persist for 7 days; unchecked = session-only ──
            if request.POST.get('remember_me') == 'on':
                request.session.set_expiry(86400 * 7)  # 7 days
                request.session['remember_me'] = True
            else:
                request.session.set_expiry(0)  # Expire on browser close
                request.session['remember_me'] = False

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
                        remaining = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
                        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                            user.locked_until = timezone.now() + LOCKOUT_DURATION
                            messages.error(request, f'Account locked for {LOCKOUT_DURATION.seconds // 60} minutes. Use Forgot Password to unlock sooner.')
                        else:
                            messages.error(request, 'Invalid username or password.')
                            failed_attempts_remaining = remaining
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

    # ── Populate course dropdown queryset from submitted college ──
    # The template loads courses dynamically via JS, but the server needs
    # the same queryset for ModelChoiceField validation to succeed.
    if request.method == 'POST':
        college_id = request.POST.get('college')
        if college_id:
            form.fields['course'].queryset = Course.objects.filter(college_id=college_id).order_by('name')

    if request.method == 'POST' and form.is_valid():
        password = form.cleaned_data['password1']
        data = form.cleaned_data

        with transaction.atomic():
            # ── Safety net: clean up orphaned User from a previously deleted Patient ──
            # The post_delete signal on Patient should handle this, but we handle it
            # here too in case of direct DB manipulation or other edge cases.
            if not Patient.objects.filter(patient_id=data['patient_id']).exists():
                User.objects.filter(username=data['patient_id']).delete()

            user = User.objects.create_user(
                username=data['patient_id'],
                password=password,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                role=User.Role.PATIENT,
                phone=data['phone'],
            )

            patient = Patient.objects.create(
                patient_id=data['patient_id'],
                first_name=data['first_name'],
                middle_name=data.get('middle_name', ''),
                last_name=data['last_name'],
                sex=data['sex'],
                college=data.get('college'),
                course=data.get('course'),
                phone=data['phone'],
                email=data['email'],
                emergency_contact_name=data['emergency_contact_name'],
                emergency_contact_phone=data['emergency_contact_phone'],
                department=data.get('department', ''),
                position=data.get('position', ''),
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

    # ── Determine which step to show ──
    # When form validation fails, navigate to the step whose fields have errors
    # so the user can see and fix the problem.
    if request.method == 'POST':
        step_1_fields = {'role', 'patient_id', 'email', 'password1', 'password2'}
        step_3_fields = {
            'first_name', 'middle_name', 'last_name', 'sex', 'birthday',
            'blood_type', 'civil_status', 'height_cm', 'weight_kg',
            'religion', 'address', 'college', 'course', 'year_level',
            'department', 'position', 'phone', 'emergency_contact_name',
            'emergency_contact_phone',
        }
        error_fields = set(form.errors.keys())
        if error_fields & step_1_fields:
            current_step = '1'
        elif error_fields & step_3_fields:
            current_step = '3'
        else:
            current_step = request.POST.get('current_step', '4')
    else:
        current_step = '1'

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

    # Check Patient record existence instead of User — deleted patients
    # should be allowed to re-register. Archived patients still have a
    # Patient record so they remain blocked.
    if Patient.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'error': 'Email already registered.'})

    # Check Patient record existence instead of User — deleted patients
    if Patient.objects.filter(patient_id=patient_id).exists():
        return JsonResponse({'success': False, 'error': 'ID already registered.'})

    # ── IP-based rate limiting: max 3 OTP sends per minute per IP ──
    is_limited, retry_after = check_ip_rate_limit(request, 'otp_send', max_requests=3, window_seconds=60)
    if is_limited:
        return JsonResponse({'success': False, 'error': f'Too many OTP requests from this IP. Please try again in {retry_after} second(s).'})

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

    plain_body, html_body = otp_email(otp, 'registration')
    try:
        send_mail(
            'Registration OTP — Patient Record System',
            plain_body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_body,
        )
    except Exception as e:
        logger.error(f"Failed to send registration OTP to {email}: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to send OTP email. Please try again later.'})
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


def courses_by_college(request):
    """Return JSON list of courses for a given college ID."""
    college_id = request.GET.get('college_id')
    if not college_id:
        return JsonResponse({'courses': []})
    courses = Course.objects.filter(college_id=college_id).order_by('name').values('id', 'name')
    return JsonResponse({'courses': list(courses)})


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

        # ── IP-based rate limiting: max 3 forgot-password POSTs per minute per IP ──
        # Checked before the User lookup so that ALL POSTs (even for non-existent
        # usernames) count toward the limit — prevents an attacker from probing
        # non-existent usernames endlessly from the same IP.
        is_limited, retry_after = check_ip_rate_limit(request, 'otp_send', max_requests=3, window_seconds=60)
        if is_limited:
            messages.error(request, f'Too many OTP requests from this IP. Please try again in {retry_after} second(s).')
            return render(request, 'accounts/forgot_password.html', {'form': form})

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

        plain_body, html_body = otp_email(otp, 'password reset')
        try:
            send_mail(
                'Password Reset OTP — Patient Record System',
                plain_body,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=html_body,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset OTP to {email}: {e}")
            messages.error(request, 'Failed to send OTP email. Please try again later.')
            return render(request, 'accounts/forgot_password.html', {'form': form})

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
        # ── Handle AJAX resend request ─────────────────────────────────
        if request.POST.get('resend_otp') == '1':
            # ── IP-based rate limiting: max 3 OTP resends per minute per IP ──
            is_limited, retry_after = check_ip_rate_limit(request, 'otp_send', max_requests=3, window_seconds=60)
            if is_limited:
                return JsonResponse({'success': False, 'error': f'Too many requests from this IP. Please try again in {retry_after} second(s).'})

            # Rate limit check
            last_sent_str = request.session.get('forgot_password_otp_sent_at')
            if last_sent_str:
                try:
                    elapsed = (timezone.now() - timezone.datetime.fromisoformat(last_sent_str)).total_seconds()
                    if elapsed < FORGOT_PASSWORD_OTP_COOLDOWN_SECONDS:
                        wait = int(FORGOT_PASSWORD_OTP_COOLDOWN_SECONDS - elapsed)
                        return JsonResponse({'success': False, 'error': f'Please wait {wait} second(s).'})
                except (ValueError, TypeError):
                    pass

            # Generate new OTP
            otp = str(random.randint(100000, 999999))
            user.reset_otp = make_password(otp)
            user.reset_otp_expiry = timezone.now() + timedelta(minutes=3)
            user.save(update_fields=['reset_otp', 'reset_otp_expiry'])

            # Send email
            email = user.email
            plain_body, html_body = otp_email(otp, 'password reset')
            try:
                send_mail(
                    'Password Reset OTP — Patient Record System',
                    plain_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                    html_message=html_body,
                )
            except Exception as e:
                logger.error(f"Failed to resend password reset OTP to {email}: {e}")
                return JsonResponse({'success': False, 'error': 'Failed to resend OTP email. Please try again later.'})

            request.session['forgot_password_otp_sent_at'] = timezone.now().isoformat()

            return JsonResponse({'success': True})

        # ── Normal OTP verification ─────────────────────────────────────
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
    if user.is_authenticated:
        log_auth_event(
            user=user,
            action='LOGOUT',
            description=f'Logout — {user.get_full_name() or user.username}',
            status='SUCCESS',
            request=request,
        )
    logout(request)
    # Use query param since logout flushes the session (messages would be lost)
    return redirect(reverse('accounts:login') + '?logged_out=1')


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
        today_iso = timezone.now().date().isoformat()
        cache_key = f'cpr:dashboard:doctor:{user.pk}:{today_iso}'
        context = cache.get(cache_key)

        if context is None:
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
                count = Triage.objects.filter(
                    triaged_by=user,
                    triaged_at__date=day
                ).count()
                daily_activity.append({'date': day.strftime('%a'), 'count': count})

            recent_consults = list(
                Consultation.objects.filter(
                    triages__triaged_by=user
                ).select_related('patient').distinct().order_by('-updated_at')[:5]
            )

            urgent_triage_count = Consultation.objects.filter(
                triages__triaged_by=user,
                triages__urgency='high',
                status__in=[
                    Consultation.Status.QUEUED,
                    Consultation.Status.SCHEDULED,
                    Consultation.Status.TRIAGED,
                ]
            ).distinct().count()

            context = {
                'user': user,
                'urgency_data_json': {
                    'Low': urgency_data.get('low', 0),
                    'Medium': urgency_data.get('medium', 0),
                    'High': urgency_data.get('high', 0),
                },
                'daily_activity_json': daily_activity,
                'recent_consults': recent_consults,
                'urgent_triage_count': urgent_triage_count,
            }
            cache.set(cache_key, context, 120)

        return render(request, 'accounts/dashboard_doctor.html', context)

    if user.role == User.Role.FRONTDESK:
        return render(request, 'accounts/dashboard_frontdesk.html', {'user': user})

    if user.role == User.Role.ADMIN:
        # ── Cacheable heavy aggregations ──
        today_iso = timezone.now().date().isoformat()
        cache_key = f'cpr:dashboard:admin:{user.pk}:{today_iso}'
        cached_data = cache.get(cache_key)

        if cached_data is None:
            college_data = []
            college_labels = []
            for college in College.objects.annotate(patient_count=Count('patients', filter=Q(patients__is_archived=False))):
                if college.patient_count > 0:
                    college_labels.append(college.abbreviation)
                    college_data.append(college.patient_count)

            # ── Diagnosis Analytics chart data ──
            completed_qs = Consultation.objects.filter(status=Consultation.Status.COMPLETED)

            # Top 5 diagnoses
            _top_diags = list(
                Prescription.objects
                .filter(consultation__in=completed_qs)
                .values('diagnosis')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
            diag_labels = [d['diagnosis'][:25] for d in _top_diags]
            diag_counts = [d['count'] for d in _top_diags]

            # ── Diagnosis Distribution by College (matrix: college × diagnosis) ──
            _diag_all_rows = (
                Prescription.objects
                .filter(
                    consultation__in=completed_qs,
                    consultation__patient__college__isnull=False,
                )
                .values(
                    'consultation__patient__college__abbreviation',
                    'diagnosis',
                )
                .annotate(count=Count('id'))
                .order_by('consultation__patient__college__abbreviation', '-count')
            )

            # Get college names (ordered)
            dash_diag_college_labels = list(
                College.objects
                .filter(patients__isnull=False)
                .distinct()
                .values_list('abbreviation', flat=True)[:8]
            )

            # Top 5 diagnosis names overall = column headers
            top_diag_names = [d['diagnosis'][:25] for d in _top_diags]

            # Build matrix: {college: {diagnosis: count}}
            _matrix = defaultdict(lambda: defaultdict(int))
            for row in _diag_all_rows:
                c_name = row['consultation__patient__college__abbreviation']
                diag = row['diagnosis'][:25]
                _matrix[c_name][diag] = row['count']

            # Build datasets for Chart.js stacked bar (one dataset per diagnosis)
            _colors = ['#ef4444', '#f97316', '#10b981', '#8b5cf6', '#ec4899',
                       '#14b8a6', '#f59e0b', '#3b82f6']
            _datasets = []
            for i, diag in enumerate(top_diag_names):
                data_row = [_matrix.get(c, {}).get(diag, 0) for c in dash_diag_college_labels]
                _datasets.append({
                    'label': diag,
                    'data': data_row,
                    'backgroundColor': _colors[i % len(_colors)],
                    'borderRadius': 2,
                    'borderSkipped': False,
                })

            dash_diag_college_datasets = json.dumps(_datasets)

            staff_count = User.objects.exclude(role=User.Role.PATIENT).count()
            doctor_count = User.objects.filter(role=User.Role.DOCTOR).count()
            frontdesk_count = User.objects.filter(role=User.Role.FRONTDESK).count()
            admin_count = User.objects.filter(role=User.Role.ADMIN).count()

            cached_data = {
                'college_labels': college_labels,
                'college_data': college_data,
                'dash_diag_labels': diag_labels,
                'dash_diag_counts': diag_counts,
                'dash_diag_college_labels': dash_diag_college_labels,
                'dash_diag_college_datasets': dash_diag_college_datasets,
                'total_staff': staff_count,
                'doctors': doctor_count,
                'front_desk_count': frontdesk_count,
                'admin_count': admin_count,
            }
            cache.set(cache_key, cached_data, 300)

        # ── Non-cached parts (simple queries + DB writes) ──
        low_stock_medicines = Medicine.objects.filter(
            quantity__lte=F('low_stock_threshold')
        ).order_by('quantity')

        total_patients = Patient.objects.filter(
            is_active=True, is_archived=False
        ).count()

        pending_consultations = Consultation.objects.filter(
            status=Consultation.Status.PENDING
        ).count()

        # ── Academic year check (ALWAYS runs — has DB write side effects) ──
        from patients.models import AcademicYearSettings as AYS
        academic_year_needs_update = False
        academic_year_settings = AYS.objects.first()
        if academic_year_settings:
            today = timezone.now().date()
            year_end = academic_year_settings.academic_year_end
            if year_end.year < today.year or year_end <= today:
                academic_year_needs_update = True

        if academic_year_needs_update:
            if not Notification.objects.filter(
                recipient_role='admin',
                title='Academic year needs updating',
                is_read=False,
            ).exists():
                notify_role(
                    'admin',
                    'Academic year needs updating',
                    'The configured academic year end has passed. Please update the settings for the new term.',
                    reverse('patients:archive_settings'),
                )
        else:
            Notification.objects.filter(
                recipient_role='admin',
                title='Academic year needs updating',
                is_read=False,
            ).update(is_read=True)

        context = {
            'user': user,
            **cached_data,
            'total_patients': total_patients,
            'pending_consultations': pending_consultations,
            'low_stock_medicines': low_stock_medicines,
            'academic_year_needs_update': academic_year_needs_update,
            'academic_year_settings': academic_year_settings,
        }
        return render(request, 'accounts/dashboard_admin.html', context)

    messages.error(request, 'Account has an unrecognised role.')
    logout(request)
    return redirect('accounts:login')


@login_required
def change_password(request):
    user = request.user
    forced = user.force_password_change

    # Use the form without old-password requirement when forced
    form_class = ForcePasswordChangeForm if forced else StaffPasswordChangeForm
    form = form_class(user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        user.force_password_change = False
        user.save(update_fields=['force_password_change'])
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

    base_tpl = 'core/base.html' if user.role == User.Role.PATIENT else _base_template(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form,
        'forced': forced,
        'base_template': base_tpl,
    })


@login_required
@admin_required
def user_list(request):
    # Base queryset
    qs = User.objects.exclude(role=User.Role.PATIENT).order_by('role', 'username')

    # ── Filters ──
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search:
        qs = qs.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    if role_filter:
        qs = qs.filter(role=role_filter)
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)
    elif status_filter == 'locked':
        qs = qs.filter(locked_until__gt=timezone.now())

    # ── Pagination ──
    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    try:
        users_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        users_page = paginator.page(1)

    return render(request, 'accounts/user_list.html', {
        'users': users_page,
        'paginator': paginator,
        'page_obj': users_page,
        'is_paginated': users_page.has_other_pages(),
        'filter_search': search,
        'filter_role': role_filter,
        'filter_status': status_filter,
    })


@login_required
@admin_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_user = form.save(commit=False)

        # ── Auto-generate 4-digit temp password ──
        from .utils import generate_temp_password
        temp_password = generate_temp_password(length=4)
        new_user.set_password(temp_password)
        new_user.temp_password = temp_password
        new_user.force_password_change = True
        new_user.save()

        log_create(
            user=request.user,
            module='User Management',
            description=f'Created staff account — {new_user.get_full_name() or new_user.username} ({new_user.role})',
            object_model='accounts.User',
            object_id=new_user.pk,
            object_repr=str(new_user),
            request=request,
        )

        # Send welcome email with temp password if user has an email address
        if new_user.email:
            try:
                plain_body, html_body = temp_password_email(
                    temp_password,
                    new_user.username,
                    recipient_name=new_user.first_name or new_user.username,
                )
                send_mail(
                    'Your staff account has been created',
                    plain_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [new_user.email],
                    fail_silently=True,
                    html_message=html_body,
                )
            except Exception:
                pass  # Email delivery is best-effort

        messages.success(
            request,
            f'Staff user created successfully. '
            f'Temporary password for {new_user.username}: {temp_password}'
            f'{" (also emailed to them)." if new_user.email else " (user has no email — share this manually)."}'
        )
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Create'})


@login_required
@admin_required
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, request.FILES or None, instance=target)
    if request.method == 'POST' and form.is_valid():
        # Capture before values for ALL tracked fields
        before = {
            'first_name': target.first_name,
            'last_name': target.last_name,
            'email': target.email,
            'phone': target.phone,
            'role': target.role,
            'is_active': target.is_active,
        }
        form.save()
        target.refresh_from_db()

        # Build changes_before and changes_after for all modified fields
        tracked_fields = ['first_name', 'last_name', 'email', 'phone',
                          'role', 'is_active']
        changes_before = {}
        changes_after = {}
        for field in tracked_fields:
            old_val = before[field]
            new_val = getattr(target, field, None)
            if old_val != new_val:
                changes_before[field] = old_val
                changes_after[field] = new_val

        log_change(
            user=request.user,
            module='User Management',
            description=f'Updated staff account — {target.get_full_name() or target.username}',
            object_model='accounts.User',
            object_id=target.pk,
            object_repr=str(target),
            changes_before=changes_before if changes_before else None,
            changes_after=changes_after if changes_after else None,
            request=request,
        )
        messages.success(request, 'User updated successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Edit', 'target': target})


@login_required
@admin_required
def user_reset_password(request, pk):
    """
    Admin-forced password reset: generates a random password and marks
    the account so the user must change it on next login.
    """
    if request.method != 'POST':
        return redirect('accounts:user_list')
    target_user = get_object_or_404(User, pk=pk)

    from .utils import generate_temp_password
    new_password = generate_temp_password(length=4)
    target_user.set_password(new_password)
    target_user.temp_password = new_password
    target_user.force_password_change = True
    target_user.failed_login_attempts = 0
    target_user.locked_until = None
    target_user.save(update_fields=['password', 'temp_password', 'force_password_change',
                                     'failed_login_attempts', 'locked_until'])

    log_change(
        user=request.user,
        module='User Management',
        description=f'Password reset by admin — {target_user.get_full_name() or target_user.username}',
        object_model='accounts.User',
        object_id=target_user.pk,
        object_repr=str(target_user),
        request=request,
    )

    # Email the new password (best-effort) and always show it to the admin
    if target_user.email:
        try:
            plain_body, html_body = temp_password_email(
                new_password,
                target_user.username,
                recipient_name=target_user.first_name or target_user.username,
            )
            send_mail(
                'Your password has been reset',
                plain_body,
                settings.DEFAULT_FROM_EMAIL,
                [target_user.email],
                fail_silently=True,
                html_message=html_body,
            )
        except Exception:
            pass

    messages.success(
        request,
        f'Password reset for {target_user.username}. '
        f'Temporary password: {new_password}'
        f' {"(also emailed to them)." if target_user.email else "(user has no email — share this manually)."}'
    )
    return redirect('accounts:user_list')


@login_required
@admin_required
def staff_temp_password_list(request):
    """
    Lists staff users who have a temp password and haven't changed it yet
    (force_password_change=True). Admin can view/reset their temp passwords.
    """
    staff_tmp = User.objects.filter(
        force_password_change=True,
    ).exclude(role=User.Role.PATIENT).order_by('role', 'username')

    return render(request, 'accounts/staff_temp_password_list.html', {
        'staff_tmp': staff_tmp,
    })


@login_required
@admin_required
def staff_get_password(request, pk):
    """
    AJAX endpoint: retrieves the stored plaintext temp password for a staff user.
    Returns JSON so the modal can display it.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

    try:
        target_user = get_object_or_404(User, pk=pk)

        # If no stored temp_password (e.g. pre-migration users),
        # generate one now and store it for future lookups.
        if not target_user.temp_password:
            from .utils import generate_temp_password
            new_tmp = generate_temp_password(length=4)
            target_user.temp_password = new_tmp
            target_user.set_password(new_tmp)
            target_user.force_password_change = True
            target_user.save(update_fields=['temp_password', 'password', 'force_password_change'])

            log_change(
                user=request.user,
                module='User Management',
                description=f'Generated temp password for staff — {target_user.username}',
                object_model='accounts.User',
                object_id=target_user.pk,
                object_repr=str(target_user),
                request=request,
            )

        return JsonResponse({
            'success': True,
            'access_code': target_user.temp_password,
            'username': target_user.username,
            'name': target_user.get_full_name() or target_user.username,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        })


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
        if patient.college:
            info_form.fields['course'].queryset = Course.objects.filter(college=patient.college).order_by('name')
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
                    request.POST, request.FILES, instance=profile, patient=patient, user=user
                )
                if patient.college:
                    info_form.fields['course'].queryset = Course.objects.filter(college=patient.college).order_by('name')
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
                    patient.college = info_form.cleaned_data.get('college')
                    patient.course = info_form.cleaned_data.get('course')
                    patient.department = info_form.cleaned_data.get('department', '')
                    patient.position = info_form.cleaned_data.get('position', '')

                    # Sync birthday onto PatientProfile (already saved via form.save())
                    # but birthday is on PatientProfile, which was saved by info_form.save()
                    profile.birthday = info_form.cleaned_data.get('birthday')
                    profile.save(update_fields=['birthday'])

                    update_fields = [
                        'phone', 'email',
                        'emergency_contact_name', 'emergency_contact_phone',
                        'college', 'course', 'department', 'position',
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

                    # Sync email to User model so Forgot Password can find it
                    user.email = info_form.cleaned_data.get('email', '')
                    user.save(update_fields=['email'])

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
                updated_user.save()
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


@login_required
@frontdesk_required
def walkin_patient_list(request):
    """
    Lists walk-in patients (created by front desk, not yet logged in).
    Front desk staff can reset/view the temp password for these patients.
    """
    # Walk-in patients: User is patient role, force_password_change=True,
    # and the linked Patient has never logged in
    walkin_users = User.objects.filter(
        role=User.Role.PATIENT,
        force_password_change=True,
    ).select_related().order_by('-date_joined')

    # Attach patient records
    walkin_data = []
    for u in walkin_users:
        patient = Patient.objects.filter(patient_id=u.username).first()
        if patient and not patient.has_logged_in:
            walkin_data.append({
                'user': u,
                'patient': patient,
            })

    return render(request, 'accounts/walkin_patient_list.html', {
        'walkin_data': walkin_data,
        'base_template': _base_template(request.user),
    })


@login_required
@frontdesk_required
def walkin_get_password(request, pk):
    """
    AJAX endpoint: retrieves the stored plaintext temp password for a
    walk-in patient. Returns it as JSON so the modal can display it.

    If no stored temp_password exists (e.g. patient was created before the
    temp_password field was added), one is generated on the fly, stored,
    and returned — subsequent clicks will show the same password.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

    try:
        target_user = get_object_or_404(User, pk=pk)
        patient = Patient.objects.filter(patient_id=target_user.username).first()

        if not patient:
            return JsonResponse({
                'success': False,
                'error': 'Patient record not found.',
            })

        # If no stored temp_password (e.g. pre-migration patients),
        # generate one now and store it for future lookups.
        if not patient.temp_password:
            from .utils import generate_temp_password
            new_tmp = generate_temp_password(length=4)
            patient.temp_password = new_tmp
            patient.save(update_fields=['temp_password'])

            # Also update the User's password hash so it matches.
            target_user.set_password(new_tmp)
            target_user.force_password_change = True
            target_user.save(update_fields=['password', 'force_password_change'])

            log_change(
                user=request.user,
                module='Patients',
                description=f'Generated temp password for walk-in patient — {target_user.username}',
                object_model='patients.Patient',
                object_id=patient.pk,
                object_repr=str(patient),
                request=request,
            )

        return JsonResponse({
            'success': True,
            'access_code': patient.temp_password,
            'username': target_user.username,
            'name': target_user.get_full_name() or target_user.username,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        })


@login_required
def logout_all_devices(request):
    """
    Logs out the current user from all other sessions (except the current one).

    Uses Redis-backed session iteration when SESSION_ENGINE is cache-based
    (fast, avoids full table scan). Falls back to the DB-based iteration
    for compatibility when sessions are still stored in the database.
    """
    if request.method != 'POST':
        return redirect('accounts:profile_settings')

    user = request.user
    current_session_key = request.session.session_key
    deleted_count = 0

    session_engine = getattr(settings, 'SESSION_ENGINE', '')
    uses_cache_sessions = 'cache' in session_engine

    if uses_cache_sessions:
        # Django's cache-based session backend prefixes keys with this constant
        SESSION_CACHE_KEY_PREFIX = 'django.contrib.sessions.cache'
        current_session_cache_key = f'{SESSION_CACHE_KEY_PREFIX}{current_session_key}'

        all_keys = cache.keys('*')
        for key in all_keys:
            if key == current_session_cache_key:
                continue  # never delete the session serving THIS request
            value = cache.get(key)
            if value is None:
                continue
            try:
                if isinstance(value, dict) and str(value.get('_auth_user_id')) == str(user.pk):
                    cache.delete(key)
                    deleted_count += 1
            except Exception:
                continue
    else:
        # ── DB-backed: fallback to DjangoSession table scan ────────────────
        for session in DjangoSession.objects.all().iterator():
            try:
                data = session.get_decoded()
            except Exception:
                continue
            if str(data.get('_auth_user_id', '')) == str(user.pk) and session.session_key != current_session_key:
                session.delete()
                deleted_count += 1

    messages.success(
        request,
        f'Logged out {deleted_count} other device{"s" if deleted_count != 1 else ""}.'
        if deleted_count > 0
        else 'No other active sessions found.'
    )
    return redirect('accounts:profile_settings')


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
    if patient.course:
        initial['course'] = patient.course

    form = ProfileCompletionForm(request.POST or None, request.FILES or None, initial=initial, user=request.user)

    # Ensure course dropdown is populated with the correct college's courses.
    # On GET, use the patient's existing college. On POST re-render (after
    # validation error), use the submitted college value.
    college_id = request.POST.get('college') if request.method == 'POST' else (patient.college_id if patient.college else None)
    if college_id:
        form.fields['course'].queryset = Course.objects.filter(college_id=college_id).order_by('name')

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data

        with transaction.atomic():
            patient.phone = cd.get('phone', '')
            patient.email = cd.get('email', '')
            patient.emergency_contact_name = cd.get('emergency_contact_name', '')
            patient.emergency_contact_phone = cd.get('emergency_contact_phone', '')
            patient.college = cd.get('college', None)
            patient.course = cd.get('course', None)
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
                'emergency_contact_phone', 'college', 'course', 'department', 'position',
                'expected_graduation_year',
            ]
            if picture:
                update_fields.append('profile_picture')

            patient.save(update_fields=update_fields)

            # Sync email to User model so Forgot Password can find it
            user.email = cd.get('email', '')
            user.save(update_fields=['email'])

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

    # ── Determine which step to show ──
    # When form validation fails, navigate to the step whose fields have errors
    # so the user can see and fix the problem.
    if request.method == 'POST':
        step_1_fields = {'role', 'email', 'phone', 'address', 'blood_type',
                         'religion', 'civil_status', 'height_cm', 'weight_kg',
                         'college', 'course', 'year_level', 'department', 'position',
                         'emergency_contact_name', 'emergency_contact_phone',
                         'profile_picture'}
        step_2_fields = {'hypertension', 'diabetes', 'asthma', 'cardiac_problems',
                         'arthritis', 'other_conditions', 'known_allergies',
                         'bcg', 'dpt', 'opv', 'hepatitis_b', 'measles', 'tt',
                         'immunization_others', 'current_medications', 'vices',
                         'previous_illnesses', 'previous_hospitalizations'}
        error_fields = set(form.errors.keys())
        if error_fields & step_1_fields:
            current_step = '1'
        elif error_fields & step_2_fields:
            current_step = '2'
        else:
            current_step = request.POST.get('current_step', '1')
    else:
        current_step = '1'

    return render(request, 'accounts/complete_profile.html', {
        'form': form,
        'patient': patient,
        'profile': profile,
        'current_step': current_step,
    })
