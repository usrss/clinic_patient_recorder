from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('create/<int:consultation_pk>/', views.create_certificate, name='create_certificate'),
    path('<int:pk>/print/', views.print_certificate, name='print_certificate'),
]