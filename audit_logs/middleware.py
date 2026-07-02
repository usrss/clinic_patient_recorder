"""
Audit logging middleware.

Captures IP addresses from incoming requests and makes them available
on ``request.audit_ip`` so that view-level logging services can use
them without repeating the extraction logic.

Also provides thread-local storage (``get_current_user()``,
``get_current_ip()``) for signal handlers that need the current
request context outside of direct view access.
"""

import threading

from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()


def get_current_user():
    """
    Return the authenticated user from the current request's thread-local
    storage, or ``None`` if no request is being processed.
    """
    return getattr(_thread_locals, 'user', None)


def get_current_ip():
    """
    Return the client IP from the current request's thread-local
    storage, or ``None`` if no request is being processed.
    """
    return getattr(_thread_locals, 'ip', None)


class AuditIPMiddleware(MiddlewareMixin):
    """
    Attach the client's IP address to the request object so that
    audit logging views can access it via ``request.audit_ip``.

    Also populates thread-local storage so signal-based audit loggers
    can capture the current user and IP without a direct request reference.

    Must be placed AFTER ``AuthenticationMiddleware`` in
    ``MIDDLEWARE`` so that ``request.user`` is available for login
    tracking.
    """

    def process_request(self, request):
        # Store the client IP for later use by audit logging helpers
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request.audit_ip = x_forwarded_for.split(',')[0].strip()
        else:
            request.audit_ip = request.META.get('REMOTE_ADDR')

        # Store in thread-local storage for signal handlers
        _thread_locals.user = request.user if request.user.is_authenticated else None
        _thread_locals.ip = request.audit_ip

    def process_response(self, request, response):
        # Clean up thread-local storage to prevent stale state
        _thread_locals.user = None
        _thread_locals.ip = None
        return response
