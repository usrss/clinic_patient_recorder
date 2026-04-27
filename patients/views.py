from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from accounts.models import User
from accounts.decorators import clinical_staff_required
from consultations.models import Consultation


@login_required
@clinical_staff_required
def patient_list(request):
    query = request.GET.get('q', '').strip()
    students = User.objects.filter(role='student').select_related('student_profile')

    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(student_profile__student_id__icontains=query) |
            Q(student_profile__college__icontains=query)
        )

    students = students.order_by('last_name', 'first_name')

    return render(request, 'patients/list.html', {
        'students': students,
        'query': query,
    })


@login_required
@clinical_staff_required
def patient_detail(request, pk):
    student = get_object_or_404(User, pk=pk, role='student')
    profile = getattr(student, 'student_profile', None)
    consultations = Consultation.objects.filter(
        patient=student
    ).select_related('triage', 'prescription').order_by('-created_at')

    return render(request, 'patients/detail.html', {
        'student': student,
        'profile': profile,
        'consultations': consultations,
    })