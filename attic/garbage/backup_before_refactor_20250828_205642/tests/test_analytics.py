from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.analytics.models import AnalyticsEvent, UserSession
from apps.analytics.services import AnalyticsService

User = get_user_model()


class AnalyticsModelTest(TestCase):
    """Test analytics models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='analyticstest',
            email='analytics@example.com',
            password='testpass123'
        )
    
    def test_create_analytics_event(self):
        """Test creating an analytics event"""
        event = AnalyticsEvent.objects.create(
            event_type='workout_completed',
            event_name='Workout Completed',
            user=self.user,
            properties={'workout_id': 123, 'duration': 45},
            user_properties={'level': 5}
        )
        
        self.assertEqual(event.event_type, 'workout_completed')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.properties['workout_id'], 123)
        self.assertFalse(event.amplitude_sent)
    
    def test_event_to_amplitude_format(self):
        """Test converting event to Amplitude format"""
        event = AnalyticsEvent.objects.create(
            event_type='screen_view',
            event_name='Dashboard View',
            user=self.user,
            properties={'screen': 'dashboard'},
            platform='web'
        )
        
        amplitude_data = event.to_amplitude_format()
        
        self.assertEqual(amplitude_data['event_type'], 'Dashboard View')
        self.assertEqual(amplitude_data['user_id'], str(self.user.id))
        self.assertEqual(amplitude_data['event_properties']['screen'], 'dashboard')
        self.assertEqual(amplitude_data['platform'], 'web')
        self.assertIn('time', amplitude_data)
        self.assertIn('insert_id', amplitude_data)


class AnalyticsServiceTest(TestCase):
    """Test analytics service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='servicetest',
            email='servicetest@example.com',
            password='testpass123'
        )
        self.service = AnalyticsService()
    
    def test_track_event(self):
        """Test tracking an event"""
        event = self.service.track_event(
            event_type='workout_completed',
            event_name='Test Workout Completed',
            user=self.user,
            properties={'workout_id': 456, 'duration': 30},
            send_to_amplitude=False  # Don't send to avoid external dependency
        )
        
        self.assertEqual(event.event_type, 'workout_completed')
        self.assertEqual(event.event_name, 'Test Workout Completed')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.properties['workout_id'], 456)
        self.assertIsNotNone(event.user_properties)
    
    def test_track_screen_view(self):
        """Test tracking screen view"""
        event = self.service.track_screen_view(
            screen_name='Dashboard',
            user=self.user,
            properties={'section': 'workouts'}
        )
        
        self.assertEqual(event.event_type, 'screen_view')
        self.assertEqual(event.event_name, 'Screen View: Dashboard')
        self.assertEqual(event.properties['screen_name'], 'Dashboard')
        self.assertEqual(event.properties['section'], 'workouts')
    
    def test_track_user_signup(self):
        """Test tracking user signup"""
        event = self.service.track_user_signup(self.user)
        
        self.assertEqual(event.event_type, 'user_signup')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.properties['signup_method'], 'email')


class AnalyticsAPITest(TestCase):
    """Test analytics API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apitest',
            email='apitest@example.com',
            password='testpass123',
            completed_onboarding=True
        )
    
    def test_track_event_unauthenticated(self):
        """Test tracking event requires authentication"""
        url = reverse('analytics:track_event')
        data = {
            'event_type': 'workout_completed',
            'properties': {'workout_id': 123}
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('apps.analytics.tasks.send_event_to_amplitude_task')
    def test_track_event_authenticated(self, mock_amplitude_task):
        """Test authenticated user can track events"""
        self.client.force_authenticate(user=self.user)
        url = reverse('analytics:track_event')
        
        data = {
            'event_type': 'workout_completed',
            'event_name': 'API Test Workout',
            'properties': {
                'workout_id': 789,
                'duration_minutes': 60,
                'completion_rate': 0.95
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify event was created
        event = AnalyticsEvent.objects.filter(user=self.user).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, 'workout_completed')
        self.assertEqual(event.event_name, 'API Test Workout')
        self.assertEqual(event.properties['workout_id'], 789)
        
        # Verify Amplitude task was called
        mock_amplitude_task.delay.assert_called_once_with(event.id)
    
    def test_track_screen_view(self):
        """Test tracking screen view"""
        self.client.force_authenticate(user=self.user)
        url = reverse('analytics:track_screen')
        
        data = {
            'screen_name': 'Settings',
            'properties': {
                'previous_screen': 'Dashboard'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify event was created
        event = AnalyticsEvent.objects.filter(
            user=self.user,
            event_type='screen_view'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.properties['screen_name'], 'Settings')
    
    def test_track_anonymous_event(self):
        """Test tracking anonymous event"""
        url = reverse('analytics:track_anonymous')
        
        data = {
            'event_type': 'page_view',
            'event_name': 'Landing Page View',
            'user_id_external': 'anonymous_123',
            'device_id': 'device_456',
            'properties': {
                'page': '/landing',
                'referrer': 'google.com'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIn('event_id', response_data)
        self.assertEqual(response_data['status'], 'tracked')
        
        # Verify event was created
        event = AnalyticsEvent.objects.filter(
            user_id_external='anonymous_123'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, 'page_view')
        self.assertEqual(event.device_id, 'device_456')
    
    def test_user_events_view(self):
        """Test getting user events"""
        self.client.force_authenticate(user=self.user)
        
        # Create some test events
        service = AnalyticsService()
        for i in range(3):
            service.track_event(
                event_type='test_event',
                event_name=f'Test Event {i}',
                user=self.user,
                send_to_amplitude=False
            )
        
        url = reverse('analytics:user_events')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('events', data)
        self.assertEqual(len(data['events']), 3)
        self.assertEqual(data['user_id'], self.user.id)
    
    def test_analytics_health_view(self):
        """Test analytics health endpoint"""
        url = reverse('analytics:analytics_health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('recent_events_24h', data)
        self.assertIn('amplitude_configured', data)


class UserSessionTest(TestCase):
    """Test user session tracking"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='sessiontest',
            email='sessiontest@example.com',
            password='testpass123'
        )
    
    def test_create_user_session(self):
        """Test creating user session"""
        session = UserSession.objects.create(
            session_id='test_session_123',
            user=self.user,
            platform='web'
        )
        
        self.assertEqual(session.session_id, 'test_session_123')
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.platform, 'web')
        self.assertEqual(session.events_count, 0)
    
    def test_end_session(self):
        """Test ending a session"""
        session = UserSession.objects.create(
            session_id='test_session_456',
            user=self.user
        )
        
        self.assertIsNone(session.ended_at)
        self.assertIsNone(session.duration_seconds)
        
        session.end_session()
        
        self.assertIsNotNone(session.ended_at)
        self.assertIsNotNone(session.duration_seconds)
        self.assertGreaterEqual(session.duration_seconds, 0)


@pytest.mark.django_db
def test_analytics_integration():
    """Integration test for analytics system"""
    from apps.analytics.services import AnalyticsService
    
    User = get_user_model()
    user = User.objects.create_user(
        username='integration',
        email='integration@test.com',
        password='testpass123'
    )
    
    service = AnalyticsService()
    
    # Track multiple events
    events = [
        ('user_login', 'User Login', {}),
        ('screen_view', 'Dashboard View', {'screen': 'dashboard'}),
        ('workout_started', 'Workout Started', {'workout_id': 1}),
        ('workout_completed', 'Workout Completed', {'workout_id': 1, 'duration': 45}),
    ]
    
    for event_type, event_name, properties in events:
        event = service.track_event(
            event_type=event_type,
            event_name=event_name,
            user=user,
            properties=properties,
            send_to_amplitude=False
        )
        assert event.event_type == event_type
        assert event.user == user
    
    # Verify all events were created
    user_events = AnalyticsEvent.objects.filter(user=user)
    assert user_events.count() == 4
    
    # Test Amplitude format conversion
    for event in user_events:
        amplitude_data = event.to_amplitude_format()
        assert 'event_type' in amplitude_data
        assert 'user_id' in amplitude_data
        assert 'time' in amplitude_data