import logging
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)


def get_git_sha():
    """
    Get current Git SHA from environment or git command
    """
    # First try environment variable (set by CI/CD)
    git_sha = os.getenv('GIT_SHA', os.getenv('RENDER_GIT_COMMIT', ''))
    
    if not git_sha:
        # Fallback to git command if available
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                git_sha = result.stdout.strip()
        except Exception:
            pass
    
    return git_sha or 'unknown'


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
        'git_sha': get_git_sha(),
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
        from apps.workouts.models import CSVExercise
        exercise_count = CSVExercise.objects.count()
        status['checks']['exercises'] = f'{exercise_count} exercises available'
        
        if exercise_count == 0:
            status['status'] = 'degraded'
            status['checks']['exercises'] = 'warning: no exercises found'
            
    except Exception as e:
        status['status'] = 'unhealthy'
        status['checks']['exercises'] = f'error: {str(e)}'
        logger.error(f"Health check exercises error: {e}")
    
    # Check R2 videos exist  
    try:
        from apps.workouts.models import R2Video
        video_count = R2Video.objects.count()
        
        status['checks']['videos'] = f'{video_count} R2 videos'
        
        if video_count == 0:
            status['status'] = 'degraded'
            status['checks']['videos'] = 'warning: no videos found'
            
    except Exception as e:
        status['status'] = 'unhealthy' 
        status['checks']['videos'] = f'error: {str(e)}'
        logger.error(f"Health check videos error: {e}")
    
    # Check Redis connection (for Celery)
    try:
        import redis
        from django_celery_beat.models import PeriodicTask

        # Get Redis URL from settings
        redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
        if not redis_url:
            redis_url = getattr(settings, 'REDIS_URL', None)
            
        if redis_url:
            # Try to connect to Redis
            r = redis.from_url(redis_url)
            r.ping()  # This will raise exception if Redis is down
            
            # Check if we have periodic tasks configured
            task_count = PeriodicTask.objects.count()
            status['checks']['redis'] = f'healthy (ping successful, {task_count} scheduled tasks)'
        else:
            status['status'] = 'degraded'
            status['checks']['redis'] = 'warning: no Redis URL configured'
            
    except redis.ConnectionError as e:
        status['status'] = 'unhealthy'
        status['checks']['redis'] = f'error: Redis connection failed - {str(e)}'
        logger.error(f"Health check Redis connection error: {e}")
    except Exception as e:
        status['status'] = 'degraded'
        status['checks']['redis'] = f'warning: Redis check failed - {str(e)}'
        logger.error(f"Health check Redis error: {e}")
    
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


def healthz_view(request):
    """
    Enhanced health check endpoint with performance monitoring and alerting
    Supports both basic and detailed health checks
    
    Query parameters:
    - details=true : Include detailed performance metrics
    """
    from .monitoring import HealthEndpoint

    # Check if detailed health check is requested
    include_details = request.GET.get('details', '').lower() in ['true', '1', 'yes']
    
    try:
        health_endpoint = HealthEndpoint()
        health_data = health_endpoint.get_health_status(include_details=include_details)
        
        # Determine HTTP status code
        status_map = {
            'healthy': 200,
            'degraded': 200,  # Still serving traffic but with issues
            'error': 503,
            'critical': 503
        }
        
        status_code = status_map.get(health_data.get('status'), 503)
        
        return JsonResponse(health_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Enhanced health check failed, falling back to basic: {e}")
        
        # Fallback to original simple health check
        # Database check
        try:
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        # Redis check
        try:
            from django.core.cache import cache
            cache.set('health_check_fallback', 'test', 30)
            redis_test = cache.get('health_check_fallback')
            redis_status = "healthy" if redis_test == 'test' else "error"
            cache.delete('health_check_fallback')
        except Exception as e:
            redis_status = f"error: {str(e)}"
            logger.error(f"Redis health check failed: {e}")
        
        # Overall status
        is_healthy = db_status == "healthy" and redis_status == "healthy"
        status_code = 200 if is_healthy else 503
        
        from django.utils import timezone
        response = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": timezone.now().isoformat(),
            "version": "0.9.0-rc1",
            "git_sha": get_git_sha(),
            "components": {
                "database": db_status,
                "redis": redis_status,
            },
            "fallback": True
        }
        
        return JsonResponse(response, status=status_code)