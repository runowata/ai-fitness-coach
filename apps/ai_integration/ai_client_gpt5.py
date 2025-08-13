"""AI client interfaces for GPT-5 with Responses API and Structured Outputs support"""
import json
import logging
from typing import Dict

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


class OpenAIClient:
    """OpenAI API client with GPT-5 and Responses API support"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIClientError("OPENAI_API_KEY not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = getattr(settings, 'OPENAI_MODEL', 'gpt-5')
        
        # Validate model is supported
        allowed_models = {"gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06"}
        if self.default_model not in allowed_models:
            raise AIClientError(f"Unsupported OPENAI_MODEL: {self.default_model}. Allowed: {allowed_models}")
        
        logger.info(f"Initialized OpenAI client with model: {self.default_model}")
        logger.info(f"GPT-5 features enabled: {self.default_model.startswith('gpt-5')}")
    
    def generate_completion(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> Dict:
        """Generate completion using GPT-5 with Structured Outputs"""
        try:
            logger.info(f"Generating completion with {self.default_model}")
            response = self._make_structured_api_call(prompt, max_tokens, temperature)
            return response
        except Exception as e:
            logger.error(f"GPT-5 completion generation failed: {str(e)}")
            raise AIClientError(f"Failed to generate GPT-5 response: {str(e)}")
    
    def generate_workout_plan(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> WorkoutPlan:
        """Generate and validate workout plan using GPT-5 with Structured Outputs"""
        try:
            logger.info(f"Generating workout plan with {self.default_model} using {'Responses API' if self.default_model.startswith('gpt-5') else 'Chat Completions API'}")
            response = self._make_structured_api_call(prompt, max_tokens, temperature)
            
            # Convert dict back to JSON string for validation
            raw_json = json.dumps(response)
            
            # Validate with strict schema
            validated_plan = validate_ai_plan_response(raw_json)
            
            logger.info(f"Successfully validated GPT-5 workout plan: {validated_plan.plan_name}, "
                       f"{validated_plan.duration_weeks} weeks, "
                       f"{sum(len(w.days) for w in validated_plan.weeks)} days, "
                       f"Model: {self.default_model}")
            
            return validated_plan
            
        except Exception as e:
            logger.error(f"GPT-5 workout plan generation/validation failed: {str(e)}")
            raise AIClientError(f"Failed to generate valid GPT-5 workout plan: {str(e)}")
    
    def generate_comprehensive_report(
        self, 
        prompt: str, 
        user_id: str = None, 
        archetype: str = None,
        max_tokens: int = 12288, 
        temperature: float = 0.7
    ) -> ComprehensiveAIReport:
        """Generate comprehensive report using GPT-5 with higher reasoning"""
        try:
            if self.default_model.startswith('gpt-5'):
                # Use GPT-5 with higher reasoning effort for comprehensive reports
                response = self.client.responses.create(
                    model=self.default_model,
                    input=[
                        {
                            "role": "developer", 
                            "content": "You are a professional fitness coach AI generating comprehensive analysis reports. Create a detailed 4-block report with user analysis, training program, motivation system, and long-term strategy."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    reasoning={
                        'effort': 'medium'  # Higher reasoning for comprehensive analysis
                    },
                    text={
                        'verbosity': 'high',  # Detailed output for comprehensive reports
                        'format': {
                            'name': 'json_schema',
                            'schema': {
                                'name': 'comprehensive_report',
                                'strict': False,
                                'schema': {
                                    "type": "object",
                                    "properties": {
                                        "user_analysis": {"type": "string"},
                                        "training_program": {"type": "string"}, 
                                        "motivation_system": {"type": "string"},
                                        "long_term_strategy": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                )
                
                # Extract content
                content = None
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content = content_item.text
                                break
                        if content:
                            break
                
                if not content:
                    raise AIClientError("No content in GPT-5 response")
                
                # Parse and validate
                parsed_json = json.loads(content)
                raw_json = json.dumps(parsed_json)
                validated_report = validate_comprehensive_ai_report(raw_json)
                
                logger.info(f"Successfully generated GPT-5 comprehensive report for archetype: {archetype}")
                return validated_report
            else:
                # Fallback to legacy client for non-GPT-5 models
                logger.warning("Using legacy approach for non-GPT-5 comprehensive reports")
                from .ai_client import OpenAIClient as LegacyClient
                legacy_client = LegacyClient()
                return legacy_client.generate_comprehensive_report(prompt, user_id, archetype, max_tokens, temperature)
                
        except Exception as e:
            logger.error(f"GPT-5 comprehensive report generation failed: {str(e)}")
            raise AIClientError(f"Failed to generate GPT-5 comprehensive report: {str(e)}")
    
    def _make_structured_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Make API call using GPT-5 with Responses API and Structured Outputs"""
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
            
            # Use new Responses API with GPT-5
            if self.default_model.startswith('gpt-5'):
                # GPT-5 with Responses API and full Structured Outputs
                api_params = {
                    'model': self.default_model,
                    'input': [
                        {"role": "developer", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    'reasoning': {
                        'effort': 'minimal'  # Fast response for workout generation
                    },
                    'text': {
                        'verbosity': 'low',  # Concise output
                        'format': {
                            'name': 'json_schema',
                            'schema': {
                                'name': 'workout_plan',
                                'strict': True,
                                'schema': workout_plan_schema
                            }
                        }
                    }
                }
            else:
                # Fallback for other models using Chat Completions API
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
            
            for attempt in range(3):
                try:
                    if self.default_model.startswith('gpt-5'):
                        response = self.client.responses.create(**api_params)
                    else:
                        response = self.client.chat.completions.create(**api_params)
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
            
            if response is None:
                raise AIClientError(f"OpenAI request failed after 3 retries: {last_error}")
            
            # Extract content based on API type
            if self.default_model.startswith('gpt-5'):
                # Responses API format
                content = None
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content = content_item.text
                                break
                        if content:
                            break
                            
                # Check for refusals in Responses API
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'type') and content_item.type == 'refusal':
                                logger.error(f"AI model refused request: {content_item.refusal}")
                                raise AIClientError(f"AI model refused the request: {content_item.refusal}")
            else:
                # Chat Completions API format
                if response.choices[0].message.refusal:
                    logger.error(f"AI model refused request: {response.choices[0].message.refusal}")
                    raise AIClientError(f"AI model refused the request: {response.choices[0].message.refusal}")
                content = response.choices[0].message.content
            
            if not content or content.strip() == "":
                raise AIClientError("AI response is empty")
                
            logger.info(f"Raw AI response (first 500 chars): {content[:500]}")
            
            # Parse JSON - guaranteed to be valid with Structured Outputs
            try:
                parsed_json = json.loads(content)
                logger.info(f"Successfully parsed GPT-5 structured JSON with keys: {list(parsed_json.keys())}")
                logger.info(f"Model: {self.default_model}, Response API used: {'Responses' if self.default_model.startswith('gpt-5') else 'Chat Completions'}")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse structured JSON: {str(e)}")
                logger.error(f"Content was: {content[:1000]}")
                raise AIClientError(f"Structured output parsing failed: {str(e)}")
                
        except Exception as e:
            logger.error(f"GPT-5 structured API call failed: {str(e)}")
            raise AIClientError(f"Failed to generate GPT-5 structured response: {str(e)}")


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