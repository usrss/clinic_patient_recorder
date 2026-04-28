import csv
import io
from datetime import date, timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Count, Q, Avg
from django.utils import timezone

from accounts.decorators import admin_required
from consultations.models import Consultation, Prescription, PrescriptionItem
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

    if request.GET.get('export') == 'csv':
        return _disease_csv(consultations)

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

    top_diagnoses = (
        Prescription.objects
        .values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

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

    frequent_patients = (
        Consultation.objects
        .values(
            'patient__first_name', 'patient__last_name',
            'patient__patient_id', 'patient__college__abbreviation',
        )
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

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


# ─── MODULE 4: CUSTOM REPORT BUILDER ─────────────────────────────────────────

# Period choices exposed to the template
PERIOD_CHOICES = [
    ('daily',   'Daily'),
    ('weekly',  'Weekly'),
    ('monthly', 'Monthly'),
    ('annual',  'Annual'),
]

ALL_METRICS = [
    ('total_consultations',  'Total Consultations'),
    ('total_patients',       'Total Unique Patients'),
    ('completion_rate',      'Completion Rate'),
    ('cancellation_rate',    'Cancellation Rate'),
    ('avg_per_day',          'Average Consultations / Day'),
    ('top_diagnoses',        'Top Diagnoses'),
    ('top_medicines',        'Most Prescribed Medicines'),
    ('cases_per_college',    'Cases per College'),
    ('cases_by_sex',         'Cases by Sex'),
    ('cases_by_patient_type','Cases by Patient Type'),
    ('trend',                'Trend Over Time'),
    ('low_stock',            'Low Stock Medicines'),
]


@login_required
@admin_required
def report_builder(request):
    colleges = College.objects.all().order_by('name')

    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str   = request.GET.get('date_to', '').strip()
    college_id    = request.GET.get('college_id', '').strip()
    keyword       = request.GET.get('keyword', '').strip()
    grouping      = request.GET.get('grouping', 'date')
    period        = request.GET.get('period', 'daily')
    metrics       = request.GET.getlist('metrics')
    export_fmt    = request.GET.get('export', '')

    date_from = _parse_date(date_from_str)
    date_to   = _parse_date(date_to_str)

    has_query  = bool(date_from_str and date_to_str)
    date_error = None
    results    = None

    if has_query:
        if not date_from:
            date_error = 'Invalid "Date From" value.'
        elif not date_to:
            date_error = 'Invalid "Date To" value.'
        elif date_from > date_to:
            date_error = '"Date From" must be before "Date To".'
        else:
            results = _build_report_results(
                date_from, date_to, college_id or None,
                keyword, grouping, period, metrics,
            )
            if export_fmt == 'csv':
                return _report_csv(results, date_from, date_to)
            if export_fmt == 'excel':
                return _report_excel(results, date_from, date_to)
            if export_fmt == 'pdf':
                return _report_pdf(results, date_from, date_to)

    if not metrics:
        metrics = [m[0] for m in ALL_METRICS]

    return render(request, 'reports/report_builder.html', {
        'colleges':       colleges,
        'date_from':      date_from_str,
        'date_to':        date_to_str,
        'college_id':     college_id,
        'keyword':        keyword,
        'grouping':       grouping,
        'period':         period,
        'metrics':        metrics,
        'all_metrics':    ALL_METRICS,
        'period_choices': PERIOD_CHOICES,
        'has_query':      has_query,
        'date_error':     date_error,
        'results':        results,
        'export_params':  _clean_export_params(request.GET.urlencode()),
    })


def _clean_export_params(qs):
    for fmt in ('csv', 'excel', 'pdf'):
        qs = qs.replace(f'&export={fmt}', '').replace(f'export={fmt}&', '').replace(f'export={fmt}', '')
    return qs


def _build_report_results(date_from, date_to, college_id, keyword, grouping, period, metrics):
    base_qs = Consultation.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )
    if college_id:
        base_qs = base_qs.filter(patient__college_id=college_id)
    if keyword:
        base_qs = base_qs.filter(prescription__diagnosis__icontains=keyword)

    completed_qs  = base_qs.filter(status=Consultation.Status.COMPLETED)
    cancelled_qs  = base_qs.filter(status=Consultation.Status.CANCELLED)
    total_count   = base_qs.count()

    results = {
        'date_from': date_from,
        'date_to':   date_to,
        'grouping':  grouping,
        'period':    period,
        'metrics':   metrics,
    }

    if 'total_consultations' in metrics:
        results['total_consultations'] = total_count

    if 'total_patients' in metrics:
        results['total_patients'] = base_qs.values('patient').distinct().count()

    if 'completion_rate' in metrics:
        completed_count = completed_qs.count()
        results['completion_rate'] = (
            round(completed_count / total_count * 100, 1) if total_count else 0
        )

    if 'cancellation_rate' in metrics:
        cancelled_count = cancelled_qs.count()
        results['cancellation_rate'] = (
            round(cancelled_count / total_count * 100, 1) if total_count else 0
        )

    if 'avg_per_day' in metrics:
        days = max((date_to - date_from).days + 1, 1)
        results['avg_per_day'] = round(total_count / days, 1)

    if 'top_diagnoses' in metrics:
        results['top_diagnoses'] = (
            Prescription.objects
            .filter(consultation__in=completed_qs)
            .values('diagnosis')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

    if 'top_medicines' in metrics:
        results['top_medicines'] = (
            PrescriptionItem.objects
            .filter(prescription__consultation__in=completed_qs)
            .exclude(medicine_name='')
            .values('medicine_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

    if 'cases_per_college' in metrics:
        results['cases_per_college'] = (
            base_qs
            .filter(patient__college__isnull=False)
            .values('patient__college__abbreviation', 'patient__college__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    if 'cases_by_sex' in metrics:
        results['cases_by_sex'] = (
            base_qs
            .values('patient__sex')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    if 'cases_by_patient_type' in metrics:
        results['cases_by_patient_type'] = {
            'students':    base_qs.filter(patient__college__isnull=False).count(),
            'staff':       base_qs.filter(patient__college__isnull=True,
                                          patient__department__gt='').count(),
            'instructors': base_qs.filter(patient__college__isnull=True,
                                          patient__position__gt='').count(),
        }

    if 'trend' in metrics:
        results['trend'] = _build_trend(base_qs, date_from, date_to, period)

    if 'low_stock' in metrics:
        results['low_stock'] = (
            Medicine.objects
            .filter(quantity__lte=F('low_stock_threshold'))
            .order_by('quantity')
            .values('name', 'quantity', 'low_stock_threshold', 'unit')
        )

    # Grouped summary
    if grouping == 'college':
        results['grouped'] = (
            base_qs
            .values('patient__college__abbreviation')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
    elif grouping == 'diagnosis':
        results['grouped'] = (
            completed_qs
            .values('prescription__diagnosis')
            .annotate(count=Count('id'))
            .order_by('-count')[:20]
        )

    return results


def _build_trend(base_qs, date_from, date_to, period):
    """Build time-series data using the selected period granularity."""
    trend = []
    delta = (date_to - date_from).days + 1

    if period == 'daily':
        for i in range(delta):
            d = date_from + timedelta(days=i)
            trend.append({
                'label': d.strftime('%b %d'),
                'count': base_qs.filter(created_at__date=d).count(),
            })

    elif period == 'weekly':
        current = date_from
        while current <= date_to:
            week_end = min(current + timedelta(days=6), date_to)
            trend.append({
                'label': f'{current.strftime("%b %d")}–{week_end.strftime("%b %d")}',
                'count': base_qs.filter(
                    created_at__date__gte=current,
                    created_at__date__lte=week_end,
                ).count(),
            })
            current = week_end + timedelta(days=1)

    elif period == 'monthly':
        # Collect unique year-month combos in range
        seen = set()
        for i in range(delta):
            d = date_from + timedelta(days=i)
            key = (d.year, d.month)
            if key not in seen:
                seen.add(key)
                trend.append({
                    'label': date(d.year, d.month, 1).strftime('%b %Y'),
                    'count': base_qs.filter(
                        created_at__year=d.year,
                        created_at__month=d.month,
                    ).count(),
                })

    elif period == 'annual':
        seen = set()
        for i in range(delta):
            d = date_from + timedelta(days=i)
            if d.year not in seen:
                seen.add(d.year)
                trend.append({
                    'label': str(d.year),
                    'count': base_qs.filter(created_at__year=d.year).count(),
                })

    return trend


# ─── EXPORT HELPERS ───────────────────────────────────────────────────────────

def _report_csv(results, date_from, date_to):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="report_{date_from}_{date_to}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Clinic Report', f'{date_from} to {date_to}'])
    writer.writerow([])

    if 'total_consultations' in results:
        writer.writerow(['Total Consultations', results['total_consultations']])
    if 'total_patients' in results:
        writer.writerow(['Total Unique Patients', results['total_patients']])
    if 'completion_rate' in results:
        writer.writerow(['Completion Rate (%)', results['completion_rate']])
    if 'cancellation_rate' in results:
        writer.writerow(['Cancellation Rate (%)', results['cancellation_rate']])
    if 'avg_per_day' in results:
        writer.writerow(['Avg Consultations / Day', results['avg_per_day']])
    writer.writerow([])

    if 'top_diagnoses' in results:
        writer.writerow(['Top Diagnoses', ''])
        writer.writerow(['Diagnosis', 'Count'])
        for row in results['top_diagnoses']:
            writer.writerow([row['diagnosis'], row['count']])
        writer.writerow([])

    if 'top_medicines' in results:
        writer.writerow(['Top Medicines', ''])
        writer.writerow(['Medicine', 'Count'])
        for row in results['top_medicines']:
            writer.writerow([row['medicine_name'], row['count']])
        writer.writerow([])

    if 'cases_per_college' in results:
        writer.writerow(['Cases per College', ''])
        writer.writerow(['College', 'Cases'])
        for row in results['cases_per_college']:
            writer.writerow([row['patient__college__abbreviation'], row['count']])
        writer.writerow([])

    if 'cases_by_sex' in results:
        writer.writerow(['Cases by Sex', ''])
        writer.writerow(['Sex', 'Cases'])
        for row in results['cases_by_sex']:
            writer.writerow([row['patient__sex'] or '—', row['count']])
        writer.writerow([])

    if 'cases_by_patient_type' in results:
        writer.writerow(['Cases by Patient Type', ''])
        t = results['cases_by_patient_type']
        writer.writerow(['Students', t['students']])
        writer.writerow(['Staff', t['staff']])
        writer.writerow(['Instructors', t['instructors']])
        writer.writerow([])

    if 'trend' in results:
        writer.writerow(['Trend Over Time', ''])
        writer.writerow(['Period', 'Consultations'])
        for row in results['trend']:
            writer.writerow([row['label'], row['count']])
        writer.writerow([])

    if 'low_stock' in results:
        writer.writerow(['Low Stock Medicines', ''])
        writer.writerow(['Medicine', 'Stock', 'Threshold'])
        for row in results['low_stock']:
            writer.writerow([row['name'], row['quantity'], row['low_stock_threshold']])

    return response


def _report_excel(results, date_from, date_to):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        return HttpResponse('openpyxl not installed.', status=500)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Report'

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='1D9E75')

    def write_header(ws, row, cols):
        for col_idx, col in enumerate(cols, start=1):
            cell = ws.cell(row=row, column=col_idx, value=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

    current_row = 1
    ws.cell(row=current_row, column=1,
            value=f'Clinic Report: {date_from} to {date_to}').font = Font(bold=True, size=14)
    current_row += 2

    def add_kv(label, value):
        nonlocal current_row
        ws.cell(row=current_row, column=1, value=label)
        ws.cell(row=current_row, column=2, value=value)
        current_row += 1

    if 'total_consultations' in results:
        add_kv('Total Consultations', results['total_consultations'])
    if 'total_patients' in results:
        add_kv('Total Unique Patients', results['total_patients'])
    if 'completion_rate' in results:
        add_kv('Completion Rate (%)', results['completion_rate'])
    if 'cancellation_rate' in results:
        add_kv('Cancellation Rate (%)', results['cancellation_rate'])
    if 'avg_per_day' in results:
        add_kv('Avg Consultations / Day', results['avg_per_day'])
    current_row += 1

    def add_table(headers, rows_data):
        nonlocal current_row
        write_header(ws, current_row, headers)
        current_row += 1
        for row in rows_data:
            for col_idx, val in enumerate(row, start=1):
                ws.cell(row=current_row, column=col_idx, value=val)
            current_row += 1
        current_row += 1

    if 'top_diagnoses' in results and results['top_diagnoses']:
        add_table(['Diagnosis', 'Count'],
                  [[r['diagnosis'], r['count']] for r in results['top_diagnoses']])

    if 'top_medicines' in results and results['top_medicines']:
        add_table(['Medicine', 'Count'],
                  [[r['medicine_name'], r['count']] for r in results['top_medicines']])

    if 'cases_per_college' in results and results['cases_per_college']:
        add_table(['College', 'Cases'],
                  [[r['patient__college__abbreviation'], r['count']]
                   for r in results['cases_per_college']])

    if 'cases_by_sex' in results and results['cases_by_sex']:
        add_table(['Sex', 'Cases'],
                  [[r['patient__sex'] or '—', r['count']] for r in results['cases_by_sex']])

    if 'cases_by_patient_type' in results:
        t = results['cases_by_patient_type']
        add_table(['Patient Type', 'Cases'],
                  [['Students', t['students']], ['Staff', t['staff']],
                   ['Instructors', t['instructors']]])

    if 'trend' in results and results['trend']:
        add_table(['Period', 'Consultations'],
                  [[r['label'], r['count']] for r in results['trend']])

    if 'low_stock' in results and results['low_stock']:
        add_table(['Medicine', 'Stock', 'Threshold'],
                  [[r['name'], r['quantity'], r['low_stock_threshold']]
                   for r in results['low_stock']])

    for col in ws.columns:
        max_len = max((len(str(c.value or '')) for c in col), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 60)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="report_{date_from}_{date_to}.xlsx"'
    )
    return response


def _report_pdf(results, date_from, date_to):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib import colors
    except ImportError:
        return HttpResponse('reportlab not installed.', status=500)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    h1    = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, spaceAfter=6)
    h2    = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12,
                           spaceAfter=4, spaceBefore=12)
    small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9,
                           textColor=colors.grey)
    primary = colors.HexColor('#1D9E75')

    story = []
    story.append(Paragraph('CLINIC RECORDER', h1))
    story.append(Paragraph(f'Custom Report: {date_from} to {date_to}', styles['Heading2']))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.4*cm))

    def table_section(title, headers, rows):
        story.append(Paragraph(title, h2))
        data = [headers] + rows
        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), primary),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1),
             [colors.white, colors.HexColor('#f5f5f3')]),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    # Summary KV table
    summary_rows = []
    if 'total_consultations' in results:
        summary_rows.append(['Total Consultations', str(results['total_consultations'])])
    if 'total_patients' in results:
        summary_rows.append(['Total Unique Patients', str(results['total_patients'])])
    if 'completion_rate' in results:
        summary_rows.append(['Completion Rate', f"{results['completion_rate']}%"])
    if 'cancellation_rate' in results:
        summary_rows.append(['Cancellation Rate', f"{results['cancellation_rate']}%"])
    if 'avg_per_day' in results:
        summary_rows.append(['Avg Consultations / Day', str(results['avg_per_day'])])
    if summary_rows:
        table_section('Summary', ['Metric', 'Value'], summary_rows)

    if 'top_diagnoses' in results and results['top_diagnoses']:
        table_section('Top Diagnoses', ['Diagnosis', 'Count'],
                      [[r['diagnosis'][:60], str(r['count'])]
                       for r in results['top_diagnoses']])

    if 'top_medicines' in results and results['top_medicines']:
        table_section('Most Prescribed Medicines', ['Medicine', 'Count'],
                      [[r['medicine_name'][:60], str(r['count'])]
                       for r in results['top_medicines']])

    if 'cases_per_college' in results and results['cases_per_college']:
        table_section('Cases per College', ['College', 'Cases'],
                      [[r['patient__college__abbreviation'], str(r['count'])]
                       for r in results['cases_per_college']])

    if 'cases_by_sex' in results and results['cases_by_sex']:
        table_section('Cases by Sex', ['Sex', 'Cases'],
                      [[r['patient__sex'] or '—', str(r['count'])]
                       for r in results['cases_by_sex']])

    if 'cases_by_patient_type' in results:
        t = results['cases_by_patient_type']
        table_section('Cases by Patient Type', ['Type', 'Cases'], [
            ['Students', str(t['students'])],
            ['Staff', str(t['staff'])],
            ['Instructors', str(t['instructors'])],
        ])

    if 'trend' in results and results['trend']:
        table_section('Trend Over Time', ['Period', 'Consultations'],
                      [[r['label'], str(r['count'])] for r in results['trend']])

    if 'low_stock' in results and results['low_stock']:
        table_section('Low Stock Medicines', ['Medicine', 'Stock', 'Threshold'],
                      [[r['name'], str(r['quantity']), str(r['low_stock_threshold'])]
                       for r in results['low_stock']])

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f'Generated: {date.today().strftime("%B %d, %Y")} | Clinic Recorder',
        small
    ))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="report_{date_from}_{date_to}.pdf"'
    )
    return response