from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


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


def health_check(request):
    """
    Health check endpoint for monitoring
    Returns system status and basic diagnostics
    """
    status = {
        'status': 'healthy',
        'timestamp': None,
        'version': '1.0.0',
        'checks': {}
    }
    
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            status['checks']['database'] = 'healthy'
    except Exception as e:
        status['status'] = 'unhealthy'
        status['checks']['database'] = f'error: {str(e)}'
        logger.error(f"Health check database error: {e}")
    
    # Check exercises exist
    try:
        from apps.workouts.models import Exercise
        exercise_count = Exercise.objects.count()
        status['checks']['exercises'] = f'{exercise_count} exercises available'
        
        if exercise_count == 0:
            status['status'] = 'degraded'
            status['checks']['exercises'] = 'warning: no exercises found'
            
    except Exception as e:
        status['status'] = 'unhealthy'
        status['checks']['exercises'] = f'error: {str(e)}'
        logger.error(f"Health check exercises error: {e}")
    
    # Check video clips exist  
    try:
        from apps.workouts.models import VideoClip
        video_count = VideoClip.objects.count()
        placeholder_count = VideoClip.objects.filter(is_placeholder=True).count()
        real_videos = video_count - placeholder_count
        
        status['checks']['videos'] = f'{video_count} total ({real_videos} real, {placeholder_count} placeholder)'
        
        if video_count == 0:
            status['status'] = 'degraded'
            status['checks']['videos'] = 'warning: no videos found'
            
    except Exception as e:
        status['status'] = 'unhealthy' 
        status['checks']['videos'] = f'error: {str(e)}'
        logger.error(f"Health check videos error: {e}")
    
    # Check AI integration
    try:
        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        if openai_key and len(openai_key) > 10:
            status['checks']['ai_integration'] = 'configured'
        else:
            status['status'] = 'degraded'
            status['checks']['ai_integration'] = 'warning: no API key configured'
            
    except Exception as e:
        status['status'] = 'unhealthy'
        status['checks']['ai_integration'] = f'error: {str(e)}'
        logger.error(f"Health check AI integration error: {e}")
    
    from django.utils import timezone
    status['timestamp'] = timezone.now().isoformat()
    
    # Return appropriate HTTP status
    http_status = 200
    if status['status'] == 'degraded':
        http_status = 206  # Partial Content
    elif status['status'] == 'unhealthy':
        http_status = 503  # Service Unavailable
    
    return JsonResponse(status, status=http_status)