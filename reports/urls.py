from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard, name='report_dashboard'),
    path('disease/', views.disease_report, name='disease_report'),
    path('summary/', views.summary_report, name='summary_report'),
    path('builder/', views.report_builder, name='report_builder'),
]