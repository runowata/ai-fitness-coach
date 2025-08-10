"""AI client interfaces for OpenAI and Anthropic"""
import json
import logging
from typing import Dict, Optional

from .schemas import validate_ai_plan_response, WorkoutPlan

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
    
    def generate_completion(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> Dict:
        """Generate completion from OpenAI API for o1 model with basic JSON parsing"""
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
    
    def _make_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Make API call to OpenAI and return parsed JSON"""
        try:
            # For o1 models, use simple approach without response_format
            # o1 models have reasoning capabilities and follow JSON instructions well
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