import pytest
import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.notifications.models import PushSubscription, PushNotificationLog
from apps.notifications.services import OneSignalService, PushNotificationService
from apps.workouts.models import WeeklyNotification, WeeklyLesson

User = get_user_model()


class PushSubscriptionModelTest(TestCase):
    """Test PushSubscription model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_push_subscription(self):
        """Test creating a push subscription"""
        subscription = PushSubscription.objects.create(
            user=self.user,
            provider='onesignal',
            platform='web',
            subscription_id='test-subscription-123'
        )
        
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.provider, 'onesignal')
        self.assertEqual(subscription.platform, 'web')
        self.assertEqual(subscription.subscription_id, 'test-subscription-123')
        self.assertTrue(subscription.is_active)
    
    def test_subscription_str(self):
        """Test subscription string representation"""
        subscription = PushSubscription.objects.create(
            user=self.user,
            provider='fcm',
            platform='android',
            subscription_id='test-token'
        )
        
        expected = f"{self.user.username} - fcm (android)"
        self.assertEqual(str(subscription), expected)


class PushSubscriptionAPITest(TestCase):
    """Test push subscription API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apitest',
            email='apitest@example.com',
            password='testpass123',
            completed_onboarding=True
        )
    
    def test_subscribe_unauthenticated(self):
        """Test subscription requires authentication"""
        url = reverse('notifications:push_subscribe')
        data = {
            'provider': 'onesignal',
            'platform': 'web',
            'subscription_id': 'test-123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_subscribe_authenticated(self):
        """Test authenticated user can subscribe"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:push_subscribe')
        
        data = {
            'provider': 'onesignal',
            'platform': 'web',
            'subscription_id': 'test-sub-123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify subscription was created
        subscription = PushSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.provider, 'onesignal')
        self.assertEqual(subscription.subscription_id, 'test-sub-123')
    
    def test_unsubscribe(self):
        """Test unsubscribing from push notifications"""
        # Create subscription first
        subscription = PushSubscription.objects.create(
            user=self.user,
            provider='onesignal',
            platform='web',
            subscription_id='test-unsub-123'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:push_unsubscribe')
        
        data = {'subscription_id': 'test-unsub-123'}
        response = self.client.delete(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription was deactivated
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)


class OneSignalServiceTest(TestCase):
    """Test OneSignal service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='pushtest',
            email='pushtest@example.com',
            password='testpass123'
        )
        self.subscription = PushSubscription.objects.create(
            user=self.user,
            provider='onesignal',
            platform='web',
            subscription_id='onesignal-player-id'
        )
        self.service = OneSignalService()
    
    @patch('apps.notifications.services.requests.post')
    @patch.object(OneSignalService, '__init__', return_value=None)
    def test_send_notification_success(self, mock_init, mock_post):
        """Test successful notification sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'notification-id-123',
            'recipients': 1
        }
        mock_post.return_value = mock_response
        
        # Manually set service attributes to avoid settings dependency
        service = OneSignalService()
        service.app_id = 'test-app-id'
        service.rest_api_key = 'test-key'
        service.base_url = "https://api.onesignal.com/notifications"
        
        result = service.send_notification(
            self.subscription, 
            'Test Title', 
            'Test Body',
            {'custom': 'data'}
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['provider_message_id'], 'notification-id-123')
        
        # Verify log was created
        log = PushNotificationLog.objects.get(subscription=self.subscription)
        self.assertEqual(log.status, 'sent')
        self.assertEqual(log.title, 'Test Title')
        self.assertEqual(log.provider_message_id, 'notification-id-123')
    
    @patch('apps.notifications.services.requests.post')
    @patch.object(OneSignalService, '__init__', return_value=None)
    def test_send_notification_failure(self, mock_init, mock_post):
        """Test failed notification sending"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'errors': ['Invalid player ID']
        }
        mock_post.return_value = mock_response
        
        # Manually set service attributes
        service = OneSignalService()
        service.app_id = 'test-app-id'
        service.rest_api_key = 'test-key'
        service.base_url = "https://api.onesignal.com/notifications"
        
        result = service.send_notification(
            self.subscription, 
            'Test Title', 
            'Test Body'
        )
        
        self.assertFalse(result['success'])
        
        # Verify log shows failure
        log = PushNotificationLog.objects.get(subscription=self.subscription)
        self.assertEqual(log.status, 'failed')


class PushNotificationServiceTest(TestCase):
    """Test main push notification service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='servicetest',
            email='servicetest@example.com',
            password='testpass123'
        )
        # Enable push notifications for user
        self.user.profile.push_notifications_enabled = True
        self.user.profile.save()
        
        self.subscription = PushSubscription.objects.create(
            user=self.user,
            provider='onesignal',
            platform='web',
            subscription_id='service-test-id'
        )
        self.service = PushNotificationService()
    
    @patch.object(OneSignalService, 'send_notification')
    def test_send_to_user(self, mock_send):
        """Test sending notification to user"""
        # Mock successful send
        mock_send.return_value = {
            'success': True,
            'provider_message_id': 'test-msg-id'
        }
        
        results = self.service.send_to_user(
            self.user,
            'Test Notification',
            'Test notification body',
            {'type': 'test'}
        )
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['success'])
        self.assertEqual(results[0]['subscription_id'], 'service-test-id')
        self.assertEqual(results[0]['provider'], 'onesignal')
        
        # Verify OneSignal service was called
        mock_send.assert_called_once_with(
            self.subscription,
            'Test Notification',
            'Test notification body',
            {'type': 'test'}
        )
    
    def test_send_to_user_disabled_notifications(self):
        """Test sending to user with disabled notifications"""
        self.user.profile.push_notifications_enabled = False
        self.user.profile.save()
        
        results = self.service.send_to_user(
            self.user,
            'Test Notification',
            'Test notification body'
        )
        
        # Should return empty list
        self.assertEqual(len(results), 0)


class WeeklyLessonPushTest(TestCase):
    """Test weekly lesson push notifications"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='weeklytest',
            email='weeklytest@example.com',
            password='testpass123'
        )
        self.user.profile.archetype = '222'
        self.user.profile.push_notifications_enabled = True
        self.user.profile.save()
        
        self.subscription = PushSubscription.objects.create(
            user=self.user,
            provider='onesignal',
            platform='web',
            subscription_id='weekly-test-id'
        )
        
        self.weekly_notification = WeeklyNotification.objects.create(
            user=self.user,
            week=1,
            archetype='222',
            lesson_title='Test Lesson',
            lesson_script='Test lesson content'
        )
    
    @patch.object(PushNotificationService, 'send_to_user')
    def test_send_weekly_lesson_notification(self, mock_send):
        """Test sending weekly lesson push notification"""
        mock_send.return_value = [{'success': True}]
        
        service = PushNotificationService()
        results = service.send_weekly_lesson_notification(self.weekly_notification)
        
        # Verify correct notification was sent
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        self.assertEqual(args[0], self.user)
        self.assertIn('Test Lesson', args[1])  # Title should contain lesson title
        
        # Check data payload (it's passed as a positional argument)
        call_args = mock_send.call_args[0]  # positional args
        if len(call_args) >= 4:  # user, title, body, data
            data = call_args[3]
            self.assertEqual(data['type'], 'weekly_lesson')
            self.assertEqual(data['week'], 1)
            self.assertEqual(data['archetype'], '222')


class WebhookTest(TestCase):
    """Test webhook endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='webhooktest',
            email='webhooktest@example.com',
            password='testpass123'
        )
        self.subscription = PushSubscription.objects.create(
            user=self.user,
            provider='onesignal',
            platform='web',
            subscription_id='webhook-test-id'
        )
        self.log = PushNotificationLog.objects.create(
            subscription=self.subscription,
            title='Webhook Test',
            body='Test notification',
            status='sent',
            provider_message_id='webhook-msg-123'
        )
    
    def test_onesignal_webhook_delivered(self):
        """Test OneSignal delivered webhook"""
        url = reverse('notifications:onesignal_webhook')
        data = {
            'event': 'notification.delivered',
            'id': 'webhook-msg-123'
        }
        
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify log was updated
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'delivered')
        self.assertIsNotNone(self.log.delivered_at)
    
    def test_onesignal_webhook_clicked(self):
        """Test OneSignal clicked webhook"""
        url = reverse('notifications:onesignal_webhook')
        data = {
            'event': 'notification.clicked',
            'id': 'webhook-msg-123'
        }
        
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify log was updated
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'clicked')
        self.assertIsNotNone(self.log.clicked_at)
    
    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON"""
        url = reverse('notifications:onesignal_webhook')
        
        response = self.client.post(
            url,
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


@pytest.mark.django_db
def test_push_stats_endpoint():
    """Test push notification statistics endpoint"""
    from django.test import Client
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    client = Client()
    
    # Create staff user
    staff_user = User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='testpass123',
        is_staff=True
    )
    
    client.force_login(staff_user)
    response = client.get('/api/push/stats/')
    
    assert response.status_code == 200
    data = response.json()
    assert 'total_subscriptions' in data
    assert 'subscriptions_by_provider' in data