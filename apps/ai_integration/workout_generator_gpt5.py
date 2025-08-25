"""
GPT-5 optimized workout plan generator using Structured Outputs and Responses API
"""

import json
import logging
from typing import Dict, Set, Optional, Any
from django.conf import settings
from pathlib import Path

from .ai_client_gpt5_structured import GPT5StructuredClient
from apps.core.services.exercise_validation import ExerciseValidationService
from apps.core.metrics import incr, MetricNames

logger = logging.getLogger(__name__)


class GPT5WorkoutGenerator:
    """
    GPT-5 optimized workout plan generator
    Uses Structured Outputs for guaranteed JSON compliance
    """
    
    def __init__(self):
        self.client = GPT5StructuredClient()
        self.prompts_dir = Path(__file__).resolve().parents[2] / 'prompts' / 'gpt5'
        logger.info("GPT-5 Workout Generator initialized")
    
    def _load_prompt_file(self, filename: str) -> str:
        """Load prompt file content"""
        file_path = self.prompts_dir / filename
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to load prompt file {filename}: {e}")
            return ""
    
    def _build_system_prompt(self, archetype: str) -> str:
        """Build complete system prompt for archetype"""
        # Load intro and archetype-specific system prompt
        intro = self._load_prompt_file("_intro.txt")
        system_prompt = self._load_prompt_file(f"system/{archetype}.system.md")
        
        return f"{intro}\n\n{system_prompt}".strip()
    
    def _build_user_prompt(self, archetype: str, user_data: Dict, allowed_exercises: Set[str]) -> str:
        """Build complete user prompt with data and exercise whitelist"""
        # Load archetype-specific user prompt
        user_template = self._load_prompt_file(f"user/{archetype}.user.md")
        
        # Format with user data
        try:
            formatted_prompt = user_template.format(**user_data)
        except KeyError as e:
            logger.warning(f"Missing user data key: {e}, using template as-is")
            formatted_prompt = user_template
        
        # Add exercise whitelist
        exercise_list = ', '.join(sorted(allowed_exercises))
        whitelist_section = f"""

<exercise_whitelist>
CRITICAL: You MUST use ONLY these exercise codes. Do not invent new codes.

Available Exercises: {exercise_list}

Exercise Code Patterns:
- Warmup: WZ001-WZ021 (mobility, activation)
- Main: EX001-EX063 (strength, movement patterns)  
- Endurance: SX001-SX021 (cardio, conditioning)
- Cooldown: CZ001-CZ021, CX001-CX021 (flexibility, recovery)

If an exercise type is unavailable, choose the closest alternative from the available codes based on movement pattern and muscle groups.
</exercise_whitelist>"""
        
        return f"{formatted_prompt}{whitelist_section}"
    
    def generate_plan(
        self, 
        user_data: Dict, 
        archetype: Optional[str] = None,
        reasoning_effort: str = 'medium',
        verbosity: str = 'medium'
    ) -> Dict[str, Any]:
        """
        Generate workout plan using GPT-5 Structured Outputs
        
        Args:
            user_data: Client information and preferences
            archetype: Trainer archetype (mentor, professional, peer)
            reasoning_effort: GPT-5 reasoning level (minimal, medium, high)
            verbosity: Response verbosity (low, medium, high)
            
        Returns:
            Complete workout plan with metadata
        """
        # Default archetype
        archetype = archetype or user_data.get('archetype', 'mentor')
        
        # Normalize archetype name
        archetype_map = {
            'bro': 'peer',
            'sergeant': 'professional', 
            'intellectual': 'mentor'
        }
        archetype = archetype_map.get(archetype, archetype)
        
        logger.info(f"Generating GPT-5 plan for archetype: {archetype}")
        logger.info(f"User profile: {user_data.get('age')}y, {user_data.get('primary_goal')}")
        
        # Get allowed exercises for archetype
        allowed_exercises = ExerciseValidationService.get_allowed_exercise_slugs(archetype=archetype)
        incr(MetricNames.AI_WHITELIST_COUNT, len(allowed_exercises))
        
        logger.info(f"Exercise whitelist: {len(allowed_exercises)} codes for {archetype}")
        
        # Build prompts
        system_prompt = self._build_system_prompt(archetype)
        user_prompt = self._build_user_prompt(archetype, user_data, allowed_exercises)
        
        logger.info(f"System prompt length: {len(system_prompt)} chars")
        logger.info(f"User prompt length: {len(user_prompt)} chars")
        
        # Generate with GPT-5
        try:
            result = self.client.generate_workout_plan(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity
            )
            
            # Extract plan data
            plan_data = result['plan_data']
            
            # Add metadata
            plan_data['generation_metadata'] = {
                'archetype': archetype,
                'model': result.get('model'),
                'generation_time': result.get('generation_time'),
                'reasoning_effort': result.get('reasoning_effort'),
                'verbosity': result.get('verbosity'),
                'response_id': result.get('response_id'),  # For context reuse
                'exercises_available': len(allowed_exercises),
                'structured_outputs': True
            }
            
            logger.info("GPT-5 plan generation successful")
            logger.info(f"Plan: {plan_data.get('plan_name', 'Unnamed')}")
            logger.info(f"Duration: {plan_data.get('duration_weeks', 0)} weeks")
            logger.info(f"Response ID: {result.get('response_id')}")
            
            return plan_data
            
        except Exception as e:
            logger.error(f"GPT-5 plan generation failed: {str(e)}")
            raise
    
    def generate_with_context(
        self,
        user_data: Dict,
        previous_response_id: str,
        archetype: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate plan with reasoning context reuse from previous response
        Improves efficiency and consistency in multi-turn scenarios
        """
        logger.info(f"Generating with context reuse from: {previous_response_id}")
        
        # Use the context reuse method
        archetype = archetype or user_data.get('archetype', 'mentor')
        archetype = {'bro': 'peer', 'sergeant': 'professional', 'intellectual': 'mentor'}.get(archetype, archetype)
        
        allowed_exercises = ExerciseValidationService.get_allowed_exercise_slugs(archetype=archetype)
        
        system_prompt = self._build_system_prompt(archetype)
        user_prompt = self._build_user_prompt(archetype, user_data, allowed_exercises)
        
        try:
            result = self.client.generate_with_context_reuse(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                previous_response_id=previous_response_id,
                **kwargs
            )
            
            plan_data = result['plan_data']
            plan_data['generation_metadata'] = {
                'archetype': archetype,
                'context_reused': True,
                'previous_response_id': previous_response_id,
                'new_response_id': result.get('response_id'),
                **result
            }
            
            return plan_data
            
        except Exception as e:
            logger.error(f"GPT-5 context generation failed: {str(e)}")
            raise
    
    def test_generation(self) -> bool:
        """Test GPT-5 generation with minimal example"""
        try:
            test_user_data = {
                'age': 30,
                'height': 175,
                'weight': 70,
                'archetype': 'mentor',
                'primary_goal': 'general fitness',
                'injuries': 'None',
                'equipment_list': 'Bodyweight exercises only',
                'duration_weeks': 2,
                'onboarding_payload_json': '{"fitness_level": "beginner"}'
            }
            
            logger.info("Testing GPT-5 generation...")
            result = self.generate_plan(
                user_data=test_user_data,
                reasoning_effort='minimal',  # Fast test
                verbosity='low'
            )
            
            # Verify structure
            if (result.get('plan_name') and 
                result.get('duration_weeks') == 2 and
                len(result.get('weeks', [])) == 2):
                logger.info("GPT-5 generation test successful")
                return True
            else:
                logger.error("GPT-5 generation test failed - invalid structure")
                return False
                
        except Exception as e:
            logger.error(f"GPT-5 generation test failed: {str(e)}")
            return False


# Convenience function
def create_gpt5_generator() -> GPT5WorkoutGenerator:
    """Create GPT-5 workout generator instance"""
    return GPT5WorkoutGenerator()


# Test script
if __name__ == "__main__":
    generator = create_gpt5_generator()
    
    if generator.test_generation():
        print("✅ GPT-5 generator test successful")
    else:
        print("❌ GPT-5 generator test failed")