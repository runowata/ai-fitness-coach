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
        self.default_model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Generate completion from OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are a professional fitness coach AI. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise AIClientError(f"Failed to generate AI response: {str(e)}")
    
    def parse_json_response(self, response_text: str) -> Dict:
        """Parse and validate JSON response from AI"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise AIClientError(f"Invalid JSON response from AI: {str(e)}")


class AnthropicClient:
    """Anthropic Claude API client (placeholder for future implementation)"""
    
    def __init__(self):
        # Future implementation for Anthropic
        pass
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate completion from Anthropic API"""
        raise NotImplementedError("Anthropic client not yet implemented")


class AIClientFactory:
    """Factory for creating AI clients"""
    
    @staticmethod
    def create_client(provider: str = None):
        """Create AI client based on provider"""
        if provider is None:
            provider = getattr(settings, 'AI_PROVIDER', 'openai')
        
        if provider.lower() == 'openai':
            return OpenAIClient()
        elif provider.lower() == 'anthropic':
            return AnthropicClient()
        else:
            raise AIClientError(f"Unsupported AI provider: {provider}")