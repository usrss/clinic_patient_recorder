from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('<int:pk>/profile/', views.patient_profile_setup, name='patient_profile_setup'),
    path('<int:pk>/contact/', views.patient_contact_edit, name='patient_contact_edit'),

    # ── Academic Year & Archiving ────────────────────────────────────────
    path('archive/settings/', views.archive_settings, name='archive_settings'),
    path('archive/browser/', views.archive_browser, name='archive_browser'),
    path('archive/<int:pk>/unarchive/', views.unarchive_patient, name='unarchive_patient'),
]