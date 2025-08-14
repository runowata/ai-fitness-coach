"""
Builder functions for GPT-5 Responses API payload construction
Handles proper parameter formatting for GPT-5 Responses API vs Chat Completions API
"""
import logging
from typing import Dict

from django.conf import settings

from .schemas_json import WORKOUT_PLAN_JSON_SCHEMA

logger = logging.getLogger(__name__)


def build_responses_payload(
    prompt: str, 
    system_message: str = None, 
    max_tokens: int = 8192, 
    temperature: float = 0.7, 
    model: str = None
) -> Dict:
    """
    Build API payload based on model type (GPT-5 Responses API vs Chat Completions API)
    
    Args:
        prompt: User prompt for workout generation
        system_message: System prompt (optional)
        max_tokens: Maximum tokens for response
        temperature: Response randomness (0.0 to 1.0)
        model: Model to use (defaults to settings.OPENAI_MODEL)
        
    Returns:
        Dictionary with correct API parameters for the model
    """
    if model is None:
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-5')
    
    if system_message is None:
        system_message = """You are a professional fitness coach AI. Create a personalized workout plan based on the user's requirements. Generate ALL weeks requested (typically 4-8 weeks). Each week MUST have 7 days. Include rest days as appropriate."""
    
    # Use the corrected JSON Schema with blocks structure
    workout_plan_schema = WORKOUT_PLAN_JSON_SCHEMA
    
    if model.startswith('gpt-5'):
        # GPT-5 Responses API - uses 'text.format' parameter structure
        logger.info(f"Building Responses API payload for model: {model}")
        payload = {
            'model': model,
            'input': [
                {"role": "developer", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            'reasoning': {
                'effort': 'minimal'  # Fast response for workout generation
            },
            'text': {
                'verbosity': 'medium',
                'format': {
                    'type': 'json_schema',
                    'name': 'WorkoutPlan',
                    'json_schema': workout_plan_schema,
                    'strict': True
                }
            }
        }
        logger.debug("Created Responses API payload with text.format structure")
    else:
        # Chat Completions API - uses 'response_format' parameter
        logger.info(f"Building Chat Completions API payload for model: {model}")
        payload = {
            'model': model,
            'messages': [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            'max_tokens': min(max_tokens, getattr(settings, 'OPENAI_MAX_TOKENS', 16384)),
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
        logger.debug("Created Chat Completions API payload with response_format structure")
    
    return payload


def build_comprehensive_payload(
    prompt: str,
    system_message: str = None,
    max_tokens: int = 12288,
    temperature: float = 0.7,
    model: str = None
) -> Dict:
    """
    Build API payload for comprehensive AI reports with higher reasoning effort
    
    Args:
        prompt: User prompt for comprehensive analysis
        system_message: System prompt (optional)
        max_tokens: Maximum tokens for response
        temperature: Response randomness (0.0 to 1.0)
        model: Model to use (defaults to settings.OPENAI_MODEL)
        
    Returns:
        Dictionary with correct API parameters for comprehensive reports
    """
    if model is None:
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-5')
    
    if system_message is None:
        system_message = """You are a professional fitness coach AI generating comprehensive analysis reports. Create a detailed 4-block report with user analysis, training program, motivation system, and long-term strategy."""
    
    # Comprehensive report schema (simplified for flexibility)
    report_schema = {
        "type": "object",
        "properties": {
            "meta": {"type": "object"},
            "user_analysis": {"type": "object"},
            "training_program": {"type": "object"},
            "motivation_system": {"type": "object"},
            "long_term_strategy": {"type": "object"}
        },
        "required": ["meta", "user_analysis", "training_program", "motivation_system", "long_term_strategy"]
    }
    
    if model.startswith('gpt-5'):
        # GPT-5 Responses API with higher reasoning effort for comprehensive reports
        logger.info(f"Building comprehensive Responses API payload for model: {model}")
        payload = {
            'model': model,
            'input': [
                {"role": "developer", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            'reasoning': {
                'effort': 'medium'  # Higher reasoning for comprehensive analysis
            },
            'text': {
                'verbosity': 'high',
                'format': {
                    'type': 'json_schema',
                    'name': 'ComprehensiveReport',
                    'json_schema': report_schema,
                    'strict': False  # More flexible for comprehensive reports
                }
            }
        }
        logger.debug("Created comprehensive Responses API payload with medium reasoning effort")
    else:
        # Chat Completions API fallback for comprehensive reports
        logger.info(f"Building comprehensive Chat Completions API payload for model: {model}")
        payload = {
            'model': model,
            'messages': [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            'max_tokens': min(max_tokens, getattr(settings, 'OPENAI_MAX_TOKENS', 16384)),
            'temperature': temperature,
            'response_format': {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'comprehensive_report',
                    'strict': False,
                    'schema': report_schema
                }
            }
        }
        logger.debug("Created comprehensive Chat Completions API payload")
    
    return payload