import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.workouts.models import Exercise, WorkoutPlan, DailyWorkout
from apps.achievements.models import Achievement, UserAchievement
from apps.onboarding.models import OnboardingQuestion, AnswerOption

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model with integrated profile data"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_adult_confirmed=True
        )
    
    def test_user_profile_integrated(self):
        """Test that user has integrated profile fields"""
        self.assertTrue(hasattr(self.user, 'experience_points'))
        self.assertTrue(hasattr(self.user, 'level'))
        self.assertTrue(hasattr(self.user, 'archetype'))
    
    def test_user_xp_system(self):
        """Test XP and level calculation"""
        # Initially level 1 with 0 XP
        self.assertEqual(self.user.level, 1)
        self.assertEqual(self.user.experience_points, 0)
        
        # Add XP and check level up
        self.user.add_xp(150)
        self.assertEqual(self.user.experience_points, 150)
        self.assertEqual(self.user.level, 2)  # 150 XP = level 2
        
        self.user.add_xp(50)
        self.assertEqual(self.user.experience_points, 200)
        self.assertEqual(self.user.level, 3)  # 200 XP = level 3


class ExerciseModelTest(TestCase):
    """Test Exercise model"""
    
    def setUp(self):
        self.exercise = Exercise.objects.create(
            id='push-up',  # Add ID field
            slug='push-up',
            name='Отжимания',
            description='Базовое упражнение',
            difficulty='beginner',
            muscle_groups='chest,arms',  # Text field now
            equipment=""
        )
    
    def test_exercise_creation(self):
        """Test exercise creation and properties"""
        self.assertEqual(str(self.exercise), 'Отжимания')
        self.assertEqual(self.exercise.difficulty, 'beginner')
        self.assertEqual(self.exercise.muscle_groups, 'chest,arms')  # Now text field
    
    # def test_exercise_alternatives(self):
    #     """Test exercise alternatives system - DISABLED: field removed"""
    #     pass


class WorkoutPlanModelTest(TestCase):
    """Test WorkoutPlan and DailyWorkout models"""
    
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
    
    def test_workout_plan_creation(self):
        """Test workout plan creation"""
        self.assertEqual(str(self.plan), 'Test Plan')
        self.assertEqual(self.plan.user, self.user)
        self.assertTrue(self.plan.is_active)
    
    def test_current_week_calculation(self):
        """Test current week calculation"""
        # Just started, should be week 1
        current_week = self.plan.get_current_week()
        self.assertEqual(current_week, 1)
    
    def test_daily_workout_creation(self):
        """Test daily workout creation"""
        workout = DailyWorkout.objects.create(
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
        
        self.assertEqual(workout.plan, self.plan)
        self.assertFalse(workout.is_rest_day)
        self.assertEqual(len(workout.exercises), 1)


class AchievementModelTest(TestCase):
    """Test Achievement system"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.achievement = Achievement.objects.create(
            slug='first-workout',
            name='Первая тренировка',
            description='Завершите вашу первую тренировку',
            trigger_type='workout_count',
            trigger_value=1,
            xp_reward=100
        )
    
    def test_achievement_creation(self):
        """Test achievement creation"""
        self.assertEqual(str(self.achievement), 'Первая тренировка')
        self.assertEqual(self.achievement.trigger_type, 'workout_count')
        self.assertEqual(self.achievement.xp_reward, 100)
    
    def test_user_achievement_unlock(self):
        """Test unlocking achievement"""
        user_achievement = UserAchievement.objects.create(
            user=self.user,
            achievement=self.achievement
        )
        
        self.assertEqual(user_achievement.user, self.user)
        self.assertEqual(user_achievement.achievement, self.achievement)
        self.assertIsNotNone(user_achievement.unlocked_at)


class OnboardingModelTest(TestCase):
    """Test Onboarding system"""
    
    def setUp(self):
        self.question = OnboardingQuestion.objects.create(
            order=1,
            question_text='Какова ваша цель?',
            question_type='single_choice',
            ai_field_name='primary_goal'
        )
        
        self.option = AnswerOption.objects.create(
            question=self.question,
            option_text='Похудеть',
            option_value='weight_loss',
            order=1
        )
    
    def test_onboarding_question_creation(self):
        """Test onboarding question creation"""
        self.assertEqual(self.question.order, 1)
        self.assertEqual(self.question.question_type, 'single_choice')
        self.assertTrue(self.question.is_required)
    
    def test_answer_option_creation(self):
        """Test answer option creation"""
        self.assertEqual(str(self.option), 'Похудеть')
        self.assertEqual(self.option.question, self.question)
        self.assertEqual(self.option.option_value, 'weight_loss')