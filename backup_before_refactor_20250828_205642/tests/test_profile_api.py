import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class ProfileAPITestCase(TestCase):
    """Tests for user profile API endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            completed_onboarding=True
        )
        # UserProfile is created automatically by signals
        self.profile = self.user.profile
        self.profile.archetype = '111'  # Наставник
        self.profile.age = 25
        self.profile.height = 180
        self.profile.weight = 75
        self.profile.level = 5
        self.profile.experience_points = 450
        self.profile.current_streak = 7
        self.profile.longest_streak = 10
        self.profile.total_workouts_completed = 20
        self.profile.save()
    
    def test_profile_api_unauthenticated(self):
        """Test profile API requires authentication"""
        url = reverse('api_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_profile_api_get(self):
        """Test GET /api/profile/ returns complete user data"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_profile')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Check user data
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertTrue(data['completed_onboarding'])
        
        # Check profile data
        profile_data = data['profile']
        self.assertEqual(profile_data['archetype'], '111')
        self.assertEqual(profile_data['archetype_display'], 'Наставник')
        self.assertEqual(profile_data['age'], 25)
        self.assertEqual(profile_data['height'], 180)
        self.assertEqual(profile_data['weight'], 75)
        self.assertEqual(profile_data['level'], 5)
        self.assertEqual(profile_data['experience_points'], 450)
        self.assertEqual(profile_data['current_streak'], 7)
        self.assertEqual(profile_data['longest_streak'], 10)
        self.assertEqual(profile_data['total_workouts_completed'], 20)
    
    def test_profile_api_update(self):
        """Test PATCH /api/profile/ updates user data"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_profile')
        
        update_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'timezone': 'America/New_York'
        }
        
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify changes
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')
        self.assertEqual(self.user.timezone, 'America/New_York')
    
    def test_profile_readonly_fields(self):
        """Test that readonly fields cannot be updated"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_profile')
        
        # Try to update readonly fields
        update_data = {
            'id': 999,
            'created_at': '2020-01-01T00:00:00Z',
            'completed_onboarding': False
        }
        
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify readonly fields weren't changed
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.id, 999)
        self.assertNotEqual(str(self.user.created_at), '2020-01-01T00:00:00+00:00')
        self.assertTrue(self.user.completed_onboarding)  # Should remain True


@pytest.mark.django_db
def test_profile_api_smoke():
    """Pytest smoke test for profile endpoint"""
    from django.test import Client
    
    client = Client()
    response = client.get('/api/profile/')
    
    # Should require authentication
    assert response.status_code in [401, 403]