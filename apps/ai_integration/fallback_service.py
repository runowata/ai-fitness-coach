"""
Comprehensive Fallback Service for AI Fitness Coach
Handles all failure scenarios with graceful degradation
"""
import json
import logging
from typing import Dict, List, Optional

from django.utils import timezone

from apps.users.models import UserProfile
from apps.workouts.models import CSVExercise, DailyWorkout, WorkoutExecution, WorkoutPlan

from .schemas import WorkoutPlan as WorkoutPlanSchema

logger = logging.getLogger(__name__)

class FallbackService:
    """Handles all fallback scenarios for AI generation and workout creation"""
    
    def __init__(self):
        self.fallback_exercises = self._get_reliable_exercises()
        self.default_plan_templates = self._load_default_templates()
    
    def generate_default_workout_plan(
        self, 
        user_data: Dict, 
        error_context: str = "AI_GENERATION_FAILED"
    ) -> WorkoutPlanSchema:
        """
        Generate a reliable default workout plan when AI fails
        
        Args:
            user_data: User profile and preferences
            error_context: Why we're using fallback
        
        Returns:
            WorkoutPlanSchema: Valid workout plan
        """
        logger.warning(f"Using fallback plan generation: {error_context}")
        
        # Determine user parameters
        experience = user_data.get('experience_level', 'beginner').lower()
        days_per_week = min(max(int(user_data.get('days_per_week', 3)), 2), 6)
        duration_weeks = min(max(int(user_data.get('duration_weeks', 4)), 2), 8)
        
        # Select appropriate template
        template_key = f"{experience}_{days_per_week}days"
        template = self.default_plan_templates.get(
            template_key, 
            self.default_plan_templates['beginner_3days']  # Ultimate fallback
        )
        
        # Generate plan
        plan_data = self._build_plan_from_template(
            template=template,
            user_data=user_data,
            duration_weeks=duration_weeks
        )
        
        # Convert to JSON and validate
        plan_json = json.dumps(plan_data)
        
        try:
            from .schemas import validate_ai_plan_response
            validated_plan = validate_ai_plan_response(plan_json)
            logger.info(f"Generated fallback plan: {validated_plan.plan_name}")
            return validated_plan
        except Exception as validation_error:
            logger.error(f"Fallback plan validation failed: {validation_error}")
            return self._generate_minimal_emergency_plan(user_data)
    
    def get_fallback_exercise(
        self, 
        target_exercise: str, 
        muscle_groups: List[str], 
        equipment: str = "bodyweight"
    ) -> Optional[str]:
        """
        Find fallback exercise when target is unavailable
        
        Priority:
        1. Same muscle group, same equipment
        2. Same muscle group, different equipment  
        3. Different muscle group, same equipment
        4. Basic fallback exercises
        """
        logger.info(f"Finding fallback for '{target_exercise}' targeting {muscle_groups}")
        
        # Level 1: Same muscle + same equipment
        for exercise_slug, exercise_data in self.fallback_exercises.items():
            if (set(muscle_groups) & set(exercise_data.get('muscle_groups', [])) and 
                exercise_data.get('equipment') == equipment):
                logger.info(f"Level 1 fallback: {exercise_slug}")
                return exercise_slug
        
        # Level 2: Same muscle + different equipment  
        for exercise_slug, exercise_data in self.fallback_exercises.items():
            if set(muscle_groups) & set(exercise_data.get('muscle_groups', [])):
                logger.info(f"Level 2 fallback: {exercise_slug}")
                return exercise_slug
        
        # Level 3: Same equipment + different muscle
        for exercise_slug, exercise_data in self.fallback_exercises.items():
            if exercise_data.get('equipment') == equipment:
                logger.info(f"Level 3 fallback: {exercise_slug}")
                return exercise_slug
        
        # Level 4: Ultimate fallback - basic exercises
        ultimate_fallbacks = ['push-ups', 'squats', 'planks', 'jumping-jacks']
        for fallback in ultimate_fallbacks:
            if fallback in self.fallback_exercises:
                logger.warning(f"Ultimate fallback: {fallback}")
                return fallback
        
        logger.error(f"No fallback found for {target_exercise}")
        return None
    
    def create_emergency_workout(self, user_profile: UserProfile) -> Optional[DailyWorkout]:
        """
        Create a basic workout when all else fails
        Emergency 15-minute bodyweight routine
        """
        logger.warning(f"Creating emergency workout for user {user_profile.user.id}")
        
        emergency_exercises = [
            ('push-ups', 3, '5-10', 45),
            ('squats', 3, '10-15', 45), 
            ('planks', 3, '20-30 seconds', 45),
            ('jumping-jacks', 2, '30 seconds', 45),
        ]
        
        try:
            # Create minimal workout plan if none exists
            plan, created = WorkoutPlan.objects.get_or_create(
                user=user_profile.user,
                defaults={
                    'plan_name': 'Emergency Basic Workout',
                    'goal': 'Stay active',
                    'duration_weeks': 1,
                    'archetype': user_profile.archetype or 'mentor',
                    'created_by_ai': False,
                }
            )
            
            # Create today's workout
            today = timezone.now().date()
            workout = DailyWorkout.objects.create(
                plan=plan,
                workout_date=today,
                workout_name="Emergency 15-Minute Routine",
                is_rest_day=False,
                confidence_task="Complete this emergency workout - you're building consistency!"
            )
            
            # Add exercises
            for order, (slug, sets, reps, rest) in enumerate(emergency_exercises, 1):
                try:
                    exercise = CSVExercise.objects.get(slug=slug)
                    WorkoutExecution.objects.create(
                        workout=workout,
                        exercise=exercise,
                        sets=sets,
                        reps=reps,
                        rest_seconds=rest,
                        order=order
                    )
                except CSVExercise.DoesNotExist:
                    logger.warning(f"Emergency exercise {slug} not found, skipping")
                    continue
            
            logger.info(f"Created emergency workout {workout.id}")
            return workout
            
        except Exception as e:
            logger.error(f"Failed to create emergency workout: {e}")
            return None
    
    def _get_reliable_exercises(self) -> Dict:
        """Get list of exercises that should always be available"""
        reliable_exercises = {}
        
        try:
            # Query most common exercises from database by technical names  
            # CSVExercise uses 'id' field, not 'slug'
            common_exercises = CSVExercise.objects.filter(
                id__in=[
                    'push-ups', 'squats', 'planks', 'jumping-jacks', 
                    'lunges', 'mountain-climbers', 'burpees',
                    'sit-ups', 'calf-raises', 'wall-sits'
                ]
            ).values('id', 'muscle_group', 'exercise_type')
            
            for exercise in common_exercises:
                reliable_exercises[exercise['id']] = {
                    'muscle_groups': [exercise['muscle_group']] if exercise['muscle_group'] else [],
                    'equipment': 'bodyweight'  # Default for CSVExercise
                }
                
        except Exception as e:
            logger.error(f"Failed to load reliable exercises: {e}")
            # Hardcoded fallback using technical names from R2
            reliable_exercises = {
                'push-ups': {'muscle_groups': ['chest', 'triceps'], 'equipment': 'bodyweight'},
                'squats': {'muscle_groups': ['legs', 'glutes'], 'equipment': 'bodyweight'},
                'planks': {'muscle_groups': ['core'], 'equipment': 'bodyweight'},
                'jumping-jacks': {'muscle_groups': ['cardio'], 'equipment': 'bodyweight'},
            }
        
        return reliable_exercises
    
    def _get_r2_exercise_fallback(self, exercise_slug: str) -> str:
        """Get real R2 exercise name as fallback"""
        import json
        import os

        from django.conf import settings
        
        try:
            # Load real exercise names from R2 upload state
            r2_state_path = os.path.join(settings.BASE_DIR, 'r2_upload_state.json')
            if os.path.exists(r2_state_path):
                with open(r2_state_path, 'r') as f:
                    uploaded_files = json.load(f)
                
                # Extract all exercise names from R2
                r2_exercises = []
                for file_path in uploaded_files:
                    if 'videos/exercises/' in file_path and '_technique_' in file_path:
                        filename = file_path.split('/')[-1]
                        exercise_name = filename.split('_technique_')[0]
                        r2_exercises.append(exercise_name)
                
                # Try to find the exact exercise
                if exercise_slug in r2_exercises:
                    return exercise_slug
                
                # Return first available R2 exercise as fallback
                if r2_exercises:
                    logger.info(f"Using R2 fallback: {r2_exercises[0]} for {exercise_slug}")
                    return r2_exercises[0]
                    
        except Exception as e:
            logger.error(f"Failed to load R2 exercises: {e}")
        
        # Ultimate fallback - use common R2 exercises
        r2_common = ['push-ups', 'squats', 'planks', 'jumping-jacks']
        return r2_common[0]  # Return first common exercise
    
    def _load_default_templates(self) -> Dict:
        """Load hardcoded workout templates for different experience levels"""
        return {
            'beginner_3days': {
                'plan_name': 'Beginner 3-Day Foundation',
                'goal': 'Build basic fitness foundation',
                'exercises_per_day': [
                    ['push-ups', 'squats', 'planks'],
                    ['lunges', 'crunches', 'jumping-jacks'], 
                    ['wall-sits', 'mountain-climbers', 'calf-raises'],
                ],
                'sets_range': [2, 3],
                'reps_range': ['5-8', '8-12'],
                'rest_seconds': 60,
            },
            'intermediate_4days': {
                'plan_name': 'Intermediate 4-Day Builder',
                'goal': 'Increase strength and endurance',
                'exercises_per_day': [
                    ['push-ups', 'squats', 'planks', 'lunges'],
                    ['burpees', 'crunches', 'mountain-climbers'],
                    ['jumping-jacks', 'wall-sits', 'calf-raises'],
                    ['push-ups', 'squats', 'planks', 'burpees'],
                ],
                'sets_range': [3, 4],
                'reps_range': ['8-12', '10-15'],
                'rest_seconds': 45,
            }
        }
    
    def _build_plan_from_template(
        self, 
        template: Dict, 
        user_data: Dict, 
        duration_weeks: int
    ) -> Dict:
        """Build complete workout plan from template"""
        import random
        
        plan_data = {
            'plan_name': template['plan_name'],
            'duration_weeks': duration_weeks,
            'goal': template['goal'],
            'weeks': []
        }
        
        exercises_per_day = template['exercises_per_day']
        num_exercise_patterns = len(exercises_per_day)
        
        for week_num in range(1, duration_weeks + 1):
            week_data = {
                'week_number': week_num,
                'week_focus': f"Week {week_num} - Building Consistency",
                'days': []
            }
            
            for day_num in range(1, 8):  # 7 days per week
                if day_num in [6, 7]:  # Weekend rest days
                    day_data = {
                        'day_number': day_num,
                        'workout_name': f"Rest Day {day_num}",
                        'is_rest_day': True,
                        'exercises': [],
                        'confidence_task': "Rest and recovery - you're doing great!"
                    }
                else:
                    # Select exercise pattern
                    pattern_idx = (day_num - 1) % num_exercise_patterns
                    exercise_pattern = exercises_per_day[pattern_idx]
                    
                    exercises = []
                    for exercise_slug in exercise_pattern:
                        # Check if exercise exists, use fallback if not
                        final_exercise = self._ensure_exercise_exists(exercise_slug)
                        if final_exercise:
                            exercises.append({
                                'exercise_slug': final_exercise,
                                'sets': random.choice(template['sets_range']),
                                'reps': random.choice(template['reps_range']),
                                'rest_seconds': template['rest_seconds']
                            })
                    
                    day_data = {
                        'day_number': day_num,
                        'workout_name': f"Day {day_num} Workout",
                        'is_rest_day': False,
                        'exercises': exercises,
                        'confidence_task': f"Complete Day {day_num} - you're building strength!"
                    }
                
                week_data['days'].append(day_data)
            
            plan_data['weeks'].append(week_data)
        
        return plan_data
    
    def _ensure_exercise_exists(self, exercise_slug: str) -> Optional[str]:
        """Ensure exercise exists in database, return R2 fallback if not"""
        try:
            CSVExercise.objects.get(id=exercise_slug)
            return exercise_slug
        except CSVExercise.DoesNotExist:
            logger.warning(f"Exercise {exercise_slug} not found, using R2 fallback")
            # Use real R2 exercise names when database is empty
            return self._get_r2_exercise_fallback(exercise_slug)
    
    def _generate_minimal_emergency_plan(self, user_data: Dict) -> WorkoutPlanSchema:
        """Last resort - minimal plan that will definitely validate"""
        from .schemas import validate_ai_plan_response
        
        minimal_plan = {
            "plan_name": "Emergency Basic Plan",
            "duration_weeks": 4,
            "goal": "Stay active",
            "weeks": [
                {
                    "week_number": 1,
                    "week_focus": "Getting started",
                    "days": [
                        {
                            "day_number": 1,
                            "workout_name": "Basic Movement",
                            "is_rest_day": False,
                            "exercises": [
                                {
                                    "exercise_slug": "push-ups",
                                    "sets": 2,
                                    "reps": "5-8",
                                    "rest_seconds": 60
                                }
                            ],
                            "confidence_task": "You started - that's the hardest part!"
                        },
                        {
                            "day_number": 2,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Rest and recover"
                        },
                        {
                            "day_number": 3,
                            "workout_name": "Basic Movement",
                            "is_rest_day": False,
                            "exercises": [
                                {
                                    "exercise_slug": "squats",
                                    "sets": 2,
                                    "reps": "8-12",
                                    "rest_seconds": 60
                                }
                            ],
                            "confidence_task": "Building consistency"
                        },
                        {
                            "day_number": 4,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Recovery is important"
                        },
                        {
                            "day_number": 5,
                            "workout_name": "Basic Movement", 
                            "is_rest_day": False,
                            "exercises": [
                                {
                                    "exercise_slug": "planks",
                                    "sets": 2,
                                    "reps": "15-30 seconds",
                                    "rest_seconds": 45
                                }
                            ],
                            "confidence_task": "You're getting stronger!"
                        },
                        {
                            "day_number": 6,
                            "workout_name": "Weekend Rest",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Enjoy your weekend"
                        },
                        {
                            "day_number": 7,
                            "workout_name": "Weekend Rest",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Ready for next week"
                        }
                    ]
                },
                {
                    "week_number": 2,
                    "week_focus": "Building momentum",
                    "days": [
                        {
                            "day_number": 1,
                            "workout_name": "Progressive Movement",
                            "is_rest_day": False,
                            "exercises": [
                                {
                                    "exercise_slug": "push-ups",
                                    "sets": 3,
                                    "reps": "8-10",
                                    "rest_seconds": 60
                                },
                                {
                                    "exercise_slug": "squats",
                                    "sets": 3,
                                    "reps": "10-15",
                                    "rest_seconds": 60
                                }
                            ],
                            "confidence_task": "You're progressing!"
                        },
                        {
                            "day_number": 2,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Rest and prepare"
                        },
                        {
                            "day_number": 3,
                            "workout_name": "Full Body Basic",
                            "is_rest_day": False,
                            "exercises": [
                                {
                                    "exercise_slug": "jumping-jacks",
                                    "sets": 3,
                                    "reps": "30 seconds",
                                    "rest_seconds": 45
                                },
                                {
                                    "exercise_slug": "planks",
                                    "sets": 3,
                                    "reps": "20-45 seconds",
                                    "rest_seconds": 45
                                }
                            ],
                            "confidence_task": "You're building real habits!"
                        },
                        {
                            "day_number": 4,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Recovery helps you grow"
                        },
                        {
                            "day_number": 5,
                            "workout_name": "Challenge Day",
                            "is_rest_day": False,
                            "exercises": [
                                {
                                    "exercise_slug": "push-ups",
                                    "sets": 3,
                                    "reps": "max effort",
                                    "rest_seconds": 90
                                },
                                {
                                    "exercise_slug": "squats",
                                    "sets": 3,
                                    "reps": "max effort",
                                    "rest_seconds": 90
                                },
                                {
                                    "exercise_slug": "planks",
                                    "sets": 1,
                                    "reps": "max time",
                                    "rest_seconds": 90
                                }
                            ],
                            "confidence_task": "You've completed the program! Ready for more challenges?"
                        },
                        {
                            "day_number": 6,
                            "workout_name": "Victory Rest",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Celebrate your progress!"
                        },
                        {
                            "day_number": 7,
                            "workout_name": "Planning Day",
                            "is_rest_day": True,
                            "exercises": [],
                            "confidence_task": "Plan your next fitness journey!"
                        }
                    ]
                }
            ]
        }
        
        plan_json = json.dumps(minimal_plan)
        return validate_ai_plan_response(plan_json)