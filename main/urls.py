from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

urlpatterns = [
    path('', lambda request: render(request, 'core/home.html'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('consultations/', include('consultations.urls', namespace='consultations')),
    path('patients/', include('patients.urls', namespace='patients')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('certificates/', include('certificates.urls', namespace='certificates')),
]