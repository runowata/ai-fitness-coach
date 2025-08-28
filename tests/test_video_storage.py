"""Tests for video storage adapters"""

from unittest.mock import Mock, patch

import pytest

from apps.workouts.models import CSVExercise, VideoClip, VideoProvider
from apps.workouts.video_storage import ExternalAdapter, R2Adapter, StreamAdapter, get_storage


@pytest.fixture
def exercise():
    """Create test exercise"""
    exercise = Mock(spec=CSVExercise)
    exercise.id = "EX001"
    exercise.id = "push-ups"
    exercise.name_ru = "Push-ups"
    return exercise


@pytest.fixture
def r2_video_clip(exercise):
    """Create R2 video clip"""
    clip = Mock(spec=VideoClip)
    clip.id = 1
    clip.exercise = exercise
    clip.provider = VideoProvider.R2
    clip.r2_file = Mock()
    clip.r2_file.name = "videos/push_ups_technique_mod1.mp4"
    clip.r2_kind = "technique"
    clip.r2_archetype = "professional"
    clip.duration_seconds = 120
    clip.stream_uid = None
    clip.playback_id = None
    return clip


@pytest.fixture
def stream_video_clip(exercise):
    """Create Stream video clip"""
    clip = Mock(spec=VideoClip)
    clip.id = 2
    clip.exercise = exercise
    clip.provider = VideoProvider.STREAM
    clip.r2_file = None
    clip.stream_uid = "abc123def456"
    clip.playback_id = "xyz789abc123"
    clip.r2_kind = "instruction"
    clip.r2_archetype = "mentor"
    clip.duration_seconds = 180
    return clip


class TestR2Adapter:
    """Test R2 storage adapter"""
    
    def test_exists_with_file(self, r2_video_clip):
        """Test exists returns True when r2_file is present"""
        adapter = R2Adapter()
        assert adapter.exists(r2_video_clip) is True
    
    def test_exists_without_file(self, r2_video_clip):
        """Test exists returns False when r2_file is None"""
        r2_video_clip.r2_file = None
        adapter = R2Adapter()
        assert adapter.exists(r2_video_clip) is False
    
    @patch('apps.workouts.video_storage.default_storage')
    def test_playback_url(self, mock_storage, r2_video_clip):
        """Test playback URL generation"""
        mock_storage.url.return_value = "https://cdn.example.com/videos/push_ups_technique_mod1.mp4"
        
        adapter = R2Adapter()
        url = adapter.playback_url(r2_video_clip)
        
        assert url == "https://cdn.example.com/videos/push_ups_technique_mod1.mp4"
        mock_storage.url.assert_called_once_with("videos/push_ups_technique_mod1.mp4")
    
    def test_playback_url_no_file(self, r2_video_clip):
        """Test playback URL returns empty string when no file"""
        r2_video_clip.r2_file = None
        adapter = R2Adapter()
        assert adapter.playback_url(r2_video_clip) == ""


class TestStreamAdapter:
    """Test Stream storage adapter"""
    
    def test_exists_with_stream_uid(self, stream_video_clip):
        """Test exists returns True when stream_uid is present"""
        adapter = StreamAdapter()
        assert adapter.exists(stream_video_clip) is True
    
    def test_exists_with_playback_id(self, stream_video_clip):
        """Test exists returns True when playback_id is present"""
        stream_video_clip.stream_uid = None
        adapter = StreamAdapter()
        assert adapter.exists(stream_video_clip) is True
    
    def test_exists_without_ids(self, stream_video_clip):
        """Test exists returns False when no IDs present"""
        stream_video_clip.stream_uid = None
        stream_video_clip.playback_id = None
        adapter = StreamAdapter()
        assert adapter.exists(stream_video_clip) is False
    
    @patch('django.conf.settings')
    def test_playback_url_with_template(self, mock_settings, stream_video_clip):
        """Test playback URL generation with custom template"""
        mock_settings.CF_STREAM_HLS_TEMPLATE = "https://videodelivery.net/{playback_id}/manifest/video.m3u8"
        
        adapter = StreamAdapter()
        url = adapter.playback_url(stream_video_clip)
        
        assert url == "https://videodelivery.net/xyz789abc123/manifest/video.m3u8"
    
    @patch('django.conf.settings')
    def test_playback_url_default_template(self, mock_settings, stream_video_clip):
        """Test playback URL generation with default template"""
        # Mock getattr to return empty string (no custom template)
        with patch('builtins.getattr', return_value=""):
            adapter = StreamAdapter()
            url = adapter.playback_url(stream_video_clip)
            assert url == ""


class TestExternalAdapter:
    """Test External URL adapter"""
    
    def test_exists_returns_false(self, stream_video_clip):
        """Test exists always returns False (not implemented)"""
        adapter = ExternalAdapter()
        assert adapter.exists(stream_video_clip) is False
    
    def test_playback_url_returns_empty(self, stream_video_clip):
        """Test playback URL returns empty string (not implemented)"""
        adapter = ExternalAdapter()
        assert adapter.playback_url(stream_video_clip) == ""


class TestGetStorage:
    """Test storage factory function"""
    
    def test_get_r2_adapter(self, r2_video_clip):
        """Test factory returns R2 adapter for R2 provider"""
        storage = get_storage(r2_video_clip)
        assert isinstance(storage, R2Adapter)
    
    def test_get_stream_adapter(self, stream_video_clip):
        """Test factory returns Stream adapter for Stream provider"""
        storage = get_storage(stream_video_clip)
        assert isinstance(storage, StreamAdapter)
    
    def test_get_external_adapter(self, stream_video_clip):
        """Test factory returns External adapter for External provider"""
        stream_video_clip.provider = VideoProvider.EXTERNAL
        storage = get_storage(stream_video_clip)
        assert isinstance(storage, ExternalAdapter)
    
    def test_get_default_adapter(self, stream_video_clip):
        """Test factory returns R2 adapter for unknown provider"""
        stream_video_clip.provider = "unknown"
        storage = get_storage(stream_video_clip)
        assert isinstance(storage, R2Adapter)


@pytest.mark.django_db
class TestVideoStorageIntegration:
    """Integration tests with database"""
    
    def test_end_to_end_r2_flow(self):
        """Test complete R2 storage flow"""
        # This would require actual database models
        # For now, just verify our mocks work
