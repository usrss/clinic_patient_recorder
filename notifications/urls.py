from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:pk>/read/', views.mark_read, name='mark_read'),
    path('<int:pk>/read-no-redirect/', views.mark_read_no_redirect, name='mark_read_no_redirect'),
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('delete-read/', views.delete_read_notifications, name='delete_read_notifications'),
    path('unread-count/', views.unread_count, name='unread_count'),
]