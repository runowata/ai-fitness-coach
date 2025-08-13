from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.achievements.models import Achievement, UserAchievement
from apps.content.models import Story, StoryChapter, UserStoryAccess
from apps.onboarding.models import AnswerOption, OnboardingQuestion, UserOnboardingResponse
from apps.workouts.models import DailyWorkout, Exercise, WorkoutPlan

User = get_user_model()


class EndToEndUserFlowTest(TestCase):
    """Test complete user journey from registration to achievement unlock"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test data
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create required test data"""
        # Create onboarding questions
        self.question1 = OnboardingQuestion.objects.create(
            order=1,
            question_text="Какова ваша цель?",
            question_type="single_choice",
            ai_field_name="primary_goal",
            is_active=True
        )
        
        self.option1 = AnswerOption.objects.create(
            question=self.question1,
            option_text="Похудеть",
            option_value="weight_loss",
            order=1
        )
        
        # Create exercise
        self.exercise = Exercise.objects.create(
            slug="push-up",
            name="Отжимания",
            description="Базовое упражнение",
            difficulty="beginner",
            muscle_groups=["chest", "arms"],
            equipment_needed=[]
        )
        
        # Create achievement
        self.achievement = Achievement.objects.create(
            slug="first-workout",
            name="Первая тренировка",
            description="Завершите первую тренировку",
            trigger_type="workout_count",
            trigger_value=1,
            xp_reward=100
        )
        
        # Create story and chapter
        self.story = Story.objects.create(
            slug="test-story",
            title="Тестовая история",
            author="Тестовый автор",
            description="Описание истории",
            cover_image_url="https://example.com/cover.jpg",
            total_chapters=2,
            is_published=True
        )
        
        self.chapter = StoryChapter.objects.create(
            story=self.story,
            chapter_number=1,
            title="Первая глава",
            content="Содержание первой главы...",
            estimated_reading_time=5,
            is_published=True
        )
        
        # Link achievement to chapter
        self.achievement.unlocks_story_chapter = self.chapter
        self.achievement.save()
    
    def test_complete_user_journey(self):
        """Test the complete user journey from registration to story unlock"""
        
        # 1. User registration
        response = self.client.post(reverse('users:register'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'age_confirmed': True,
            'agree_to_terms': True
        })
        
        # Should redirect to onboarding
        self.assertEqual(response.status_code, 302)
        
        # User should be created and logged in
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        self.assertTrue(hasattr(user, 'profile'))
        
        # 2. Start onboarding
        response = self.client.get(reverse('onboarding:start'))
        self.assertEqual(response.status_code, 302)  # Redirect to first question
        
        # 3. Answer onboarding question
        response = self.client.post(
            reverse('onboarding:save_answer', kwargs={'question_id': self.question1.id}),
            data='{"answer": ' + str(self.option1.id) + '}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response was saved
        response_obj = UserOnboardingResponse.objects.get(
            user=user,
            question=self.question1
        )
        self.assertIn(self.option1, response_obj.answer_options.all())
        
        # 4. Select archetype
        response = self.client.post(reverse('onboarding:select_archetype'), {
            'archetype': 'bro'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to generate plan
        
        user.refresh_from_db()
        self.assertEqual(user.profile.archetype, 'bro')
        
        # 5. Generate workout plan (mock AI response)
        mock_plan_data = {
            'plan_name': 'Test Plan',
            'duration_weeks': 4,
            'weeks': [
                {
                    'week_number': 1,
                    'theme': 'Getting Started',
                    'days': [
                        {
                            'day_number': 1,
                            'workout_name': 'First Workout',
                            'is_rest_day': False,
                            'exercises': [
                                {
                                    'exercise_slug': 'push-up',
                                    'exercise_name': 'Отжимания',
                                    'sets': 3,
                                    'reps': '10-12',
                                    'rest_seconds': 60
                                }
                            ],
                            'confidence_task': 'Посмотрите на себя в зеркало и улыбнитесь'
                        }
                    ]
                }
            ]
        }
        
        with patch('apps.ai_integration.services.WorkoutPlanGenerator.generate_plan') as mock_generate:
            mock_generate.return_value = mock_plan_data
            
            response = self.client.get(reverse('onboarding:generate_plan'))
            
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        
        # Check workout plan was created
        workout_plan = WorkoutPlan.objects.get(user=user)
        self.assertEqual(workout_plan.name, 'Test Plan')
        self.assertEqual(workout_plan.duration_weeks, 4)
        
        # Check daily workout was created
        daily_workout = DailyWorkout.objects.get(plan=workout_plan)
        self.assertEqual(daily_workout.name, 'First Workout')
        self.assertFalse(daily_workout.is_rest_day)
        
        # Check onboarding completion
        user.refresh_from_db()
        self.assertIsNotNone(user.profile.onboarding_completed_at)
        
        # 6. Access dashboard
        response = self.client.get(reverse('users:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Workout')
        
        # 7. Start workout
        response = self.client.get(
            reverse('workouts:daily_workout', kwargs={'workout_id': daily_workout.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Workout')
        
        # 8. Complete workout
        response = self.client.post(
            reverse('workouts:complete_workout', kwargs={'workout_id': daily_workout.id}),
            data='{"feedback_rating": "fire", "feedback_note": "Great workout!"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['xp_earned'], 125)  # 100 base + 25 bonus for 'fire'
        self.assertEqual(len(data['new_achievements']), 1)
        self.assertEqual(data['new_achievements'][0]['name'], 'Первая тренировка')
        
        # 9. Check achievement was unlocked
        user_achievement = UserAchievement.objects.get(
            user=user,
            achievement=self.achievement
        )
        self.assertIsNotNone(user_achievement.unlocked_at)
        
        # 10. Check story access was granted
        story_access = UserStoryAccess.objects.get(
            user=user,
            chapter=self.chapter
        )
        self.assertEqual(story_access.unlocked_by_achievement, self.achievement)
        
        # 11. Access story library
        response = self.client.get(reverse('content:stories'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)
        
        # 12. Read unlocked chapter
        response = self.client.get(
            reverse('content:read_chapter', kwargs={
                'story_slug': self.story.slug,
                'chapter_number': self.chapter.chapter_number
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.chapter.title)
        self.assertContains(response, self.chapter.content)
        
        # Check reading was tracked
        story_access.refresh_from_db()
        self.assertIsNotNone(story_access.first_read_at)
        self.assertEqual(story_access.read_count, 1)
        
        # 13. Try to access locked chapter (should fail)
        chapter2 = StoryChapter.objects.create(
            story=self.story,
            chapter_number=2,
            title="Вторая глава",
            content="Заблокированное содержание",
            estimated_reading_time=5,
            is_published=True
        )
        
        response = self.client.get(
            reverse('content:read_chapter', kwargs={
                'story_slug': self.story.slug,
                'chapter_number': chapter2.chapter_number
            })
        )
        # Should redirect back to story detail with error message
        self.assertEqual(response.status_code, 302)
        
        # 14. Check user stats
        user.refresh_from_db()
        self.assertEqual(user.profile.total_workouts_completed, 1)
        self.assertEqual(user.profile.current_streak, 1)
        self.assertEqual(user.profile.experience_points, 225)  # 100 from achievement + 125 from workout
        self.assertEqual(user.profile.level, 3)  # 225 XP = level 3
    
    def test_workout_substitution_flow(self):
        """Test exercise substitution during workout"""
        # Create user and workout
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            is_adult_confirmed=True
        )
        user.profile.archetype = 'bro'
        user.profile.save()
        
        # Create alternative exercise
        alt_exercise = Exercise.objects.create(
            slug="knee-push-up",
            name="Отжимания с колен",
            description="Упрощенная версия",
            difficulty="beginner",
            muscle_groups=["chest", "arms"],
            equipment_needed=[]
        )
        
        # Link as alternative
        self.exercise.alternatives.add(alt_exercise)
        
        # Create workout plan and daily workout
        plan = WorkoutPlan.objects.create(
            user=user,
            name="Test Plan",
            duration_weeks=4,
            goal="test",
            plan_data={},
            started_at=timezone.now()
        )
        
        workout = DailyWorkout.objects.create(
            plan=plan,
            day_number=1,
            week_number=1,
            name="Test Workout",
            exercises=[{
                'exercise_slug': 'push-up',
                'exercise_name': 'Отжимания',
                'sets': 3,
                'reps': '10-12'
            }]
        )
        
        # Login user
        self.client.force_login(user)
        
        # Substitute exercise
        response = self.client.post(
            reverse('workouts:substitute_exercise', kwargs={'workout_id': workout.id}),
            data='{"original_exercise": "push-up", "substitute_exercise": "knee-push-up"}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('заменено', data['message'])
        
        # Check substitution was recorded
        workout.refresh_from_db()
        self.assertEqual(workout.substitutions['push-up'], 'knee-push-up')
        self.assertEqual(workout.exercises[0]['exercise_slug'], 'knee-push-up')


@pytest.mark.django_db
def test_achievement_checking_service():
    """Test achievement checking service in isolation"""
    from apps.achievements.services import AchievementChecker

    # Create user
    user = User.objects.create_user(
        username='testuser3',
        email='test3@example.com',
        password='testpass123'
    )
    
    # Create achievements
    achievement1 = Achievement.objects.create(
        slug="test-workout-count",
        name="5 Workouts",
        description="Complete 5 workouts",
        trigger_type="workout_count",
        trigger_value=5,
        xp_reward=100
    )
    
    achievement2 = Achievement.objects.create(
        slug="test-xp",
        name="500 XP",
        description="Earn 500 XP",
        trigger_type="xp_earned",
        trigger_value=500,
        xp_reward=50
    )
    
    # Set user stats
    user.profile.total_workouts_completed = 5
    user.profile.experience_points = 600
    user.profile.save()
    
    # Check achievements
    checker = AchievementChecker()
    new_achievements = checker.check_user_achievements(user)
    
    # Should unlock both achievements
    assert len(new_achievements) == 2
    
    # Check database records
    assert UserAchievement.objects.filter(user=user, achievement=achievement1).exists()
    assert UserAchievement.objects.filter(user=user, achievement=achievement2).exists()
    
    # Running again should not create duplicates
    new_achievements_2 = checker.check_user_achievements(user)
    assert len(new_achievements_2) == 0