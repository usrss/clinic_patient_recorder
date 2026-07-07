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
def unread_count(request):
    """AJAX endpoint for unread count."""
    count = get_unread_count(request.user)
    return JsonResponse({'count': count})