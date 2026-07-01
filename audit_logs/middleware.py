"""
Audit logging middleware.

Captures IP addresses from incoming requests and makes them available
on ``request.audit_ip`` so that view-level logging services can use
them without repeating the extraction logic.

Also logs authentication-related events that occur at the middleware
level (e.g. failed login attempts).
"""

from django.utils.deprecation import MiddlewareMixin


class AuditIPMiddleware(MiddlewareMixin):
    """
    Attach the client's IP address to the request object so that
    audit logging views can access it via ``request.audit_ip``.

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


# ── Optional: attach to the existing ProfileCompletionMiddleware ─────
# We don't need to duplicate IP logic — the middleware above suffices.
