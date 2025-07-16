from django.test import TestCase, Client
from django.urls import reverse


class GuestAccessTest(TestCase):
    """Test guest access to protected views"""
    
    def setUp(self):
        self.client = Client()
    
    def test_guest_redirected_from_dashboard(self):
        """Guest should be redirected to login when accessing dashboard"""
        response = self.client.get(reverse("users:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login", response.url)
    
    def test_guest_can_access_home(self):
        """Guest should be able to access home page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
    
    def test_home_shows_landing_for_guests(self):
        """Test that home page shows landing page for guests"""
        response = self.client.get("/")
        # For unauthenticated users, should render home template
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "html")  # Should contain HTML content
        
    def test_home_redirects_authenticated_users(self):
        """Test that home page redirects authenticated users"""
        from apps.users.models import User
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.client.force_login(user)
        
        response = self.client.get("/")
        # Authenticated user without onboarding should redirect to onboarding
        self.assertEqual(response.status_code, 302)
        self.assertIn("/onboarding/start/", response.url)