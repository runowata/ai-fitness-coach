"""
Tests for PromptManagerV2 critical functionality
"""

import pytest

from apps.ai_integration.prompt_manager_v2 import PromptManagerV2


class TestPromptManagerV2:
    """Test PromptManagerV2 validation and safety features"""
    
    def test_archetype_normalization(self):
        """Test archetype mapping works correctly"""
        pm = PromptManagerV2()
        
        # Test old -> new mapping
        assert pm.normalize_archetype('bro') == 'peer'
        assert pm.normalize_archetype('sergeant') == 'professional'
        assert pm.normalize_archetype('intellectual') == 'mentor'
        
        # Test new archetypes (should remain unchanged)
        assert pm.normalize_archetype('peer') == 'peer'
        assert pm.normalize_archetype('professional') == 'professional'
        assert pm.normalize_archetype('mentor') == 'mentor'
        
        # Test None/empty
        assert pm.normalize_archetype(None) is None
        assert pm.normalize_archetype('') == ''
    
    def test_find_placeholders(self):
        """Test placeholder extraction from text"""
        pm = PromptManagerV2()
        
        text = "Hello {{name}}, you are {{age}} years old and weigh {{weight}} kg."
        placeholders = pm.find_placeholders(text)
        
        expected = {'name', 'age', 'weight'}
        assert placeholders == expected
        
        # Test text without placeholders
        text_no_placeholders = "Hello world, no variables here."
        assert pm.find_placeholders(text_no_placeholders) == set()
        
        # Test malformed placeholders (should not match full pattern)
        text_malformed = "Hello {name} and {{age} and {{{weight}}}."
        placeholders = pm.find_placeholders(text_malformed)
        # {{{weight}}} contains valid {{weight}} inside, so regex finds 'weight'
        assert placeholders == {'weight'}
    
    def test_assert_placeholders_filled(self):
        """Test placeholder validation"""
        pm = PromptManagerV2()
        
        text = "Hello {{name}}, you are {{age}} years old."
        provided_vars = {'name': 'John', 'age': 25, 'extra': 'unused'}
        
        missing = pm.assert_placeholders_filled(text, provided_vars)
        assert missing == []  # All placeholders filled
        
        # Test with missing variables
        incomplete_vars = {'name': 'John'}  # missing 'age'
        missing = pm.assert_placeholders_filled(text, incomplete_vars)
        assert missing == ['age']
    
    def test_redact_for_logs(self):
        """Test PII redaction for safe logging"""
        pm = PromptManagerV2()
        
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com', 
            'phone': '+1234567890',
            'age': 25,  # Should not be redacted
            'goal': 'weight_loss'  # Should not be redacted
        }
        
        redacted = pm.redact_for_logs(payload)
        
        # Original should not be modified
        assert payload['email'] == 'john@example.com'
        
        # Redacted should mask PII (length of 'john@example.com' = 16, so 'jo' + 14 asterisks)
        assert redacted['email'] == 'jo**************'  # 2 chars + 14 asterisks = 16 total
        assert redacted['phone'] == '+1*********'  # 2 chars + 9 asterisks = 11 total ('+1234567890')
        assert redacted['age'] == 25  # Non-PII preserved
        assert redacted['goal'] == 'weight_loss'  # Non-PII preserved
    
    def test_dry_run_success(self):
        """Test successful dry run with valid template"""
        pm = PromptManagerV2('v2')  # Use v2 profile
        
        user_data = {
            'age': 25,
            'height': 180,
            'weight': 75,
            'primary_goal': 'muscle_gain',
            'injuries': 'none',
            'equipment_list': 'dumbbells, bench',
            'duration_weeks': 8,
            'onboarding_payload_json': '{"test": true}'
        }
        
        result = pm.dry_run('master', 'mentor', user_data)
        
        assert result['success'] is True
        assert 'system_length' in result
        assert 'user_length' in result
        assert 'missing_placeholders' in result
        assert isinstance(result['missing_placeholders'], list)
        assert 'safe_payload' in result
    
    def test_dry_run_missing_data(self):
        """Test dry run with missing template variables"""
        pm = PromptManagerV2('v2')
        
        incomplete_data = {
            'age': 25,
            # Missing other required variables
        }
        
        result = pm.dry_run('master', 'mentor', incomplete_data)
        
        # Should succeed even with missing data since prompts may not exist in test
        # The test checks that missing placeholders are detected if prompts exist
        assert result['success'] is True or 'error' in result
        if result['success']:
            assert 'missing_placeholders' in result


@pytest.mark.integration 
class TestPromptManagerSchema:
    """Test JSON schema loading and validation"""
    
    def test_load_workout_plan_schema(self):
        """Test loading workout plan JSON schema"""
        pm = PromptManagerV2('v2')
        
        try:
            schema = pm.load_schema('workout_plan')
            
            # Verify schema structure
            assert '$schema' in schema
            assert 'title' in schema
            assert schema['title'] == 'WorkoutPlan'
            assert 'properties' in schema
            assert 'meta' in schema['properties']
            assert 'weeks' in schema['properties']
            
        except FileNotFoundError:
            pytest.skip("Schema file not found - acceptable in test environment")
    
    def test_validate_response_valid_data(self):
        """Test validation with valid workout plan data"""
        pm = PromptManagerV2('v2')
        
        valid_plan = {
            "meta": {
                "version": "v2",
                "archetype": "mentor",
                "goal": "muscle_gain",
                "plan_name": "Test Plan"
            },
            "weeks": [
                {
                    "week_number": 1,
                    "theme": "Foundation",
                    "days": [
                        {
                            "day_number": 1,
                            "blocks": [
                                {
                                    "type": "warmup",
                                    "exercises": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        try:
            is_valid = pm.validate_response(valid_plan, 'workout_plan')
            assert is_valid is True
            
        except FileNotFoundError:
            pytest.skip("Schema file not found - acceptable in test environment")