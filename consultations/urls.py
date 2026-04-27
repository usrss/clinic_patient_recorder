from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    # Student
    path('', views.student_home, name='student_home'),
    path('submit/', views.student_submit, name='student_submit'),
    path('<int:pk>/', views.student_detail, name='student_detail'),

    # Front desk
    path('queue/', views.queue, name='queue'),
    path('queue/<int:pk>/', views.queue_detail, name='queue_detail'),

    # Nurse
    path('triage/', views.triage_list, name='triage_list'),
    path('triage/<int:pk>/', views.triage_form, name='triage_form'),

    # Doctor
    path('doctor/', views.doctor_list, name='doctor_list'),
    path('prescribe/<int:pk>/', views.prescribe, name='prescribe'),
]