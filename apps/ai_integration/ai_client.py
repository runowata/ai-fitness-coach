"""AI client interfaces for OpenAI and Anthropic"""
import json
import logging
from typing import Dict, Optional

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Custom exception for AI client errors"""
    pass


class OpenAIClient:
    """OpenAI API client with error handling"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIClientError("OPENAI_API_KEY not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = getattr(settings, 'OPENAI_MODEL', 'o1')
    
    def generate_completion(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.7) -> Dict:
        """Generate completion from OpenAI API for o1 model"""
        try:
            # For o1 models, use simple approach without response_format
            # o1 models have reasoning capabilities and follow JSON instructions well
            system_message = """You are a professional fitness coach AI. Create a workout plan following EXACTLY this JSON structure.

CRITICAL: Return ONLY the JSON below with NO additional fields, NO markdown, NO explanations.

{
    "plan_name": "string",
    "duration_weeks": number,
    "goal": "string",
    "weeks": [
        {
            "week_number": number,
            "week_focus": "string",
            "days": [
                {
                    "day_number": number,
                    "workout_name": "string",
                    "is_rest_day": boolean,
                    "exercises": [
                        {
                            "exercise_slug": "string",
                            "sets": number,
                            "reps": "string",
                            "rest_seconds": number
                        }
                    ],
                    "confidence_task": "string"
                }
            ]
        }
    ]
}

DO NOT add any extra fields like bro_intro, commander_briefing, trainer_motivation, etc.
Use ONLY the fields shown above."""

            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=240  # 4 minutes - safe buffer before gunicorn timeout
            )
            
            # Parse the JSON content directly
            content = response.choices[0].message.content.strip()
            
            # Log the raw response for debugging
            logger.info(f"Raw AI response (first 1000 chars): {content[:1000]}")
            
            # Remove any markdown formatting if present
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            # Try to parse JSON
            try:
                parsed_json = json.loads(content)
                logger.info(f"Successfully parsed JSON with keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                logger.error(f"Content that failed to parse: {content[:500]}")
                raise
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}, Content: {content[:500]}")
            raise AIClientError(f"AI response is not valid JSON: {str(e)}")
        except Exception as e:
            error_str = str(e).lower()
            if 'timeout' in error_str or 'timed out' in error_str:
                logger.error(f"OpenAI API timeout after 240 seconds: {str(e)}")
                raise AIClientError("AI service is taking too long to respond. Please try again in a few moments.")
            else:
                logger.error(f"OpenAI API error: {str(e)}")
                raise AIClientError(f"Failed to generate AI response: {str(e)}")


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