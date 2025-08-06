"""Analytics services for tracking user events and sending to external platforms"""
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid

from .models import AnalyticsEvent, UserSession

logger = logging.getLogger(__name__)
User = get_user_model()


class AmplitudeService:
    """Service for sending events to Amplitude"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'AMPLITUDE_API_KEY', None)
        self.base_url = "https://api2.amplitude.com/2/httpapi"
        self.batch_size = getattr(settings, 'AMPLITUDE_BATCH_SIZE', 10)
        
    def send_event(self, event: AnalyticsEvent) -> Dict[str, Any]:
        """Send single event to Amplitude"""
        if not self.api_key:
            logger.warning("Amplitude API key not configured")
            return {"success": False, "error": "API key not configured"}
        
        amplitude_data = event.to_amplitude_format()
        
        payload = {
            "api_key": self.api_key,
            "events": [amplitude_data]
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if result_data.get('code') == 200:
                    # Mark event as sent
                    event.amplitude_sent = True
                    event.amplitude_sent_at = timezone.now()
                    event.save(update_fields=['amplitude_sent', 'amplitude_sent_at'])
                    
                    logger.info(f"Event sent to Amplitude: {event.event_name}")
                    return {"success": True, "response": result_data}
                else:
                    error_msg = f"Amplitude API error: {result_data}"
                    event.amplitude_error = error_msg
                    event.save(update_fields=['amplitude_error'])
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
            else:
                error_msg = f"Amplitude HTTP error {response.status_code}: {response.text}"
                event.amplitude_error = error_msg
                event.save(update_fields=['amplitude_error'])
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except requests.RequestException as e:
            error_msg = f"Amplitude request error: {str(e)}"
            event.amplitude_error = error_msg
            event.save(update_fields=['amplitude_error'])
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def send_events_batch(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Send multiple events to Amplitude in batch"""
        if not self.api_key:
            logger.warning("Amplitude API key not configured")
            return {"success": False, "error": "API key not configured"}
        
        if not events:
            return {"success": True, "sent_count": 0}
        
        # Convert events to Amplitude format
        amplitude_events = []
        for event in events:
            try:
                amplitude_data = event.to_amplitude_format()
                amplitude_events.append(amplitude_data)
            except Exception as e:
                logger.error(f"Error converting event {event.id} to Amplitude format: {e}")
                event.amplitude_error = str(e)
                event.save(update_fields=['amplitude_error'])
        
        if not amplitude_events:
            return {"success": False, "error": "No valid events to send"}
        
        payload = {
            "api_key": self.api_key,
            "events": amplitude_events
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if result_data.get('code') == 200:
                    # Mark all events as sent
                    sent_count = 0
                    for event in events:
                        if not event.amplitude_error:  # Only mark successful conversions
                            event.amplitude_sent = True
                            event.amplitude_sent_at = timezone.now()
                            event.save(update_fields=['amplitude_sent', 'amplitude_sent_at'])
                            sent_count += 1
                    
                    logger.info(f"Batch sent to Amplitude: {sent_count} events")
                    return {"success": True, "sent_count": sent_count, "response": result_data}
                else:
                    error_msg = f"Amplitude batch API error: {result_data}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
            else:
                error_msg = f"Amplitude batch HTTP error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except requests.RequestException as e:
            error_msg = f"Amplitude batch request error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}


class AnalyticsService:
    """Main analytics service for tracking user events"""
    
    def __init__(self):
        self.amplitude = AmplitudeService()
    
    def track_event(
        self,
        event_type: str,
        event_name: str = None,
        user: User = None,
        user_id_external: str = None,
        properties: Dict[str, Any] = None,
        user_properties: Dict[str, Any] = None,
        request=None,
        session_id: str = None,
        device_id: str = None,
        send_to_amplitude: bool = True
    ) -> AnalyticsEvent:
        """Track an analytics event"""
        
        # Use event_type as event_name if not provided
        if not event_name:
            event_name = event_type.replace('_', ' ').title()
        
        # Extract context from request if provided
        platform = None
        user_agent = None
        ip_address = None
        
        if request:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = self._get_client_ip(request)
            
            # Detect platform from user agent
            if 'Mobile' in user_agent:
                if 'iPhone' in user_agent or 'iPad' in user_agent:
                    platform = 'ios'
                elif 'Android' in user_agent:
                    platform = 'android'
                else:
                    platform = 'mobile'
            else:
                platform = 'web'
        
        # Get or create session
        if not session_id and request and hasattr(request, 'session'):
            session_id = request.session.session_key
        
        # Extract user properties if user provided
        if user and not user_properties:
            user_properties = self._get_user_properties(user)
        
        # Create event
        event = AnalyticsEvent.objects.create(
            event_type=event_type,
            event_name=event_name,
            user=user,
            user_id_external=user_id_external,
            properties=properties or {},
            user_properties=user_properties or {},
            session_id=session_id,
            device_id=device_id,
            platform=platform,
            user_agent=user_agent,
            ip_address=ip_address,
            insert_id=str(uuid.uuid4())
        )
        
        # Update session if exists
        if session_id:
            self._update_session(session_id, user, request)
        
        # Send to Amplitude asynchronously
        if send_to_amplitude:
            try:
                from .tasks import send_event_to_amplitude_task
                send_event_to_amplitude_task.delay(event.id)
            except ImportError:
                # Fallback to synchronous sending if Celery not available
                logger.info("Celery not available, sending to Amplitude synchronously")
                self.amplitude.send_event(event)
        
        logger.info(f"Tracked event: {event_name} for user {user.username if user else user_id_external}")
        return event
    
    def track_screen_view(
        self,
        screen_name: str,
        user: User = None,
        properties: Dict[str, Any] = None,
        request=None
    ) -> AnalyticsEvent:
        """Track screen view event"""
        event_properties = {
            'screen_name': screen_name,
            **(properties or {})
        }
        
        return self.track_event(
            event_type='screen_view',
            event_name=f'Screen View: {screen_name}',
            user=user,
            properties=event_properties,
            request=request
        )
    
    def track_user_signup(self, user: User, request=None) -> AnalyticsEvent:
        """Track user signup event"""
        properties = {
            'signup_method': 'email',
            'archetype': user.profile.archetype if hasattr(user, 'profile') else None,
        }
        
        return self.track_event(
            event_type='user_signup',
            user=user,
            properties=properties,
            request=request
        )
    
    def track_workout_completed(
        self,
        user: User,
        workout_id: int,
        duration_minutes: int,
        completion_rate: float,
        feedback_rating: int = None,
        request=None
    ) -> AnalyticsEvent:
        """Track workout completion"""
        properties = {
            'workout_id': workout_id,
            'duration_minutes': duration_minutes,
            'completion_rate': completion_rate,
            'feedback_rating': feedback_rating,
            'archetype': user.profile.archetype if hasattr(user, 'profile') else None,
        }
        
        return self.track_event(
            event_type='workout_completed',
            user=user,
            properties=properties,
            request=request
        )
    
    def track_weekly_lesson_viewed(
        self,
        user: User,
        week: int,
        lesson_title: str,
        archetype: str,
        request=None
    ) -> AnalyticsEvent:
        """Track weekly lesson view"""
        properties = {
            'week': week,
            'lesson_title': lesson_title,
            'archetype': archetype,
        }
        
        return self.track_event(
            event_type='weekly_lesson_viewed',
            user=user,
            properties=properties,
            request=request
        )
    
    def track_achievement_unlocked(
        self,
        user: User,
        achievement_name: str,
        achievement_type: str,
        xp_earned: int,
        request=None
    ) -> AnalyticsEvent:
        """Track achievement unlock"""
        properties = {
            'achievement_name': achievement_name,
            'achievement_type': achievement_type,
            'xp_earned': xp_earned,
            'user_level': user.profile.level if hasattr(user, 'profile') else None,
        }
        
        return self.track_event(
            event_type='achievement_unlocked',
            user=user,
            properties=properties,
            request=request
        )
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _get_user_properties(self, user: User) -> Dict[str, Any]:
        """Extract user properties for analytics"""
        properties = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'signup_date': user.date_joined.isoformat(),
            'completed_onboarding': user.completed_onboarding,
        }
        
        # Add profile properties if available
        if hasattr(user, 'profile'):
            profile = user.profile
            properties.update({
                'archetype': profile.archetype,
                'age': profile.age,
                'level': profile.level,
                'experience_points': profile.experience_points,
                'current_streak': profile.current_streak,
                'total_workouts': profile.total_workouts_completed,
                'push_notifications_enabled': profile.push_notifications_enabled,
            })
        
        return properties
    
    def _update_session(self, session_id: str, user: User = None, request=None):
        """Update or create user session"""
        try:
            session, created = UserSession.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'user': user,
                    'platform': 'web',  # Default, can be enhanced
                    'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
                    'ip_address': self._get_client_ip(request) if request else None,
                }
            )
            
            # Update user if session was anonymous
            if not session.user and user:
                session.user = user
                session.save(update_fields=['user'])
                
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
    
    def get_pending_amplitude_events(self, limit: int = 100) -> List[AnalyticsEvent]:
        """Get events that haven't been sent to Amplitude yet"""
        return AnalyticsEvent.objects.filter(
            amplitude_sent=False,
            amplitude_error=''
        ).order_by('event_time')[:limit]