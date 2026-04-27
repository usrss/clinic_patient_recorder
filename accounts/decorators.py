from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """Restrict a view to users with one of the given roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access that page.')
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def nurse_required(view_func):
    return role_required('nurse', 'admin')(view_func)


def doctor_required(view_func):
    return role_required('doctor', 'admin')(view_func)


def frontdesk_required(view_func):
    return role_required('frontdesk', 'admin')(view_func)


def admin_required(view_func):
    return role_required('admin')(view_func)


def clinical_staff_required(view_func):
    """Any staff role (nurse, doctor, frontdesk, admin)."""
    return role_required('nurse', 'doctor', 'frontdesk', 'admin')(view_func)