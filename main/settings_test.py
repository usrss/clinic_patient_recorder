"""Test-only settings: run tests without a Redis server.

Used locally as:  python manage.py test --settings=main.settings_test
(Kept out of the project's normal settings file; swap cache/session backends.)
"""
from .settings import *  # noqa: F401,F403

# ── Local-memory cache instead of Redis ──────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── DB-backed sessions instead of cache sessions ─────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
