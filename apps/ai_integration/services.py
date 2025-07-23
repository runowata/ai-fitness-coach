import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from openai import OpenAI
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def create_workout_plan_from_onboarding(user):
    """
    Main function to create workout plan from onboarding data
    Called from onboarding views
    """
    from apps.onboarding.models import UserOnboardingResponse, OnboardingSession
    from apps.workouts.models import WorkoutPlan, DailyWorkout
    
    # Collect all user responses
    responses = UserOnboardingResponse.objects.filter(user=user)
    user_data = {
        'archetype': user.profile.archetype,
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
    
    # Post-process specific fields
    if isinstance(user_data.get('days_per_week'), str):
        # Convert "3-4" to 3 for AI processing
        user_data['days_per_week'] = int(user_data['days_per_week'].split('-')[0])
    
    if isinstance(user_data.get('workout_duration'), str):
        # Convert "30-45" to 45 for AI processing
        if '-' in user_data['workout_duration']:
            user_data['workout_duration'] = int(user_data['workout_duration'].split('-')[1])
        elif user_data['workout_duration'] == '60+':
            user_data['workout_duration'] = 60
        else:
            user_data['workout_duration'] = int(user_data['workout_duration'])
    
    if isinstance(user_data.get('duration_weeks'), str):
        user_data['duration_weeks'] = int(user_data['duration_weeks'])
    
    # Convert lists to comma-separated strings for AI prompt
    if isinstance(user_data.get('available_equipment'), list):
        user_data['available_equipment'] = ', '.join(user_data['available_equipment'])
    
    if isinstance(user_data.get('health_limitations'), list):
        user_data['health_limitations'] = ', '.join(user_data['health_limitations'])
    
    if isinstance(user_data.get('preferred_exercise_types'), list):
        user_data['preferred_exercise_types'] = ', '.join(user_data['preferred_exercise_types'])
    
    # Generate plan with AI
    generator = WorkoutPlanGenerator()
    plan_data = generator.generate_plan(user_data)
    
    # Create workout plan
    workout_plan = WorkoutPlan.objects.create(
        user=user,
        name=plan_data.get('plan_name', 'Персональный план'),
        duration_weeks=plan_data.get('duration_weeks', 6),
        goal=user_data.get('primary_goal', 'general_fitness'),
        plan_data=plan_data,
        started_at=timezone.now()
    )
    
    # Create daily workouts
    for week in plan_data.get('weeks', []):
        for day in week.get('days', []):
            DailyWorkout.objects.create(
                plan=workout_plan,
                day_number=day.get('day_number'),
                week_number=week.get('week_number'),
                name=day.get('workout_name', f'День {day.get("day_number")}'),
                exercises=day.get('exercises', []),
                is_rest_day=day.get('is_rest_day', False),
                confidence_task=day.get('confidence_task', {}).get('description', '')
            )
    
    # Mark onboarding as completed
    user.profile.onboarding_completed_at = timezone.now()
    user.profile.save()
    
    # Update session
    session = OnboardingSession.objects.filter(
        user=user,
        is_completed=False
    ).first()
    if session:
        session.is_completed = True
        session.completed_at = timezone.now()
        session.ai_request_data = user_data
        session.ai_response_data = plan_data
        session.save()
    
    return workout_plan


class WorkoutPlanGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = getattr(settings, 'OPENAI_TEMPERATURE', 0.7)
    
    def generate_plan(self, user_data: Dict) -> Dict:
        """Generate a complete workout plan based on user onboarding data"""
        prompt = self._build_prompt(user_data)
        
        try:
            logger.info(f"Generating workout plan for user with model {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            logger.info("OpenAI response received successfully")
            plan_data = json.loads(response.choices[0].message.content)
            return self._validate_and_enhance_plan(plan_data, user_data)
            
        except Exception as e:
            import traceback
            logger.error(f"Error generating workout plan: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def adapt_weekly_plan(self, current_plan: Dict, user_feedback: List[Dict], week_number: int) -> Dict:
        """Adapt the plan for the upcoming week based on user feedback"""
        adaptation_prompt = self._build_adaptation_prompt(current_plan, user_feedback, week_number)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_adaptation_system_prompt()},
                    {"role": "user", "content": adaptation_prompt}
                ],
                temperature=0.5,  # Lower temperature for consistency
                max_tokens=1000
            )
            
            adaptation = json.loads(response.choices[0].message.content)
            return self._apply_adaptation(current_plan, adaptation, week_number)
            
        except Exception as e:
            logger.error(f"Error adapting workout plan: {str(e)}")
            return current_plan  # Return unchanged plan on error
    
    def _build_prompt(self, user_data: Dict) -> str:
        """Build the prompt for plan generation"""
        prompt_template = """
        Create a {duration}-week workout plan for a user with the following profile:
        
        Age: {age}
        Height: {height} {height_unit}
        Weight: {weight} {weight_unit}
        Experience Level: {experience}
        Goals: {goals}
        Limitations: {limitations}
        Available Equipment: {equipment}
        Workout Days per Week: {days_per_week}
        Preferred Workout Duration: {workout_duration} minutes
        
        The plan should:
        1. Progress gradually from week to week
        2. Include rest days and active recovery
        3. Target the specified goals while respecting limitations
        4. Include variety to maintain engagement
        5. Include daily confidence-building tasks
        6. Mark clearly which days are rest/recovery days
        
        Return the plan as a JSON object with the following structure:
        {{
            "plan_name": "string",
            "duration_weeks": number,
            "weeks": [
                {{
                    "week_number": number,
                    "focus": "string",
                    "days": [
                        {{
                            "day_number": number,
                            "workout_name": "string",
                            "is_rest_day": boolean,
                            "exercises": [
                                {{
                                    "exercise_slug": "string",
                                    "sets": number,
                                    "reps": "string",
                                    "rest_seconds": number,
                                    "notes": "string"
                                }}
                            ],
                            "confidence_task": "string"
                        }}
                    ]
                }}
            ]
        }}
        """
        
        return prompt_template.format(**user_data)
    
    def _get_system_prompt(self) -> str:
        return """You are an expert fitness coach specializing in creating personalized workout plans 
        for gay men. You understand the importance of building both physical strength and self-confidence. 
        Your plans are progressive, safe, and engaging. Always include appropriate rest days and 
        confidence-building tasks that help users feel more comfortable in their bodies and social situations."""
    
    def _get_adaptation_system_prompt(self) -> str:
        return """You are an expert fitness coach reviewing a user's progress to make weekly adjustments. 
        Based on their feedback, you will suggest minor modifications to maintain optimal challenge and engagement. 
        Only suggest changes that improve the experience without completely restructuring the plan."""
    
    def _validate_and_enhance_plan(self, plan_data: Dict, user_data: Dict) -> Dict:
        """Validate the generated plan and add any missing elements"""
        # Add metadata
        plan_data['generated_at'] = timezone.now().isoformat()
        plan_data['user_archetype'] = user_data.get('archetype', 'bro')
        
        # Ensure all weeks have proper rest days
        for week in plan_data['weeks']:
            rest_days = sum(1 for day in week['days'] if day.get('is_rest_day', False))
            if rest_days == 0:
                # Add a rest day if none exists
                week['days'].append({
                    'day_number': len(week['days']) + 1,
                    'workout_name': 'Active Recovery',
                    'is_rest_day': True,
                    'exercises': [],
                    'confidence_task': 'Take a relaxing walk and practice positive self-talk'
                })
        
        return plan_data
    
    def _build_adaptation_prompt(self, current_plan: Dict, user_feedback: List[Dict], week_number: int) -> str:
        """Build prompt for weekly adaptation"""
        feedback_summary = self._summarize_feedback(user_feedback)
        
        return f"""
        Review the user's workout feedback from week {week_number - 1} and suggest adaptations for week {week_number}.
        
        Feedback Summary:
        - Completion rate: {feedback_summary['completion_rate']}%
        - Average difficulty rating: {feedback_summary['avg_difficulty']}
        - Most challenging exercises: {', '.join(feedback_summary['challenging_exercises'])}
        - Substitutions made: {feedback_summary['substitution_count']}
        
        Current week {week_number} plan:
        {json.dumps(current_plan['weeks'][week_number - 1], indent=2)}
        
        Suggest modifications as a JSON object:
        {{
            "intensity_adjustment": "increase|maintain|decrease",
            "exercise_swaps": [
                {{"from": "exercise_slug", "to": "exercise_slug", "reason": "string"}}
            ],
            "volume_changes": {{"exercise_slug": {{"sets": number, "reps": "string"}}}},
            "additional_notes": "string"
        }}
        """
    
    def _summarize_feedback(self, user_feedback: List[Dict]) -> Dict:
        """Summarize user feedback for the adaptation prompt"""
        total_workouts = len(user_feedback)
        completed_workouts = sum(1 for f in user_feedback if f.get('completed'))
        
        difficulty_map = {'fire': 1, 'smile': 2, 'neutral': 3, 'tired': 4}
        difficulties = [difficulty_map.get(f.get('feedback_rating', 'neutral'), 3) for f in user_feedback]
        
        return {
            'completion_rate': int((completed_workouts / total_workouts * 100) if total_workouts > 0 else 0),
            'avg_difficulty': sum(difficulties) / len(difficulties) if difficulties else 3,
            'challenging_exercises': [],  # Would need to analyze exercise-level feedback
            'substitution_count': sum(len(f.get('substitutions', {})) for f in user_feedback)
        }
    
    def _apply_adaptation(self, current_plan: Dict, adaptation: Dict, week_number: int) -> Dict:
        """Apply the suggested adaptations to the plan"""
        # This would implement the actual plan modifications
        # For now, just log the suggestions
        logger.info(f"Adaptation suggestions for week {week_number}: {adaptation}")
        return current_plan


class PromptManager:
    """Manage AI prompts from files"""
    
    PROMPT_DIR = 'prompts'
    
    @classmethod
    def get_prompt(cls, prompt_name: str, **kwargs) -> str:
        """Load a prompt template from file and format it with provided kwargs"""
        prompt_path = f"{cls.PROMPT_DIR}/{prompt_name}.txt"
        
        try:
            with open(prompt_path, 'r') as f:
                template = f.read()
            return template.format(**kwargs)
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_path}")
            raise
        except KeyError as e:
            logger.error(f"Missing template variable in prompt {prompt_name}: {e}")
            raise