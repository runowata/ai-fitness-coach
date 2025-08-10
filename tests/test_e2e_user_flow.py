"""End-to-end tests for complete user flow"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from apps.onboarding.views import generate_plan_ajax
from apps.workouts.models import WorkoutPlan, DailyWorkout
from apps.users.models import UserProfile
from apps.ai_integration.schemas import WorkoutPlan as WorkoutPlanSchema

User = get_user_model()


@pytest.fixture
def user():
    """Create test user"""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    return user


@pytest.fixture
def user_profile():
    """Create test user profile"""
    profile = Mock(spec=UserProfile)
    profile.archetype = "professional"
    profile.onboarding_completed_at = None
    return profile


@pytest.fixture
def request_factory():
    """Django request factory"""
    return RequestFactory()


@pytest.fixture
def mock_workout_plan():
    """Create mock workout plan"""
    plan = Mock(spec=WorkoutPlan)
    plan.id = 1
    plan.name = "6-Week Strength Program"
    plan.duration_weeks = 6
    plan.is_active = True
    plan.is_confirmed = False
    return plan


@pytest.fixture
def valid_ai_plan_data():
    """Valid AI plan data matching Pydantic schema"""
    return {
        "plan_name": "6-Week Progressive Strength Training",
        "duration_weeks": 6,
        "goal": "Build strength and muscle mass through progressive overload",
        "weeks": [
            {
                "week_number": week_num,
                "week_focus": f"Week {week_num} Focus",
                "days": [
                    {
                        "day_number": day_num,
                        "workout_name": f"Week {week_num} Day {day_num}" if day_num != 7 else "Rest Day",
                        "is_rest_day": day_num == 7,
                        "exercises": [] if day_num == 7 else [
                            {
                                "exercise_slug": "push-ups",
                                "sets": 3,
                                "reps": "10-12",
                                "rest_seconds": 60
                            },
                            {
                                "exercise_slug": "squats",
                                "sets": 3,
                                "reps": "15",
                                "rest_seconds": 90
                            }
                        ],
                        "confidence_task": "Complete your workout with confidence"
                    }
                    for day_num in range(1, 8)
                ]
            }
            for week_num in range(1, 7)
        ]
    }


class TestCompleteUserFlow:
    """Test complete user flow from onboarding to workout"""
    
    @patch('apps.onboarding.views.create_workout_plan_from_onboarding')
    @patch('apps.workouts.models.WorkoutPlan.objects.filter')
    def test_generate_plan_ajax_success(self, mock_filter, mock_create_plan,
                                       request_factory, user, mock_workout_plan):
        """Test successful plan generation via AJAX"""
        # Mock no existing plan
        mock_filter.return_value.first.return_value = None
        
        # Mock plan creation
        mock_create_plan.return_value = mock_workout_plan
        
        # Create request
        request = request_factory.post('/onboarding/generate-plan-ajax/')
        request.user = user
        
        response = generate_plan_ajax(request)
        
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['status'] == 'success'
        assert 'plan_id' in response_data
    
    @patch('apps.workouts.models.WorkoutPlan.objects.filter')
    def test_generate_plan_ajax_existing_plan(self, mock_filter, request_factory, 
                                             user, mock_workout_plan):
        """Test AJAX with existing plan"""
        # Mock existing plan
        mock_filter.return_value.first.return_value = mock_workout_plan
        
        request = request_factory.post('/onboarding/generate-plan-ajax/')
        request.user = user
        
        response = generate_plan_ajax(request)
        
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['status'] == 'success'
        assert 'redirect_url' in response_data
    
    @patch('apps.onboarding.views.create_workout_plan_from_onboarding')
    @patch('apps.workouts.models.WorkoutPlan.objects.filter')
    def test_generate_plan_ajax_error(self, mock_filter, mock_create_plan, 
                                     request_factory, user):
        """Test AJAX plan generation with error"""
        mock_filter.return_value.first.return_value = None
        mock_create_plan.side_effect = Exception("AI service error")
        
        request = request_factory.post('/onboarding/generate-plan-ajax/')
        request.user = user
        
        response = generate_plan_ajax(request)
        
        assert response.status_code == 500
        response_data = json.loads(response.content)
        assert response_data['status'] == 'error'
        assert 'AI service error' in response_data['error']


class TestWorkoutPlanCreation:
    """Test workout plan creation with AI integration"""
    
    @patch('apps.ai_integration.ai_client.OpenAIClient.generate_workout_plan')
    def test_ai_plan_generation_success(self, mock_generate_plan, valid_ai_plan_data):
        """Test successful AI plan generation with validation"""
        # Mock AI client to return valid plan
        validated_plan = WorkoutPlanSchema.model_validate(valid_ai_plan_data)
        mock_generate_plan.return_value = validated_plan
        
        from apps.ai_integration.ai_client import OpenAIClient
        
        client = OpenAIClient()
        result = client.generate_workout_plan("Generate a 6-week plan")
        
        assert isinstance(result, WorkoutPlanSchema)
        assert result.plan_name == "6-Week Progressive Strength Training"
        assert result.duration_weeks == 6
        assert len(result.weeks) == 6
    
    @patch('apps.ai_integration.ai_client.OpenAIClient._make_api_call')
    def test_ai_plan_generation_validation_error(self, mock_api_call):
        """Test AI plan generation with validation error"""
        # Mock API to return invalid data
        invalid_data = {
            "plan_name": "",  # Too short
            "duration_weeks": 0,  # Invalid
            "goal": "short",  # Too short
            "weeks": []
        }
        mock_api_call.return_value = invalid_data
        
        from apps.ai_integration.ai_client import OpenAIClient, AIClientError
        
        client = OpenAIClient()
        
        with pytest.raises(AIClientError, match="Failed to generate valid workout plan"):
            client.generate_workout_plan("Generate a plan")


class TestVideoPlaylistGeneration:
    """Test video playlist generation for workouts"""
    
    @patch('apps.workouts.services.VideoPlaylistBuilder._get_video_with_storage')
    def test_playlist_generation_success(self, mock_get_video):
        """Test successful playlist generation"""
        from apps.workouts.services import VideoPlaylistBuilder
        
        # Mock video responses
        mock_get_video.side_effect = [
            {'url': 'intro.mp4', 'duration': 30, 'clip_id': 1},  # intro
            {'url': 'technique.mp4', 'duration': 120, 'clip_id': 2},  # technique
            {'url': 'instruction.mp4', 'duration': 180, 'clip_id': 3},  # instruction
        ]
        
        # Mock workout
        workout = Mock()
        workout.is_rest_day = False
        workout.day_number = 1
        workout.week_number = 1
        workout.exercises = [
            {
                'exercise_slug': 'push-ups',
                'sets': 3,
                'reps': '10-12',
                'rest_seconds': 60
            }
        ]
        
        builder = VideoPlaylistBuilder(archetype="professional")
        
        with patch.object(builder, '_build_exercise_playlist') as mock_build_exercise:
            mock_build_exercise.return_value = [
                {'type': 'technique', 'url': 'technique.mp4'},
                {'type': 'instruction', 'url': 'instruction.mp4'}
            ]
            
            playlist = builder.build_workout_playlist(workout, "professional")
            
            assert len(playlist) >= 1  # At least intro
            assert playlist[0]['type'] == 'intro'
    
    @patch('apps.workouts.services.VideoPlaylistBuilder._get_rest_day_video')
    def test_rest_day_playlist(self, mock_rest_video):
        """Test playlist generation for rest day"""
        from apps.workouts.services import VideoPlaylistBuilder
        
        mock_rest_video.return_value = {
            'type': 'rest_day',
            'url': 'rest.mp4',
            'duration': 300,
            'title': 'Rest Day Motivation'
        }
        
        # Mock rest day workout
        workout = Mock()
        workout.is_rest_day = True
        workout.week_number = 1
        
        builder = VideoPlaylistBuilder(archetype="mentor")
        playlist = builder.build_workout_playlist(workout, "mentor")
        
        assert len(playlist) == 1
        assert playlist[0]['type'] == 'rest_day'


class TestExerciseValidationIntegration:
    """Test exercise validation in complete flow"""
    
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_clips_with_video')
    def test_exercise_validation_with_provider_abstraction(self, mock_get_clips):
        """Test exercise validation uses provider abstraction"""
        from apps.core.services.exercise_validation import ExerciseValidationService
        
        # Mock queryset
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.values_list.return_value = ['push-ups', 'squats']
        mock_get_clips.return_value = mock_queryset
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = None
            
            slugs = ExerciseValidationService.get_allowed_exercise_slugs()
            
            assert 'push-ups' in slugs
            assert 'squats' in slugs
            
            # Verify get_clips_with_video was called
            mock_get_clips.assert_called_once()
    
    @patch('apps.workouts.video_storage.get_storage')
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_clips_with_video')
    def test_video_storage_integration(self, mock_get_clips, mock_get_storage):
        """Test video storage integration in validation"""
        from apps.workouts.services import VideoPlaylistBuilder
        
        # Mock clip
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
        
        builder = VideoPlaylistBuilder(archetype="professional")
        result = builder._get_video_with_storage(r2_kind='technique')
        
        assert result is not None
        assert result['url'] == "https://example.com/video.mp4"
        mock_get_storage.assert_called_once_with(mock_clip)


@pytest.mark.django_db
class TestFullIntegrationFlow:
    """Test complete integration with database (when available)"""
    
    def test_user_flow_constants(self):
        """Test that required constants are properly defined"""
        from apps.workouts.models import VideoProvider
        from apps.core.services.exercise_validation import ExerciseValidationService
        
        # VideoProvider choices
        assert VideoProvider.R2 == "r2"
        assert VideoProvider.STREAM == "stream"
        assert VideoProvider.EXTERNAL == "external"
        
        # Validation constants
        assert ExerciseValidationService.REQUIRED_KINDS == ["instruction", "technique", "mistake"]
        assert ExerciseValidationService.CACHE_TIMEOUT == 300
    
    def test_pydantic_schema_validation(self, valid_ai_plan_data):
        """Test Pydantic schema validation works correctly"""
        from apps.ai_integration.schemas import WorkoutPlan, validate_ai_plan_response
        
        # Test direct validation
        plan = WorkoutPlan.model_validate(valid_ai_plan_data)
        plan.validate_structure()
        
        # Test validation function
        json_data = json.dumps(valid_ai_plan_data)
        validated_plan = validate_ai_plan_response(json_data)
        
        assert validated_plan.duration_weeks == 6
        assert len(validated_plan.weeks) == 6
        assert all(len(week.days) == 7 for week in validated_plan.weeks)


class TestErrorHandling:
    """Test error handling throughout the flow"""
    
    def test_ai_client_error_handling(self):
        """Test AI client error handling"""
        from apps.ai_integration.ai_client import AIClientError
        
        # Test custom exception
        error = AIClientError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    @patch('apps.ai_integration.schemas.json.loads')
    def test_schema_validation_json_error(self, mock_json_loads):
        """Test schema validation with JSON error"""
        from apps.ai_integration.schemas import validate_ai_plan_response
        
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with pytest.raises(ValueError, match="Invalid JSON from AI"):
            validate_ai_plan_response('{"invalid": json}')
    
    def test_video_storage_error_handling(self):
        """Test video storage error handling"""
        from apps.workouts.video_storage import R2Adapter
        
        adapter = R2Adapter()
        
        # Mock clip without file
        mock_clip = Mock()
        mock_clip.r2_file = None
        
        assert adapter.exists(mock_clip) is False
        assert adapter.playback_url(mock_clip) == ""


# Performance and edge case tests
class TestPerformanceAndEdgeCases:
    """Test performance considerations and edge cases"""
    
    def test_large_playlist_generation(self):
        """Test playlist generation with many exercises"""
        from apps.workouts.services import VideoPlaylistBuilder
        
        # Create workout with many exercises
        workout = Mock()
        workout.is_rest_day = False
        workout.day_number = 1
        workout.week_number = 1
        workout.exercises = [
            {
                'exercise_slug': f'exercise-{i}',
                'sets': 3,
                'reps': '10',
                'rest_seconds': 60
            }
            for i in range(20)  # 20 exercises
        ]
        
        builder = VideoPlaylistBuilder(archetype="professional")
        
        with patch.object(builder, '_build_exercise_playlist') as mock_build:
            mock_build.return_value = [{'type': 'technique', 'url': 'test.mp4'}]
            
            playlist = builder.build_workout_playlist(workout, "professional")
            
            # Should handle large number of exercises without issues
            assert isinstance(playlist, list)
            # Number of calls should match number of exercises
            assert mock_build.call_count == 20
    
    def test_empty_exercise_data(self):
        """Test handling of empty or malformed exercise data"""
        from apps.workouts.services import VideoPlaylistBuilder
        
        builder = VideoPlaylistBuilder(archetype="professional")
        
        # Test with empty exercise data
        result = builder._build_exercise_playlist('', 'professional', {})
        assert result == []
        
        # Test with None exercise slug
        with patch('apps.workouts.services.Exercise.objects.get') as mock_get:
            mock_get.side_effect = Exception("DoesNotExist")
            result = builder._build_exercise_playlist('nonexistent', 'professional', {})
            assert result == []