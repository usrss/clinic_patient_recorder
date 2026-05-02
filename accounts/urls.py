from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-registration-otp/', views.verify_registration_otp, name='verify_registration_otp'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('change-password/', views.change_password, name='change_password'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle/', views.user_toggle_active, name='user_toggle_active'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('send-otp/', views.send_registration_otp, name='send_registration_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
]