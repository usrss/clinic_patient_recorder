from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.utils import timezone

from accounts.decorators import admin_required
from accounts.models import User
from consultations.models import Consultation
from inventory.models import Medicine, StockMovement


@login_required
@admin_required
def dashboard(request):
    today = timezone.now().date()

    total_consultations = Consultation.objects.count()
    consultations_today = Consultation.objects.filter(created_at__date=today).count()
    total_students = User.objects.filter(role='student').count()

    # Consultations by status
    status_breakdown = []
    for status in Consultation.Status:
        status_breakdown.append({
            'label': status.label,
            'value': status.value,
            'count': Consultation.objects.filter(status=status.value).count(),
        })

    # Top 5 most dispensed medicines (by quantity OUT movements)
    top_medicines = (
        StockMovement.objects
        .filter(movement_type=StockMovement.MovementType.OUT)
        .values('medicine__name', 'medicine__unit')
        .annotate(total_dispensed=Sum('quantity'))
        .order_by('-total_dispensed')[:5]
    )


    # Low stock medicines
    low_stock = Medicine.objects.filter(
        quantity__lte=F('low_stock_threshold')
    ).order_by('quantity')

    return render(request, 'reports/report_dashboard.html', {
        'total_consultations': total_consultations,
        'consultations_today': consultations_today,
        'total_students': total_students,
        'status_breakdown': status_breakdown,
        'top_medicines': top_medicines,
        'low_stock': low_stock,
    })