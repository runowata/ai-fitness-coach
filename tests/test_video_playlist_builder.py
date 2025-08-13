"""Tests for VideoPlaylistBuilder service"""

import random
from unittest.mock import Mock, patch

import pytest

from apps.workouts.models import DailyWorkout, Exercise
from apps.workouts.services import VideoPlaylistBuilder


@pytest.fixture
def mock_exercise():
    """Create mock exercise"""
    exercise = Mock(spec=Exercise)
    exercise.id = "EX001"
    exercise.slug = "push-ups"
    exercise.name = "Push-ups"
    return exercise


@pytest.fixture
def mock_daily_workout():
    """Create mock daily workout"""
    workout = Mock(spec=DailyWorkout)
    workout.id = 1
    workout.week_number = 1
    workout.day_number = 1
    workout.is_rest_day = False
    workout.exercises = [
        {
            'exercise_slug': 'push-ups',
            'sets': 3,
            'reps': '10-12',
            'rest_seconds': 60
        },
        {
            'exercise_slug': 'squats',
            'sets': 3,
            'reps': '15',
            'rest_seconds': 90
        }
    ]
    return workout


@pytest.fixture
def mock_rest_workout():
    """Create mock rest day workout"""
    workout = Mock(spec=DailyWorkout)
    workout.id = 2
    workout.week_number = 1
    workout.day_number = 7
    workout.is_rest_day = True
    workout.exercises = []
    return workout


@pytest.fixture
def playlist_builder():
    """Create VideoPlaylistBuilder instance"""
    return VideoPlaylistBuilder(archetype="professional")


@pytest.fixture
def seeded_playlist_builder():
    """Create VideoPlaylistBuilder instance with fixed RNG seed for deterministic tests"""
    fixed_rng = random.Random(12345)  # Fixed seed for reproducibility
    return VideoPlaylistBuilder(archetype="professional", rng=fixed_rng)


class TestVideoPlaylistBuilder:
    """Test VideoPlaylistBuilder main functionality"""
    
    @patch('apps.workouts.services.VideoPlaylistBuilder._get_video_with_storage')
    def test_build_workout_playlist_regular_day(self, mock_get_video, playlist_builder, mock_daily_workout):
        """Test building playlist for regular workout day"""
        # Mock intro video
        mock_get_video.side_effect = [
            {'url': 'intro.mp4', 'duration': 30, 'clip_id': 1},  # intro
            {'url': 'technique.mp4', 'duration': 120, 'clip_id': 2},  # technique
            {'url': 'instruction.mp4', 'duration': 180, 'clip_id': 3},  # instruction
            None,  # mistake video (30% chance, mock as None)
            {'url': 'technique2.mp4', 'duration': 100, 'clip_id': 4},  # squats technique
            {'url': 'instruction2.mp4', 'duration': 160, 'clip_id': 5},  # squats instruction
            None,  # squats mistake video
        ]
        
        with patch.object(playlist_builder, '_build_exercise_playlist') as mock_exercise_playlist:
            mock_exercise_playlist.side_effect = [
                [{'type': 'technique', 'url': 'push_ups.mp4', 'exercise_slug': 'push-ups'}],
                [{'type': 'technique', 'url': 'squats.mp4', 'exercise_slug': 'squats'}]
            ]
            
            playlist = playlist_builder.build_workout_playlist(mock_daily_workout, "professional")
            
            # Should have intro + exercise videos
            assert len(playlist) >= 1  # At least intro video
            assert playlist[0]['type'] == 'intro'
            assert playlist[0]['url'] == 'intro.mp4'
    
    def test_build_workout_playlist_rest_day(self, playlist_builder, mock_rest_workout):
        """Test building playlist for rest day"""
        with patch.object(playlist_builder, '_get_rest_day_video') as mock_rest_video:
            mock_rest_video.return_value = {
                'type': 'rest_day',
                'url': 'rest.mp4',
                'duration': 300,
                'title': 'Rest Day Motivation'
            }
            
            playlist = playlist_builder.build_workout_playlist(mock_rest_workout, "professional")
            
            assert len(playlist) == 1
            assert playlist[0]['type'] == 'rest_day'
            assert playlist[0]['url'] == 'rest.mp4'
    
    @patch('apps.workouts.services.Exercise.objects.get')
    @patch('apps.workouts.services.random.random')
    def test_build_exercise_playlist_with_mistake_video(self, mock_random, mock_exercise_get, 
                                                       playlist_builder, mock_exercise):
        """Test building exercise playlist with mistake video"""
        mock_exercise_get.return_value = mock_exercise
        mock_random.return_value = 0.2  # Force mistake video inclusion (< 0.3)
        
        exercise_data = {'exercise_slug': 'push-ups', 'sets': 3, 'reps': '10'}
        
        with patch.object(playlist_builder, '_get_video_with_storage') as mock_get_video:
            mock_get_video.side_effect = [
                {'url': 'technique.mp4', 'duration': 120, 'clip_id': 1},
                {'url': 'instruction.mp4', 'duration': 180, 'clip_id': 2},
                {'url': 'mistake.mp4', 'duration': 90, 'clip_id': 3}
            ]
            
            playlist = playlist_builder._build_exercise_playlist('push-ups', 'professional', exercise_data)
            
            assert len(playlist) == 3
            assert any(video['type'] == 'technique' for video in playlist)
            assert any(video['type'] == 'instruction' for video in playlist)
            assert any(video['type'] == 'mistake' for video in playlist)
    
    @patch('apps.workouts.services.Exercise.objects.get')
    @patch('apps.workouts.services.random.random')
    def test_build_exercise_playlist_without_mistake_video(self, mock_random, mock_exercise_get,
                                                          playlist_builder, mock_exercise):
        """Test building exercise playlist without mistake video"""
        mock_exercise_get.return_value = mock_exercise
        mock_random.return_value = 0.8  # Don't include mistake video (> 0.3)
        
        exercise_data = {'exercise_slug': 'push-ups', 'sets': 3, 'reps': '10'}
        
        with patch.object(playlist_builder, '_get_video_with_storage') as mock_get_video:
            mock_get_video.side_effect = [
                {'url': 'technique.mp4', 'duration': 120, 'clip_id': 1},
                {'url': 'instruction.mp4', 'duration': 180, 'clip_id': 2}
            ]
            
            playlist = playlist_builder._build_exercise_playlist('push-ups', 'professional', exercise_data)
            
            assert len(playlist) == 2
            assert any(video['type'] == 'technique' for video in playlist)
            assert any(video['type'] == 'instruction' for video in playlist)
            assert not any(video['type'] == 'mistake' for video in playlist)
    
    @patch('apps.workouts.services.Exercise.objects.get')
    def test_build_exercise_playlist_exercise_not_found(self, mock_exercise_get, playlist_builder):
        """Test building playlist when exercise is not found"""
        from django.core.exceptions import ObjectDoesNotExist
        mock_exercise_get.side_effect = ObjectDoesNotExist()
        
        playlist = playlist_builder._build_exercise_playlist('nonexistent', 'professional', {})
        
        assert playlist == []
    
    @patch('apps.workouts.services.Exercise.objects.get')
    def test_exercise_slug_formats(self, mock_exercise_get, playlist_builder, mock_exercise):
        """Test handling different exercise slug formats"""
        mock_exercise_get.return_value = mock_exercise
        
        # Test lowercase exercise code
        with patch.object(playlist_builder, '_get_video_with_storage', return_value=None):
            playlist_builder._build_exercise_playlist('ex001', 'professional', {})
            # Should search by primary key with uppercase
            mock_exercise_get.assert_called_with(pk='EX001')
        
        mock_exercise_get.reset_mock()
        
        # Test regular slug
        with patch.object(playlist_builder, '_get_video_with_storage', return_value=None):
            playlist_builder._build_exercise_playlist('push-ups', 'professional', {})
            # Should search by slug
            mock_exercise_get.assert_called_with(slug='push-ups')


class TestVideoWithStorage:
    """Test _get_video_with_storage method"""
    
    @patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video')
    @patch('apps.workouts.services.get_storage')
    def test_get_video_with_storage_success(self, mock_get_storage, mock_get_clips, playlist_builder):
        """Test successful video retrieval with storage"""
        # Mock video clip
        mock_clip = Mock()
        mock_clip.id = 1
        mock_clip.duration_seconds = 120
        
        # Mock queryset
        mock_queryset = Mock()
        mock_queryset.order_by.return_value.first.return_value = mock_clip
        mock_get_clips.return_value = mock_queryset
        
        # Mock storage adapter
        mock_storage = Mock()
        mock_storage.exists.return_value = True
        mock_storage.playback_url.return_value = "https://example.com/video.mp4"
        mock_get_storage.return_value = mock_storage
        
        result = playlist_builder._get_video_with_storage(r2_kind='technique', archetype='professional')
        
        assert result is not None
        assert result['url'] == "https://example.com/video.mp4"
        assert result['duration'] == 120
        assert result['clip_id'] == 1
    
    @patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video')
    def test_get_video_with_storage_no_clip(self, mock_get_clips, playlist_builder):
        """Test video retrieval when no clip found"""
        mock_queryset = Mock()
        mock_queryset.order_by.return_value.first.return_value = None
        mock_get_clips.return_value = mock_queryset
        
        result = playlist_builder._get_video_with_storage(r2_kind='technique')
        
        assert result is None
    
    @patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video')
    @patch('apps.workouts.services.get_storage')
    def test_get_video_with_storage_not_exists(self, mock_get_storage, mock_get_clips, playlist_builder):
        """Test video retrieval when storage says doesn't exist"""
        mock_clip = Mock()
        mock_clip.id = 1
        
        mock_queryset = Mock()
        mock_queryset.order_by.return_value.first.return_value = mock_clip
        mock_get_clips.return_value = mock_queryset
        
        # Mock storage adapter that says video doesn't exist
        mock_storage = Mock()
        mock_storage.exists.return_value = False
        mock_get_storage.return_value = mock_storage
        
        result = playlist_builder._get_video_with_storage(r2_kind='technique')
        
        assert result is None
    
    @patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video')
    def test_get_video_with_storage_query_filters(self, mock_get_clips, playlist_builder):
        """Test that query filters are applied correctly"""
        mock_exercise = Mock()
        
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.order_by.return_value.first.return_value = None
        mock_get_clips.return_value = mock_queryset
        
        playlist_builder._get_video_with_storage(
            exercise=mock_exercise,
            r2_kind='technique',
            archetype='professional',
            exclude_id=5
        )
        
        # Verify all filters were called
        assert mock_queryset.filter.call_count >= 3  # exercise, r2_kind, archetype
        mock_queryset.exclude.assert_called_once_with(id=5)


class TestSpecialVideos:
    """Test special video methods"""
    
    def test_get_rest_day_video(self, playlist_builder):
        """Test getting rest day video"""
        with patch.object(playlist_builder, '_get_video_with_storage') as mock_get_video:
            mock_get_video.return_value = {'url': 'weekly.mp4', 'duration': 300, 'clip_id': 1}
            
            result = playlist_builder._get_rest_day_video(1, 'professional')
            
            assert result is not None
            assert result['type'] == 'rest_day'
            assert result['url'] == 'weekly.mp4'
            assert result['title'] == 'День отдыха - Восстановление и мотивация'
    
    def test_get_weekly_motivation_video(self, playlist_builder):
        """Test getting weekly motivation video"""
        with patch.object(playlist_builder, '_get_video_with_storage') as mock_get_video:
            mock_get_video.return_value = {'url': 'closing.mp4', 'duration': 180, 'clip_id': 1}
            
            result = playlist_builder._get_weekly_motivation_video(2, 'mentor')
            
            assert result is not None
            assert result['type'] == 'weekly_motivation'
            assert result['url'] == 'closing.mp4'
            assert result['title'] == 'Поздравляем с завершением недели 2!'
    
    def test_get_rest_day_video_none(self, playlist_builder):
        """Test getting rest day video when none available"""
        with patch.object(playlist_builder, '_get_video_with_storage') as mock_get_video:
            mock_get_video.return_value = None
            
            result = playlist_builder._get_rest_day_video(1, 'professional')
            
            assert result is None


@pytest.mark.django_db
class TestVideoPlaylistBuilderIntegration:
    """Integration tests that might need database"""
    
    def test_archetype_initialization(self):
        """Test builder initialization with different archetypes"""
        builder_pro = VideoPlaylistBuilder(archetype="professional")
        assert builder_pro.archetype == "professional"
        
        builder_mentor = VideoPlaylistBuilder(archetype="mentor", locale="en")
        assert builder_mentor.archetype == "mentor"
        assert builder_mentor.locale == "en"
    
    def test_substitution_options_method_exists(self, playlist_builder):
        """Test that substitution options method exists and callable"""
        # This method exists in the original code
        assert hasattr(playlist_builder, 'get_substitution_options')
        assert callable(playlist_builder.get_substitution_options)


class TestDeterministicRNG:
    """Test deterministic RNG functionality for reproducible playlists"""
    
    def test_rng_seeding_with_workout_data(self, seeded_playlist_builder, mock_daily_workout):
        """Test that RNG is seeded deterministically based on workout data"""
        # Mock workout with consistent properties
        workout1 = Mock(spec=DailyWorkout)
        workout1.id = 100
        workout1.week_number = 2
        workout1.day_number = 3
        
        workout2 = Mock(spec=DailyWorkout)
        workout2.id = 100  # Same workout
        workout2.week_number = 2
        workout2.day_number = 3
        
        # Seed RNG for both workouts - should produce same seed
        seeded_playlist_builder._seed_rng_for_workout(workout1, "professional")
        first_random = seeded_playlist_builder.rng.random()
        
        # Reset builder with same seed
        seeded_playlist_builder._seed_rng_for_workout(workout2, "professional")
        second_random = seeded_playlist_builder.rng.random()
        
        # Should be identical due to deterministic seeding
        assert first_random == second_random
    
    def test_different_workouts_different_seeds(self, seeded_playlist_builder):
        """Test that different workouts produce different random sequences"""
        workout1 = Mock(spec=DailyWorkout)
        workout1.id = 100
        workout1.week_number = 1
        workout1.day_number = 1
        
        workout2 = Mock(spec=DailyWorkout)
        workout2.id = 200  # Different workout
        workout2.week_number = 1
        workout2.day_number = 1
        
        # Seed and get random values
        seeded_playlist_builder._seed_rng_for_workout(workout1, "professional")
        first_random = seeded_playlist_builder.rng.random()
        
        seeded_playlist_builder._seed_rng_for_workout(workout2, "professional")
        second_random = seeded_playlist_builder.rng.random()
        
        # Should be different
        assert first_random != second_random
    
    @patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video')
    @patch('apps.workouts.services.get_storage')
    def test_deterministic_video_selection(self, mock_get_storage, mock_get_clips, seeded_playlist_builder):
        """Test that video selection is deterministic with fixed seed"""
        # Create multiple mock clips
        mock_clips = []
        for i in range(5):
            clip = Mock()
            clip.id = i + 1
            clip.duration_seconds = 60 + i * 10
            mock_clips.append(clip)
        
        mock_queryset = Mock()
        mock_queryset.order_by.return_value.__getitem__ = lambda self, key: mock_clips[:20]
        mock_get_clips.return_value = mock_queryset
        
        mock_storage = Mock()
        mock_storage.exists.return_value = True
        mock_storage.playback_url.return_value = "https://example.com/video.mp4"
        mock_get_storage.return_value = mock_storage
        
        # Get video twice with same parameters
        result1 = seeded_playlist_builder._get_video_with_storage(r2_kind='technique', archetype='professional')
        result2 = seeded_playlist_builder._get_video_with_storage(r2_kind='technique', archetype='professional')
        
        # Should select same clip due to fixed seed
        assert result1['clip_id'] == result2['clip_id']
    
    def test_mistake_video_probability_with_fixed_seed(self, seeded_playlist_builder):
        """Test that mistake video probability is deterministic with fixed seed"""
        # Set fixed seed to ensure deterministic behavior
        seeded_playlist_builder.rng.seed(99999)
        
        # Call random multiple times and check consistency
        randoms = [seeded_playlist_builder.rng.random() for _ in range(10)]
        
        # Reset seed and get same sequence
        seeded_playlist_builder.rng.seed(99999)
        randoms2 = [seeded_playlist_builder.rng.random() for _ in range(10)]
        
        assert randoms == randoms2


class TestFallbackScenarios:
    """Test fallback scenarios and error handling"""
    
    @patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video')
    @patch('apps.workouts.services.get_storage')
    def test_video_fallback_when_first_choice_unavailable(self, mock_get_storage, mock_get_clips, seeded_playlist_builder):
        """Test fallback to second video when first choice doesn't exist in storage"""
        # Create mock clips
        clip1 = Mock()
        clip1.id = 1
        clip1.duration_seconds = 60
        
        clip2 = Mock()
        clip2.id = 2
        clip2.duration_seconds = 90
        
        mock_queryset = Mock()
        mock_queryset.order_by.return_value.__getitem__ = lambda self, key: [clip1, clip2]
        mock_get_clips.return_value = mock_queryset
        
        # First storage call returns False (doesn't exist), second returns True
        mock_storage = Mock()
        mock_storage.exists.side_effect = [False, True]  # First clip missing, second available
        mock_storage.playback_url.return_value = "https://example.com/fallback.mp4"
        mock_get_storage.return_value = mock_storage
        
        result = seeded_playlist_builder._get_video_with_storage(r2_kind='technique')
        
        # Should fallback to second clip
        assert result is not None
        assert result['clip_id'] == 2
        assert result['duration'] == 90
    
    @patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video')
    @patch('apps.workouts.services.get_storage')
    def test_no_fallback_when_all_unavailable(self, mock_get_storage, mock_get_clips, playlist_builder):
        """Test that None is returned when no videos are available"""
        clip1 = Mock()
        clip1.id = 1
        
        mock_queryset = Mock()
        mock_queryset.order_by.return_value.__getitem__ = lambda self, key: [clip1]
        mock_get_clips.return_value = mock_queryset
        
        # Storage says video doesn't exist
        mock_storage = Mock()
        mock_storage.exists.return_value = False
        mock_get_storage.return_value = mock_storage
        
        result = playlist_builder._get_video_with_storage(r2_kind='technique')
        
        assert result is None
    
    @patch('apps.workouts.services.get_storage')
    def test_storage_adapter_error_handling(self, mock_get_storage, playlist_builder):
        """Test handling when storage adapter raises exception"""
        mock_clip = Mock()
        mock_clip.id = 1
        mock_clip.duration_seconds = 60
        
        # Mock storage adapter that raises exception
        mock_storage = Mock()
        mock_storage.exists.side_effect = Exception("Storage connection failed")
        mock_get_storage.return_value = mock_storage
        
        with patch('apps.workouts.services.ExerciseValidationService.get_clips_with_video') as mock_get_clips:
            mock_queryset = Mock()
            mock_queryset.order_by.return_value.__getitem__ = lambda self, key: [mock_clip]
            mock_get_clips.return_value = mock_queryset
            
            # Should handle exception gracefully
            result = playlist_builder._get_video_with_storage(r2_kind='technique')
            assert result is None
    
    def test_empty_playlist_on_no_exercises(self, playlist_builder):
        """Test that empty playlist is returned for workout with no exercises"""
        empty_workout = Mock(spec=DailyWorkout)
        empty_workout.id = 1
        empty_workout.week_number = 1
        empty_workout.day_number = 1
        empty_workout.is_rest_day = False
        empty_workout.exercises = []  # No exercises
        
        with patch.object(playlist_builder, '_get_video_with_storage') as mock_get_video:
            mock_get_video.return_value = {'url': 'intro.mp4', 'duration': 30, 'clip_id': 1}
            
            playlist = playlist_builder.build_workout_playlist(empty_workout, "professional")
            
            # Should only contain intro video
            assert len(playlist) == 1
            assert playlist[0]['type'] == 'intro'
    
    @patch('apps.workouts.services.Exercise.objects.get')
    def test_invalid_exercise_slug_handling(self, mock_exercise_get, playlist_builder):
        """Test handling of invalid exercise slugs"""
        from apps.workouts.models import Exercise
        mock_exercise_get.side_effect = Exercise.DoesNotExist()
        
        exercise_data = {'exercise_slug': 'invalid-exercise', 'sets': 3, 'reps': '10'}
        
        # Should return empty playlist for invalid exercise
        playlist = playlist_builder._build_exercise_playlist('invalid-exercise', 'professional', exercise_data)
        assert playlist == []
    
    def test_rng_initialization_fallback(self):
        """Test that VideoPlaylistBuilder initializes with default RNG when none provided"""
        builder_no_rng = VideoPlaylistBuilder(archetype="professional")
        builder_with_rng = VideoPlaylistBuilder(archetype="professional", rng=random.Random(123))
        
        # Both should have rng attribute
        assert hasattr(builder_no_rng, 'rng')
        assert hasattr(builder_with_rng, 'rng')
        
        # Should be different instances
        assert builder_no_rng.rng is not builder_with_rng.rng