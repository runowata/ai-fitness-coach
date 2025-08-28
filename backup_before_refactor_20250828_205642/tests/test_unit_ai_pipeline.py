"""
Unit tests for AI pipeline validation and robust processing
"""

import json
from unittest.mock import Mock, patch

import pytest
from django.test import TestCase, override_settings

from apps.ai_integration.ai_client_gpt5 import AIClientFactory
from apps.ai_integration.services import WorkoutPlanGenerator


@pytest.mark.unit
class TestJSONExtraction(TestCase):
    """Test robust JSON extraction from AI responses"""
    
    def setUp(self):
        self.ai_client = AIClientFactory.create_client('openai')
    
    def test_extract_clean_json(self):
        """Test extraction of clean JSON"""
        clean_json = '{"plan_name": "Test Plan", "weeks": []}'
        
        result = self.ai_client._extract_json_robust(clean_json)
        
        self.assertEqual(result['plan_name'], 'Test Plan')
        self.assertEqual(result['weeks'], [])
    
    def test_extract_json_with_markdown(self):
        """Test extraction from markdown JSON block"""
        markdown_response = """
        Here's your workout plan:
        
        ```json
        {"plan_name": "Markdown Plan", "duration_weeks": 4}
        ```
        
        Hope this helps!
        """
        
        result = self.ai_client._extract_json_robust(markdown_response)
        
        self.assertEqual(result['plan_name'], 'Markdown Plan')
        self.assertEqual(result['duration_weeks'], 4)
    
    def test_extract_json_with_chatter(self):
        """Test extraction with surrounding chatter"""
        chatty_response = """
        I'll create a great plan for you! Here's what I recommend:
        
        {"plan_name": "Chatty Plan", "weeks": [{"week": 1}]}
        
        This plan focuses on building strength gradually.
        """
        
        result = self.ai_client._extract_json_robust(chatty_response)
        
        self.assertEqual(result['plan_name'], 'Chatty Plan')
        self.assertEqual(len(result['weeks']), 1)
    
    def test_extract_malformed_json_raises_error(self):
        """Test malformed JSON raises JSONDecodeError"""
        malformed = '{"plan_name": "Broken Plan", "weeks": ['  # Unclosed bracket
        
        with self.assertRaises(json.JSONDecodeError):
            self.ai_client._extract_json_robust(malformed)
    
    def test_extract_no_json_raises_error(self):
        """Test response with no JSON raises error"""
        no_json = "Sorry, I can't create a plan right now. Please try again later."
        
        with self.assertRaises(json.JSONDecodeError):
            self.ai_client._extract_json_robust(no_json)


@pytest.mark.unit
@override_settings(
    AI_REPROMPT_MAX_ATTEMPTS=1,
    FALLBACK_TO_LEGACY_FLOW=False
)
class TestWorkoutPlanGeneration(TestCase):
    """Test workout plan generation with validation"""
    
    def setUp(self):
        self.generator = WorkoutPlanGenerator()
        self.user_data = {
            'archetype': 'professional',
            'fitness_level': 'beginner',
            'available_days': [1, 2, 3, 4, 5],
            'session_duration': 45
        }
    
    @patch('apps.ai_integration.services.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('apps.core.metrics.incr')
    def test_whitelisting_and_substitutions(self, mock_incr, mock_get_allowed):
        """Test exercise whitelisting and substitutions work correctly"""
        # Setup allowed exercises
        allowed_slugs = {'push-ups', 'squats'}
        mock_get_allowed.return_value = allowed_slugs
        
        # Mock AI response with disallowed exercise
        plan_with_disallowed = {
            'plan_name': 'Test Plan',
            'weeks': [{
                'days': [{
                    'exercises': [
                        {'exercise_slug': 'push-ups'},  # Allowed
                        {'exercise_slug': 'bench-press'}  # Not allowed
                    ]
                }]
            }]
        }
        
        # Mock catalog to provide substitution
        with patch('apps.ai_integration.services.get_catalog') as mock_get_catalog:
            mock_catalog = Mock()
            mock_catalog.find_similar.return_value = ['squats']  # Substitute
            mock_get_catalog.return_value = mock_catalog
            
            # Mock AI client
            mock_ai_client = Mock()
            mock_ai_client.generate_completion.return_value = plan_with_disallowed
            self.generator.ai_client = mock_ai_client
            
            # Mock validation method
            with patch.object(self.generator, '_validate_and_enhance_plan') as mock_validate:
                mock_validate.side_effect = lambda x, y=None: x
                
                result = self.generator.generate_plan(self.user_data)
        
        # Should track substitutions
        mock_incr.assert_any_call('ai.plan.exercises_substituted', 1)
        
        # Should have substituted exercise
        exercises = result['weeks'][0]['days'][0]['exercises']
        exercise_slugs = [ex['exercise_slug'] for ex in exercises]
        self.assertIn('squats', exercise_slugs)  # Substituted
        self.assertNotIn('bench-press', exercise_slugs)  # Original removed
    
    @patch('apps.ai_integration.services.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('apps.core.metrics.incr')
    def test_reprompt_cycle_with_limit(self, mock_incr, mock_get_allowed):
        """Test reprompt cycle respects attempt limits"""
        allowed_slugs = {'push-ups'}
        mock_get_allowed.return_value = allowed_slugs
        
        # AI always returns disallowed exercise
        bad_plan = {
            'weeks': [{
                'days': [{
                    'exercises': [{'exercise_slug': 'bench-press'}]  # Never allowed
                }]
            }]
        }
        
        # Mock catalog with no substitutions
        with patch('apps.ai_integration.services.get_catalog') as mock_get_catalog:
            mock_catalog = Mock()
            mock_catalog.find_similar.return_value = []  # No substitutes
            mock_get_catalog.return_value = mock_catalog
            
            # Mock AI client
            mock_ai_client = Mock()
            mock_ai_client.generate_completion.return_value = bad_plan
            self.generator.ai_client = mock_ai_client
            
            # Should raise ValueError after max attempts
            with self.assertRaises(ValueError) as context:
                self.generator.generate_plan(self.user_data)
        
        self.assertIn('Unable to generate valid plan', str(context.exception))
        
        # Should track validation failure
        mock_incr.assert_any_call('ai.plan.validation_failed')
        
        # Should have made max attempts (1 initial + 1 reprompt = 2 total)
        self.assertEqual(mock_ai_client.generate_completion.call_count, 2)
    
    @override_settings(FALLBACK_TO_LEGACY_FLOW=True)
    @patch('apps.ai_integration.services.incr')
    def test_legacy_flow_fallback(self, mock_incr):
        """Test fallback to legacy flow when enabled"""
        with patch.object(self.generator, '_generate_plan_legacy') as mock_legacy:
            mock_legacy.return_value = {'plan_name': 'Legacy Plan'}
            
            result = self.generator.generate_plan(self.user_data)
        
        # Should use legacy method
        mock_legacy.assert_called_once_with(self.user_data)
        self.assertEqual(result['plan_name'], 'Legacy Plan')
    
    def test_build_prompt_with_whitelist(self):
        """Test prompt building includes exercise whitelist"""
        allowed_slugs = {'push-ups', 'squats', 'pull-ups'}
        
        prompt = self.generator._build_prompt_with_whitelist(self.user_data, allowed_slugs)
        
        # Should contain whitelist instruction
        self.assertIn('IMPORTANT: You MUST use ONLY exercises from this allowed list', prompt)
        
        # Should contain all allowed exercises
        for slug in allowed_slugs:
            self.assertIn(slug, prompt)
    
    def test_build_reprompt_with_corrections(self):
        """Test reprompt building with specific corrections"""
        original_prompt = "Generate a workout plan"
        unresolved = ['bench-press', 'deadlifts']
        allowed_slugs = {'push-ups', 'squats'}
        
        reprompt = self.generator._build_reprompt(original_prompt, unresolved, allowed_slugs)
        
        # Should contain correction instruction
        self.assertIn('CORRECTION NEEDED', reprompt)
        self.assertIn(original_prompt, reprompt)
        
        # Should mention specific problems
        for exercise in unresolved:
            self.assertIn(exercise, reprompt)
        
        # Should provide allowed alternatives
        for allowed in allowed_slugs:
            self.assertIn(allowed, reprompt)
    
    def test_enforce_allowed_exercises_preserves_allowed(self):
        """Test enforcement preserves allowed exercises unchanged"""
        plan_data = {
            'weeks': [{
                'days': [{
                    'exercises': [
                        {'exercise_slug': 'push-ups', 'sets': 3},
                        {'exercise_slug': 'squats', 'sets': 3}
                    ]
                }]
            }]
        }
        
        allowed_slugs = {'push-ups', 'squats'}
        
        result_plan, substitutions, unresolved = self.generator._enforce_allowed_exercises(
            plan_data, allowed_slugs
        )
        
        # Should preserve allowed exercises
        exercises = result_plan['weeks'][0]['days'][0]['exercises']
        self.assertEqual(len(exercises), 2)
        self.assertEqual(substitutions, 0)
        self.assertEqual(len(unresolved), 0)
        
        # Original data should be preserved
        self.assertEqual(exercises[0]['sets'], 3)


@pytest.mark.unit 
class TestPydanticValidation(TestCase):
    """Test Pydantic schema validation"""
    
    def setUp(self):
        self.ai_client = AIClientFactory.create_client('openai')
    
    @patch('apps.ai_integration.ai_client.openai')
    def test_valid_plan_passes_validation(self, mock_openai):
        """Test valid plan passes Pydantic validation"""
        valid_response = {
            'plan_name': 'Test Plan',
            'duration_weeks': 4,
            'weekly_frequency': 3,
            'session_duration': 45,
            'analysis': {
                'strengths': 'Good foundation',
                'challenges': 'Building consistency',
                'recommendations': 'Start gradually'
            },
            'weeks': [{
                'week': 1,
                'focus': 'Foundation',
                'days': [{
                    'day': 1,
                    'exercises': [{
                        'exercise_slug': 'push-ups',
                        'sets': 3,
                        'reps': 10
                    }]
                }]
            }]
        }
        
        # Mock OpenAI response
        mock_openai.chat.completions.create.return_value = Mock(
            choices=[Mock(
                message=Mock(
                    content=json.dumps(valid_response)
                )
            )]
        )
        
        # Should not raise validation error
        result = self.ai_client.generate_workout_plan("test prompt")
        
        self.assertEqual(result.plan_name, 'Test Plan')
        self.assertEqual(result.duration_weeks, 4)
    
    @patch('apps.ai_integration.ai_client.openai')
    def test_invalid_plan_raises_validation_error(self, mock_openai):
        """Test invalid plan raises ValidationError"""
        invalid_response = {
            'plan_name': 'Test Plan',
            # Missing required fields
            'weeks': []  # Empty weeks not allowed
        }
        
        # Mock OpenAI response  
        mock_openai.chat.completions.create.return_value = Mock(
            choices=[Mock(
                message=Mock(
                    content=json.dumps(invalid_response)
                )
            )]
        )
        
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self.ai_client.generate_workout_plan("test prompt")


@pytest.mark.integration
@override_settings(OPENAI_API_KEY='test-key')
def test_ai_client_factory():
    """Test AI client factory creates correct client types"""
    openai_client = AIClientFactory.create_client('openai')
    anthropic_client = AIClientFactory.create_client('anthropic')
    
    # Should return different client types
    assert type(openai_client).__name__ == 'OpenAIClient'
    assert type(anthropic_client).__name__ == 'AnthropicClient'
    
    # Should have required methods
    assert hasattr(openai_client, 'generate_workout_plan')
    assert hasattr(openai_client, '_extract_json_robust')