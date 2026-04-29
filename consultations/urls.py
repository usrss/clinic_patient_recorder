from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    # ── Patient portal ────────────────────────────────────────────────
    path('my/', views.patient_home, name='patient_home'),
    path('my/submit/', views.patient_submit, name='patient_submit'),
    path('my/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('my/<int:pk>/cancel/', views.patient_cancel, name='patient_cancel'),

    # ── Front desk ────────────────────────────────────────────────────
    path('', views.queue, name='queue'),
    path('create/', views.consultation_create, name='consultation_create'),
    path('queue/<int:pk>/', views.queue_detail, name='queue_detail'),
    path('queue/<int:pk>/cancel/', views.frontdesk_cancel, name='frontdesk_cancel'),

    # ── Admin ─────────────────────────────────────────────────────────
    path('<int:pk>/reopen/', views.admin_reopen, name='admin_reopen'),

    # ── Nurse ─────────────────────────────────────────────────────────
    path('triage/', views.triage_list, name='triage_list'),
    path('triage/<int:pk>/', views.triage_form, name='triage_form'),
    path('triage/<int:pk>/edit/', views.triage_edit, name='triage_edit'),

    # ── Doctor ────────────────────────────────────────────────────────
    path('doctor/', views.doctor_list, name='doctor_list'),
    path('prescribe/<int:pk>/', views.prescribe, name='prescribe'),

    # ── Medical History (Module 3) ────────────────────────────────────
    path('history/<int:patient_pk>/', views.patient_medical_history, name='medical_history'),
    path('history/<int:patient_pk>/pdf/', views.patient_medical_history_pdf, name='medical_history_pdf'),

    # ── Clinical staff shared ─────────────────────────────────────────
    path('detail/<int:pk>/', views.clinical_detail, name='clinical_detail'),

    # Print Consultation
    path('<int:pk>/print/', views.print_consultation, name='print_consultation'),

]