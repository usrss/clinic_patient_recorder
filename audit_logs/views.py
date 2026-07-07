from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from accounts.decorators import clinical_staff_required
from .models import AuditLog
from .forms import AuditLogFilterForm


_PER_PAGE = 25


def _base_template(user):
    """Return the correct base template for the current user's role."""
    if user.role == 'admin':
        return 'core/base_admin.html'
    return 'core/base_staff.html'


@login_required
@clinical_staff_required
def audit_log_list(request):
    """
    Display audit log entries with filtering, search, and pagination.

    Access control:
    - Admin: see all logs.
    - Doctor: see only their own activities.
    - Front Desk: see only their own activities.
    """
    user = request.user

    # ── Base queryset ────────────────────────────────────────────────
    if user.role == 'admin':
        qs = AuditLog.objects.all()
    else:
        # Doctor and front desk see only their own entries
        qs = AuditLog.objects.filter(user=user)

    qs = qs.select_related('user').order_by('-timestamp')

    # ── Apply filters ────────────────────────────────────────────────
    form = AuditLogFilterForm(request.GET or None)
    # Validate the form to populate cleaned_data.
    # Note: DateField with required=False still rejects invalid date strings,
    # so is_valid() may return False. Fall back to raw GET values in that case.
    is_valid = form.is_valid()

    if is_valid:
        date_from = form.cleaned_data.get('date_from', '') or ''
        date_to = form.cleaned_data.get('date_to', '') or ''
        raw_date_from = ''
        raw_date_to = ''
        user_filter = form.cleaned_data.get('user', '') or ''
        role_filter = form.cleaned_data.get('role', '') or ''
        action_filter = form.cleaned_data.get('action', '') or ''
        module_filter = form.cleaned_data.get('module', '') or ''
        status_filter = form.cleaned_data.get('status', '') or ''
        search = form.cleaned_data.get('search', '') or ''
    else:
        # Fall back to raw GET values when validation fails.
        # Date fields stay empty to avoid ORM errors with invalid date
        # strings, but the raw GET values are passed as separate template
        # context variables so the user's input remains visible in the
        # form fields and they can see and correct their mistake.
        date_from = ''
        date_to = ''
        raw_date_from = request.GET.get('date_from', '')
        raw_date_to = request.GET.get('date_to', '')
        user_filter = request.GET.get('user', '')
        role_filter = request.GET.get('role', '')
        action_filter = request.GET.get('action', '')
        module_filter = request.GET.get('module', '')
        status_filter = request.GET.get('status', '')
        search = request.GET.get('search', '')

    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)

    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    if user_filter:
        qs = qs.filter(
            Q(user_name__icontains=user_filter) |
            Q(user__username__icontains=user_filter)
        )

    if role_filter:
        qs = qs.filter(user_role=role_filter)

    if action_filter:
        qs = qs.filter(action=action_filter)

    if module_filter:
        qs = qs.filter(module=module_filter)

    if status_filter:
        qs = qs.filter(status=status_filter)

    if search:
        qs = qs.filter(
            Q(description__icontains=search) |
            Q(object_repr__icontains=search) |
            Q(object_id__icontains=search) |
            Q(user_name__icontains=search)
        )

    # ── Pagination ──────────────────────────────────────────────────
    paginator = Paginator(qs, _PER_PAGE)
    page = request.GET.get('page', 1)
    try:
        logs_page = paginator.page(page)
    except PageNotAnInteger:
        logs_page = paginator.page(1)
    except EmptyPage:
        logs_page = paginator.page(paginator.num_pages)

    return render(request, 'audit_logs/audit_log_list.html', {
        'logs': logs_page,
        'form': form,
        'is_paginated': logs_page.has_other_pages(),
        'page_obj': logs_page,
        'paginator': paginator,
        'base_template': _base_template(user),
        'module_choices': AuditLog.Module.choices,

        # Preserve filter values in template (use raw GET values on validation
        # failure so the user's invalid input stays visible for correction)
        'filter_date_from': date_from if is_valid else raw_date_from,
        'filter_date_to': date_to if is_valid else raw_date_to,
        'filter_user': user_filter,
        'filter_role': role_filter,
        'filter_action': action_filter,
        'filter_module': module_filter,
        'filter_status': status_filter,
        'filter_search': search,
    })


@login_required
@clinical_staff_required
def audit_log_detail(request, pk):
    """
    Display a single audit log entry with full details including
    change history (before/after values) and technical information.
    """
    user = request.user

    # ── Permission scoping ───────────────────────────────────────────
    if user.role == 'admin':
        log_entry = get_object_or_404(
            AuditLog.objects.select_related('user'),
            pk=pk,
        )
    else:
        # Non-admin staff can only see their own entries
        log_entry = get_object_or_404(
            AuditLog.objects.select_related('user'),
            pk=pk,
            user=user,
        )

    return render(request, 'audit_logs/audit_log_detail.html', {
        'log': log_entry,
        'base_template': _base_template(user),
    })
