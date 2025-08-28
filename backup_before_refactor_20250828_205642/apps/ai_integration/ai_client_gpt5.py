"""AI client interfaces for GPT-5 with Responses API and Structured Outputs support"""
import json
import logging
import time
from typing import Dict

import random
import httpx
from django.conf import settings
from openai import OpenAI, APITimeoutError, APIError

from .schemas import (
    ComprehensiveAIReport,
    WorkoutPlan,
    validate_ai_plan_response,
    validate_comprehensive_ai_report,
)
from .schemas_simple import SimpleWorkoutPlan, validate_simple_ai_plan
from .schemas_json_simple import WORKOUT_PLAN_JSON_SCHEMA_SIMPLE

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Custom exception for AI client errors"""


class ServiceTimeoutError(AIClientError):
    """Raised when OpenAI service times out"""


class ServiceCallError(AIClientError):
    """Raised when OpenAI service returns an error"""


class OpenAIClient:
    """OpenAI API client with GPT-5 and Responses API support"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIClientError("OPENAI_API_KEY not configured")
        
        # Set comprehensive timeouts (prevent hanging)
        self.connect_timeout = getattr(settings, 'OPENAI_CONNECT_TIMEOUT', 15)
        self.read_timeout = getattr(settings, 'OPENAI_READ_TIMEOUT', 600)  # GPT-5 needs more time for large plans
        self.total_timeout = getattr(settings, 'OPENAI_TOTAL_TIMEOUT', 720)  # overall limit
        self.max_retries = getattr(settings, 'OPENAI_MAX_RETRIES', 3)
        
        # Create httpx client with connection pooling and limits
        timeout = httpx.Timeout(
            timeout=self.total_timeout,
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=30,
            pool=self.total_timeout
        )
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
        self.httpx_client = httpx.Client(timeout=timeout, limits=limits)
        
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            http_client=self.httpx_client
        )
        self.default_model = getattr(settings, 'OPENAI_MODEL', 'gpt-5')
        
        # Validate model is supported - prioritize GPT-5 series
        gpt5_models = {"gpt-5", "gpt-5-mini", "gpt-5-nano"}
        legacy_models = {"gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06"}
        
        if self.default_model not in gpt5_models | legacy_models:
            raise AIClientError(f"Unsupported OPENAI_MODEL: {self.default_model}. GPT-5 models: {gpt5_models}")
        
        # Recommend GPT-5 if using legacy model
        if self.default_model in legacy_models:
            logger.warning(f"Using legacy model {self.default_model}. Consider upgrading to GPT-5 series for better performance.")
        
        logger.info(f"Initialized OpenAI client with model: {self.default_model}")
        logger.info(f"Timeouts: connect={self.connect_timeout}s, read={self.read_timeout}s, total={self.total_timeout}s")
        logger.info(f"Retries: max={self.max_retries}, connection pooling enabled")
        logger.info(f"GPT-5 features enabled: {self.default_model.startswith('gpt-5')}")
    
    def _with_retries(self, call_func, operation_name="OpenAI API call"):
        """Execute function with exponential backoff retries"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return call_func()
            except (httpx.ConnectError, httpx.ReadTimeout, APIError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"{operation_name} attempt {attempt + 1} failed: {str(e)}, retrying in {backoff:.1f}s")
                    time.sleep(backoff)
                else:
                    logger.error(f"{operation_name} failed after {self.max_retries} attempts: {str(e)}")
        
        # Convert to our specific exceptions
        if isinstance(last_error, (httpx.ConnectError, httpx.ReadTimeout)):
            raise ServiceTimeoutError(f"{operation_name} timeout after {self.max_retries} retries: {str(last_error)}")
        elif isinstance(last_error, APIError):
            raise ServiceCallError(f"{operation_name} error after {self.max_retries} retries: {str(last_error)}")
        else:
            raise ServiceCallError(f"{operation_name} failed: {str(last_error)}")
    
    def generate_completion(self, prompt: str, max_tokens: int = 8000, temperature: float = 0.7) -> Dict:
        """Generate completion using GPT-5 with Structured Outputs"""
        try:
            logger.info(f"Generating completion with {self.default_model}")
            response = self._make_structured_api_call(prompt, max_tokens, temperature)
            return response
        except Exception as e:
            logger.error(f"GPT-5 completion generation failed: {str(e)}")
            raise AIClientError(f"Failed to generate GPT-5 response: {str(e)}")
    
    def generate_workout_plan(self, prompt: str, max_tokens: int = 6000, temperature: float = 0.7) -> SimpleWorkoutPlan:
        """Generate and validate workout plan using GPT-5 with Structured Outputs"""
        try:
            logger.info(f"Generating workout plan with {self.default_model} using {'Responses API' if self.default_model.startswith('gpt-5') else 'Chat Completions API'}")
            response = self._make_structured_api_call(prompt, max_tokens, temperature)
            
            # Convert dict back to JSON string for validation
            raw_json = json.dumps(response)
            
            # Validate with simple schema
            validated_plan = validate_simple_ai_plan(raw_json)
            
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
        max_tokens: int = 32000,  # Maximum for comprehensive reports 
        temperature: float = 0.7
    ) -> ComprehensiveAIReport:
        """Generate comprehensive report using GPT-5 with higher reasoning"""
        start_time = time.time()
        try:
            if self.default_model.startswith('gpt-5'):
                from .builder import build_comprehensive_payload
                
                # Build comprehensive report payload
                api_params = build_comprehensive_payload(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=self.default_model
                )
                
                # Log and validate payload sizes for debugging  
                payload_bytes = len(json.dumps(api_params, ensure_ascii=False).encode('utf-8'))
                logger.info(f"Payload sizes: prompt={len(prompt)} chars, "
                           f"system={len(api_params.get('input', [{}])[0].get('content', ''))}, "
                           f"max_tokens={max_tokens}, total_bytes={payload_bytes}")
                
                # Validate payload size to prevent upstream errors
                if payload_bytes > 900_000:  # ~0.9 MB limit
                    raise ServiceCallError(f"Payload too large for AI request: {payload_bytes} bytes (max 900KB)")
                
                # Use GPT-5 with higher reasoning effort and retries
                try:
                    logger.info("Starting OpenAI API call for comprehensive report...")
                    response = self._with_retries(
                        lambda: self.client.responses.create(**api_params),
                        operation_name="GPT-5 comprehensive report"
                    )
                    duration = time.time() - start_time
                    logger.info(f"OpenAI call finished in {duration:.1f}s")
                    
                except (ServiceTimeoutError, ServiceCallError):
                    # These are already properly formatted by _with_retries
                    raise
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"Unexpected error during OpenAI call after {duration:.1f}s: {str(e)}")
                    raise ServiceCallError(f"Unexpected service error: {str(e)}")
                
                # Extract content
                content = None
                for item in response.output:
                    # Look for message type (contains actual response)
                    if item.type == 'message' and hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content = content_item.text
                                break
                        if content:
                            break
                    # Fallback: also check text type
                    elif item.type == 'text' and hasattr(item, 'content') and item.content:
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
                
                total_duration = time.time() - start_time
                logger.info(f"Successfully generated GPT-5 comprehensive report for archetype: {archetype} in {total_duration:.1f}s")
                return validated_report
            else:
                # Fallback to legacy client for non-GPT-5 models
                logger.warning("Using legacy approach for non-GPT-5 comprehensive reports")
                from .ai_client import OpenAIClient as LegacyClient
                legacy_client = LegacyClient()
                return legacy_client.generate_comprehensive_report(prompt, user_id, archetype, max_tokens, temperature)
                
        except AIClientError:
            # Re-raise our own errors without wrapping
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"GPT-5 comprehensive report generation failed after {duration:.1f}s: {str(e)}")
            raise AIClientError(f"Failed to generate GPT-5 comprehensive report: {str(e)}")
    
    def _make_structured_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Make API call using GPT-5 with Responses API and Structured Outputs"""
        try:
            import time
            start_time = time.time()
            
            from .builder import build_responses_payload

            # Build API payload using the builder function
            api_params = build_responses_payload(
                prompt=prompt,
                model=self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                schema=WORKOUT_PLAN_JSON_SCHEMA_SIMPLE,
            )

            # Add retry logic
            import time
            last_error = None
            response = None
            
            for attempt in range(3):
                try:
                    # All models should be GPT-5 series now
                    if not self.default_model.startswith('gpt-5'):
                        raise AIClientError(f"Only GPT-5 models supported, got: {self.default_model}")
                    response = self.client.responses.create(**api_params)
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
            
            if response is None:
                raise AIClientError(f"OpenAI request failed after 3 retries: {last_error}")
            
            # Extract content from Responses API (GPT-5 only)
            content = None
            for item in response.output:
                # Look for message type (contains actual response)
                if item.type == 'message' and hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            content = content_item.text
                            break
                    if content:
                        break
                # Fallback: also check text type  
                elif item.type == 'text' and hasattr(item, 'content') and item.content:
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
            
            if not content or content.strip() == "":
                raise AIClientError("AI response is empty")
                
            logger.info(f"Raw AI response (first 500 chars): {content[:500]}")
            
            # Parse JSON - guaranteed to be valid with Structured Outputs
            try:
                parsed_json = json.loads(content)
                
                # Calculate and log performance metrics
                duration = time.time() - start_time
                api_type = 'Responses' if self.default_model.startswith('gpt-5') else 'Chat Completions'
                
                logger.info(f"✅ GPT-5 generation completed in {duration:.1f}s")
                logger.info(f"📊 Model: {self.default_model}, API: {api_type}, max_tokens: {max_tokens}")
                logger.info(f"🔧 Successfully parsed JSON with keys: {list(parsed_json.keys())}")
                
                # Log token usage if available
                if hasattr(response, 'usage'):
                    # GPT-5 Responses API has different usage structure
                    prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
                    output_tokens = getattr(response.usage, 'output_tokens', 0) or getattr(response.usage, 'completion_tokens', 0)
                    total_tokens = getattr(response.usage, 'total_tokens', prompt_tokens + output_tokens)
                    
                    if duration > 0 and output_tokens > 0:
                        efficiency = output_tokens / duration
                        logger.info(f"💰 Tokens: {prompt_tokens}→{output_tokens} "
                                   f"(total: {total_tokens}, {efficiency:.1f} tokens/sec)")
                    else:
                        logger.info(f"💰 Tokens: {prompt_tokens}→{output_tokens} (total: {total_tokens})")
                
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