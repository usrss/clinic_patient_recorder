from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard, name='report_dashboard'),
    path('diagnosis-analytics/', views.diagnosis_analytics, name='diagnosis_analytics'),
    path('diagnosis-full-report/', views.diagnosis_full_report, name='diagnosis_full_report'),
    path('builder/', views.report_builder, name='report_builder'),
    path('feedback/', views.feedback_report, name='feedback_report'),
]