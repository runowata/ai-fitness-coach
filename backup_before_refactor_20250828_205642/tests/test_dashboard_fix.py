"""
Test suite for dashboard fixes and error handling.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from apps.users.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestDashboardFix:
    """Test dashboard view with various edge cases."""

    def test_dashboard_with_no_profile(self):
        """Test dashboard creates profile automatically for users without one."""
        client = Client()
        user = User.objects.create_user(username='testuser', password='testpass')
        
        # Ensure user has no profile initially
        assert not hasattr(user, 'profile') or not UserProfile.objects.filter(user=user).exists()
        
        # Login and access dashboard
        client.login(username='testuser', password='testpass')
        response = client.get(reverse('users:dashboard'))
        
        # Should not raise 500, should create profile
        assert response.status_code in [200, 302]  # 200 for success, 302 for redirect to onboarding
        
        # Profile should now exist
        assert UserProfile.objects.filter(user=user).exists()
        profile = UserProfile.objects.get(user=user)
        assert profile.user == user

    def test_dashboard_with_no_workout_plan(self):
        """Test dashboard handles users without workout plans gracefully."""
        client = Client()
        user = User.objects.create_user(username='testuser', password='testpass')
        profile = UserProfile.objects.create(user=user)
        
        client.login(username='testuser', password='testpass')
        response = client.get(reverse('users:dashboard'))
        
        # Should not raise 500
        assert response.status_code == 200
        
        # Template should handle missing workout plan gracefully
        content = response.content.decode()
        assert 'добро пожаловать' in content.lower() or 'онбординг' in content.lower()

    def test_dashboard_safe_attribute_access(self):
        """Test dashboard template handles missing profile attributes safely."""
        client = Client()
        user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create profile with minimal data
        profile = UserProfile.objects.create(user=user)
        
        client.login(username='testuser', password='testpass')
        response = client.get(reverse('users:dashboard'))
        
        # Should not raise 500 even with minimal profile data
        assert response.status_code == 200
        
        # Should show default values
        content = response.content.decode()
        assert 'stat-number' in content  # Stats section should be present