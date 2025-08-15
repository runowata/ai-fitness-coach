"""AI client interfaces for OpenAI and Anthropic"""
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
    """OpenAI API client with error handling"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIClientError("OPENAI_API_KEY not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = getattr(settings, 'OPENAI_MODEL', 'gpt-5')
        
        # ONLY GPT-5 models supported
        gpt5_models = {"gpt-5", "gpt-5-mini", "gpt-5-nano"}
        
        if self.default_model not in gpt5_models:
            raise AIClientError(f"ONLY GPT-5 models supported. Got: {self.default_model}. Supported: {gpt5_models}")
        
        logger.info(f"Using GPT-5 model: {self.default_model}")
    
    def generate_completion(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> Dict:
        """Generate completion from OpenAI API with JSON parsing (legacy client)"""
        # This method maintains backward compatibility - returns raw dict
        try:
            response = self._make_api_call(prompt, max_tokens, temperature)
            return response
        except Exception as e:
            logger.error(f"Completion generation failed: {str(e)}")
            raise AIClientError(f"Failed to generate AI response: {str(e)}")
    
    def generate_workout_plan(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> WorkoutPlan:
        """Generate and validate workout plan with strict Pydantic validation"""
        try:
            response = self._make_api_call(prompt, max_tokens, temperature)
            
            # Apply pre-validation fixes BEFORE Pydantic validation
            from apps.ai_integration.validators import WorkoutPlanValidator
            validator = WorkoutPlanValidator()
            
            # Fix common issues that would cause Pydantic validation to fail
            fixed_response, validation_report = validator.validate_and_fix_plan(response)
            
            if validation_report.get('fixes_applied', 0) > 0:
                logger.info(f"Pre-validation fixes applied: {validation_report.get('fixes_applied', 0)}")
                for fix in validation_report.get('fixes', []):
                    logger.info(f"Fix: {fix}")
            
            # Convert dict back to JSON string for validation
            raw_json = json.dumps(fixed_response)
            
            # Validate with strict schema (should now pass)
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
        """Generate and validate comprehensive 4-block AI report"""
        try:
            response = self._make_comprehensive_api_call(prompt, archetype, max_tokens, temperature)
            
            # Apply comprehensive validation and fixes
            from apps.ai_integration.comprehensive_validator import ComprehensiveReportValidator
            validator = ComprehensiveReportValidator()
            
            # Fix common issues that would cause validation to fail
            fixed_response, validation_report = validator.validate_and_fix_comprehensive_report(
                response, user_id, archetype
            )
            
            if validation_report.get('fixes_applied', 0) > 0:
                logger.info(f"Comprehensive report fixes applied: {validation_report.get('fixes_applied', 0)}")
                for fix in validation_report.get('fixes', []):
                    logger.info(f"Fix: {fix}")
            
            # Convert dict back to JSON string for validation
            raw_json = json.dumps(fixed_response)
            
            # Validate with comprehensive schema (should now pass)
            validated_report = validate_comprehensive_ai_report(raw_json)
            
            logger.info("Successfully validated comprehensive report: "
                       f"user_analysis={bool(validated_report.user_analysis)}, "
                       f"training_program={validated_report.training_program.plan_name}, "
                       f"motivation_system={bool(validated_report.motivation_system)}, "
                       f"long_term_strategy={bool(validated_report.long_term_strategy)}")
            
            return validated_report
            
        except Exception as e:
            logger.error(f"Comprehensive report generation/validation failed: {str(e)}")
            raise AIClientError(f"Failed to generate valid comprehensive report: {str(e)}")
    
    def _make_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Make API call to OpenAI and return parsed JSON"""
        try:
            # For GPT-5 models, use simple approach without response_format
            # GPT-5 has strong reasoning capabilities and follows JSON instructions well
            system_message = """You are a professional fitness coach AI. Create a workout plan following EXACTLY this JSON structure.

CRITICAL: 
1. Return ONLY valid JSON with NO markdown, NO explanations
2. Generate ALL weeks requested (typically 4-8 weeks)
3. Each week MUST have 7 days
4. Include rest days as appropriate

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

IMPORTANT: The weeks array must contain the full number of weeks specified in duration_weeks."""

            # Add retry logic with exponential backoff
            import time
            last_error = None
            response = None
            
            # Create API parameters - reasoning models have different parameter requirements
            api_params = {
                'model': self.default_model,
                'messages': [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                'timeout': 240  # 4 minutes - safe buffer before gunicorn timeout
            }
            
            # GPT-5 models use different parameters than legacy models
            if self.default_model.startswith('gpt-5'):
                api_params['max_completion_tokens'] = min(max_tokens, settings.OPENAI_MAX_TOKENS)
                # GPT-5 only supports default temperature (1.0) in chat completions
                if temperature != 1.0:
                    logger.warning(f"GPT-5 only supports temperature=1.0, ignoring temperature={temperature}")
                # Don't set temperature parameter for GPT-5
            else:
                # Should not reach here since we only support GPT-5
                logger.error(f"Unexpected model: {self.default_model}")
                api_params['max_tokens'] = min(max_tokens, settings.OPENAI_MAX_TOKENS)
                api_params['temperature'] = temperature
            
            for attempt in range(3):
                try:
                    response = self.client.chat.completions.create(**api_params)
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:  # Don't sleep on last attempt
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
            
            if response is None:
                raise AIClientError(f"OpenAI request failed after 3 retries: {last_error}")
            
            # Parse the JSON content directly
            content = response.choices[0].message.content.strip()
            
            # Log the raw response for debugging
            logger.info(f"Raw AI response (first 1000 chars): {content[:1000]}")
            
            # Try multiple strategies to extract valid JSON
            parsed_json = self._extract_json_robust(content)
            logger.info(f"Successfully parsed JSON with keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}")
            return parsed_json
            
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
    
    def _make_comprehensive_api_call(self, prompt: str, archetype: str, max_tokens: int, temperature: float) -> Dict:
        """Make API call for comprehensive 4-block report generation"""
        try:
            # Comprehensive system message for 4-block structure
            system_message = """You are a professional fitness coach AI generating comprehensive analysis reports. Create a detailed 4-block report following EXACTLY this JSON structure.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON with NO markdown, NO explanations
2. Generate ALL 4 blocks: user_analysis, training_program, motivation_system, long_term_strategy
3. Each block must have meaningful, detailed content
4. Training program must include full weeks as requested

REQUIRED JSON STRUCTURE:
{{
    "meta": {{
        "version": "v2_comprehensive",
        "archetype": "{archetype or 'mentor'}",
        "generation_date": "current_datetime",
        "user_id": "anonymized"
    }},
    "user_analysis": {{
        "fitness_level_assessment": "detailed assessment (50-800 chars)",
        "psychological_profile": "psychological analysis (50-600 chars)",
        "limitations_analysis": "limitations analysis (up to 500 chars)",
        "interaction_strategy": "interaction approach (30-400 chars)",
        "archetype_adaptation": "archetype adaptation (30-300 chars)"
    }},
    "training_program": {{
        "plan_name": "personalized plan name",
        "duration_weeks": number,
        "goal": "specific goal",
        "weeks": [
            {{
                "week_number": 1,
                "week_focus": "week theme",
                "days": [
                    {{
                        "day_number": 1,
                        "workout_name": "workout name",
                        "is_rest_day": false,
                        "exercises": [
                            {{
                                "exercise_slug": "exercise-slug-from-database",
                                "sets": number,
                                "reps": "string",
                                "rest_seconds": number_10_to_600,
                                "duration_seconds": optional_number
                            }}
                        ],
                        "confidence_task": "daily confidence task"
                    }}
                ]
            }}
        ]
    }},
    "motivation_system": {{
        "psychological_support": "support plan (100-800 chars)",
        "reward_system": "reward system (50-500 chars)",
        "confidence_building": "confidence strategy (50-600 chars)",
        "community_integration": "community plan (up to 400 chars)"
    }},
    "long_term_strategy": {{
        "progression_plan": "long-term plan (100-800 chars)",
        "adaptation_triggers": "adaptation triggers (50-500 chars)",
        "lifestyle_integration": "lifestyle integration (50-600 chars)",
        "success_metrics": "success metrics (30-400 chars)"
    }}
}}

ARCHETYPE SPECIFIC GUIDANCE:
- mentor: Wise, patient, long-term focused approach
- professional: Results-oriented, efficient, strategic approach  
- peer: Friendly, relatable, supportive approach

IMPORTANT: Each field must contain meaningful content appropriate to the archetype. The training_program section must follow the same structure as standard workout plans but be embedded within the comprehensive report."""

            # Add retry logic with exponential backoff
            import time
            last_error = None
            response = None
            
            # Create API parameters - reasoning models have different parameter requirements
            api_params = {
                'model': self.default_model,
                'messages': [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                'timeout': 300  # 5 minutes for comprehensive reports
            }
            
            # GPT-5 models use different parameters than legacy models
            if self.default_model.startswith('gpt-5'):
                api_params['max_completion_tokens'] = min(max_tokens, settings.OPENAI_MAX_TOKENS)
                # GPT-5 only supports default temperature (1.0) in chat completions
                if temperature != 1.0:
                    logger.warning(f"GPT-5 only supports temperature=1.0, ignoring temperature={temperature}")
                # Don't set temperature parameter for GPT-5
            else:
                # Should not reach here since we only support GPT-5
                logger.error(f"Unexpected model: {self.default_model}")
                api_params['max_tokens'] = min(max_tokens, settings.OPENAI_MAX_TOKENS)
                api_params['temperature'] = temperature
            
            for attempt in range(3):
                try:
                    response = self.client.chat.completions.create(**api_params)
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    logger.warning(f"OpenAI API comprehensive attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:  # Don't sleep on last attempt
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
            
            if response is None:
                raise AIClientError(f"OpenAI comprehensive request failed after 3 retries: {last_error}")
            
            # Parse the JSON content directly
            content = response.choices[0].message.content.strip()
            
            # Log the raw response for debugging (truncated)
            logger.info(f"Raw comprehensive AI response (first 1500 chars): {content[:1500]}")
            
            # Try multiple strategies to extract valid JSON
            parsed_json = self._extract_json_robust(content)
            logger.info(f"Successfully parsed comprehensive JSON with keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}")
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in comprehensive report: {str(e)}, Content: {content[:500]}")
            raise AIClientError(f"AI comprehensive response is not valid JSON: {str(e)}")
        except Exception as e:
            error_str = str(e).lower()
            if 'timeout' in error_str or 'timed out' in error_str:
                logger.error(f"OpenAI API timeout for comprehensive report after 300 seconds: {str(e)}")
                raise AIClientError("AI service is taking too long to generate comprehensive report. Please try again in a few moments.")
            else:
                logger.error(f"OpenAI API error for comprehensive report: {str(e)}")
                raise AIClientError(f"Failed to generate comprehensive AI report: {str(e)}")
    
    def _extract_json_robust(self, content: str) -> Dict:
        """Extract JSON from AI response using multiple robust strategies"""
        import re

        # Strategy 1: Direct parsing (clean content first)
        cleaned_content = content.strip()
        
        # Remove common markdown patterns
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[7:]
        elif cleaned_content.startswith('```'):
            cleaned_content = cleaned_content[3:]
            
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-3]
            
        cleaned_content = cleaned_content.strip()
        
        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError:
            logger.debug("Strategy 1 (direct) failed, trying extraction strategies...")
        
        # Strategy 2: Find JSON object with braces matching
        try:
            # Find first opening brace and matching closing brace
            start_idx = content.find('{')
            if start_idx != -1:
                # Count braces to find matching closing brace
                brace_count = 0
                end_idx = -1
                
                for i in range(start_idx, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx != -1:
                    json_candidate = content[start_idx:end_idx]
                    return json.loads(json_candidate)
                    
        except json.JSONDecodeError:
            logger.debug("Strategy 2 (brace matching) failed, trying regex...")
        
        # Strategy 3: Regex extraction for JSON objects
        try:
            # More sophisticated regex to find JSON object
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, content, re.DOTALL)
            
            for match in matches:
                try:
                    # Try parsing each potential JSON match
                    result = json.loads(match)
                    if isinstance(result, dict) and len(result) > 2:  # Basic sanity check
                        return result
                except json.JSONDecodeError:
                    continue
                    
        except Exception:
            logger.debug("Strategy 3 (regex) failed, trying line-by-line...")
        
        # Strategy 4: Line-by-line reconstruction
        try:
            lines = content.split('\n')
            json_lines = []
            in_json = False
            brace_count = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Start collecting when we see opening brace
                if '{' in stripped and not in_json:
                    in_json = True
                    
                if in_json:
                    json_lines.append(line)
                    # Count braces in this line
                    brace_count += stripped.count('{') - stripped.count('}')
                    
                    # Stop when braces are balanced
                    if brace_count == 0 and '}' in stripped:
                        break
            
            if json_lines:
                json_text = '\n'.join(json_lines)
                return json.loads(json_text)
                
        except json.JSONDecodeError:
            logger.debug("Strategy 4 (line reconstruction) failed...")
        
        # Strategy 5: Remove common prefixes/suffixes and try again
        try:
            # Remove explanatory text before/after JSON
            patterns_to_remove = [
                r'^.*?(?=\{)',  # Remove everything before first {
                r'\}.*?$',      # Remove everything after last }
            ]
            
            for pattern in patterns_to_remove:
                content = re.sub(pattern, '', content, flags=re.DOTALL)
            
            # Add back the closing brace if removed
            if content.strip().endswith(','):
                content = content.strip()[:-1] + '}'
            elif not content.strip().endswith('}'):
                content = content.strip() + '}'
                
            return json.loads(content.strip())
            
        except (json.JSONDecodeError, re.error):
            pass
        
        # If all strategies fail, raise error with helpful message
        logger.error(f"All JSON extraction strategies failed. Content preview: {content[:200]}...")
        raise json.JSONDecodeError(
            "Could not extract valid JSON from AI response using any strategy", 
            content, 
            0
        )


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