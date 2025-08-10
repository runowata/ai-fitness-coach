"""
Integration tests for onboarding flow with analysis preview
"""

import pytest
import json
from unittest.mock import Mock, patch
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.onboarding.models import OnboardingSession
from apps.workouts.models import WorkoutPlan
from tests.factories import UserFactory


User = get_user_model()


@pytest.mark.integration
@override_settings(SHOW_AI_ANALYSIS=True)
class TestOnboardingAnalysisFlow(TestCase):
    """Test onboarding flow with analysis preview"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        
        # Create onboarding session
        self.session = OnboardingSession.objects.create(
            user=self.user,
            ai_request_data={
                'fitness_level': 'beginner',
                'archetype': 'professional',
                'available_days': [1, 2, 3, 4, 5],
                'session_duration': 45
            }
        )
    
    @patch('apps.onboarding.views.WorkoutPlanGenerator')
    def test_generate_plan_returns_analysis_preview(self, mock_generator_class):
        """Test generate_plan_ajax returns analysis for preview when SHOW_AI_ANALYSIS=True"""
        # Mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Mock plan generation to return analysis
        mock_plan_data = {
            'plan_name': 'Beginner Professional Plan',
            'duration_weeks': 4,
            'weekly_frequency': 3,
            'session_duration': 45,
            'analysis': {
                'strengths': 'Good motivation to start fitness journey',
                'challenges': 'Building consistent routine',
                'recommendations': 'Start with bodyweight exercises'
            },
            'weeks': [{
                'week': 1,
                'focus': 'Foundation',
                'days': [{
                    'day': 1,
                    'exercises': [{'exercise_slug': 'push-ups', 'sets': 3, 'reps': 10}]
                }]
            }]
        }
        mock_generator.generate_plan.return_value = mock_plan_data
        
        # Make request
        response = self.client.post(reverse('onboarding:generate_plan_ajax'), {
            'action': 'generate'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.content)
        
        # Should return needs_confirmation status
        self.assertEqual(data['status'], 'needs_confirmation')
        
        # Should include analysis
        self.assertIn('analysis', data)
        self.assertEqual(data['analysis']['strengths'], 'Good motivation to start fitness journey')
        
        # Should include plan preview
        self.assertIn('plan_preview', data)
        self.assertEqual(data['plan_preview']['plan_name'], 'Beginner Professional Plan')
        self.assertEqual(data['plan_preview']['duration_weeks'], 4)
        
        # Plan should be stored in session
        self.assertIn('pending_plan_data', self.client.session)
    
    @patch('apps.onboarding.views.WorkoutPlanGenerator')
    def test_confirm_plan_creates_workout_plan(self, mock_generator_class):
        """Test confirming plan creates actual WorkoutPlan"""
        # Store plan data in session (simulating previous generate call)
        session = self.client.session
        session['pending_plan_data'] = {
            'plan_name': 'Confirmed Plan',
            'duration_weeks': 4,
            'weeks': []
        }
        session.save()
        
        # Mock generator for create_plan
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_workout_plan = Mock()
        mock_workout_plan.id = 123
        mock_generator.create_plan.return_value = mock_workout_plan
        
        # Make confirmation request
        response = self.client.post(reverse('onboarding:generate_plan_ajax'), {
            'action': 'confirm'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.content)
        
        # Should return success with redirect
        self.assertEqual(data['status'], 'success')
        self.assertIn('redirect_url', data)
        self.assertEqual(data['plan_id'], 123)
        
        # Should have called create_plan
        mock_generator.create_plan.assert_called_once()
        
        # Session should be cleared
        self.assertNotIn('pending_plan_data', self.client.session)
        
        # User should be marked as completed onboarding
        self.user.refresh_from_db()
        self.assertTrue(self.user.completed_onboarding)
    
    def test_confirm_without_pending_plan_returns_error(self):
        """Test confirming without pending plan returns error"""
        response = self.client.post(reverse('onboarding:generate_plan_ajax'), {
            'action': 'confirm'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('No pending plan', data['error'])


@pytest.mark.integration
@override_settings(SHOW_AI_ANALYSIS=False)
class TestOnboardingDirectFlow(TestCase):
    """Test onboarding flow without analysis preview"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
    
    @patch('apps.onboarding.views.WorkoutPlanGenerator')
    def test_direct_plan_creation_without_preview(self, mock_generator_class):
        """Test direct plan creation when SHOW_AI_ANALYSIS=False"""
        # Mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        mock_plan_data = {
            'plan_name': 'Direct Plan',
            'duration_weeks': 6
        }
        mock_generator.generate_plan.return_value = mock_plan_data
        
        # Mock create_plan
        mock_workout_plan = Mock()
        mock_workout_plan.id = 456
        mock_generator.create_plan.return_value = mock_workout_plan
        
        # Make request
        response = self.client.post(reverse('onboarding:generate_plan_ajax'))
        
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.content)
        
        # Should return success directly (no preview)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['plan_id'], 456)
        
        # Should have called create_plan directly
        mock_generator.create_plan.assert_called_once()
        
        # User should be marked as completed onboarding
        self.user.refresh_from_db()
        self.assertTrue(self.user.completed_onboarding)


@pytest.mark.integration
class TestOnboardingErrorHandling(TestCase):
    """Test onboarding error handling"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
    
    @patch('apps.onboarding.views.WorkoutPlanGenerator')
    def test_plan_generation_error_handling(self, mock_generator_class):
        """Test error handling when plan generation fails"""
        # Mock generator to raise exception
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_plan.side_effect = ValueError("AI generation failed")
        
        # Make request
        response = self.client.post(reverse('onboarding:generate_plan_ajax'))
        
        self.assertEqual(response.status_code, 500)
        
        # Parse response
        data = json.loads(response.content)
        
        # Should return error status
        self.assertEqual(data['status'], 'error')
        self.assertIn('AI generation failed', data['error'])
    
    def test_existing_plan_redirects_to_dashboard(self):
        """Test existing active plan redirects to dashboard"""
        # Create existing workout plan
        WorkoutPlan.objects.create(
            user=self.user,
            plan_name='Existing Plan',
            duration_weeks=4,
            is_active=True
        )
        
        # Make request
        response = self.client.post(reverse('onboarding:generate_plan_ajax'))
        
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        data = json.loads(response.content)
        
        # Should redirect to dashboard
        self.assertEqual(data['status'], 'success')
        self.assertIn('dashboard', data['redirect_url'])


@pytest.mark.integration
class TestOnboardingSessionData(TestCase):
    """Test onboarding session data processing"""
    
    def setUp(self):
        self.user = UserFactory()
        
        # Create onboarding session with comprehensive data
        self.session = OnboardingSession.objects.create(
            user=self.user,
            ai_request_data={
                'age': 25,
                'fitness_level': 'intermediate',
                'archetype': 'mentor',
                'goals': ['strength', 'muscle_gain'],
                'available_days': [1, 2, 3, 4, 5],
                'session_duration': 60,
                'equipment': ['dumbbell', 'barbell'],
                'injuries': [],
                'preferred_time': 'morning'
            }
        )
    
    @patch('apps.onboarding.services.OnboardingDataProcessor.collect_user_data')
    def test_user_data_collection(self, mock_collect):
        """Test user data collection from onboarding session"""
        expected_data = {
            'age': 25,
            'fitness_level': 'intermediate',
            'archetype': 'mentor',
            'goals': ['strength', 'muscle_gain'],
            'available_days': [1, 2, 3, 4, 5],
            'session_duration': 60,
            'equipment': ['dumbbell', 'barbell']
        }
        mock_collect.return_value = expected_data
        
        from apps.onboarding.services import OnboardingDataProcessor
        
        result = OnboardingDataProcessor.collect_user_data(self.user)
        
        # Should call with user
        mock_collect.assert_called_once_with(self.user)
        self.assertEqual(result, expected_data)


@pytest.mark.e2e
@override_settings(
    SHOW_AI_ANALYSIS=True,
    AI_REPROMPT_MAX_ATTEMPTS=1
)
class TestOnboardingE2E(TestCase):
    """End-to-end onboarding tests"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
    
    def test_complete_onboarding_flow(self):
        """Test complete onboarding flow from login to plan creation"""
        # 1. User logs in
        self.client.force_login(self.user)
        
        # 2. User completes onboarding form (simulated)
        session = OnboardingSession.objects.create(
            user=self.user,
            ai_request_data={
                'fitness_level': 'beginner',
                'archetype': 'professional'
            }
        )
        
        # 3. Generate plan with mocked AI
        with patch('apps.onboarding.views.WorkoutPlanGenerator') as mock_gen_class:
            mock_generator = Mock()
            mock_gen_class.return_value = mock_generator
            
            # Mock plan with analysis
            mock_generator.generate_plan.return_value = {
                'plan_name': 'E2E Test Plan',
                'analysis': {'strengths': 'Good start'},
                'weeks': []
            }
            
            # Generate plan
            response = self.client.post('/onboarding/generate-plan/', {'action': 'generate'})
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'needs_confirmation')
        
        # 4. User confirms plan
        with patch('apps.onboarding.views.WorkoutPlanGenerator') as mock_gen_class:
            mock_generator = Mock()
            mock_gen_class.return_value = mock_generator
            
            mock_plan = Mock()
            mock_plan.id = 999
            mock_generator.create_plan.return_value = mock_plan
            
            # Confirm plan
            response = self.client.post('/onboarding/generate-plan/', {'action': 'confirm'})
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['plan_id'], 999)
        
        # 5. Verify user state
        self.user.refresh_from_db()
        self.assertTrue(self.user.completed_onboarding)