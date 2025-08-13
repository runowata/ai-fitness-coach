import pytest
from django.test import Client, TestCase
from django.urls import reverse


class HealthEndpointTestCase(TestCase):
    """Test health check endpoint"""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_endpoint_exists(self):
        """Test that health endpoint is accessible"""
        url = reverse('core:health_check')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 206, 503])  # Any valid health status
    
    def test_health_endpoint_structure(self):
        """Test that health endpoint returns proper structure"""
        url = reverse('core:health_check')
        response = self.client.get(url)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertIn('checks', data)
        
        # Check that we have expected checks
        checks = data['checks']
        self.assertIn('database', checks)
        self.assertIn('redis', checks)  # New Redis check
        self.assertIn('ai_integration', checks)
        
    def test_health_endpoint_redis_check(self):
        """Test that Redis check is included"""
        url = reverse('core:health_check')
        response = self.client.get(url)
        
        data = response.json()
        redis_status = data['checks'].get('redis')
        self.assertIsNotNone(redis_status)
        
        # Should be either healthy, warning, or error
        self.assertTrue(
            'healthy' in redis_status or 
            'warning' in redis_status or 
            'error' in redis_status
        )


@pytest.mark.django_db
def test_health_endpoint_smoke():
    """Pytest smoke test for health endpoint"""
    from django.test import Client
    
    client = Client()
    response = client.get('/healthz/')
    
    # Should not return 404 or 500
    assert response.status_code in [200, 206, 503]
    
    # Should return JSON
    data = response.json()
    assert 'status' in data
    assert 'checks' in data
    assert 'redis' in data['checks']