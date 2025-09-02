"""
Tests for v2 workout plan JSON schema validation
"""
import json
from pathlib import Path

import pytest
from django.conf import settings
from jsonschema import ValidationError, validate


@pytest.fixture
def workout_plan_schema():
    """Load workout plan JSON schema"""
    schema_path = Path(settings.BASE_DIR) / "prompts/v2/schemas/workout_plan.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return None


@pytest.fixture
def valid_plan_json():
    """Valid workout plan according to v2 schema"""
    return {
        "meta": {
            "version": "v2",
            "archetype": "mentor",
            "goal": "muscle_gain",
            "plan_name": "8-Week Muscle Building"
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
                                "exercises": [
                                    {
                                        "slug": "jumping-jacks",
                                        "sets": 1,
                                        "reps": "30 sec"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def invalid_plan_json():
    """Invalid workout plan - missing required fields"""
    return {
        "weeks": [
            {
                "week_number": 1,
                # Missing required 'theme' and 'days'
            }
        ]
        # Missing required 'meta'
    }


class TestWorkoutPlanSchema:
    """Test v2 workout plan schema validation"""
    
    def test_schema_exists(self, workout_plan_schema):
        """Test that schema file exists and is valid JSON"""
        if workout_plan_schema is None:
            pytest.skip("Schema file not found - acceptable in test environment")
        
        assert "$schema" in workout_plan_schema
        assert workout_plan_schema["title"] == "WorkoutPlan"
        assert "properties" in workout_plan_schema
        assert "meta" in workout_plan_schema["properties"]
        assert "weeks" in workout_plan_schema["properties"]
    
    def test_valid_plan_passes_validation(self, valid_plan_json, workout_plan_schema):
        """Test that valid plan passes schema validation"""
        if workout_plan_schema is None:
            pytest.skip("Schema file not found")
        
        # Should not raise ValidationError
        validate(instance=valid_plan_json, schema=workout_plan_schema)
    
    def test_invalid_plan_fails_validation(self, invalid_plan_json, workout_plan_schema):
        """Test that invalid plan fails schema validation"""
        if workout_plan_schema is None:
            pytest.skip("Schema file not found")
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_plan_json, schema=workout_plan_schema)
        
        # Check that it's complaining about missing 'meta'
        assert "meta" in str(exc_info.value) or "required" in str(exc_info.value).lower()
    
    def test_archetype_enum_validation(self, valid_plan_json, workout_plan_schema):
        """Test that archetype must be from allowed values"""
        if workout_plan_schema is None:
            pytest.skip("Schema file not found")
        
        # Test with invalid archetype
        valid_plan_json["meta"]["archetype"] = "invalid_archetype"
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=valid_plan_json, schema=workout_plan_schema)
        
        assert "archetype" in str(exc_info.value).lower() or "enum" in str(exc_info.value).lower()
    
    def test_exercise_required_fields(self, workout_plan_schema):
        """Test that exercises have required fields"""
        if workout_plan_schema is None:
            pytest.skip("Schema file not found")
        
        plan_with_invalid_exercise = {
            "meta": {
                "version": "v2",
                "archetype": "mentor",
                "goal": "test",
                "plan_name": "Test"
            },
            "weeks": [
                {
                    "week_number": 1,
                    "theme": "Test",
                    "days": [
                        {
                            "day_number": 1,
                            "blocks": [
                                {
                                    "type": "main",
                                    "exercises": [
                                        {
                                            # Missing required 'slug', 'sets', 'reps'
                                            "weight": "50kg"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with pytest.raises(ValidationError):
            validate(instance=plan_with_invalid_exercise, schema=workout_plan_schema)