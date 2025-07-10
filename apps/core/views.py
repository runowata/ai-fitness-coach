from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Homepage - redirect authenticated users to dashboard"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return render(request, 'core/home.html')


def about_view(request):
    """About page"""
    return render(request, 'core/about.html')


def privacy_view(request):
    """Privacy policy page"""
    return render(request, 'core/privacy.html')


def terms_view(request):
    """Terms of service page"""
    return render(request, 'core/terms.html')


@login_required
def help_view(request):
    """Help and FAQ page"""
    return render(request, 'core/help.html')