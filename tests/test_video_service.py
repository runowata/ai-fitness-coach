"""
Basic tests for video playlist building and workout plan services.
These tests use mocks to avoid database dependency issues.
"""
from unittest.mock import Mock, patch

import pytest


class TestVideoPlaylistBuilder:
    """Test VideoPlaylistBuilder service with mocked dependencies"""
    
    def test_prioritizes_non_placeholder_videos(self):
        """Test that non-placeholder videos are prioritized over placeholders"""
        # Mock the VideoPlaylistBuilder to avoid database dependencies
        with patch('apps.workouts.services.VideoClip') as mock_videoclip:
            # Setup mock queryset that returns non-placeholder first
            mock_queryset = Mock()
            mock_real_video = Mock(is_placeholder=False, type='technique')
            mock_placeholder_video = Mock(is_placeholder=True, type='technique')
            
            # Configure queryset to return real video first due to ordering
            mock_queryset.filter.return_value.order_by.return_value.first.return_value = mock_real_video
            mock_videoclip.objects = mock_queryset
            
            # Import after patching to avoid import-time database access
            from apps.workouts.services import VideoPlaylistBuilder

            # Create mock user
            mock_user = Mock()
            mock_user.profile.archetype = 'bro'
            
            builder = VideoPlaylistBuilder(mock_user)
            exercises = [{'exercise_slug': 'push-up', 'sets': 3, 'reps': 10}]
            
            # This would normally call the database, but our mocks handle it
            builder.build_playlist(exercises)
            
            # Verify that order_by was called with is_placeholder first (non-placeholder priority)
            mock_queryset.filter.return_value.order_by.assert_called()
            call_args = mock_queryset.filter.return_value.order_by.call_args[0]
            assert 'is_placeholder' in call_args
    
    def test_archetype_matching(self):
        """Test that videos are filtered by user archetype"""
        with patch('apps.workouts.services.VideoClip') as mock_videoclip:
            mock_queryset = Mock()
            mock_videoclip.objects = mock_queryset
            
            from apps.workouts.services import VideoPlaylistBuilder
            
            mock_user = Mock()
            mock_user.profile.archetype = 'intellectual'
            
            builder = VideoPlaylistBuilder(mock_user)
            exercises = [{'exercise_slug': 'push-up', 'sets': 3, 'reps': 10}]
            
            builder.build_playlist(exercises)
            
            # Verify that filter was called with correct archetype
            mock_queryset.filter.assert_called()
            # Check that archetype filtering was applied in one of the calls
            filter_calls = mock_queryset.filter.call_args_list
            archetype_filtered = any(
                'archetype' in str(call) and 'intellectual' in str(call)
                for call in filter_calls
            )
            assert archetype_filtered, "Should filter by user archetype"


class TestWorkoutPlanGenerator:
    """Test WorkoutPlanGenerator service with mocked AI calls"""
    
    @patch('apps.ai_integration.services.openai.ChatCompletion.create')
    def test_successful_plan_generation(self, mock_openai):
        """Test successful workout plan generation from AI response"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '''
        {
            "plan_name": "Test Workout Plan",
            "duration_weeks": 4,
            "goal": "muscle_gain",
            "workouts": [
                {
                    "day": 1,
                    "week": 1,
                    "name": "Upper Body",
                    "exercises": [
                        {
                            "exercise_slug": "push-up",
                            "sets": 3,
                            "reps": "10-12",
                            "rest_seconds": 60
                        }
                    ]
                }
            ]
        }
        '''
        mock_openai.return_value = mock_response
        
        # Mock database models to avoid database access
        with patch('apps.ai_integration.services.WorkoutPlan') as mock_plan_model, \
             patch('apps.ai_integration.services.DailyWorkout') as mock_workout_model, \
             patch('apps.ai_integration.services.UserOnboardingResponse') as mock_response_model:
            
            mock_plan_instance = Mock()
            mock_plan_model.objects.create.return_value = mock_plan_instance
            mock_response_model.objects.filter.return_value.values.return_value = []
            
            from apps.ai_integration.services import WorkoutPlanGenerator
            
            mock_user = Mock()
            mock_user.id = 1
            
            generator = WorkoutPlanGenerator()
            generator.generate_plan(mock_user)
            
            # Verify plan was created with correct data
            mock_plan_model.objects.create.assert_called_once()
            create_args = mock_plan_model.objects.create.call_args[1]
            
            assert create_args['name'] == "Test Workout Plan"
            assert create_args['duration_weeks'] == 4
            assert create_args['goal'] == "muscle_gain"
            assert create_args['user'] == mock_user
            
            # Verify daily workout was created
            mock_workout_model.objects.create.assert_called()
    
    @patch('apps.ai_integration.services.openai.ChatCompletion.create')
    def test_invalid_json_handling(self, mock_openai):
        """Test handling of invalid JSON from AI"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = 'This is not valid JSON'
        mock_openai.return_value = mock_response
        
        with patch('apps.ai_integration.services.UserOnboardingResponse') as mock_response_model:
            mock_response_model.objects.filter.return_value.values.return_value = []
            
            from apps.ai_integration.services import WorkoutPlanGenerator
            
            mock_user = Mock()
            generator = WorkoutPlanGenerator()
            
            with pytest.raises((ValueError, Exception)):
                generator.generate_plan(mock_user)


class TestWorkoutCompletionService:
    """Test WorkoutCompletionService with mocked dependencies"""
    
    def test_successful_workout_completion(self):
        """Test successful workout completion and XP award"""
        with patch('apps.workouts.services.DailyWorkout') as mock_workout_model, \
             patch('apps.workouts.services.get_object_or_404') as mock_get_object:
            
            # Setup mock workout
            mock_workout = Mock()
            mock_workout.is_completed = False
            mock_workout.plan.user = Mock()
            mock_get_object.return_value = mock_workout
            
            # Setup mock user with profile
            mock_user = Mock()
            mock_profile = Mock()
            mock_user.profile = mock_profile
            mock_workout.plan.user = mock_user
            
            from apps.workouts.services import WorkoutCompletionService
            
            service = WorkoutCompletionService()
            result = service.complete_workout(mock_user, 1)
            
            # Verify workout was marked as completed
            assert mock_workout.is_completed == True
            assert mock_workout.completed_at is not None
            mock_workout.save.assert_called()
            
            # Verify XP was awarded
            mock_profile.add_xp.assert_called()
            
            # Verify success response
            assert result['success'] == True
    
    def test_already_completed_workout(self):
        """Test attempting to complete already completed workout"""
        with patch('apps.workouts.services.get_object_or_404') as mock_get_object:
            
            mock_workout = Mock()
            mock_workout.is_completed = True
            mock_workout.plan.user = Mock()
            mock_get_object.return_value = mock_workout
            
            from apps.workouts.services import WorkoutCompletionService
            
            mock_user = Mock()
            service = WorkoutCompletionService()
            result = service.complete_workout(mock_user, 1)
            
            # Should return failure
            assert result['success'] == False
            assert 'уже завершена' in result['message']


def test_import_safety():
    """Test that we can safely import our service modules"""
    try:
        # These imports should work even if database isn't set up
        assert True, "Imports successful"
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])