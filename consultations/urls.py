from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    # Student
    path('', views.student_home, name='student_home'),
    path('submit/', views.student_submit, name='student_submit'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/cancel/', views.student_cancel, name='student_cancel'),

    # Front desk
    path('queue/', views.queue, name='queue'),
    path('queue/<int:pk>/', views.queue_detail, name='queue_detail'),
    path('queue/<int:pk>/cancel/', views.frontdesk_cancel, name='frontdesk_cancel'),
    # Admin
    path('<int:pk>/reopen/', views.admin_reopen, name='admin_reopen'),

    # Nurse
    path('triage/', views.triage_list, name='triage_list'),
    path('triage/<int:pk>/', views.triage_form, name='triage_form'),
    path('triage/<int:pk>/edit/', views.triage_edit, name='triage_edit'),

    # Doctor
    path('doctor/', views.doctor_list, name='doctor_list'),
    path('prescribe/<int:pk>/', views.prescribe, name='prescribe'),

    # Clinical staff shared
    path('detail/<int:pk>/', views.clinical_detail, name='clinical_detail'), 
]