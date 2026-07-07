from django.shortcuts import render, redirect


def home(request):
    """Homepage — redirects logged-in users to their dashboard."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'core/home.html')
