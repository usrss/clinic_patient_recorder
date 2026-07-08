from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse


class ProfileCompletionMiddleware:
    """
    Redirect authenticated patients to the profile completion page if their
    profile is not yet complete.  Excludes logout and the completion page
    itself to avoid redirect loops.
    """

    SAFE_URL_NAMES = {
        'accounts:logout',
        'accounts:complete_profile',
        'accounts:change_password',
        'accounts:courses_by_college',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                match = resolve(request.path_info)
                url_name = f'{match.namespaces[0]}:{match.url_name}' if match.namespaces else match.url_name
            except Resolver404:
                url_name = None

            if url_name not in self.SAFE_URL_NAMES:
                # Force password change first (walk-in patients have temp passwords;
                # staff can have this flag set by admin)
                if request.user.force_password_change:
                    return redirect('accounts:change_password')
                # Then force profile completion for patients (including email setup)
                is_patient = getattr(request.user, 'role', None) == 'patient'
                if is_patient:
                    patient = request.user.get_patient_record()
                    if patient and not patient.is_profile_complete:
                        return redirect('accounts:complete_profile')

        return self.get_response(request)


class IdleSessionTimeoutMiddleware:
    """
    Checks for idle session timeout on authenticated requests.
    Updates the last-activity timestamp in the session on each request.
    If the idle time exceeds IDLE_SESSION_TIMEOUT_MINUTES, the session
    is logged out and the user is redirected to the login page with a
    session-expired message.

    AJAX requests return a 403 with a specific header so the frontend
    can detect forced logout and redirect.
    """

    IDLE_TIMEOUT = getattr(settings, 'IDLE_SESSION_TIMEOUT_MINUTES', 30)
    SAFE_URL_NAMES = {
        'accounts:logout',
        'accounts:login',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                match = resolve(request.path_info)
                url_name = f'{match.namespaces[0]}:{match.url_name}' if match.namespaces else match.url_name
            except Resolver404:
                url_name = None

            # Skip timeout check for safe URLs
            if url_name not in self.SAFE_URL_NAMES:
                last_activity = request.session.get('last_activity')
                if last_activity:
                    try:
                        elapsed = (timezone.now() - timezone.datetime.fromisoformat(last_activity)).total_seconds()
                        if elapsed > self.IDLE_TIMEOUT * 60:
                            logout(request)
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({
                                    'logout': True,
                                    'reason': 'session_expired',
                                    'message': 'Your session has expired due to inactivity. Please log in again.'
                                }, status=403)
                            messages.warning(request, 'Your session has expired due to inactivity. Please log in again.')
                            return redirect('accounts:login')
                    except (ValueError, TypeError):
                        pass

                # Update last activity timestamp
                request.session['last_activity'] = timezone.now().isoformat()

        return self.get_response(request)
