"""
Pytest configuration and shared fixtures
"""

import random
from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.test import override_settings

from apps.workouts.catalog import get_catalog
from apps.workouts.services import VideoPlaylistBuilder
from tests.factories import SeededExerciseSetFactory


@pytest.fixture
def seeded_rng():
    """Fixed RNG for deterministic tests"""
    return random.Random(12345)


@pytest.fixture
def clear_caches():
    """Clear all caches before each test"""
    cache.clear()
    catalog = get_catalog()
    catalog.invalidate_cache()
    yield
    cache.clear()


@pytest.fixture
def allowed_slugs():
    """Standard set of exercise slugs with complete video coverage"""
    return {'push-ups', 'squats', 'pull-ups', 'bench-press', 'deadlifts'}


@pytest.fixture
def metrics_noop():
    """Disable metrics collection for tests"""
    with patch('apps.core.metrics.incr') as mock_incr, \
         patch('apps.core.metrics.timing') as mock_timing, \
         patch('apps.core.metrics.gauge') as mock_gauge:
        mock_incr.return_value = None
        mock_timing.return_value = None 
        mock_gauge.return_value = None
        yield {
            'incr': mock_incr,
            'timing': mock_timing,
            'gauge': mock_gauge
        }


@pytest.fixture
def storage_mock():
    """Mock video storage that always reports files as available"""
    mock_storage = Mock()
    mock_storage.exists.return_value = True
    mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
    
    with patch('apps.workouts.video_storage.get_storage', return_value=mock_storage):
        yield mock_storage


@pytest.fixture
def standard_exercises():
    """Create standard exercise set with complete video coverage"""
    return SeededExerciseSetFactory.create_standard_set()


@pytest.fixture
def test_user():
    """Create test user with completed onboarding"""
    from tests.factories import UserFactory
    
    user = UserFactory(
        username='testuser',
        email='test@example.com',
        completed_onboarding=True
    )
    
    # Mock user profile data
    user.profile_data = {
        'fitness_level': 'beginner',
        'archetype': 'professional',
        'available_days': [1, 2, 3, 4, 5],
        'session_duration': 45,
        'equipment': ['none', 'dumbbell']
    }
    
    return user


@pytest.fixture
def test_workout(standard_exercises):
    """Create test workout with standard exercises"""
    from tests.factories import DailyWorkoutFactory
    
    workout = DailyWorkoutFactory(
        id=123,
        week_number=2,
        day_number=3,
        exercises=[
            {'exercise_slug': 'push-ups', 'sets': 3, 'reps': 12},
            {'exercise_slug': 'squats', 'sets': 3, 'reps': 15}
        ]
    )
    
    return workout


@pytest.fixture
def playlist_builder(seeded_rng):
    """VideoPlaylistBuilder with fixed RNG"""
    return VideoPlaylistBuilder(archetype='professional', rng=seeded_rng)


@pytest.fixture
def mock_ai_client():
    """Mock AI client for testing plan generation"""
    mock_client = Mock()
    
    # Standard successful response
    mock_client.generate_workout_plan.return_value = Mock(
        model_dump=lambda: {
            'plan_name': 'Test Plan',
            'duration_weeks': 4,
            'weekly_frequency': 3,
            'session_duration': 45,
            'analysis': {
                'strengths': 'Good fitness foundation',
                'challenges': 'Building consistency', 
                'recommendations': 'Start with basics'
            },
            'weeks': [
                {
                    'week': 1,
                    'focus': 'Foundation',
                    'days': [
                        {
                            'day': 1,
                            'exercises': [
                                {'exercise_slug': 'push-ups', 'sets': 3, 'reps': 10}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    return mock_client


# Test settings overrides
@pytest.fixture
def test_settings():
    """Common test settings"""
    return override_settings(
        # Disable caching for tests
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
            }
        },
        
        # Test-friendly playlist settings
        PLAYLIST_MISTAKE_PROB=0.5,
        PLAYLIST_FALLBACK_MAX_CANDIDATES=10,
        PLAYLIST_STORAGE_RETRY=2,
        
        # AI settings for testing
        AI_REPROMPT_MAX_ATTEMPTS=1,
        SHOW_AI_ANALYSIS=True,
        FALLBACK_TO_LEGACY_FLOW=False,
        
        # Metrics in logging mode
        METRICS_BACKEND='logging'
    )


# Database optimization for tests
@pytest.fixture(scope='session')
def django_db_setup():
    """Optimize database for testing"""
    pass


# Custom markers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line('markers', 'unit: Unit tests')
    config.addinivalue_line('markers', 'integration: Integration tests') 
    config.addinivalue_line('markers', 'e2e: End-to-end tests')
    config.addinivalue_line('markers', 'slow: Slow tests')
    config.addinivalue_line('markers', 'ai: Tests requiring AI client')


# Skip tests based on markers
def pytest_runtest_setup(item):
    """Skip tests based on environment or markers"""
    # Skip AI tests if no API key
    if 'ai' in item.keywords:
        import os
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip('OPENAI_API_KEY not set')


# Custom assertions
class VideoPlaylistAssertions:
    """Custom assertions for video playlist testing"""
    
    @staticmethod
    def assert_playlist_deterministic(playlist1, playlist2):
        """Assert two playlists are identical"""
        clip_ids1 = [item.get('clip_id') for item in playlist1 if 'clip_id' in item]
        clip_ids2 = [item.get('clip_id') for item in playlist2 if 'clip_id' in item]
        
        assert clip_ids1 == clip_ids2, f"Playlists differ: {clip_ids1} != {clip_ids2}"
        assert len(clip_ids1) > 0, "Playlist should contain clips"
    
    @staticmethod
    def assert_playlist_has_required_fields(playlist):
        """Assert playlist items have all required fields"""
        required_fields = {'type', 'url', 'duration', 'clip_id', 'kind'}
        
        for item in playlist:
            if 'clip_id' in item:  # Skip items without clips (like rest day messages)
                missing = required_fields - set(item.keys())
                assert not missing, f"Missing fields in playlist item: {missing}"
    
    @staticmethod
    def assert_playlist_has_required_videos(playlist, exercises):
        """Assert playlist contains required videos for exercises"""
        kinds_found = set()
        for item in playlist:
            if item.get('kind'):
                kinds_found.add(item['kind'])
        
        from apps.workouts.constants import REQUIRED_VIDEO_KINDS_PLAYLIST
        for required_kind in REQUIRED_VIDEO_KINDS_PLAYLIST:
            assert required_kind in kinds_found, f"Missing required video kind: {required_kind}"


@pytest.fixture
def playlist_assertions():
    """Video playlist custom assertions"""
    return VideoPlaylistAssertions()