from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from consultations.models import Consultation
from .models import ConsultationFeedback
from accounts.decorators import admin_required



def _base_template(user):
    """Return the correct base template for the current user's role."""
    if user.role == 'admin':
        return 'core/base_admin.html'
    return 'core/base_staff.html'

@require_POST
@login_required
def submit_feedback(request):
    consultation_id = request.POST.get('consultation_id')
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if not consultation_id or not rating:
        return JsonResponse({'success': False, 'error': 'Missing data.'})

    consultation = get_object_or_404(Consultation, pk=consultation_id)

    if consultation.patient != request.user.get_patient_record():
        return JsonResponse({'success': False, 'error': 'Not your consultation.'})

    if hasattr(consultation, 'feedback'):
        return JsonResponse({'success': False, 'error': 'Already reviewed.'})

    ConsultationFeedback.objects.create(
        consultation=consultation,
        rating=int(rating),
        comment=comment,
    )

    return JsonResponse({'success': True})


@login_required
@admin_required
def feedback_list(request):
    feedbacks = ConsultationFeedback.objects.select_related(
        'consultation__patient'
    ).order_by('-created_at')

    # ── Search ──
    search = request.GET.get('search', '').strip()
    if search:
        feedbacks = feedbacks.filter(
            Q(consultation__patient__first_name__icontains=search) |
            Q(consultation__patient__last_name__icontains=search) |
            Q(consultation__patient__patient_id__icontains=search) |
            Q(comment__icontains=search)
        )

    # ── Rating filter ──
    rating = request.GET.get('rating', '')
    if rating in ('1','2','3','4','5'):
        feedbacks = feedbacks.filter(rating=int(rating))

    # ── Pagination ──
    paginator = Paginator(feedbacks, 10)
    try:
        page_number = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_number = 1
    page_number = max(page_number, 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'feedback/feedback_list.html', {
        'page_obj': page_obj,
        'search': search,
        'rating_filter': rating,
        'base_template': _base_template(request.user),
    })