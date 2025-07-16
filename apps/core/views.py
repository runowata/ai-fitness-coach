from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


def home_view(request):
    """Homepage - show landing page for guests, redirect authenticated users"""
    if request.user.is_authenticated:
        # Import here to avoid circular imports
        from apps.onboarding.services import OnboardingService
        
        # Check if user needs onboarding - use same validation as dashboard
        if not OnboardingService.validate_and_fix_onboarding_status(request.user):
            return redirect('onboarding:start')
        else:
            return redirect('users:dashboard')
    
    # Show landing page for guests
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


def health_check(request):
    """Health check endpoint for Render"""
    return JsonResponse({"status": "ok", "health": "good"})