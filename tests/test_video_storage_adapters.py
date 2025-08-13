"""
Test video storage adapters (R2, Stream, External)
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from django.test import TestCase, override_settings

from apps.workouts.models import VideoClip, VideoProvider
from apps.workouts.video_storage import ExternalAdapter, R2Adapter, StreamAdapter, get_storage


class TestR2Adapter(TestCase):
    """Test R2 storage adapter"""
    
    def setUp(self):
        self.adapter = R2Adapter()
        self.clip = Mock(spec=VideoClip)
        self.clip.provider = VideoProvider.R2
        self.clip.r2_file = Mock()
        self.clip.r2_file.name = 'videos/test.mp4'
    
    def test_exists_with_file(self):
        """Test exists returns True when r2_file is present"""
        self.assertTrue(self.adapter.exists(self.clip))
    
    def test_exists_without_file(self):
        """Test exists returns False when r2_file is None"""
        self.clip.r2_file = None
        self.assertFalse(self.adapter.exists(self.clip))
    
    @override_settings(R2_CDN_BASE_URL='https://cdn.example.com')
    def test_playback_url_with_cdn(self):
        """Test CDN URL generation when CDN is configured"""
        url = self.adapter.playback_url(self.clip)
        self.assertEqual(url, 'https://cdn.example.com/videos/test.mp4')
    
    @override_settings(R2_SIGNED_URLS=True, R2_SIGNED_URL_TTL=7200)
    @patch('apps.workouts.video_storage.default_storage')
    def test_playback_url_with_signed_urls(self, mock_storage):
        """Test signed URL generation when enabled"""
        # Mock storage with S3 client
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = 'https://signed.url/test.mp4'
        mock_storage.connection.meta.client = mock_client
        mock_storage.bucket_name = 'test-bucket'
        
        url = self.adapter.playback_url(self.clip)
        
        # Verify presigned URL was generated with correct params
        mock_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': 'videos/test.mp4'},
            ExpiresIn=7200
        )
        self.assertEqual(url, 'https://signed.url/test.mp4')
    
    @patch('apps.workouts.video_storage.default_storage')
    def test_playback_url_fallback(self, mock_storage):
        """Test fallback to regular storage URL"""
        mock_storage.url.return_value = 'https://storage.url/test.mp4'
        
        url = self.adapter.playback_url(self.clip)
        
        mock_storage.url.assert_called_once_with('videos/test.mp4')
        self.assertEqual(url, 'https://storage.url/test.mp4')
    
    @override_settings(R2_SIGNED_URLS=True)
    @patch('apps.workouts.video_storage.default_storage')
    def test_signed_url_fallback_on_error(self, mock_storage):
        """Test fallback when signed URL generation fails"""
        # Mock storage that raises exception
        mock_storage.connection.meta.client.generate_presigned_url.side_effect = Exception('S3 error')
        mock_storage.url.return_value = 'https://fallback.url/test.mp4'
        
        url = self.adapter.playback_url(self.clip)
        
        # Should fallback to regular URL
        self.assertEqual(url, 'https://fallback.url/test.mp4')


class TestStreamAdapter(TestCase):
    """Test Cloudflare Stream adapter"""
    
    def setUp(self):
        self.adapter = StreamAdapter()
        self.clip = Mock(spec=VideoClip)
        self.clip.provider = VideoProvider.STREAM
    
    def test_exists_with_stream_uid(self):
        """Test exists with stream_uid"""
        self.clip.stream_uid = 'abc123'
        self.clip.playback_id = None
        self.assertTrue(self.adapter.exists(self.clip))
    
    def test_exists_with_playback_id(self):
        """Test exists with playback_id"""
        self.clip.stream_uid = None
        self.clip.playback_id = 'xyz789'
        self.assertTrue(self.adapter.exists(self.clip))
    
    def test_exists_without_identifiers(self):
        """Test exists returns False without identifiers"""
        self.clip.stream_uid = None
        self.clip.playback_id = None
        self.assertFalse(self.adapter.exists(self.clip))
    
    def test_playback_url_with_playback_id(self):
        """Test HLS URL generation with playback_id"""
        self.clip.stream_uid = 'abc123'
        self.clip.playback_id = 'xyz789'
        
        url = self.adapter.playback_url(self.clip)
        
        # Should prefer playback_id
        self.assertEqual(url, 'https://videodelivery.net/xyz789/manifest/video.m3u8')
    
    def test_playback_url_with_stream_uid_only(self):
        """Test HLS URL generation with stream_uid only"""
        self.clip.stream_uid = 'abc123'
        self.clip.playback_id = None
        
        url = self.adapter.playback_url(self.clip)
        
        self.assertEqual(url, 'https://videodelivery.net/abc123/manifest/video.m3u8')
    
    @override_settings(CF_STREAM_HLS_TEMPLATE='https://custom.cdn/{playback_id}/stream.m3u8')
    def test_playback_url_with_custom_template(self):
        """Test custom HLS template from settings"""
        self.clip.stream_uid = None
        self.clip.playback_id = 'custom123'
        
        url = self.adapter.playback_url(self.clip)
        
        self.assertEqual(url, 'https://custom.cdn/custom123/stream.m3u8')


class TestExternalAdapter(TestCase):
    """Test external URL adapter"""
    
    def setUp(self):
        self.adapter = ExternalAdapter()
        self.clip = Mock(spec=VideoClip)
        self.clip.provider = VideoProvider.EXTERNAL
    
    def test_exists_returns_false(self):
        """Test exists always returns False (not implemented)"""
        self.assertFalse(self.adapter.exists(self.clip))
    
    def test_playback_url_returns_empty(self):
        """Test playback_url returns empty string (not implemented)"""
        self.assertEqual(self.adapter.playback_url(self.clip), '')


class TestGetStorage(TestCase):
    """Test storage factory function"""
    
    def test_get_r2_storage(self):
        """Test R2 adapter is returned for R2 provider"""
        clip = Mock(spec=VideoClip)
        clip.provider = VideoProvider.R2
        
        storage = get_storage(clip)
        
        self.assertIsInstance(storage, R2Adapter)
    
    def test_get_stream_storage(self):
        """Test Stream adapter is returned for Stream provider"""
        clip = Mock(spec=VideoClip)
        clip.provider = VideoProvider.STREAM
        
        storage = get_storage(clip)
        
        self.assertIsInstance(storage, StreamAdapter)
    
    def test_get_external_storage(self):
        """Test External adapter is returned for External provider"""
        clip = Mock(spec=VideoClip)
        clip.provider = VideoProvider.EXTERNAL
        
        storage = get_storage(clip)
        
        self.assertIsInstance(storage, ExternalAdapter)
    
    def test_default_to_r2(self):
        """Test R2 adapter is default for unknown provider"""
        clip = Mock(spec=VideoClip)
        clip.provider = 'unknown'
        
        storage = get_storage(clip)
        
        self.assertIsInstance(storage, R2Adapter)


@pytest.mark.integration
class TestStorageIntegration(TestCase):
    """Integration tests with real model instances"""
    
    def setUp(self):
        from apps.workouts.models import CSVExercise

        # Create test exercise
        self.exercise = CSVExercise.objects.create(
            slug='test-exercise',
            name='Test Exercise',
            muscle_group='chest',
            is_active=True
        )
    
    def test_r2_clip_with_cdn(self):
        """Test R2 clip with CDN URL generation"""
        clip = VideoClip.objects.create(
            exercise=self.exercise,
            r2_archetype='peer',
            model_name='mod1',
            duration_seconds=30,
            provider=VideoProvider.R2,
            r2_file='videos/test.mp4',
            r2_kind='instruction'
        )
        
        with override_settings(R2_CDN_BASE_URL='https://cdn.test.com'):
            storage = get_storage(clip)
            url = storage.playback_url(clip)
            
            self.assertEqual(url, 'https://cdn.test.com/videos/test.mp4')
            self.assertTrue(storage.exists(clip))
    
    def test_stream_clip_playback(self):
        """Test Stream clip with HLS URL"""
        clip = VideoClip.objects.create(
            exercise=self.exercise,
            r2_archetype='professional',
            model_name='mod2',
            duration_seconds=45,
            provider=VideoProvider.STREAM,
            stream_uid='stream123',
            playback_id='play456',
            r2_kind='technique'
        )
        
        storage = get_storage(clip)
        url = storage.playback_url(clip)
        
        self.assertEqual(url, 'https://videodelivery.net/play456/manifest/video.m3u8')
        self.assertTrue(storage.exists(clip))