"""
Builder functions for GPT-5 Responses API payload construction
Handles proper parameter formatting for GPT-5 Responses API vs Chat Completions API
"""
import logging
from typing import Dict

from django.conf import settings

from .schemas_json import WORKOUT_PLAN_JSON_SCHEMA

logger = logging.getLogger(__name__)


def build_responses_payload(prompt: str, model: str, max_tokens: int, temperature: float, schema: dict):
    payload = {
        "model": model,
        "input": [
            {"role": "developer", "content": "You are a professional fitness coach AI."},
            {"role": "user", "content": prompt},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "WorkoutPlan",
                "schema": schema,
                "strict": True,
            }
        },
        "max_output_tokens": max_tokens,
    }
    
    # GPT-5 Responses API doesn't support temperature parameter
    # Only default temperature (1.0) is supported
    if not model.startswith('gpt-5'):
        payload["temperature"] = temperature
    
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
                'effort': getattr(settings, 'OPENAI_REASONING_EFFORT', 'medium')  # Configurable reasoning effort
            },
            'text': {
                'verbosity': getattr(settings, 'OPENAI_TEXT_VERBOSITY', 'low'),  # Configurable verbosity
                'format': {
                    'type': 'json_schema',
                    'name': 'ComprehensiveReport',
                    'schema': report_schema,
                    'strict': False  # More flexible for comprehensive reports
                }
            },
            'max_output_tokens': max_tokens,
        }
        # GPT-5 Responses API doesn't support temperature parameter
        # Note: temperature parameter removed for GPT-5 compatibility
        logger.debug(f"Created comprehensive Responses API payload: reasoning={payload['reasoning']['effort']}, verbosity={payload['text']['verbosity']}, max_tokens={max_tokens}")
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