import csv
import io
from datetime import date, timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Count, Q
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

@login_required
@admin_required
def report_builder(request):
    """
    Custom report engine. Admin selects date range (required), optional filters,
    grouping, and which metrics to include. Results displayed on same page.
    Export available as CSV, Excel, or PDF.
    """
    colleges = College.objects.all().order_by('name')

    # Parse inputs
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str   = request.GET.get('date_to', '').strip()
    college_id    = request.GET.get('college_id', '').strip()
    keyword       = request.GET.get('keyword', '').strip()
    grouping      = request.GET.get('grouping', 'date')
    metrics       = request.GET.getlist('metrics')
    export_fmt    = request.GET.get('export', '')

    date_from = _parse_date(date_from_str)
    date_to   = _parse_date(date_to_str)

    # Validation: date range required before generating
    has_query   = bool(date_from_str and date_to_str)
    date_error  = None
    results     = None

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
                keyword, grouping, metrics,
            )
            if export_fmt == 'csv':
                return _report_csv(results, date_from, date_to)
            if export_fmt == 'excel':
                return _report_excel(results, date_from, date_to)
            if export_fmt == 'pdf':
                return _report_pdf(results, date_from, date_to)

    # Default metrics checklist
    all_metrics = [
        ('total_consultations', 'Total Consultations'),
        ('total_patients',      'Total Unique Patients'),
        ('top_diagnoses',       'Top Diagnoses'),
        ('top_medicines',       'Most Prescribed Medicines'),
        ('cases_per_college',   'Cases per College'),
        ('trend',               'Trend Over Time'),
    ]
    if not metrics:
        metrics = [m[0] for m in all_metrics]  # default: all selected

    return render(request, 'reports/report_builder.html', {
        'colleges':      colleges,
        'date_from':     date_from_str,
        'date_to':       date_to_str,
        'college_id':    college_id,
        'keyword':       keyword,
        'grouping':      grouping,
        'metrics':       metrics,
        'all_metrics':   all_metrics,
        'has_query':     has_query,
        'date_error':    date_error,
        'results':       results,
        'export_params': request.GET.urlencode().replace('&export=csv','').replace('&export=excel','').replace('&export=pdf',''),
    })


def _build_report_results(date_from, date_to, college_id, keyword, grouping, metrics):
    """Assemble report data from live records. Nothing is stored."""

    base_qs = Consultation.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )
    if college_id:
        base_qs = base_qs.filter(patient__college_id=college_id)
    if keyword:
        base_qs = base_qs.filter(prescription__diagnosis__icontains=keyword)

    completed_qs = base_qs.filter(status=Consultation.Status.COMPLETED)

    results = {
        'date_from': date_from,
        'date_to':   date_to,
        'grouping':  grouping,
        'metrics':   metrics,
    }

    # Total consultations
    if 'total_consultations' in metrics:
        results['total_consultations'] = base_qs.count()

    # Total unique patients
    if 'total_patients' in metrics:
        results['total_patients'] = base_qs.values('patient').distinct().count()

    # Top diagnoses
    if 'top_diagnoses' in metrics:
        results['top_diagnoses'] = (
            Prescription.objects
            .filter(consultation__in=completed_qs)
            .values('diagnosis')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

    # Most prescribed medicines (free-text items)
    if 'top_medicines' in metrics:
        results['top_medicines'] = (
            PrescriptionItem.objects
            .filter(prescription__consultation__in=completed_qs)
            .exclude(medicine_name='')
            .values('medicine_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

    # Cases per college
    if 'cases_per_college' in metrics:
        results['cases_per_college'] = (
            base_qs
            .filter(patient__college__isnull=False)
            .values('patient__college__abbreviation', 'patient__college__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    # Trend over time
    if 'trend' in metrics:
        results['trend'] = _build_trend(base_qs, date_from, date_to, grouping)

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


def _build_trend(base_qs, date_from, date_to, grouping):
    """Build time-series data across the date range."""
    delta = date_to - date_from
    days = delta.days + 1
    trend = []

    if days <= 31 or grouping == 'date':
        # Daily
        for i in range(days):
            d = date_from + timedelta(days=i)
            trend.append({
                'label': d.strftime('%b %d'),
                'count': base_qs.filter(created_at__date=d).count(),
            })
    else:
        # Weekly buckets
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

    if 'trend' in results:
        writer.writerow(['Trend Over Time', ''])
        writer.writerow(['Period', 'Consultations'])
        for row in results['trend']:
            writer.writerow([row['label'], row['count']])

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
    ws.cell(row=current_row, column=1, value=f'Clinic Report: {date_from} to {date_to}').font = Font(bold=True, size=14)
    current_row += 2

    if 'total_consultations' in results:
        ws.cell(row=current_row, column=1, value='Total Consultations')
        ws.cell(row=current_row, column=2, value=results['total_consultations'])
        current_row += 1
    if 'total_patients' in results:
        ws.cell(row=current_row, column=1, value='Total Unique Patients')
        ws.cell(row=current_row, column=2, value=results['total_patients'])
        current_row += 1
    current_row += 1

    if 'top_diagnoses' in results and results['top_diagnoses']:
        write_header(ws, current_row, ['Diagnosis', 'Count'])
        current_row += 1
        for row in results['top_diagnoses']:
            ws.cell(row=current_row, column=1, value=row['diagnosis'])
            ws.cell(row=current_row, column=2, value=row['count'])
            current_row += 1
        current_row += 1

    if 'top_medicines' in results and results['top_medicines']:
        write_header(ws, current_row, ['Medicine', 'Count'])
        current_row += 1
        for row in results['top_medicines']:
            ws.cell(row=current_row, column=1, value=row['medicine_name'])
            ws.cell(row=current_row, column=2, value=row['count'])
            current_row += 1
        current_row += 1

    if 'cases_per_college' in results and results['cases_per_college']:
        write_header(ws, current_row, ['College', 'Cases'])
        current_row += 1
        for row in results['cases_per_college']:
            ws.cell(row=current_row, column=1, value=row['patient__college__abbreviation'])
            ws.cell(row=current_row, column=2, value=row['count'])
            current_row += 1
        current_row += 1

    if 'trend' in results and results['trend']:
        write_header(ws, current_row, ['Period', 'Consultations'])
        current_row += 1
        for row in results['trend']:
            ws.cell(row=current_row, column=1, value=row['label'])
            ws.cell(row=current_row, column=2, value=row['count'])
            current_row += 1

    # Auto-fit columns
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
    response['Content-Disposition'] = f'attachment; filename="report_{date_from}_{date_to}.xlsx"'
    return response


def _report_pdf(results, date_from, date_to):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib import colors
    except ImportError:
        return HttpResponse('reportlab not installed.', status=500)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, spaceAfter=6)
    h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, spaceAfter=4, spaceBefore=12)
    body = styles['Normal']
    small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9, textColor=colors.grey)

    story = []
    story.append(Paragraph('CLINIC RECORDER', h1))
    story.append(Paragraph(f'Custom Report: {date_from} to {date_to}', styles['Heading2']))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.4*cm))

    primary = colors.HexColor('#1D9E75')

    def table_section(title, headers, rows):
        story.append(Paragraph(title, h2))
        data = [headers] + rows
        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f3')]),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    if 'total_consultations' in results or 'total_patients' in results:
        summary_rows = []
        if 'total_consultations' in results:
            summary_rows.append(['Total Consultations', str(results['total_consultations'])])
        if 'total_patients' in results:
            summary_rows.append(['Total Unique Patients', str(results['total_patients'])])
        table_section('Summary', ['Metric', 'Value'], summary_rows)

    if 'top_diagnoses' in results and results['top_diagnoses']:
        rows = [[r['diagnosis'][:60], str(r['count'])] for r in results['top_diagnoses']]
        table_section('Top Diagnoses', ['Diagnosis', 'Count'], rows)

    if 'top_medicines' in results and results['top_medicines']:
        rows = [[r['medicine_name'][:60], str(r['count'])] for r in results['top_medicines']]
        table_section('Most Prescribed Medicines', ['Medicine', 'Count'], rows)

    if 'cases_per_college' in results and results['cases_per_college']:
        rows = [[r['patient__college__abbreviation'], str(r['count'])] for r in results['cases_per_college']]
        table_section('Cases per College', ['College', 'Cases'], rows)

    if 'trend' in results and results['trend']:
        rows = [[r['label'], str(r['count'])] for r in results['trend']]
        table_section('Trend Over Time', ['Period', 'Consultations'], rows)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f'Generated: {date.today().strftime("%B %d, %Y")} | Clinic Recorder',
        small
    ))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{date_from}_{date_to}.pdf"'
    return response