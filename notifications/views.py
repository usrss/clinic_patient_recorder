import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Notification
from .utils import get_notifications, get_unread_count



def _base_template(user):
    """Return the correct base template for the current user's role."""
    if user.role == 'patient':
        return 'core/base.html'
    elif user.role == 'admin':
        return 'core/base_admin.html'
    return 'core/base_staff.html'


@login_required
def notification_list(request):
    """View all notifications with filtering and pagination."""
    filter_by = request.GET.get('filter', 'all')
    page = int(request.GET.get('page', 1))
    result = get_notifications(request.user, filter_by=filter_by, page=page)
    return render(request, 'notifications/list.html', {
        'result': result,
        'filter_by': filter_by,
        'base_template': _base_template(request.user),
    })


@login_required
def mark_read(request, pk):
    """Mark a notification as read and redirect to its link."""
    notification = get_object_or_404(Notification, pk=pk)
    # Ensure notification belongs to this user
    if notification.recipient != request.user and notification.recipient_role != request.user.role:
        return redirect('notifications:list')
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:list')


@login_required
def mark_read_no_redirect(request, pk):
    """Mark a notification as read without redirecting (AJAX or back to list)."""
    notification = get_object_or_404(Notification, pk=pk)
    # Ensure notification belongs to this user
    if notification.recipient != request.user and notification.recipient_role != request.user.role:
        return redirect('notifications:list')
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})

    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(
        Q(recipient=request.user) | Q(recipient_role=request.user.role),
        is_read=False,
    ).update(is_read=True)

    next_url = request.GET.get('next') or request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('notifications:list')


@login_required
def delete_notification(request, pk):
    """Delete a single notification."""
    if request.method != 'POST':
        return redirect('notifications:list')

    notification = get_object_or_404(Notification, pk=pk)
    # Ensure notification belongs to this user
    if notification.recipient != request.user and notification.recipient_role != request.user.role:
        return redirect('notifications:list')
    notification.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})

    return redirect('notifications:list')


@login_required
def delete_read_notifications(request):
    """Delete all read notifications for the current user."""
    if request.method != 'POST':
        return redirect('notifications:list')

    Notification.objects.filter(
        Q(recipient=request.user) | Q(recipient_role=request.user.role),
        is_read=True,
    ).delete()

    return redirect('notifications:list')


@login_required
def notification_detail_api(request, pk):
    """
    AJAX endpoint: returns consultation/triage summary data for a notification.
    Used to populate the detail modal when a notification is clicked.
    """
    notification = get_object_or_404(Notification, pk=pk)

    # Ensure notification belongs to this user
    if notification.recipient != request.user and notification.recipient_role != request.user.role:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    data = {
        'notification': {
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.isoformat(),
        },
        'consultation': None,
        'triage': None,
        'prescription': None,
    }

    # Try to extract consultation PK from the notification link
    consultation_pk = None
    if notification.link:
        # Pattern: .../<int:pk>/...  — grab the last integer segment
        matches = re.findall(r'/(\d+)/', notification.link)
        if matches:
            consultation_pk = int(matches[-1])

    if consultation_pk:
        from consultations.models import Consultation, Triage, Prescription
        try:
            consultation = Consultation.objects.select_related(
                'patient',
            ).prefetch_related(
                'triages',
                'prescriptions__items',
            ).get(pk=consultation_pk)

            patient = consultation.patient
            data['consultation'] = {
                'id': consultation.pk,
                'patient_name': patient.get_full_name(),
                'patient_id': patient.patient_id,
                'status': consultation.get_status_display(),
                'symptoms': consultation.symptoms,
                'severity': consultation.severity_description,
                'created_at': consultation.created_at.isoformat(),
            }

            triage = consultation.triages.first()
            if triage:
                data['triage'] = {
                    'blood_pressure': triage.blood_pressure,
                    'temperature': float(triage.temperature),
                    'pulse_rate': triage.pulse_rate,
                    'respiratory_rate': triage.respiratory_rate,
                    'oxygen_saturation': float(triage.oxygen_saturation) if triage.oxygen_saturation else None,
                    'weight': float(triage.weight) if triage.weight else None,
                    'urgency': triage.get_urgency_display(),
                    'notes': triage.notes,
                    'triaged_at': triage.triaged_at.isoformat(),
                    'triaged_by': str(triage.triaged_by) if triage.triaged_by else None,
                }

            prescription = consultation.prescriptions.first()
            if prescription:
                items = []
                for item in prescription.items.all():
                    items.append({
                        'name': item.get_display_name(),
                        'dosage': item.dosage,
                        'frequency': item.frequency,
                        'duration': item.duration,
                        'instructions': item.instructions,
                    })
                data['prescription'] = {
                    'diagnosis': prescription.diagnosis,
                    'treatment_plan': prescription.treatment_plan,
                    'items': items,
                }
        except Consultation.DoesNotExist:
            pass

    return JsonResponse(data)


@login_required
def unread_count(request):
    """AJAX endpoint for unread count."""
    count = get_unread_count(request.user)
    return JsonResponse({'count': count})