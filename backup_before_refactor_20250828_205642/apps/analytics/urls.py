from django.urls import path

from .views import (
    TrackEventView,
    TrackScreenView,
    analytics_health_view,
    analytics_stats_view,
    track_anonymous_event,
    user_events_view,
    user_session_view,
)

app_name = 'analytics'

urlpatterns = [
    # Event tracking endpoints
    path('api/analytics/track/', TrackEventView.as_view(), name='track_event'),
    path('api/analytics/screen/', TrackScreenView.as_view(), name='track_screen'),
    path('api/analytics/track-anonymous/', track_anonymous_event, name='track_anonymous'),
    
    # User data endpoints
    path('api/analytics/user/events/', user_events_view, name='user_events'),
    path('api/analytics/user/session/', user_session_view, name='user_session'),
    
    # System endpoints
    path('api/analytics/health/', analytics_health_view, name='analytics_health'),
    path('api/analytics/stats/', analytics_stats_view, name='analytics_stats'),
]