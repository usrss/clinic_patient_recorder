"""
IP-based rate limiting using Django's cache (Redis).

Provides a single entry point — check_ip_rate_limit() — that returns
(is_limited, retry_after_seconds).  The caller decides what to render
(AJAX JSON error, redirect with messages.error, etc.) so each view can
stay consistent with its own response conventions.

Graceful degradation: because the Django cache backend has
IGNORE_EXCEPTIONS = True, a Redis outage will silently bypass the
rate limiter rather than crashing the entire request.
"""

import time

from django.core.cache import cache


# ── Public helpers ──────────────────────────────────────────────────────────


def get_client_ip(request) -> str:
    """
    Extract the real client IP from the request.

    Respects X-Forwarded-For so the limiter still works when the app
    is behind a reverse proxy (Cloudflare tunnel, nginx, etc.).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def check_ip_rate_limit(
    request,
    scope: str,
    max_requests: int = 10,
    window_seconds: int = 60,
) -> tuple[bool, int]:
    """
    Check whether the caller's IP has exceeded its rate limit.

    Parameters
    ----------
    request : HttpRequest
        The current request (used to extract the client IP).
    scope : str
        A namespacing key for the rate limit (e.g. ``'login'``, ``'otp_send'``).
        Different scopes are tracked independently.
    max_requests : int
        Maximum number of requests allowed within the sliding window.
    window_seconds : int
        Length of the sliding window in seconds.

    Returns
    -------
    (is_limited, retry_after)
        ``is_limited`` is ``True`` when the caller should be blocked.
        ``retry_after`` is the number of seconds the caller should wait
        (only meaningful when ``is_limited`` is ``True``).
    """
    ip = get_client_ip(request)
    cache_key = f'ratelimit:{scope}:{ip}'

    now = time.time()
    data = cache.get(cache_key)

    if data is not None:
        count, window_start = data
        elapsed = now - window_start

        if elapsed > window_seconds:
            # Window expired — start a fresh window
            cache.set(cache_key, (1, now), window_seconds)
            return False, 0

        if count >= max_requests:
            retry_after = max(1, int(window_seconds - elapsed))
            return True, retry_after

        # Within limits — bump the counter
        cache.set(cache_key, (count + 1, window_start), window_seconds)
    else:
        # First request in this window
        cache.set(cache_key, (1, now), window_seconds)

    return False, 0
