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
        
        # Determine user parameters - enforce exactly 4 weeks as per ChatGPT plan
        experience = user_data.get('experience_level', 'beginner').lower()
        days_per_week = min(max(int(user_data.get('days_per_week', 3)), 2), 6)
        duration_weeks = 4  # Fixed to exactly 4 weeks per ChatGPT plan
        
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
        equipment: str = "bodyweight"
    ) -> Optional[str]:
        """
        Find fallback exercise when target is unavailable
        
        Note: muscle_groups parameter removed in Phase 5.6
        
        Priority:
        1. Same equipment type
        2. Basic fallback exercises
        3. Any available exercise
        """
        logger.info(f"Finding fallback for '{target_exercise}'")
        
        # Simple fallback list - use basic exercises (no muscle_groups matching)
        simple_fallbacks = [
            'push-ups',
            'squats', 
            'planks',
            'jumping-jacks'
        ]
        
        for fallback_slug in simple_fallbacks:
            if fallback_slug in self.fallback_exercises:
                logger.info(f"Simple fallback: {fallback_slug}")
                return fallback_slug
        
        # Ultimate fallback - use first available exercise from our reliable set
        if self.fallback_exercises:
            first_available = list(self.fallback_exercises.keys())[0]
            logger.warning(f"Ultimate fallback: {first_available}")
            return first_available
        
        logger.error(f"No fallback found for {target_exercise}")
        return None
    
    def create_emergency_workout(self, user_profile: UserProfile) -> Optional[DailyWorkout]:
        """
        Create a basic workout when all else fails
        Emergency 15-minute bodyweight routine
        """
        logger.warning(f"Creating emergency workout for user {user_profile.user.id}")
        
        # Use actual CSVExercise IDs from the database
        try:
            available_exercises = CSVExercise.objects.filter(
                is_active=True,
                level='beginner',
                exercise_type__in=['strength', 'cardio']
            ).order_by('id')[:4].values_list('id', flat=True)
            
            emergency_exercises = []
            for i, ex_id in enumerate(available_exercises):
                sets = 3 if i < 3 else 2
                reps = '5-10' if i == 0 else ('10-15' if i == 1 else ('20-30 seconds' if i == 2 else '30 seconds'))
                emergency_exercises.append((ex_id, sets, reps, 45))
                
            if not emergency_exercises:
                # Ultimate fallback if no exercises found
                emergency_exercises = [
                    ('EX001_v2', 3, '5-10', 45),  # Assume this exists
                ]
        except Exception as e:
            logger.error(f"Failed to load emergency exercises: {e}")
            emergency_exercises = [
                ('EX001_v2', 3, '5-10', 45),  # Ultimate fallback
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
            for order, (ex_id, sets, reps, rest) in enumerate(emergency_exercises, 1):
                try:
                    exercise = CSVExercise.objects.get(id=ex_id)
                    WorkoutExecution.objects.create(
                        workout=workout,
                        exercise=exercise,
                        sets=sets,
                        reps=reps,
                        rest_seconds=rest,
                        order=order
                    )
                except CSVExercise.DoesNotExist:
                    logger.warning(f"Emergency exercise {ex_id} not found, skipping")
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
            # Query most common exercises from database by actual exercise IDs
            # CSVExercise uses 'id' field (e.g., EX001_v2, EX002_v2, etc.)
            common_exercises = CSVExercise.objects.filter(
                is_active=True,
                level__in=['beginner', 'intermediate'],
                exercise_type__in=['strength', 'cardio']
            ).order_by('id')[:20].values('id', 'exercise_type')
            
            for exercise in common_exercises:
                reliable_exercises[exercise['id']] = {
                    'equipment': 'bodyweight'  # Default for CSVExercise
                }
                
        except Exception as e:
            logger.error(f"Failed to load reliable exercises: {e}")
            # Hardcoded fallback using technical names from R2
            reliable_exercises = {
                'push-ups': {'equipment': 'bodyweight'},
                'squats': {'equipment': 'bodyweight'},
                'planks': {'equipment': 'bodyweight'},
                'jumping-jacks': {'equipment': 'bodyweight'},
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
        # Use real exercise IDs from database
        try:
            available_exercises = list(CSVExercise.objects.filter(
                is_active=True
            ).order_by('id')[:20].values_list('id', flat=True))
        except Exception:
            # Fallback if database query fails
            available_exercises = ['CX001', 'CX002', 'CX003', 'CX004', 'CX005', 'CX006', 'CX007', 'CX008', 'CX009', 'CX010']
        
        # Use first 15 exercises and cycle through them
        base_exercises = available_exercises[:15] if len(available_exercises) >= 15 else available_exercises
        
        return {
            'beginner_3days': {
                'plan_name': 'Beginner 3-Day Foundation',
                'goal': 'Build basic fitness foundation',
                'exercises_per_day': [
                    base_exercises[:4],  # 4 exercises per day
                    base_exercises[4:8],  
                    base_exercises[8:12],
                ],
                'sets_range': [2, 3],
                'reps_range': ['5-8', '8-12'],
                'rest_seconds': 60,
            },
            'intermediate_4days': {
                'plan_name': 'Intermediate 4-Day Builder',
                'goal': 'Increase strength and endurance',
                'exercises_per_day': [
                    base_exercises[:4],
                    base_exercises[3:7], 
                    base_exercises[6:10],
                    base_exercises[9:13],
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
                    # Rest day with old schema format
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
                    
                    # Use old schema format with exercises directly on day
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
        
        # Use template builder for better exercise coverage
        logger.warning("Using template-based emergency plan")
        template_plan = self._build_plan_from_template(
            template=self.default_plan_templates['beginner_3days'],
            user_data=user_data,
            duration_weeks=4
        )
        
        plan_json = json.dumps(template_plan)
        return validate_ai_plan_response(plan_json)
        
        # Old hardcoded minimal plan (kept as backup)
        minimal_plan_backup = {
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
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Basic Exercise",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 2,
                                            "reps": "5-8",
                                            "rest_seconds": 60
                                        },
                                        {
                                            "exercise_slug": "EX002_v2",
                                            "sets": 2,
                                            "reps": "8-10",
                                            "rest_seconds": 60
                                        },
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 1,
                                            "reps": "20 seconds",
                                            "rest_seconds": 45
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "You started - that's the hardest part!",
                                    "description": "Daily motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 2,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Rest and recover",
                                    "description": "Rest day motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 3,
                            "workout_name": "Basic Movement",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Basic Exercise",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX002_v2",
                                            "sets": 2,
                                            "reps": "8-12",
                                            "rest_seconds": 60
                                        },
                                        {
                                            "exercise_slug": "EX004_v2",
                                            "sets": 2,
                                            "reps": "30 seconds",
                                            "rest_seconds": 45
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "Building consistency",
                                    "description": "Progress motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 4,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Recovery is important",
                                    "description": "Rest day wisdom"
                                }
                            ]
                        },
                        {
                            "day_number": 5,
                            "workout_name": "Basic Movement", 
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Basic Exercise",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 2,
                                            "reps": "15-30 seconds",
                                            "rest_seconds": 45
                                        },
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 1,
                                            "reps": "max effort",
                                            "rest_seconds": 60
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "You're getting stronger!",
                                    "description": "Progress celebration"
                                }
                            ]
                        },
                        {
                            "day_number": 6,
                            "workout_name": "Weekend Rest",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Enjoy your weekend",
                                    "description": "Weekend motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 7,
                            "workout_name": "Weekend Rest",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Ready for next week",
                                    "description": "Week transition"
                                }
                            ]
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
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Progressive Workout",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 3,
                                            "reps": "8-10",
                                            "rest_seconds": 60
                                        },
                                        {
                                            "exercise_slug": "EX002_v2",
                                            "sets": 3,
                                            "reps": "10-15",
                                            "rest_seconds": 60
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "You're progressing!",
                                    "description": "Week 2 progress celebration"
                                }
                            ]
                        },
                        {
                            "day_number": 2,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Rest and prepare",
                                    "description": "Preparation for next workout"
                                }
                            ]
                        },
                        {
                            "day_number": 3,
                            "workout_name": "Full Body Basic",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Full Body Training",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX004_v2",
                                            "sets": 3,
                                            "reps": "30 seconds",
                                            "rest_seconds": 45
                                        },
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 3,
                                            "reps": "20-45 seconds",
                                            "rest_seconds": 45
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "You're building real habits!",
                                    "description": "Habit formation motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 4,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Recovery helps you grow",
                                    "description": "Recovery importance"
                                }
                            ]
                        },
                        {
                            "day_number": 5,
                            "workout_name": "Challenge Day",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Challenge Workout",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 3,
                                            "reps": "max effort",
                                            "rest_seconds": 90
                                        },
                                        {
                                            "exercise_slug": "EX002_v2",
                                            "sets": 3,
                                            "reps": "max effort",
                                            "rest_seconds": 90
                                        },
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 1,
                                            "reps": "max time",
                                            "rest_seconds": 90
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "You've completed the program! Ready for more challenges?",
                                    "description": "Program completion celebration"
                                }
                            ]
                        },
                        {
                            "day_number": 6,
                            "workout_name": "Victory Rest",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Celebrate your progress!",
                                    "description": "Victory celebration"
                                }
                            ]
                        },
                        {
                            "day_number": 7,
                            "workout_name": "Planning Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Plan your next fitness journey!",
                                    "description": "Future planning motivation"
                                }
                            ]
                        }
                    ]
                },
                {
                    "week_number": 3,
                    "week_focus": "Strength building",
                    "days": [
                        {
                            "day_number": 1,
                            "workout_name": "Strength Focus",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Strength Workout",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 3,
                                            "reps": "10-12",
                                            "rest_seconds": 75
                                        },
                                        {
                                            "exercise_slug": "EX002_v2",
                                            "sets": 3,
                                            "reps": "12-15",
                                            "rest_seconds": 75
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "You're getting stronger every day!",
                                    "description": "Week 3 strength building motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 2,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Rest and recover for tomorrow",
                                    "description": "Week 3 rest day"
                                }
                            ]
                        },
                        {
                            "day_number": 3,
                            "workout_name": "Endurance Focus",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Endurance Training",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 2,
                                            "reps": "45 seconds",
                                            "rest_seconds": 30
                                        },
                                        {
                                            "exercise_slug": "EX004_v2",
                                            "sets": 2,
                                            "reps": "30 seconds",
                                            "rest_seconds": 30
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "Your endurance is improving!",
                                    "description": "Endurance progress motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 4,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Recovery builds strength",
                                    "description": "Mid-week recovery"
                                }
                            ]
                        },
                        {
                            "day_number": 5,
                            "workout_name": "Combined Training",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Mixed Workout",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 2,
                                            "reps": "8-10",
                                            "rest_seconds": 60
                                        },
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 2,
                                            "reps": "30 seconds",
                                            "rest_seconds": 45
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "You're mastering the basics!",
                                    "description": "Skill mastery celebration"
                                }
                            ]
                        },
                        {
                            "day_number": 6,
                            "workout_name": "Weekend Rest",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Enjoy your weekend break",
                                    "description": "Weekend rest motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 7,
                            "workout_name": "Weekend Rest",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Ready for week 4!",
                                    "description": "Preparation for final week"
                                }
                            ]
                        }
                    ]
                },
                {
                    "week_number": 4,
                    "week_focus": "Final challenge",
                    "days": [
                        {
                            "day_number": 1,
                            "workout_name": "Final Challenge",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Challenge Workout",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 4,
                                            "reps": "max effort",
                                            "rest_seconds": 90
                                        },
                                        {
                                            "exercise_slug": "EX002_v2",
                                            "sets": 4,
                                            "reps": "max effort",
                                            "rest_seconds": 90
                                        },
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 2,
                                            "reps": "max time",
                                            "rest_seconds": 90
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "Final week - show your strength!",
                                    "description": "Final week motivation"
                                }
                            ]
                        },
                        {
                            "day_number": 2,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "You're almost there!",
                                    "description": "Near completion encouragement"
                                }
                            ]
                        },
                        {
                            "day_number": 3,
                            "workout_name": "Final Test",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Final Assessment",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX004_v2",
                                            "sets": 3,
                                            "reps": "60 seconds",
                                            "rest_seconds": 60
                                        },
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 2,
                                            "reps": "15-20",
                                            "rest_seconds": 90
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "Look how far you've come!",
                                    "description": "Progress reflection"
                                }
                            ]
                        },
                        {
                            "day_number": 4,
                            "workout_name": "Rest Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Prepare for graduation!",
                                    "description": "Pre-completion rest"
                                }
                            ]
                        },
                        {
                            "day_number": 5,
                            "workout_name": "Graduation Day",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "main",
                                    "name": "Graduation Workout",
                                    "exercises": [
                                        {
                                            "exercise_slug": "EX001_v2",
                                            "sets": 3,
                                            "reps": "personal best",
                                            "rest_seconds": 120
                                        },
                                        {
                                            "exercise_slug": "EX002_v2",
                                            "sets": 3,
                                            "reps": "personal best",
                                            "rest_seconds": 120
                                        },
                                        {
                                            "exercise_slug": "EX003_v2",
                                            "sets": 1,
                                            "reps": "maximum time",
                                            "rest_seconds": 120
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "🎉 CONGRATULATIONS! You completed the 4-week program!",
                                    "description": "Program completion celebration"
                                }
                            ]
                        },
                        {
                            "day_number": 6,
                            "workout_name": "Victory Rest",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "Celebrate your achievement!",
                                    "description": "Victory celebration"
                                }
                            ]
                        },
                        {
                            "day_number": 7,
                            "workout_name": "Planning Day",
                            "is_rest_day": True,
                            "blocks": [
                                {
                                    "type": "confidence_task",
                                    "text": "What's your next fitness goal?",
                                    "description": "Future planning motivation"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        plan_json = json.dumps(minimal_plan)
        return validate_ai_plan_response(plan_json)