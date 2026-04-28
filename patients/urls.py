from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('<int:pk>/profile/', views.patient_profile_setup, name='patient_profile_setup'),
    path('<int:pk>/profile/setup/', views.patient_full_profile_setup, name='patient_full_profile_setup'),
    path('<int:pk>/contact/', views.patient_contact_edit, name='patient_contact_edit'),
]