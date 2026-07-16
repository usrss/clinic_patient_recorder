from django.conf import settings


def idle_session_timeout(request):
    """
    Context processor that makes the idle session timeout value available
    to all templates (in seconds) so the frontend JS can stay in sync
    with the backend middleware.
    """
    minutes = getattr(settings, 'IDLE_SESSION_TIMEOUT_MINUTES', 30)
    return {
        'idle_session_timeout_seconds': minutes * 60,
    }
