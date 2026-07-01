from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    # ── Certificate Wizard (3 steps) ──────────────────────────────────
    path('wizard/<int:consultation_pk>/type/', views.wizard_type, name='wizard_type'),
    path('wizard/<int:pk>/details/', views.wizard_details, name='wizard_details'),
    path('wizard/<int:pk>/preview/', views.wizard_preview, name='wizard_preview'),

    # ── Print / Reprint ──────────────────────────────────────────────
    path('<int:pk>/print/', views.print_certificate, name='print_certificate'),

    # ── Void / Discard ────────────────────────────────────────────────
    path('<int:pk>/void/', views.void_certificate, name='void_certificate'),
    path('<int:pk>/discard/', views.discard_draft, name='discard_draft'),

    # ── Template Text Editor (admin only) ────────────────────────────
    path('template-text/', views.template_text_list, name='template_text_list'),
    path('template-text/<int:pk>/edit/', views.template_text_edit, name='template_text_edit'),
]