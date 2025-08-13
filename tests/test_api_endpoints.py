import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.workouts.models import CSVExercise, ExplainerVideo, WeeklyLesson, WeeklyNotification

User = get_user_model()


class APIEndpointsTestCase(TestCase):
    """Smoke tests for API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # UserProfile is created automatically by signals
        self.profile = self.user.profile
        self.profile.archetype = '333'  # Ровесник (was bro)
        self.profile.save()
        
        # Create test exercise and video
        self.exercise = CSVExercise.objects.create(
            id='EX001_v1',
            name_ru='Тест упражнение',
            level='beginner'
        )
        # Create video for '333' archetype (Ровесник)
        self.video = ExplainerVideo.objects.create(
            exercise=self.exercise,
            archetype='333',
            script='Тестовый скрипт видео',
            locale='ru'
        )
    
    def test_archetype_api_unauthenticated(self):
        """Test archetype API requires authentication"""
        url = reverse('api_archetype')
        response = self.client.patch(url, {'archetype': '222'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_archetype_api_authenticated(self):
        """Test archetype API with authenticated user"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_archetype')
        
        response = self.client.patch(url, {'archetype': '222'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that archetype was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.archetype, '222')
    
    def test_explainer_video_api_unauthenticated(self):
        """Test explainer video API requires authentication"""
        url = reverse('api_exercise_video', kwargs={'exercise_id': 'EX001_v1'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_explainer_video_api_authenticated(self):
        """Test explainer video API with authenticated user"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_exercise_video', kwargs={'exercise_id': 'EX001_v1'})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response data
        data = response.json()
        self.assertEqual(data['exercise_id'], 'EX001_v1')
        self.assertEqual(data['archetype'], '333')  # Ровесник archetype
        self.assertEqual(data['script'], 'Тестовый скрипт видео')
        self.assertEqual(data['locale'], 'ru')
    
    def test_explainer_video_api_not_found(self):
        """Test explainer video API with non-existent exercise"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_exercise_video', kwargs={'exercise_id': 'NONEXISTENT'})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())
    
    def test_explainer_video_api_no_archetype(self):
        """Test explainer video API with user having no archetype"""
        self.profile.archetype = ''
        self.profile.save()
        
        self.client.force_authenticate(user=self.user)
        url = reverse('api_exercise_video', kwargs={'exercise_id': 'EX001_v1'})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())


@pytest.mark.django_db
def test_api_endpoints_smoke():
    """Pytest smoke test to ensure endpoints are accessible"""
    from django.test import Client

    # Test that URLs resolve without 500 errors
    client = Client()
    
    # These should return 401/403, not 500
    response = client.get('/api/archetype/')
    assert response.status_code in [401, 403, 405]  # Not authenticated
    
    response = client.get('/api/exercise/EX001_v1/video/')
    assert response.status_code in [401, 403]  # Not authenticated
    
    response = client.get('/api/weekly/current/')
    assert response.status_code in [401, 403]  # Not authenticated
    
    response = client.get('/api/weekly/1/')
    assert response.status_code in [401, 403]  # Not authenticated
    
    response = client.get('/api/weekly/unread/')
    assert response.status_code in [401, 403]  # Not authenticated


class WeeklyAPITestCase(TestCase):
    """Tests for weekly lesson API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.profile = self.user.profile
        self.profile.archetype = '111'  # Наставник
        self.profile.save()
        
        # Create test lesson
        self.lesson = WeeklyLesson.objects.create(
            week=1,
            archetype='111',
            title='Test Lesson',
            script='Test lesson content',
            locale='ru'
        )
    
    def test_weekly_current_unauthenticated(self):
        """Test weekly current API requires authentication"""
        url = reverse('api_weekly_current')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_weekly_current_no_notification(self):
        """Test weekly current API with no notifications"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_current')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())
    
    def test_weekly_current_with_notification(self):
        """Test weekly current API with unread notification"""
        # Create notification
        notification = WeeklyNotification.objects.create(
            user=self.user,
            week=1,
            archetype='111',
            lesson_title='Test Lesson',
            lesson_script='Test lesson content'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_current')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['week'], 1)
        self.assertEqual(data['lesson_title'], 'Test Lesson')
        self.assertTrue(data['is_read'])  # Should be marked as read
        
        # Verify it's marked as read in DB
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_weekly_lesson_by_week(self):
        """Test weekly lesson API by week number"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_lesson', kwargs={'week': 1})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['week'], 1)
        self.assertEqual(data['title'], 'Test Lesson')
        self.assertEqual(data['archetype'], '111')
    
    def test_weekly_lesson_not_found(self):
        """Test weekly lesson API with non-existent week"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_lesson', kwargs={'week': 999})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())
    
    def test_weekly_lesson_no_archetype(self):
        """Test weekly lesson API with user having no archetype"""
        self.profile.archetype = ''
        self.profile.save()
        
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_lesson', kwargs={'week': 1})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
    
    def test_weekly_unread_unauthenticated(self):
        """Test weekly unread API requires authentication"""
        url = reverse('api_weekly_unread')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_weekly_unread_no_notifications(self):
        """Test weekly unread API with no notifications"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_unread')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'unread': False})
    
    def test_weekly_unread_with_notification(self):
        """Test weekly unread API with unread notification"""
        # Create unread notification
        WeeklyNotification.objects.create(
            user=self.user,
            week=1,
            archetype='111',
            lesson_title='Test Lesson',
            lesson_script='Test lesson content'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_unread')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'unread': True})
    
    def test_weekly_unread_only_read_notifications(self):
        """Test weekly unread API with only read notifications"""
        # Create read notification
        notification = WeeklyNotification.objects.create(
            user=self.user,
            week=1,
            archetype='111',
            lesson_title='Test Lesson',
            lesson_script='Test lesson content'
        )
        notification.mark_as_read()
        
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_unread')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'unread': False})
    
    def test_weekly_lesson_includes_duration_sec(self):
        """Test that weekly lesson API includes duration_sec field"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_weekly_lesson', kwargs={'week': 1})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('duration_sec', data)
        self.assertEqual(data['duration_sec'], 180)  # Default value