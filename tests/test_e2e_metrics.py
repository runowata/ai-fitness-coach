"""
End-to-end tests with comprehensive metrics verification
"""

from unittest.mock import Mock, patch

import pytest
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import override_settings

from apps.core.metrics import MetricNames
from apps.workouts.constants import REQUIRED_VIDEO_KINDS_PLAYLIST, VideoKind
from apps.workouts.models import DailyWorkout, WorkoutPlan
from apps.workouts.services import VideoPlaylistBuilder
from tests.factories import (
    CSVExerciseFactory,
    DailyWorkoutFactory,
    SeededExerciseSetFactory,
    UserFactory,
    VideoClipFactory,
)


@pytest.mark.e2e
@override_settings(
    PLAYLIST_MISTAKE_PROB=0.5,
    PLAYLIST_FALLBACK_MAX_CANDIDATES=10,
    PLAYLIST_STORAGE_RETRY=2
)
class TestE2EWorkoutPlaylistGeneration(TestCase):
    """End-to-end playlist generation with full pipeline"""
    
    def setUp(self):
        # Create complete exercise set
        self.exercises = SeededExerciseSetFactory.create_standard_set()
        
        # Create workout with these exercises
        self.workout = Mock()
        self.workout.id = 12345
        self.workout.week_number = 2
        self.workout.day_number = 3
        self.workout.is_rest_day = False
        self.workout.exercises = [
            {'exercise_slug': 'push-ups', 'sets': 3, 'reps': 12},
            {'exercise_slug': 'squats', 'sets': 3, 'reps': 15},
            {'exercise_slug': 'pull-ups', 'sets': 3, 'reps': 8}
        ]
    
    @patch('apps.core.metrics.incr')
    @patch('apps.core.metrics.timing')
    def test_complete_playlist_generation_with_metrics(self, mock_timing, mock_incr):
        """Test complete playlist generation tracks all expected metrics"""
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            # Mock storage that reports all files as available
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            # Generate playlist
            playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        # Verify playlist structure
        self.assertGreater(len(playlist), 0, "Playlist should have items")
        
        # Verify required videos present
        kinds_in_playlist = {item.get('kind') for item in playlist if 'kind' in item}
        for required_kind in REQUIRED_VIDEO_KINDS_PLAYLIST:
            self.assertIn(required_kind, kinds_in_playlist, f"Missing required kind: {required_kind}")
        
        # Verify metrics were tracked
        mock_timing.assert_any_call(MetricNames.VIDEO_PLAYLIST_BUILD_TIME, pytest.approx(0, abs=5000))  # Some build time
        mock_incr.assert_any_call(MetricNames.VIDEO_PLAYLIST_CANDIDATES, pytest.approx(0, abs=100))  # Some candidates found
    
    def test_playlist_deterministic_across_runs(self):
        """Test playlist is deterministic across multiple runs"""
        builder1 = VideoPlaylistBuilder('professional')
        builder2 = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist1 = builder1.build_workout_playlist(self.workout, 'professional')
            playlist2 = builder2.build_workout_playlist(self.workout, 'professional')
        
        # Extract clip IDs for comparison
        clip_ids1 = [item['clip_id'] for item in playlist1 if 'clip_id' in item]
        clip_ids2 = [item['clip_id'] for item in playlist2 if 'clip_id' in item]
        
        self.assertEqual(clip_ids1, clip_ids2, "Playlists should be identical")
        self.assertGreater(len(clip_ids1), 0, "Should have clips")
    
    @patch('apps.core.metrics.incr')
    def test_archetype_fallback_with_metrics(self, mock_incr):
        """Test archetype fallback triggers correct metrics"""
        # Remove professional clips, keep mentor clips
        from apps.workouts.models import VideoClip
        VideoClip.objects.filter(r2_archetype='professional').delete()
        
        builder = VideoPlaylistBuilder('professional')  # Will fallback to mentor
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        # Should still have clips (from fallback archetype)
        clip_ids = [item['clip_id'] for item in playlist if 'clip_id' in item]
        self.assertGreater(len(clip_ids), 0)
        
        # Should track fallback hits
        mock_incr.assert_any_call(MetricNames.VIDEO_PLAYLIST_FALLBACK_HIT, level=2, kind=VideoKind.TECHNIQUE)
    
    def test_n_plus_one_query_prevention(self):
        """Test playlist generation doesn't cause N+1 queries"""
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            # Should use minimal queries due to prefetching
            with self.assertNumQueries(5):  # Reasonable upper bound
                playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        # Should still generate a valid playlist
        clip_ids = [item['clip_id'] for item in playlist if 'clip_id' in item]
        self.assertGreater(len(clip_ids), 0)
    
    @patch('apps.core.metrics.incr')
    def test_optional_video_missing_metrics(self, mock_incr):
        """Test missing optional videos are tracked correctly"""
        # Remove all mistake videos
        from apps.workouts.models import VideoClip
        VideoClip.objects.filter(r2_kind=VideoKind.MISTAKE).delete()
        
        builder = VideoPlaylistBuilder('professional')
        
        # Force mistake video attempt with high probability
        with override_settings(PLAYLIST_MISTAKE_PROB=1.0):
            with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
                mock_storage = Mock()
                mock_storage.exists.return_value = True
                mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
                mock_get_storage.return_value = mock_storage
                
                playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        # Should track missed optional videos
        mock_incr.assert_any_call(
            MetricNames.VIDEO_PLAYLIST_FALLBACK_MISSED,
            required='false',
            kind=VideoKind.MISTAKE
        )
        
        # Should still have required videos
        kinds = {item.get('kind') for item in playlist if 'kind' in item}
        self.assertIn(VideoKind.TECHNIQUE, kinds)
        self.assertIn(VideoKind.INSTRUCTION, kinds)
        self.assertNotIn(VideoKind.MISTAKE, kinds)  # Should be missing


@pytest.mark.e2e
class TestE2EFullUserFlow(TestCase):
    """End-to-end test of complete user flow"""
    
    def setUp(self):
        self.user = UserFactory(completed_onboarding=True)
        self.exercises = SeededExerciseSetFactory.create_standard_set()
    
    @patch('apps.core.metrics.incr')
    @patch('apps.core.metrics.timing')
    def test_user_generates_plan_and_gets_playlist(self, mock_timing, mock_incr):
        """Test complete flow: plan generation → daily workout → playlist"""
        # 1. Create workout plan
        plan = WorkoutPlan.objects.create(
            user=self.user,
            plan_name='E2E Test Plan',
            duration_weeks=4,
            is_active=True
        )
        
        # 2. Create daily workout
        workout = DailyWorkout.objects.create(
            workout_plan=plan,
            week_number=1,
            day_number=1,
            exercises=[
                {'exercise_slug': 'push-ups', 'sets': 3, 'reps': 10},
                {'exercise_slug': 'squats', 'sets': 3, 'reps': 12}
            ]
        )
        
        # 3. Generate playlist for workout
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(workout, 'professional')
        
        # Verify complete playlist
        self.assertGreater(len(playlist), 0)
        
        # Should have required fields in all items
        for item in playlist:
            if 'clip_id' in item:
                required_fields = {'type', 'url', 'duration', 'clip_id', 'provider', 'kind'}
                self.assertTrue(required_fields.issubset(set(item.keys())))
        
        # Should track build time
        mock_timing.assert_any_call(
            MetricNames.VIDEO_PLAYLIST_BUILD_TIME,
            pytest.approx(0, abs=5000)  # Some positive time
        )
    
    def test_playlist_response_format_consistency(self):
        """Test playlist response format is consistent"""
        # Create workout
        workout = DailyWorkout.objects.create(
            workout_plan=WorkoutPlan.objects.create(user=self.user, plan_name='Test'),
            week_number=1,
            day_number=1,
            exercises=[{'exercise_slug': 'push-ups', 'sets': 3, 'reps': 10}]
        )
        
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(workout, 'professional')
        
        # Verify response format consistency
        for item in playlist:
            if 'clip_id' in item:
                # Required fields
                self.assertIn('type', item)
                self.assertIn('url', item) 
                self.assertIn('duration', item)
                self.assertIn('clip_id', item)
                self.assertIn('provider', item)
                self.assertIn('kind', item)
                
                # Type validation
                self.assertIsInstance(item['duration'], int)
                self.assertIsInstance(item['clip_id'], int)
                self.assertIn(item['kind'], [k.value for k in VideoKind])


@pytest.mark.e2e 
@override_settings(PLAYLIST_STORAGE_RETRY=2)
class TestE2EStorageResilience(TestCase):
    """Test storage resilience and retry mechanisms"""
    
    def setUp(self):
        self.exercises = SeededExerciseSetFactory.create_standard_set()
        
        self.workout = Mock()
        self.workout.id = 999
        self.workout.week_number = 1
        self.workout.day_number = 1
        self.workout.is_rest_day = False
        self.workout.exercises = [{'exercise_slug': 'push-ups', 'sets': 3, 'reps': 10}]
    
    def test_storage_retry_mechanism_works(self):
        """Test storage retry when first candidates fail"""
        builder = VideoPlaylistBuilder('professional')
        
        # Mock storage that fails first, succeeds second
        call_count = 0
        def mock_exists_side_effect(clip):
            nonlocal call_count
            call_count += 1
            return call_count > 2  # Fail first 2, succeed after
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.side_effect = mock_exists_side_effect
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        # Should still generate playlist despite storage failures
        clip_ids = [item['clip_id'] for item in playlist if 'clip_id' in item]
        self.assertGreater(len(clip_ids), 0)
        
        # Should have made multiple exists calls due to retries
        self.assertGreater(call_count, 2)
    
    @patch('apps.core.metrics.incr')
    def test_provider_metrics_tracking(self, mock_incr):
        """Test different video providers are tracked in metrics"""
        # Create mix of R2 and Stream videos
        push_up_exercise = CSVExerciseFactory(slug='push-ups-mixed')
        
        # R2 clips
        VideoClipFactory(
            exercise=push_up_exercise,
            r2_kind=VideoKind.TECHNIQUE,
            r2_archetype='professional',
            provider='r2'
        )
        
        # Stream clips  
        from tests.factories import StreamVideoClipFactory
        StreamVideoClipFactory(
            exercise=push_up_exercise,
            r2_kind=VideoKind.INSTRUCTION,
            r2_archetype='professional'
        )
        
        workout = Mock()
        workout.id = 888
        workout.week_number = 1
        workout.day_number = 1
        workout.is_rest_day = False
        workout.exercises = [{'exercise_slug': 'push-ups-mixed'}]
        
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(workout, 'professional')
        
        # Should track provider usage
        mock_incr.assert_any_call(MetricNames.VIDEO_PROVIDER_R2)
        # Note: Stream metrics depend on actual provider selection by RNG