"""Analytics API views for tracking events and providing metrics"""
import json
import logging

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AnalyticsEvent, UserSession
from .serializers import AnalyticsEventSerializer, TrackEventSerializer
from .services import AnalyticsService

logger = logging.getLogger(__name__)


class TrackEventView(generics.CreateAPIView):
    """
    POST /api/analytics/track/ - Track analytics event
    
    Expected payload:
    {
        "event_type": "workout_completed",
        "event_name": "Workout Completed",
        "properties": {
            "workout_id": 123,
            "duration_minutes": 45,
            "completion_rate": 0.95
        },
        "user_properties": {
            "level": 5,
            "archetype": "222"
        }
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrackEventSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract data from serializer
        event_type = serializer.validated_data['event_type']
        event_name = serializer.validated_data.get('event_name')
        properties = serializer.validated_data.get('properties', {})
        user_properties = serializer.validated_data.get('user_properties', {})
        device_id = serializer.validated_data.get('device_id')
        
        # Track the event
        analytics = AnalyticsService()
        event = analytics.track_event(
            event_type=event_type,
            event_name=event_name,
            user=request.user,
            properties=properties,
            user_properties=user_properties,
            request=request,
            device_id=device_id
        )
        
        # Return event details
        response_serializer = AnalyticsEventSerializer(event)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class TrackScreenView(generics.CreateAPIView):
    """
    POST /api/analytics/screen/ - Track screen view
    
    Expected payload:
    {
        "screen_name": "Dashboard",
        "properties": {
            "previous_screen": "Onboarding"
        }
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        screen_name = request.data.get('screen_name')
        properties = request.data.get('properties', {})
        
        if not screen_name:
            return Response(
                {"error": "screen_name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Track screen view
        analytics = AnalyticsService()
        event = analytics.track_screen_view(
            screen_name=screen_name,
            user=request.user,
            properties=properties,
            request=request
        )
        
        response_serializer = AnalyticsEventSerializer(event)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
@api_view(['POST'])
@permission_classes([])
def track_anonymous_event(request):
    """
    POST /api/analytics/track-anonymous/ - Track event for anonymous users
    
    Expected payload:
    {
        "event_type": "page_view",
        "event_name": "Landing Page View",
        "user_id_external": "anonymous_12345",
        "device_id": "device_abc123",
        "properties": {
            "page": "/landing"
        }
    }
    """
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
        event_type = data.get('event_type')
        event_name = data.get('event_name')
        user_id_external = data.get('user_id_external')
        device_id = data.get('device_id')
        properties = data.get('properties', {})
        
        if not event_type:
            return JsonResponse(
                {"error": "event_type is required"},
                status=400
            )
        
        # Track anonymous event
        analytics = AnalyticsService()
        event = analytics.track_event(
            event_type=event_type,
            event_name=event_name,
            user_id_external=user_id_external,
            device_id=device_id,
            properties=properties,
            request=request
        )
        
        return JsonResponse({
            "event_id": str(event.event_id),
            "status": "tracked",
            "timestamp": event.event_time.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error tracking anonymous event: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_events_view(request):
    """
    GET /api/analytics/user/events/ - Get user's recent events
    
    Query parameters:
    - limit: Number of events to return (default: 50, max: 200)
    - event_type: Filter by event type
    - days: Number of days to look back (default: 30)
    """
    limit = min(int(request.GET.get('limit', 50)), 200)
    event_type = request.GET.get('event_type')
    days = int(request.GET.get('days', 30))
    
    # Filter events
    events = AnalyticsEvent.objects.filter(
        user=request.user,
        event_time__gte=timezone.now() - timezone.timedelta(days=days)
    )
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    events = events.order_by('-event_time')[:limit]
    
    # Serialize events
    serializer = AnalyticsEventSerializer(events, many=True)
    
    return Response({
        "events": serializer.data,
        "count": events.count(),
        "user_id": request.user.id
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_session_view(request):
    """
    GET /api/analytics/user/session/ - Get or create current session
    """
    session_id = request.session.session_key
    
    if not session_id:
        # Create new session
        request.session.create()
        session_id = request.session.session_key
    
    # Get or create UserSession
    session, created = UserSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            'user': request.user,
            'platform': 'web',
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': get_client_ip(request),
        }
    )
    
    # Update session user if it was anonymous
    if not session.user and request.user.is_authenticated:
        session.user = request.user
        session.save()
    
    return Response({
        "session_id": session_id,
        "started_at": session.started_at,
        "events_count": session.events_count,
        "duration_seconds": session.duration_seconds
    })


@api_view(['GET'])
@permission_classes([])
def analytics_health_view(request):
    """
    GET /api/analytics/health/ - Health check for analytics system
    """
    try:
        # Check database connectivity
        recent_events_count = AnalyticsEvent.objects.filter(
            event_time__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        # Check Amplitude configuration
        from django.conf import settings
        amplitude_configured = bool(getattr(settings, 'AMPLITUDE_API_KEY', None))
        
        # Check pending events
        pending_amplitude = AnalyticsEvent.objects.filter(
            amplitude_sent=False,
            amplitude_error=''
        ).count()
        
        return JsonResponse({
            "status": "healthy",
            "recent_events_24h": recent_events_count,
            "amplitude_configured": amplitude_configured,
            "pending_amplitude_events": pending_amplitude,
            "timestamp": timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


# Admin/Staff only views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_stats_view(request):
    """
    GET /api/analytics/stats/ - Get analytics statistics (staff only)
    """
    if not request.user.is_staff:
        return Response({"error": "Permission denied"}, status=403)
    
    from datetime import datetime, timedelta

    from django.db.models import Avg, Count

    # Calculate stats
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    stats = {
        "events_24h": AnalyticsEvent.objects.filter(event_time__gte=yesterday).count(),
        "events_7d": AnalyticsEvent.objects.filter(event_time__gte=week_ago).count(),
        "events_30d": AnalyticsEvent.objects.filter(event_time__gte=month_ago).count(),
        "unique_users_24h": AnalyticsEvent.objects.filter(
            event_time__gte=yesterday
        ).values('user').distinct().count(),
        "unique_users_7d": AnalyticsEvent.objects.filter(
            event_time__gte=week_ago
        ).values('user').distinct().count(),
        "top_events_7d": list(
            AnalyticsEvent.objects.filter(event_time__gte=week_ago)
            .values('event_type', 'event_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        ),
        "amplitude_sync_status": {
            "total_events": AnalyticsEvent.objects.count(),
            "sent_to_amplitude": AnalyticsEvent.objects.filter(amplitude_sent=True).count(),
            "pending": AnalyticsEvent.objects.filter(amplitude_sent=False, amplitude_error='').count(),
            "errors": AnalyticsEvent.objects.exclude(amplitude_error='').count(),
        }
    }
    
    return Response(stats)