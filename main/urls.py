from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from core.views import home

urlpatterns = [
    path('', home, name='home'),
    # Redirect /favicon.ico to static logo (browsers auto-request this at root)
    re_path(r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'core/images/norsu-logo.png', permanent=True)),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('consultations/', include('consultations.urls', namespace='consultations')),
    path('patients/', include('patients.urls', namespace='patients')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('certificates/', include('certificates.urls', namespace='certificates')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
    path('audit-logs/', include('audit_logs.urls', namespace='audit_logs')),
]

# Media files — served by Django only in development (DEBUG=True).
# In production (PythonAnywhere), configure the Web tab's static file mappings
# for /media/ -> /home/your-username/.../media instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)