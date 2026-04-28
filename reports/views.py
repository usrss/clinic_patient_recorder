import csv
from datetime import date, timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Count
from django.utils import timezone

from accounts.decorators import admin_required
from consultations.models import Consultation, Prescription
from inventory.models import Medicine, StockMovement
from patients.models import Patient
from colleges.models import College


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required
@admin_required
def dashboard(request):
    today = timezone.now().date()

    total_consultations = Consultation.objects.count()
    consultations_today = Consultation.objects.filter(created_at__date=today).count()
    total_patients      = Patient.objects.filter(is_active=True).count()

    status_breakdown = []
    for status in Consultation.Status:
        status_breakdown.append({
            'label': status.label,
            'value': status.value,
            'count': Consultation.objects.filter(status=status.value).count(),
        })

    top_medicines = (
        StockMovement.objects
        .filter(movement_type=StockMovement.MovementType.OUT)
        .values('medicine__name', 'medicine__unit')
        .annotate(total_dispensed=Sum('quantity'))
        .order_by('-total_dispensed')[:5]
    )

    low_stock = Medicine.objects.filter(
        quantity__lte=F('low_stock_threshold')
    ).order_by('quantity')

    return render(request, 'reports/report_dashboard.html', {
        'total_consultations': total_consultations,
        'consultations_today': consultations_today,
        'total_patients':      total_patients,
        'status_breakdown':    status_breakdown,
        'top_medicines':       top_medicines,
        'low_stock':           low_stock,
    })


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _build_disease_queryset(keyword, date_from, date_to, patient_type, college_id):
    qs = (
        Consultation.objects
        .filter(status=Consultation.Status.COMPLETED)
        .select_related('prescription', 'patient', 'patient__college')
    )

    if keyword:
        qs = qs.filter(prescription__diagnosis__icontains=keyword)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    if patient_type == 'student':
        qs = qs.filter(patient__college__isnull=False)
    elif patient_type == 'staff':
        qs = qs.filter(patient__college__isnull=True, patient__department__gt='')
    elif patient_type == 'instructor':
        qs = qs.filter(patient__college__isnull=True, patient__position__gt='')

    if college_id:
        qs = qs.filter(patient__college_id=college_id)

    return qs.order_by('-created_at')


# ─── DISEASE REPORT ───────────────────────────────────────────────────────────

@login_required
@admin_required
def disease_report(request):
    colleges = College.objects.all().order_by('name')

    keyword       = request.GET.get('keyword', '').strip()
    date_from_str = request.GET.get('date_from', '')
    date_to_str   = request.GET.get('date_to', '')
    patient_type  = request.GET.get('patient_type', 'all')
    college_id    = request.GET.get('college_id', '')

    date_from = _parse_date(date_from_str)
    date_to   = _parse_date(date_to_str)

    consultations = _build_disease_queryset(
        keyword, date_from, date_to, patient_type, college_id or None,
    )

    # CSV export
    if request.GET.get('export') == 'csv':
        return _disease_csv(consultations)

    # Aggregate breakdowns
    total_affected = consultations.values('patient').distinct().count()

    by_type = {
        'student':    consultations.filter(patient__college__isnull=False)
                                   .values('patient').distinct().count(),
        'staff':      consultations.filter(patient__college__isnull=True,
                                           patient__department__gt='')
                                   .values('patient').distinct().count(),
        'instructor': consultations.filter(patient__college__isnull=True,
                                           patient__position__gt='')
                                   .values('patient').distinct().count(),
    }

    by_college = (
        consultations
        .filter(patient__college__isnull=False)
        .values('patient__college__abbreviation', 'patient__college__name')
        .annotate(count=Count('patient', distinct=True))
        .order_by('-count')
    )

    return render(request, 'reports/disease_report.html', {
        'consultations':  consultations,
        'colleges':       colleges,
        'keyword':        keyword,
        'date_from':      date_from_str,
        'date_to':        date_to_str,
        'patient_type':   patient_type,
        'college_id':     college_id,
        'total_affected': total_affected,
        'by_type':        by_type,
        'by_college':     by_college,
        'has_filters':    any([keyword, date_from_str, date_to_str,
                               patient_type != 'all', college_id]),
    })


def _disease_csv(consultations):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="disease_report_{date.today()}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow([
        'Consultation #', 'Date', 'Patient Name', 'Patient ID',
        'Type', 'College / Department', 'Diagnosis', 'Treatment Plan',
    ])
    for c in consultations:
        rx = getattr(c, 'prescription', None)
        p  = c.patient
        if p.college:
            p_type, p_org = 'Student', p.college.abbreviation
        elif p.department:
            p_type, p_org = 'Staff', p.department
        else:
            p_type, p_org = 'Instructor', p.position or '—'
        writer.writerow([
            c.pk,
            c.created_at.strftime('%Y-%m-%d'),
            p.get_full_name(),
            p.patient_id,
            p_type,
            p_org,
            rx.diagnosis if rx else '—',
            rx.treatment_plan if rx else '—',
        ])
    return response


# ─── SUMMARY REPORT ───────────────────────────────────────────────────────────

@login_required
@admin_required
def summary_report(request):
    today = timezone.now().date()

    # Monthly consultations — last 12 months
    monthly_data = []
    for i in range(11, -1, -1):
        year  = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year  -= 1
        count = Consultation.objects.filter(
            created_at__year=year,
            created_at__month=month,
        ).count()
        monthly_data.append({
            'label': date(year, month, 1).strftime('%b %Y'),
            'count': count,
        })

    # Top 10 diagnoses overall
    top_diagnoses = (
        Prescription.objects
        .values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Top diagnosis per college
    top_per_college = []
    for college in College.objects.all():
        top = (
            Prescription.objects
            .filter(consultation__patient__college=college)
            .values('diagnosis')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        if top:
            top_per_college.append({
                'college':   college.abbreviation,
                'diagnosis': top['diagnosis'],
                'count':     top['count'],
            })

    # Most frequent patients — top 5
    frequent_patients = (
        Consultation.objects
        .values(
            'patient__first_name', 'patient__last_name',
            'patient__patient_id', 'patient__college__abbreviation',
        )
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    # Average consultations per day — last 30 days
    thirty_days_ago = today - timedelta(days=30)
    recent_count    = Consultation.objects.filter(
        created_at__date__gte=thirty_days_ago
    ).count()
    avg_per_day = round(recent_count / 30, 1)

    total_completed = Consultation.objects.filter(
        status=Consultation.Status.COMPLETED
    ).count()
    total_cancelled = Consultation.objects.filter(
        status=Consultation.Status.CANCELLED
    ).count()

    return render(request, 'reports/summary_report.html', {
        'monthly_data':      monthly_data,
        'top_diagnoses':     top_diagnoses,
        'top_per_college':   top_per_college,
        'frequent_patients': frequent_patients,
        'avg_per_day':       avg_per_day,
        'total_completed':   total_completed,
        'total_cancelled':   total_cancelled,
        'today':             today,
    })