"""
Test AI whitelist enforcement and exercise substitutions
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from django.test import TestCase, override_settings

from apps.ai_integration.services import WorkoutPlanGenerator
from apps.workouts.catalog import ExerciseAttributes, ExerciseCatalog
from apps.workouts.constants import EXERCISE_FALLBACK_PRIORITY


class TestExerciseCatalog(TestCase):
    """Test exercise catalog functionality"""
    
    def setUp(self):
        from apps.workouts.models import CSVExercise

        # Create test exercises
        self.exercises = [
            CSVExercise.objects.create(
                slug='push-ups',
                name='Push-ups',
                muscle_group='chest',
                equipment='none',
                difficulty='beginner',
                is_active=True
            ),
            CSVExercise.objects.create(
                slug='bench-press',
                name='Bench Press',
                muscle_group='chest',
                equipment='barbell',
                difficulty='intermediate',
                is_active=True
            ),
            CSVExercise.objects.create(
                slug='dumbbell-press',
                name='Dumbbell Press',
                muscle_group='chest',
                equipment='dumbbell',
                difficulty='beginner',
                is_active=True
            ),
            CSVExercise.objects.create(
                slug='squats',
                name='Squats',
                muscle_group='legs',
                equipment='none',
                difficulty='beginner',
                is_active=True
            ),
        ]
        
        self.catalog = ExerciseCatalog()
        self.catalog.invalidate_cache()  # Clear any existing cache
    
    def test_get_attributes(self):
        """Test getting exercise attributes"""
        attrs = self.catalog.get_attributes('push-ups')
        
        self.assertIsNotNone(attrs)
        self.assertEqual(attrs.slug, 'push-ups')
        self.assertEqual(attrs.muscle_group, 'chest')
        self.assertEqual(attrs.equipment, 'none')
    
    def test_find_similar_by_muscle_group(self):
        """Test finding similar exercises by muscle group"""
        allowed = {'bench-press', 'dumbbell-press', 'squats'}
        
        similar = self.catalog.find_similar(
            'push-ups',  # chest exercise not in allowed
            allowed,
            priority=EXERCISE_FALLBACK_PRIORITY
        )
        
        # Should return chest exercises from allowed set
        self.assertIn(similar[0], ['bench-press', 'dumbbell-press'])
        self.assertNotIn('squats', similar)  # Different muscle group
    
    def test_find_similar_with_equipment_fallback(self):
        """Test fallback to equipment similarity"""
        allowed = {'push-ups', 'squats'}  # Only bodyweight exercises
        
        similar = self.catalog.find_similar(
            'bench-press',  # barbell exercise
            allowed,
            priority={'equipment': 1, 'muscle_group': 2, 'difficulty': 3}
        )
        
        # Should prefer same equipment (none) over muscle group
        # But since no barbell exercises, should fall back to muscle group
        self.assertEqual(similar[0], 'push-ups')  # Same muscle group
    
    def test_similarity_score(self):
        """Test exercise similarity scoring"""
        push_ups = ExerciseAttributes(
            slug='push-ups',
            name='Push-ups',
            muscle_group='chest',
            equipment='none',
            difficulty='beginner'
        )
        
        bench_press = ExerciseAttributes(
            slug='bench-press',
            name='Bench Press',
            muscle_group='chest',
            equipment='barbell',
            difficulty='intermediate'
        )
        
        squats = ExerciseAttributes(
            slug='squats',
            name='Squats',
            muscle_group='legs',
            equipment='none',
            difficulty='beginner'
        )
        
        # Same muscle group, different equipment/difficulty
        score1 = push_ups.similarity_score(bench_press, EXERCISE_FALLBACK_PRIORITY)
        
        # Different muscle group, same equipment
        score2 = push_ups.similarity_score(squats, EXERCISE_FALLBACK_PRIORITY)
        
        # Lower score = more similar
        self.assertLess(score1, score2)  # bench_press is more similar to push_ups than squats
    
    def test_get_by_muscle_group(self):
        """Test getting exercises by muscle group"""
        chest_exercises = self.catalog.get_by_muscle_group('chest')
        
        self.assertEqual(len(chest_exercises), 3)
        self.assertIn('push-ups', chest_exercises)
        self.assertIn('bench-press', chest_exercises)
        self.assertNotIn('squats', chest_exercises)
    
    def test_get_by_muscle_group_with_allowed_filter(self):
        """Test filtering by allowed set"""
        allowed = {'push-ups', 'squats'}
        chest_exercises = self.catalog.get_by_muscle_group('chest', allowed)
        
        self.assertEqual(len(chest_exercises), 1)
        self.assertEqual(chest_exercises[0], 'push-ups')


class TestWhitelistEnforcement(TestCase):
    """Test whitelist enforcement in plan generation"""
    
    def setUp(self):
        self.generator = WorkoutPlanGenerator()
        
        # Mock AI client
        self.mock_ai_client = Mock()
        self.generator.ai_client = self.mock_ai_client
    
    @patch('apps.ai_integration.services.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('apps.ai_integration.services.get_catalog')
    def test_enforce_allowed_exercises_with_substitutions(self, mock_get_catalog, mock_get_allowed):
        """Test exercise substitution for disallowed exercises"""
        # Setup
        allowed_slugs = {'push-ups', 'squats', 'plank'}
        mock_get_allowed.return_value = allowed_slugs
        
        mock_catalog = Mock()
        mock_catalog.find_similar.side_effect = [
            ['push-ups'],  # Substitute for bench-press
            [],  # No substitute for deadlifts
        ]
        mock_get_catalog.return_value = mock_catalog
        
        plan_data = {
            'weeks': [{
                'days': [{
                    'exercises': [
                        {'exercise_slug': 'push-ups'},  # Allowed
                        {'exercise_slug': 'bench-press'},  # Not allowed, has substitute
                        {'exercise_slug': 'deadlifts'},  # Not allowed, no substitute
                    ]
                }]
            }]
        }
        
        # Execute
        result_plan, substitutions, unresolved = self.generator._enforce_allowed_exercises(
            plan_data, allowed_slugs
        )
        
        # Verify
        exercises = result_plan['weeks'][0]['days'][0]['exercises']
        
        # First exercise unchanged
        self.assertEqual(exercises[0]['exercise_slug'], 'push-ups')
        self.assertNotIn('_substituted', exercises[0])
        
        # Second exercise substituted
        self.assertEqual(exercises[1]['exercise_slug'], 'push-ups')
        self.assertTrue(exercises[1]['_substituted'])
        self.assertEqual(exercises[1]['_original'], 'bench-press')
        
        # Third exercise unresolved
        self.assertEqual(exercises[2]['exercise_slug'], 'deadlifts')
        self.assertTrue(exercises[2]['_unresolved'])
        
        self.assertEqual(substitutions, 1)
        self.assertEqual(unresolved, ['deadlifts'])
    
    def test_build_prompt_with_whitelist(self):
        """Test prompt building with whitelist"""
        user_data = {'fitness_level': 'beginner'}
        allowed_slugs = {'push-ups', 'squats', 'plank'}
        
        prompt = self.generator._build_prompt_with_whitelist(user_data, allowed_slugs)
        
        # Check whitelist is in prompt
        self.assertIn('IMPORTANT: You MUST use ONLY exercises from this allowed list', prompt)
        self.assertIn('plank', prompt)
        self.assertIn('push-ups', prompt)
        self.assertIn('squats', prompt)
    
    def test_build_reprompt(self):
        """Test reprompt building for unresolved exercises"""
        original_prompt = "Generate a workout plan"
        unresolved = ['deadlifts', 'pull-ups']
        allowed_slugs = {'push-ups', 'squats'}
        
        reprompt = self.generator._build_reprompt(original_prompt, unresolved, allowed_slugs)
        
        self.assertIn('CORRECTION NEEDED', reprompt)
        self.assertIn('deadlifts', reprompt)
        self.assertIn('pull-ups', reprompt)
        self.assertIn('push-ups', reprompt)
        self.assertIn(original_prompt, reprompt)


@override_settings(
    AI_REPROMPT_MAX_ATTEMPTS=2,
    FALLBACK_TO_LEGACY_FLOW=False,
    SHOW_AI_ANALYSIS=False
)
class TestRepromptCycle(TestCase):
    """Test reprompt cycle with limits"""
    
    @patch('apps.ai_integration.services.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('apps.ai_integration.services.get_catalog')
    @patch('apps.ai_integration.services.incr')
    def test_successful_reprompt(self, mock_incr, mock_get_catalog, mock_get_allowed):
        """Test successful resolution after reprompt"""
        generator = WorkoutPlanGenerator()
        
        # Setup
        allowed_slugs = {'push-ups', 'squats'}
        mock_get_allowed.return_value = allowed_slugs
        
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog
        
        # First attempt has unresolved, second attempt succeeds
        mock_catalog.find_similar.side_effect = [
            [],  # No substitute for deadlifts (first attempt)
            ['squats'],  # Found substitute (second attempt)
        ]
        
        # Mock AI responses
        mock_ai_client = Mock()
        generator.ai_client = mock_ai_client
        
        # First response has disallowed exercise
        first_response = {
            'plan_name': 'Test Plan',
            'weeks': [{
                'days': [{
                    'exercises': [{'exercise_slug': 'deadlifts'}]
                }]
            }]
        }
        
        # Second response uses allowed exercise
        second_response = {
            'plan_name': 'Test Plan',
            'weeks': [{
                'days': [{
                    'exercises': [{'exercise_slug': 'squats'}]
                }]
            }]
        }
        
        mock_ai_client.generate_completion.side_effect = [
            first_response,
            second_response
        ]
        
        # Mock _validate_and_enhance_plan to return as-is
        with patch.object(generator, '_validate_and_enhance_plan') as mock_validate:
            mock_validate.side_effect = lambda x, y: x
            
            # Execute
            result = generator.generate_plan({'archetype': 'peer'})
        
        # Verify reprompt happened
        mock_incr.assert_any_call('ai.plan.reprompted')
        self.assertEqual(mock_ai_client.generate_completion.call_count, 2)
        
        # Verify final result
        self.assertEqual(result['weeks'][0]['days'][0]['exercises'][0]['exercise_slug'], 'squats')
    
    @patch('apps.ai_integration.services.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('apps.ai_integration.services.get_catalog')
    @patch('apps.ai_integration.services.incr')
    def test_reprompt_limit_exceeded(self, mock_incr, mock_get_catalog, mock_get_allowed):
        """Test failure when reprompt limit exceeded"""
        generator = WorkoutPlanGenerator()
        
        # Setup
        allowed_slugs = {'push-ups'}
        mock_get_allowed.return_value = allowed_slugs
        
        mock_catalog = Mock()
        mock_catalog.find_similar.return_value = []  # Never finds substitute
        mock_get_catalog.return_value = mock_catalog
        
        # Mock AI always returns disallowed exercise
        mock_ai_client = Mock()
        generator.ai_client = mock_ai_client
        mock_ai_client.generate_completion.return_value = {
            'weeks': [{
                'days': [{
                    'exercises': [{'exercise_slug': 'deadlifts'}]
                }]
            }]
        }
        
        # Execute and expect failure
        with self.assertRaises(ValueError) as context:
            generator.generate_plan({'archetype': 'peer'})
        
        self.assertIn('Unable to generate valid plan', str(context.exception))
        
        # Verify metrics
        mock_incr.assert_any_call('ai.plan.validation_failed')
        
        # Verify attempted max times (initial + 2 reprompts)
        self.assertEqual(mock_ai_client.generate_completion.call_count, 3)