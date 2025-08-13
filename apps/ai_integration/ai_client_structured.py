"""AI client interfaces for OpenAI with Structured Outputs support"""
import json
import logging
from typing import Dict, Optional

from django.conf import settings
from openai import OpenAI

from .schemas import (
    ComprehensiveAIReport,
    WorkoutPlan,
    validate_ai_plan_response,
    validate_comprehensive_ai_report,
)

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Custom exception for AI client errors"""
    pass


class OpenAIClient:
    """OpenAI API client with Structured Outputs support"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIClientError("OPENAI_API_KEY not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = getattr(settings, 'OPENAI_MODEL', 'o1')
        
        # Validate model is supported
        allowed_models = {"o1", "o1-mini", "o1-preview", "gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06"}
        if self.default_model not in allowed_models:
            raise AIClientError(f"Unsupported OPENAI_MODEL: {self.default_model}. Allowed: {allowed_models}")
    
    def generate_completion(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> Dict:
        """Generate completion from OpenAI API using Structured Outputs"""
        try:
            response = self._make_structured_api_call(prompt, max_tokens, temperature)
            return response
        except Exception as e:
            logger.error(f"Completion generation failed: {str(e)}")
            raise AIClientError(f"Failed to generate AI response: {str(e)}")
    
    def generate_workout_plan(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> WorkoutPlan:
        """Generate and validate workout plan with Structured Outputs"""
        try:
            response = self._make_structured_api_call(prompt, max_tokens, temperature)
            
            # Convert dict back to JSON string for validation
            raw_json = json.dumps(response)
            
            # Validate with strict schema
            validated_plan = validate_ai_plan_response(raw_json)
            
            logger.info(f"Successfully validated workout plan: {validated_plan.plan_name}, "
                       f"{validated_plan.duration_weeks} weeks, "
                       f"{sum(len(w.days) for w in validated_plan.weeks)} days")
            
            return validated_plan
            
        except Exception as e:
            logger.error(f"Workout plan generation/validation failed: {str(e)}")
            raise AIClientError(f"Failed to generate valid workout plan: {str(e)}")
    
    def generate_comprehensive_report(
        self, 
        prompt: str, 
        user_id: str = None, 
        archetype: str = None,
        max_tokens: int = 12288, 
        temperature: float = 0.7
    ) -> ComprehensiveAIReport:
        """Generate comprehensive report - fallback to legacy for now"""
        logger.warning("Comprehensive reports using legacy approach temporarily")
        # Import the legacy client for comprehensive reports
        from .ai_client import OpenAIClient as LegacyClient
        legacy_client = LegacyClient()
        return legacy_client.generate_comprehensive_report(prompt, user_id, archetype, max_tokens, temperature)
    
    def _make_structured_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Make API call using OpenAI Structured Outputs"""
        try:
            # Define JSON Schema for workout plan
            workout_plan_schema = {
                "type": "object",
                "properties": {
                    "plan_name": {"type": "string"},
                    "duration_weeks": {"type": "integer"},
                    "goal": {"type": "string"},
                    "weeks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "week_number": {"type": "integer"},
                                "week_focus": {"type": "string"},
                                "days": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "day_number": {"type": "integer"},
                                            "workout_name": {"type": "string"},
                                            "is_rest_day": {"type": "boolean"},
                                            "exercises": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "exercise_slug": {"type": "string"},
                                                        "sets": {"type": "integer"},
                                                        "reps": {"type": "string"},
                                                        "rest_seconds": {"type": "integer"}
                                                    },
                                                    "required": ["exercise_slug", "sets", "reps", "rest_seconds"],
                                                    "additionalProperties": False
                                                }
                                            },
                                            "confidence_task": {"type": "string"}
                                        },
                                        "required": ["day_number", "workout_name", "is_rest_day", "exercises", "confidence_task"],
                                        "additionalProperties": False
                                    }
                                }
                            },
                            "required": ["week_number", "week_focus", "days"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["plan_name", "duration_weeks", "goal", "weeks"],
                "additionalProperties": False
            }

            system_message = """You are a professional fitness coach AI. Create a personalized workout plan based on the user's requirements. Generate ALL weeks requested (typically 4-8 weeks). Each week MUST have 7 days. Include rest days as appropriate."""

            # Add retry logic
            import time
            last_error = None
            response = None
            
            # Check if model supports Structured Outputs
            supports_structured_outputs = self.default_model in ["gpt-4o-2024-08-06", "gpt-4o-mini", "gpt-4o-mini-2024-07-18"]
            
            if supports_structured_outputs:
                # Use full Structured Outputs
                api_params = {
                    'model': self.default_model,
                    'messages': [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    'max_tokens': min(max_tokens, settings.OPENAI_MAX_TOKENS),
                    'temperature': temperature,
                    'response_format': {
                        'type': 'json_schema',
                        'json_schema': {
                            'name': 'workout_plan',
                            'strict': True,
                            'schema': workout_plan_schema
                        }
                    }
                }
            elif self.default_model.startswith('o1'):
                # Use JSON mode for o1 models
                combined_prompt = f"{system_message}\n\nIMPORTANT: Return response as valid JSON matching the workout plan structure.\n\nUSER REQUEST:\n{prompt}"
                api_params = {
                    'model': self.default_model,
                    'messages': [
                        {"role": "user", "content": combined_prompt}
                    ],
                    'max_completion_tokens': min(max_tokens, settings.OPENAI_MAX_TOKENS),
                    'response_format': {'type': 'json_object'}
                }
            else:
                # Use JSON mode for other models
                system_with_json = f"{system_message}\n\nIMPORTANT: Return response as valid JSON matching the workout plan structure."
                api_params = {
                    'model': self.default_model,
                    'messages': [
                        {"role": "system", "content": system_with_json},
                        {"role": "user", "content": prompt}
                    ],
                    'max_tokens': min(max_tokens, settings.OPENAI_MAX_TOKENS),
                    'temperature': temperature,
                    'response_format': {'type': 'json_object'}
                }
            
            for attempt in range(3):
                try:
                    response = self.client.chat.completions.create(**api_params)
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
            
            if response is None:
                raise AIClientError(f"OpenAI request failed after 3 retries: {last_error}")
            
            # Handle refusals
            if response.choices[0].message.refusal:
                logger.error(f"AI model refused request: {response.choices[0].message.refusal}")
                raise AIClientError(f"AI model refused the request: {response.choices[0].message.refusal}")
            
            # Get response content
            content = response.choices[0].message.content
            
            if not content or content.strip() == "":
                raise AIClientError("AI response is empty")
                
            logger.info(f"Raw AI response (first 500 chars): {content[:500]}")
            
            # Parse JSON
            try:
                parsed_json = json.loads(content)
                logger.info(f"Successfully parsed JSON with keys: {list(parsed_json.keys())}")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                logger.error(f"Content was: {content[:1000]}")
                raise AIClientError(f"JSON parsing failed: {str(e)}")
                
        except Exception as e:
            logger.error(f"Structured API call failed: {str(e)}")
            raise AIClientError(f"Failed to generate structured response: {str(e)}")


class AIClientFactory:
    """Factory for creating AI clients"""
    
    @staticmethod
    def create_client(provider: str = None):
        """Create AI client based on provider"""
        if provider is None:
            provider = getattr(settings, 'AI_PROVIDER', 'openai')
        
        if provider.lower() == 'openai':
            return OpenAIClient()
        else:
            raise AIClientError(f"Unsupported AI provider: {provider}")