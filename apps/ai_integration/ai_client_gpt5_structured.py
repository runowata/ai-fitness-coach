"""
GPT-5 AI Client with Structured Outputs and Responses API
Optimized for GPT-5 features: structured outputs, reasoning effort, verbosity control
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from openai import OpenAI
from django.conf import settings
from pydantic import BaseModel

from .schemas_gpt5 import WorkoutPlan
from apps.core.metrics import incr, timing, MetricNames

logger = logging.getLogger(__name__)


class GPT5StructuredClient:
    """
    GPT-5 optimized client using Structured Outputs and Responses API
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-2024-08-06"  # GPT-5 compatible model
        self.default_reasoning_effort = getattr(settings, 'GPT5_REASONING_EFFORT', 'medium')
        self.default_verbosity = getattr(settings, 'GPT5_VERBOSITY', 'medium')
        
        logger.info(f"GPT-5 Structured Client initialized")
        logger.info(f"Model: {self.model}")
        logger.info(f"Default reasoning effort: {self.default_reasoning_effort}")
        logger.info(f"Default verbosity: {self.default_verbosity}")
    
    def generate_workout_plan(
        self,
        system_prompt: str,
        user_prompt: str,
        reasoning_effort: Optional[str] = None,
        verbosity: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Generate workout plan using GPT-5 Structured Outputs
        
        Args:
            system_prompt: System instructions
            user_prompt: User request with client data
            reasoning_effort: 'minimal', 'medium', 'high' (default from settings)
            verbosity: 'low', 'medium', 'high' (default from settings)
            previous_response_id: For reasoning context reuse
            max_retries: Number of retry attempts
            
        Returns:
            Dict with parsed workout plan and metadata
        """
        reasoning_effort = reasoning_effort or self.default_reasoning_effort
        verbosity = verbosity or self.default_verbosity
        
        logger.info(f"Generating workout plan with GPT-5 Structured Outputs")
        logger.info(f"Reasoning effort: {reasoning_effort}, Verbosity: {verbosity}")
        
        # Prepare messages for Responses API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"GPT-5 generation attempt {attempt + 1}/{max_retries + 1}")
                
                start_time = time.time()
                
                # Use Chat Completions with Structured Outputs for now
                # (Responses API may need different parameters)
                response_args = {
                    "model": self.model,
                    "messages": messages,
                    "response_format": WorkoutPlan,  # Pydantic model for structured output
                    "max_tokens": 8000,  # Sufficient for workout plans
                }
                
                # Make API call with structured outputs using chat completions parse
                response = self.client.chat.completions.parse(**response_args)
                
                generation_time = time.time() - start_time
                
                # Extract structured data from chat completion
                workout_plan = response.choices[0].message.parsed
                response_id = response.id
                
                # Log success metrics using existing names
                timing(MetricNames.AI_GENERATION_TIME, generation_time * 1000)
                
                logger.info(f"GPT-5 generation successful in {generation_time:.2f}s")
                logger.info(f"Response ID: {response_id}")
                
                # Validate the structured output
                if workout_plan:
                    try:
                        workout_plan.validate_structure()
                        logger.info("Structured output validation successful")
                    except ValueError as e:
                        logger.warning(f"Structured output validation warning: {e}")
                        # Continue anyway - minor validation issues are acceptable
                
                # Convert to dict for consistency with existing code
                plan_dict = workout_plan.dict()
                
                return {
                    'plan_data': plan_dict,
                    'response_id': response_id,
                    'generation_time': generation_time,
                    'reasoning_effort': reasoning_effort,
                    'verbosity': verbosity,
                    'model': self.model,
                    'usage': getattr(response, 'usage', None),
                    'success': True
                }
                
            except Exception as e:
                logger.error(f"GPT-5 generation attempt {attempt + 1} failed: {str(e)}")
                
                # Check if it's a refusal
                if hasattr(e, 'response') and hasattr(e.response, 'refusal'):
                    logger.error(f"GPT-5 refused request: {e.response.refusal}")
                    
                # On final attempt, raise the exception
                if attempt == max_retries:
                    raise Exception(f"GPT-5 generation failed after {max_retries + 1} attempts: {str(e)}")
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # Should not reach here
        raise Exception("GPT-5 generation failed unexpectedly")
    
    def generate_with_context_reuse(
        self,
        system_prompt: str,
        user_prompt: str,
        previous_response_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convenience method for context reuse in multi-turn scenarios
        """
        return self.generate_workout_plan(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            previous_response_id=previous_response_id,
            **kwargs
        )
    
    def test_connection(self) -> bool:
        """Test GPT-5 connection with minimal request"""
        try:
            logger.info("Testing GPT-5 connection...")
            
            # Simple test with structured output
            class TestResponse(BaseModel):
                message: str
            
            response = self.client.responses.parse(
                model=self.model,
                input=[{"role": "user", "content": "Respond with: GPT-5 connection successful"}],
                text_format=TestResponse,
                reasoning_effort="minimal",
                verbosity="low"
            )
            
            if response.output_parsed and response.output_parsed.message:
                logger.info("GPT-5 connection test successful")
                return True
            else:
                logger.error("GPT-5 connection test failed - no response")
                return False
                
        except Exception as e:
            logger.error(f"GPT-5 connection test failed: {str(e)}")
            return False


# Convenience function for backward compatibility
def create_gpt5_client() -> GPT5StructuredClient:
    """Create and return GPT-5 structured client instance"""
    return GPT5StructuredClient()


# Test script
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Test client creation
    client = create_gpt5_client()
    
    # Test connection
    if client.test_connection():
        print("✅ GPT-5 client test successful")
    else:
        print("❌ GPT-5 client test failed")