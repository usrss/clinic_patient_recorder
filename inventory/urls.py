from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # FIX: Renamed 'list' → 'medicine_list' and 'detail' → 'medicine_detail'
    # to match references in base.html nav, dashboard templates, and other cross-app links.
    # The old names ('list', 'detail') caused NoReverseMatch at runtime.
    path('', views.medicine_list, name='medicine_list'),
    path('medicine/<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('medicine/create/', views.medicine_create, name='create'),
    path('medicine/<int:pk>/edit/', views.medicine_edit, name='edit'),
    path('medicine/<int:pk>/restock/', views.medicine_restock, name='restock'),
    path('medicine/<int:pk>/deduct/', views.medicine_deduct, name='deduct'),
    path('medicine/<int:pk>/delete/', views.medicine_delete, name='delete'),
    path('movements/', views.stock_movements, name='movements'),
    path('movements/<int:medicine_pk>/', views.stock_movements, name='movements_by_medicine'),
]