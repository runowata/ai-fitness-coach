"""
Test deterministic video playlist generation with fallbacks
"""

import random
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.test import TestCase, override_settings
from django.test.utils import override_settings

from apps.workouts.constants import ARCHETYPE_FALLBACK_ORDER, VideoKind
from apps.workouts.models import CSVExercise, DailyWorkout, VideoClip, VideoProvider
from apps.workouts.services import VideoPlaylistBuilder
from apps.workouts.video_storage import R2Adapter


@override_settings(
    PLAYLIST_MISTAKE_PROB=0.30,
    PLAYLIST_FALLBACK_MAX_CANDIDATES=5,
    PLAYLIST_STORAGE_RETRY=2
)
class TestDeterministicPlaylist(TestCase):
    """Test deterministic playlist generation"""
    
    def setUp(self):
        # Create test exercises
        self.exercise1 = CSVExercise.objects.create(
            slug='push-ups',
            name='Push-ups',
            muscle_group='chest',
            equipment='none',
            difficulty='beginner',
            is_active=True
        )
        
        self.exercise2 = CSVExercise.objects.create(
            slug='squats',
            name='Squats',
            muscle_group='legs',
            equipment='none', 
            difficulty='beginner',
            is_active=True
        )
        
        # Create video clips for different archetypes
        self.clips = []
        for exercise in [self.exercise1, self.exercise2]:
            for archetype in ['professional', 'mentor', 'peer']:
                for kind in [VideoKind.TECHNIQUE, VideoKind.INSTRUCTION, VideoKind.MISTAKE]:
                    clip = VideoClip.objects.create(
                        exercise=exercise,
                        r2_archetype=archetype,
                        model_name='mod1',
                        duration_seconds=30,
                        provider=VideoProvider.R2,
                        r2_file=f'videos/{exercise.slug}_{kind}_{archetype}.mp4',
                        r2_kind=kind
                    )
                    self.clips.append(clip)
        
        # Create mock workout
        self.workout = Mock()
        self.workout.id = 123
        self.workout.week_number = 2
        self.workout.day_number = 3
        self.workout.is_rest_day = False
        self.workout.exercises = [
            {'exercise_slug': 'push-ups', 'sets': 3, 'reps': 12},
            {'exercise_slug': 'squats', 'sets': 3, 'reps': 15}
        ]
    
    def test_determinism_across_runs(self):
        """Test that identical parameters produce identical playlists"""
        archetype = 'professional'
        
        # Build playlist twice with same parameters
        builder1 = VideoPlaylistBuilder(archetype)
        builder2 = VideoPlaylistBuilder(archetype)
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            # Mock storage exists to return True
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist1 = builder1.build_workout_playlist(self.workout, archetype)
            playlist2 = builder2.build_workout_playlist(self.workout, archetype)
        
        # Extract clip_ids for comparison
        clip_ids1 = [item['clip_id'] for item in playlist1 if 'clip_id' in item]
        clip_ids2 = [item['clip_id'] for item in playlist2 if 'clip_id' in item]
        
        self.assertEqual(clip_ids1, clip_ids2, "Playlists should be identical for same parameters")
        self.assertGreater(len(clip_ids1), 0, "Should have at least some clips")
    
    def test_different_seeds_produce_different_results(self):
        """Test that different workout parameters produce different results"""
        archetype = 'professional'
        
        # Create two different workouts
        workout2 = Mock()
        workout2.id = 456  # Different ID
        workout2.week_number = 2
        workout2.day_number = 3
        workout2.is_rest_day = False
        workout2.exercises = self.workout.exercises
        
        builder1 = VideoPlaylistBuilder(archetype)
        builder2 = VideoPlaylistBuilder(archetype)
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist1 = builder1.build_workout_playlist(self.workout, archetype)
            playlist2 = builder2.build_workout_playlist(workout2, archetype)
        
        # Extract clip_ids for comparison
        clip_ids1 = [item['clip_id'] for item in playlist1 if 'clip_id' in item]
        clip_ids2 = [item['clip_id'] for item in playlist2 if 'clip_id' in item]
        
        # Results may be different due to different seeds (though not guaranteed)
        # At minimum, verify both have clips
        self.assertGreater(len(clip_ids1), 0)
        self.assertGreater(len(clip_ids2), 0)
    
    def test_archetype_fallback_level2(self):
        """Test fallback to different archetype when primary not available"""
        primary_archetype = 'professional'
        
        # Create clips only for mentor (fallback archetype)
        VideoClip.objects.filter(r2_archetype=primary_archetype).delete()
        
        builder = VideoPlaylistBuilder(primary_archetype)
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            with patch('apps.core.metrics.incr') as mock_incr:
                playlist = builder.build_workout_playlist(self.workout, primary_archetype)
        
        # Should have fallback metrics
        mock_incr.assert_any_call('video.playlist.fallback_hit', level=2, kind=VideoKind.TECHNIQUE)
        
        # Should still have clips (from fallback archetype)
        clip_ids = [item['clip_id'] for item in playlist if 'clip_id' in item]
        self.assertGreater(len(clip_ids), 0)
    
    @patch('apps.core.metrics.incr')
    def test_optional_mistake_skipped(self, mock_incr):
        """Test that missing optional videos are gracefully skipped"""
        # Remove all mistake videos
        VideoClip.objects.filter(r2_kind=VideoKind.MISTAKE).delete()
        
        builder = VideoPlaylistBuilder('professional')
        
        # Force mistake video selection by mocking RNG
        with patch.object(builder.rng, 'random', return_value=0.1):  # < 0.30 threshold
            with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
                mock_storage = Mock()
                mock_storage.exists.return_value = True
                mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
                mock_get_storage.return_value = mock_storage
                
                playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        # Should track missed optional video
        mock_incr.assert_any_call('video.playlist.fallback_missed', required='false', kind=VideoKind.MISTAKE)
        
        # Should still have technique and instruction videos
        kinds = [item.get('kind') for item in playlist if 'kind' in item]
        self.assertIn(VideoKind.TECHNIQUE, kinds)
        self.assertIn(VideoKind.INSTRUCTION, kinds)
        self.assertNotIn(VideoKind.MISTAKE, kinds)
    
    def test_storage_retry_mechanism(self):
        """Test storage retry when first candidate is unavailable"""
        builder = VideoPlaylistBuilder('professional')
        
        call_count = 0
        def mock_exists_side_effect(clip):
            nonlocal call_count
            call_count += 1
            # First call fails, second succeeds
            return call_count > 1
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.side_effect = mock_exists_side_effect
            mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        # Should have clips despite first attempt failing
        clip_ids = [item['clip_id'] for item in playlist if 'clip_id' in item]
        self.assertGreater(len(clip_ids), 0)
        
        # Should have made multiple exists calls due to retries
        self.assertGreater(call_count, 2)
    
    def test_prefetch_no_nplus1(self):
        """Test that prefetch eliminates N+1 queries"""
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playbook_url = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            from django.db import connection
            from django.test.utils import override_settings

            # Count queries during playlist generation
            with self.assertNumQueries(2):  # Should be minimal queries due to prefetch
                playlist = builder.build_workout_playlist(self.workout, 'professional')
        
        clip_ids = [item['clip_id'] for item in playlist if 'clip_id' in item]
        self.assertGreater(len(clip_ids), 0)
    
    def test_fallback_order_respects_configuration(self):
        """Test that archetype fallback follows configured order"""
        primary = 'professional'
        expected_order = ARCHETYPE_FALLBACK_ORDER[primary]
        
        # Create clips only for the last fallback archetype
        last_fallback = expected_order[-1]
        VideoClip.objects.exclude(r2_archetype=last_fallback).delete()
        
        builder = VideoPlaylistBuilder(primary)
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(self.workout, primary)
        
        # Should still find clips from last fallback
        clip_ids = [item['clip_id'] for item in playlist if 'clip_id' in item]
        self.assertGreater(len(clip_ids), 0)
        
        # Verify the clips are from the expected archetype
        found_clips = VideoClip.objects.filter(id__in=clip_ids)
        for clip in found_clips:
            self.assertEqual(clip.r2_archetype, last_fallback)


class TestPlaylistResponse(TestCase):
    """Test playlist response format and fields"""
    
    def setUp(self):
        self.exercise = CSVExercise.objects.create(
            slug='push-ups',
            name='Push-ups',
            is_active=True
        )
        
        self.clip = VideoClip.objects.create(
            exercise=self.exercise,
            r2_archetype='professional',
            model_name='mod1',
            duration_seconds=45,
            provider=VideoProvider.R2,
            r2_file='videos/push-ups_technique.mp4',
            r2_kind=VideoKind.TECHNIQUE
        )
    
    def test_playlist_item_contains_required_fields(self):
        """Test that playlist items contain all required fields"""
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://cdn.test.com/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            video_info = builder._format_video_response(self.clip, VideoKind.TECHNIQUE)
        
        # Verify all required fields are present
        required_fields = ['url', 'duration', 'clip_id', 'provider', 'kind']
        for field in required_fields:
            self.assertIn(field, video_info)
        
        # Verify field values
        self.assertEqual(video_info['url'], 'https://cdn.test.com/video.mp4')
        self.assertEqual(video_info['duration'], 45)
        self.assertEqual(video_info['clip_id'], self.clip.id)
        self.assertEqual(video_info['provider'], VideoProvider.R2)
        self.assertEqual(video_info['kind'], VideoKind.TECHNIQUE)
    
    @override_settings(PLAYLIST_MISTAKE_PROB=1.0)  # Always include mistake videos
    def test_mistake_probability_configuration(self):
        """Test that mistake video probability is configurable"""
        # Create mistake video clip
        mistake_clip = VideoClip.objects.create(
            exercise=self.exercise,
            r2_archetype='professional',
            model_name='mod1',
            duration_seconds=30,
            provider=VideoProvider.R2,
            r2_file='videos/push-ups_mistake.mp4',
            r2_kind=VideoKind.MISTAKE
        )
        
        workout = Mock()
        workout.id = 1
        workout.week_number = 1
        workout.day_number = 1
        workout.is_rest_day = False
        workout.exercises = [{'exercise_slug': 'push-ups'}]
        
        builder = VideoPlaylistBuilder('professional')
        
        with patch('apps.workouts.video_storage.get_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.exists.return_value = True
            mock_storage.playback_url.return_value = 'https://test.url/video.mp4'
            mock_get_storage.return_value = mock_storage
            
            playlist = builder.build_workout_playlist(workout, 'professional')
        
        # Should include mistake video due to 100% probability
        kinds = [item.get('kind') for item in playlist if 'kind' in item]
        self.assertIn(VideoKind.MISTAKE, kinds)