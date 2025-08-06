import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import UserProfile
from apps.workouts.models import CSVExercise, ExplainerVideo

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