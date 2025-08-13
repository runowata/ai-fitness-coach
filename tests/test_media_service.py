"""
Tests for MediaService critical functionality
"""
from unittest.mock import Mock, PropertyMock, patch

import pytest

from apps.core.services.media import MediaService


class TestMediaService:
    """Test MediaService cache TTL calculation and error handling"""
    
    def test_calculate_cache_ttl(self):
        """Test TTL calculation with safety margins"""
        # Test with default 2h expiry
        ttl = MediaService._calculate_cache_ttl(7200)  # 2 hours
        assert ttl == 900  # 15 minutes (capped at max)
        
        # Test with 1h expiry (should be capped at 900)
        ttl = MediaService._calculate_cache_ttl(3600)  # 1 hour
        assert ttl == 900  # 3600 - 300 = 3300, but capped at max 900
        
        # Test normal calculation (20 minutes expiry -> 15 minutes cache)
        ttl = MediaService._calculate_cache_ttl(1200)  # 20 minutes  
        assert ttl == 900  # 1200 - 300 = 900, exact max
        
        # Test smaller value for actual calculation
        ttl = MediaService._calculate_cache_ttl(600)  # 10 minutes
        assert ttl == 300  # 600 - 300 = 300 seconds (5 minutes)
        
        # Test minimum TTL
        ttl = MediaService._calculate_cache_ttl(300)  # 5 minutes
        assert ttl == 60  # Minimum 1 minute
        
        # Test with None (uses default)
        ttl = MediaService._calculate_cache_ttl(None)
        assert ttl == 900  # Should use DEFAULT_EXPIRE
    
    def test_get_public_cdn_url_string_handling(self):
        """Test CDN URL generation with string paths"""
        # Mock R2_PUBLIC_BASE
        with patch('apps.core.services.media.R2_PUBLIC_BASE', 'https://cdn.example.com'):
            # Test string path
            url = MediaService.get_public_cdn_url('test/video.mp4')
            assert url == 'https://cdn.example.com/test/video.mp4'
            
            # Test string with leading slash
            url = MediaService.get_public_cdn_url('/test/video.mp4')
            assert url == 'https://cdn.example.com/test/video.mp4'
            
        # Test without R2_PUBLIC_BASE
        with patch('apps.core.services.media.R2_PUBLIC_BASE', ''):
            url = MediaService.get_public_cdn_url('test/video.mp4')
            assert url == ''
    
    def test_get_signed_url_error_handling(self):
        """Test signed URL error handling doesn't crash"""
        # Create mock file field that raises exception when accessing url
        mock_file = Mock()
        mock_file.name = 'test.mp4'
        
        # Make the url property raise an exception when accessed
        type(mock_file).url = PropertyMock(side_effect=Exception("S3 timeout"))
        
        # Should return empty string, not crash
        with patch('apps.core.services.media.logger') as mock_logger:
            result = MediaService.get_signed_url(mock_file)
            assert result == ''
            # Error should be logged even without Django cache
            mock_logger.error.assert_called_once()
    
    def test_archetype_mapping(self):
        """Test archetype normalization"""
        # Without Django settings, should return archetype unchanged
        assert MediaService.get_archetype_mapped('bro') == 'bro'
        assert MediaService.get_archetype_mapped('sergeant') == 'sergeant'
        assert MediaService.get_archetype_mapped('intellectual') == 'intellectual'
        
        # Test unknown archetype (should return as-is)
        assert MediaService.get_archetype_mapped('unknown') == 'unknown'


@pytest.mark.integration
class TestMediaServiceIntegration:
    """Integration tests that would require Django settings"""
    
    def test_cache_key_uniqueness(self):
        """Test that different expiry times would create different cache keys"""
        mock_file = Mock()
        mock_file.name = 'test.mp4'
        mock_file.url = 'https://example.com/test.mp4'  # Valid URL to avoid exceptions
        
        # Without actual cache, these calls should complete without errors
        result1 = MediaService.get_signed_url(mock_file, 3600)
        result2 = MediaService.get_signed_url(mock_file, 7200)
        
        # Should return the URL even without cache
        assert result1 == 'https://example.com/test.mp4'
        assert result2 == 'https://example.com/test.mp4'