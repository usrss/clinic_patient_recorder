from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
    """View all notifications."""
    notifications = get_notifications(request.user)
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'base_template': _base_template(request.user),
    })


@login_required
def mark_read(request, pk):
    """Mark a notification as read and redirect to its link."""
    notification = get_object_or_404(Notification, pk=pk)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read."""
    from django.db.models import Q
    Notification.objects.filter(
        Q(recipient=request.user) | Q(recipient_role=request.user.role),
        is_read=False,
    ).update(is_read=True)

    if request.GET.get('next'):
        return redirect(request.GET.get('next'))
    return redirect('notifications:list')


@login_required
def unread_count(request):
    """AJAX endpoint for unread count."""
    count = get_unread_count(request.user)
    return JsonResponse({'count': count})