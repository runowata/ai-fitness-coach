import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users.models import UserProfile
from apps.workouts.models import Exercise, WorkoutPlan, DailyWorkout, VideoClip
from apps.workouts.services import VideoPlaylistBuilder, WorkoutCompletionService
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.onboarding.models import OnboardingQuestion, AnswerOption, UserOnboardingResponse

User = get_user_model()


class VideoPlaylistBuilderTest(TestCase):
    """Test VideoPlaylistBuilder service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.profile.archetype = 'bro'
        self.user.profile.save()
        
        # Create test exercise
        self.exercise = Exercise.objects.create(
            slug='push-up',
            name='Отжимания',
            description='Базовое упражнение',
            difficulty='beginner',
            muscle_groups=['chest', 'arms'],
            equipment_needed=[]
        )
        
        # Create test video clips
        self.intro_video = VideoClip.objects.create(
            exercise=None,
            type='intro',
            archetype='bro',
            model='default',
            file_path='videos/intro_bro.mp4',
            is_placeholder=False
        )
        
        self.technique_video = VideoClip.objects.create(
            exercise=self.exercise,
            type='technique',
            archetype='bro',
            model='default',
            file_path='videos/push-up_technique_bro.mp4',
            is_placeholder=False
        )
        
        # Create placeholder video (should be deprioritized)
        self.placeholder_video = VideoClip.objects.create(
            exercise=self.exercise,
            type='technique',
            archetype='bro',
            model='default',
            file_path='videos/placeholder.mp4',
            is_placeholder=True
        )
    
    def test_build_playlist_basic(self):
        """Test basic playlist building"""
        builder = VideoPlaylistBuilder(self.user)
        exercises = [{'exercise_slug': 'push-up', 'sets': 3, 'reps': 10}]
        
        playlist = builder.build_playlist(exercises)
        
        self.assertIsInstance(playlist, list)
        self.assertGreater(len(playlist), 0)
        
        # Should include intro
        intro_clips = [clip for clip in playlist if clip.get('type') == 'intro']
        self.assertGreater(len(intro_clips), 0)
    
    def test_non_placeholder_priority(self):
        """Test that non-placeholder videos are prioritized"""
        builder = VideoPlaylistBuilder(self.user)
        exercises = [{'exercise_slug': 'push-up', 'sets': 3, 'reps': 10}]
        
        playlist = builder.build_playlist(exercises)
        
        # Find technique videos in playlist
        technique_clips = [
            clip for clip in playlist 
            if clip.get('video') and clip['video'].type == 'technique'
        ]
        
        # Should prefer non-placeholder videos
        for clip in technique_clips:
            if clip['video'].exercise == self.exercise:
                self.assertFalse(clip['video'].is_placeholder)
    
    def test_archetype_matching(self):
        """Test that videos match user archetype"""
        builder = VideoPlaylistBuilder(self.user)
        exercises = [{'exercise_slug': 'push-up', 'sets': 3, 'reps': 10}]
        
        playlist = builder.build_playlist(exercises)
        
        # All videos should match user archetype
        for clip in playlist:
            if clip.get('video'):
                self.assertEqual(clip['video'].archetype, 'bro')
    
    def test_empty_exercises_list(self):
        """Test playlist building with empty exercises"""
        builder = VideoPlaylistBuilder(self.user)
        playlist = builder.build_playlist([])
        
        # Should still include intro/outro videos
        self.assertIsInstance(playlist, list)


class WorkoutPlanGeneratorTest(TestCase):
    """Test WorkoutPlanGenerator service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create onboarding responses
        self.question = OnboardingQuestion.objects.create(
            order=1,
            question_text='Какова ваша цель?',
            question_type='single_choice',
            ai_field_name='primary_goal'
        )
        
        self.response = UserOnboardingResponse.objects.create(
            user=self.user,
            question=self.question,
            answer_text='Набрать мышечную массу',
            answer_value='muscle_gain'
        )
    
    @patch('apps.ai_integration.services.openai.ChatCompletion.create')
    def test_generate_workout_plan_success(self, mock_openai):
        """Test successful workout plan generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '''
        {
            "plan_name": "Программа для набора массы",
            "duration_weeks": 8,
            "goal": "muscle_gain",
            "workouts": [
                {
                    "day": 1,
                    "week": 1,
                    "name": "Грудь и трицепс",
                    "exercises": [
                        {
                            "exercise_slug": "push-up",
                            "sets": 3,
                            "reps": "8-12",
                            "rest_seconds": 90
                        }
                    ]
                }
            ]
        }
        '''
        mock_openai.return_value = mock_response
        
        generator = WorkoutPlanGenerator()
        plan = generator.generate_plan(self.user)
        
        self.assertIsInstance(plan, WorkoutPlan)
        self.assertEqual(plan.user, self.user)
        self.assertEqual(plan.name, "Программа для набора массы")
        self.assertEqual(plan.duration_weeks, 8)
        self.assertTrue(plan.is_active)
        
        # Check that daily workouts were created
        daily_workouts = DailyWorkout.objects.filter(plan=plan)
        self.assertGreater(daily_workouts.count(), 0)
    
    @patch('apps.ai_integration.services.openai.ChatCompletion.create')
    def test_generate_workout_plan_invalid_json(self, mock_openai):
        """Test handling of invalid JSON response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = 'Invalid JSON response'
        mock_openai.return_value = mock_response
        
        generator = WorkoutPlanGenerator()
        
        with self.assertRaises(ValueError):
            generator.generate_plan(self.user)
    
    @patch('apps.ai_integration.services.openai.ChatCompletion.create')
    def test_generate_workout_plan_api_error(self, mock_openai):
        """Test handling of API errors"""
        mock_openai.side_effect = Exception("API Error")
        
        generator = WorkoutPlanGenerator()
        
        with self.assertRaises(Exception):
            generator.generate_plan(self.user)


class WorkoutCompletionServiceTest(TestCase):
    """Test WorkoutCompletionService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.plan = WorkoutPlan.objects.create(
            user=self.user,
            name='Test Plan',
            duration_weeks=4,
            goal='muscle_gain',
            plan_data={'test': 'data'},
            started_at=timezone.now()
        )
        
        self.workout = DailyWorkout.objects.create(
            plan=self.plan,
            day_number=1,
            week_number=1,
            name='Day 1 Workout',
            exercises=[
                {
                    'exercise_slug': 'push-up',
                    'sets': 3,
                    'reps': '10-12',
                    'rest_seconds': 60
                }
            ]
        )
    
    def test_complete_workout_success(self):
        """Test successful workout completion"""
        initial_xp = self.user.profile.experience_points
        
        service = WorkoutCompletionService()
        result = service.complete_workout(self.user, self.workout.id)
        
        self.assertTrue(result['success'])
        self.workout.refresh_from_db()
        self.assertTrue(self.workout.is_completed)
        self.assertIsNotNone(self.workout.completed_at)
        
        # Check XP was awarded
        self.user.profile.refresh_from_db()
        self.assertGreater(self.user.profile.experience_points, initial_xp)
    
    def test_complete_nonexistent_workout(self):
        """Test completing non-existent workout"""
        service = WorkoutCompletionService()
        result = service.complete_workout(self.user, 99999)
        
        self.assertFalse(result['success'])
        self.assertIn('не найдена', result['message'])
    
    def test_complete_already_completed_workout(self):
        """Test completing already completed workout"""
        # Mark workout as completed
        self.workout.is_completed = True
        self.workout.completed_at = timezone.now()
        self.workout.save()
        
        service = WorkoutCompletionService()
        result = service.complete_workout(self.user, self.workout.id)
        
        self.assertFalse(result['success'])
        self.assertIn('уже завершена', result['message'])
    
    def test_complete_other_user_workout(self):
        """Test completing another user's workout"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        service = WorkoutCompletionService()
        result = service.complete_workout(other_user, self.workout.id)
        
        self.assertFalse(result['success'])
        self.assertIn('не найдена', result['message'])


@pytest.mark.slow
class IntegrationTest(TestCase):
    """Integration tests for workout system"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.profile.archetype = 'bro'
        self.user.profile.save()
        
        # Create exercise
        self.exercise = Exercise.objects.create(
            slug='push-up',
            name='Отжимания',
            description='Базовое упражнение',
            difficulty='beginner',
            muscle_groups=['chest', 'arms'],
            equipment_needed=[]
        )
        
        # Create video
        self.video = VideoClip.objects.create(
            exercise=self.exercise,
            type='technique',
            archetype='bro',
            model='default',
            file_path='videos/push-up_technique_bro.mp4',
            is_placeholder=False
        )
    
    @patch('apps.ai_integration.services.openai.ChatCompletion.create')
    def test_full_workout_flow(self, mock_openai):
        """Test complete workout flow from generation to completion"""
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '''
        {
            "plan_name": "Тестовая программа",
            "duration_weeks": 2,
            "goal": "muscle_gain",
            "workouts": [
                {
                    "day": 1,
                    "week": 1,
                    "name": "Тренировка 1",
                    "exercises": [
                        {
                            "exercise_slug": "push-up",
                            "sets": 3,
                            "reps": "10",
                            "rest_seconds": 60
                        }
                    ]
                }
            ]
        }
        '''
        mock_openai.return_value = mock_response
        
        # 1. Generate workout plan
        generator = WorkoutPlanGenerator()
        plan = generator.generate_plan(self.user)
        
        # 2. Build video playlist
        daily_workout = plan.dailyworkout_set.first()
        builder = VideoPlaylistBuilder(self.user)
        playlist = builder.build_playlist(daily_workout.exercises)
        
        # 3. Complete workout
        service = WorkoutCompletionService()
        result = service.complete_workout(self.user, daily_workout.id)
        
        # Verify complete flow
        self.assertIsInstance(plan, WorkoutPlan)
        self.assertIsInstance(playlist, list)
        self.assertTrue(result['success'])
        
        # Check state changes
        daily_workout.refresh_from_db()
        self.assertTrue(daily_workout.is_completed)
        
        self.user.profile.refresh_from_db()
        self.assertGreater(self.user.profile.experience_points, 0)