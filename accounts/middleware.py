from django.shortcuts import redirect
from django.urls import resolve, Resolver404


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

            is_patient = getattr(request.user, 'role', None) == 'patient'
            if is_patient and url_name not in self.SAFE_URL_NAMES:
                patient = request.user.get_patient_record()
                if patient and not patient.is_profile_complete:
                    return redirect('accounts:complete_profile')

        return self.get_response(request)
