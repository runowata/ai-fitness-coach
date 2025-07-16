"""Tests for onboarding redirect flow"""
from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User


class OnboardingFlowTestCase(TestCase):
    """Test onboarding redirect flow to prevent infinite loops"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_root_redirect_flow(self):
        """Test that root redirects work correctly based on onboarding status"""
        # Login user
        self.client.force_login(self.user)
        
        # User hasn't completed onboarding yet
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("onboarding:start"))
        
        # Mark onboarding as completed with required data
        self.user.completed_onboarding = True
        self.user.archetype = 'bro'
        self.user.save()
        
        # Create active workout plan
        from apps.workouts.models import WorkoutPlan
        WorkoutPlan.objects.create(
            user=self.user,
            name="Test Plan",
            duration_weeks=6,
            plan_data={},
            is_active=True
        )
        
        # Now should redirect to dashboard
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("users:dashboard"))
    
    def test_dashboard_redirect_flow(self):
        """Test that dashboard redirects to onboarding when incomplete"""
        # Login user
        self.client.force_login(self.user)
        
        # User hasn't completed onboarding yet
        resp = self.client.get(reverse("users:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("onboarding:start"))
        
        # Mark onboarding as completed with required data
        self.user.completed_onboarding = True
        self.user.archetype = 'bro'
        self.user.save()
        
        # Create active workout plan
        from apps.workouts.models import WorkoutPlan
        WorkoutPlan.objects.create(
            user=self.user,
            name="Test Plan",
            duration_weeks=6,
            plan_data={},
            is_active=True
        )
        
        # Now dashboard should load (200 or redirect to create workout plan)
        resp = self.client.get(reverse("users:dashboard"))
        self.assertIn(resp.status_code, [200, 302])  # 302 if needs workout plan creation
    
    def test_no_infinite_redirects(self):
        """Test that there are no infinite redirects between views"""
        # Login user
        self.client.force_login(self.user)
        
        # Test with follow=True to catch redirect loops
        resp = self.client.get("/", follow=True)
        
        # Should not have more than 3 redirects
        self.assertLessEqual(len(resp.redirect_chain), 3)
        
        # Final URL should be either onboarding start or dashboard
        final_url = resp.redirect_chain[-1][0] if resp.redirect_chain else "/"
        self.assertTrue(
            "/onboarding/start/" in final_url or "/users/dashboard/" in final_url,
            f"Unexpected final URL: {final_url}"
        )