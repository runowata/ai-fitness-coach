"""Prompt management for AI integration"""
import os
from pathlib import Path
from django.conf import settings


class PromptManager:
    """Manages AI prompts and templates"""
    
    def __init__(self):
        self.prompts_dir = Path(settings.BASE_DIR) / 'prompts'
    
    def load_prompt(self, prompt_name: str) -> str:
        """Load prompt template from file"""
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file {prompt_file} not found")
        
        with open(prompt_file, 'r', encoding='utf-8') as file:
            return file.read()
    
    def get_workout_plan_prompt(self, archetype: str) -> str:
        """Get workout plan generation prompt for specific archetype"""
        archetype_prompts = {
            'bro': 'workout_plan_bro.txt',
            'sergeant': 'workout_plan_sergeant.txt', 
            'intellectual': 'workout_plan_intellectual.txt'
        }
        
        prompt_file = archetype_prompts.get(archetype, 'workout_plan_generation.txt')
        return self.load_prompt(prompt_file.replace('.txt', ''))
    
    def get_weekly_adaptation_prompt(self) -> str:
        """Get weekly adaptation prompt"""
        return self.load_prompt('weekly_adaptation')
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """Format prompt template with provided variables"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable in prompt template: {e}")


class OnboardingDataProcessor:
    """Process onboarding data for AI consumption"""
    
    @staticmethod
    def collect_user_data(user) -> dict:
        """Collect all user data from onboarding responses"""
        from apps.onboarding.models import UserOnboardingResponse
        
        responses = UserOnboardingResponse.objects.filter(user=user)
        user_data = {
            'archetype': user.archetype,
            # Defaults that will be overridden by responses
            'age': 25,
            'height': 175,
            'weight': 70,
            'duration_weeks': 6,
            'workout_duration': '30-45',
            'days_per_week': '3-4',
            'primary_goal': 'general_fitness',
            'experience_level': 'beginner',
            'recent_activity_level': 'light_activity',
            'available_equipment': ['bodyweight_only'],
            'preferred_workout_time': 'evening',
            'health_limitations': ['none'],
            'preferred_exercise_types': ['strength_training'],
            'gym_comfort_level': 'neutral',
            'motivation_style': 'wellbeing'
        }
        
        # Process responses into AI-friendly format
        for response in responses:
            field_name = response.question.ai_field_name
            value = response.get_answer_value()
            user_data[field_name] = value
        
        return OnboardingDataProcessor.post_process_data(user_data)
    
    @staticmethod
    def post_process_data(user_data: dict) -> dict:
        """Post-process user data for consistency"""
        # Convert list fields to comma-separated strings if needed
        list_fields = ['available_equipment', 'health_limitations', 'preferred_exercise_types']
        for field in list_fields:
            if isinstance(user_data.get(field), list):
                user_data[field] = ', '.join(user_data[field])
        
        # Ensure numeric fields are properly typed
        numeric_fields = ['age', 'height', 'weight', 'duration_weeks']
        for field in numeric_fields:
            if field in user_data:
                try:
                    user_data[field] = int(user_data[field])
                except (ValueError, TypeError):
                    pass  # Keep original value if conversion fails
        
        return user_data