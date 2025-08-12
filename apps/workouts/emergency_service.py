"""
Emergency Workout Service
Provides emergency workouts when regular system fails
"""
import logging
from typing import Optional
from django.utils import timezone

from apps.users.models import UserProfile
from apps.workouts.models import WorkoutPlan, DailyWorkout, WorkoutExercise, CSVExercise
from apps.ai_integration.fallback_service import FallbackService

logger = logging.getLogger(__name__)


class EmergencyWorkoutService:
    """Creates emergency workouts when all else fails"""
    
    def __init__(self):
        self.fallback_service = FallbackService()
    
    def get_or_create_emergency_workout(self, user_profile: UserProfile) -> Optional[DailyWorkout]:
        """
        Get today's workout or create emergency workout if none exists
        
        This is the ultimate fallback when:
        1. AI generation failed
        2. No workout plan exists
        3. User needs something TODAY
        """
        today = timezone.now().date()
        user = user_profile.user
        
        try:
            # First, try to find existing workout for today
            existing_workout = DailyWorkout.objects.filter(
                plan__user=user,
                workout_date=today
            ).first()
            
            if existing_workout:
                logger.info(f"Found existing workout for user {user.id} on {today}")
                return existing_workout
            
            # No workout for today - check if user has any active plan
            active_plan = WorkoutPlan.objects.filter(user=user).first()
            
            if not active_plan:
                # No plan at all - create emergency plan and workout
                logger.warning(f"No active plan for user {user.id}, creating emergency plan")
                emergency_workout = self.fallback_service.create_emergency_workout(user_profile)
                return emergency_workout
            
            # Has plan but no workout for today - create emergency workout for today
            logger.info(f"User {user.id} has plan but no workout for {today}, creating emergency workout")
            emergency_workout = self._create_emergency_workout_for_plan(active_plan, today)
            return emergency_workout
            
        except Exception as e:
            logger.error(f"Failed to get/create emergency workout for user {user.id}: {e}")
            return None
    
    def _create_emergency_workout_for_plan(self, plan: WorkoutPlan, date) -> Optional[DailyWorkout]:
        """Create an emergency workout within an existing plan"""
        try:
            workout = DailyWorkout.objects.create(
                plan=plan,
                workout_date=date,
                workout_name="Emergency Quick Workout",
                is_rest_day=False,
                confidence_task="You showed up when it was hard - that's real strength!"
            )
            
            # Add 3 basic exercises
            emergency_exercises = [
                ('push_ups', 2, '5-8', 60),
                ('squats', 2, '8-12', 60),
                ('plank', 2, '15-30 seconds', 45),
            ]
            
            for order, (slug, sets, reps, rest) in enumerate(emergency_exercises, 1):
                try:
                    exercise = CSVExercise.objects.get(slug=slug)
                    WorkoutExercise.objects.create(
                        workout=workout,
                        exercise=exercise,
                        sets=sets,
                        reps=reps,
                        rest_seconds=rest,
                        order=order
                    )
                except CSVExercise.DoesNotExist:
                    # Try fallback exercise
                    fallback_slug = self.fallback_service.get_fallback_exercise(
                        slug, ['general'], 'bodyweight'
                    )
                    if fallback_slug:
                        try:
                            exercise = CSVExercise.objects.get(slug=fallback_slug)
                            WorkoutExercise.objects.create(
                                workout=workout,
                                exercise=exercise,
                                sets=sets,
                                reps=reps,
                                rest_seconds=rest,
                                order=order
                            )
                        except CSVExercise.DoesNotExist:
                            logger.warning(f"Even fallback exercise {fallback_slug} not found")
                            continue
                    else:
                        logger.warning(f"No fallback found for {slug}")
                        continue
            
            logger.info(f"Created emergency workout {workout.id} for plan {plan.id}")
            return workout
            
        except Exception as e:
            logger.error(f"Failed to create emergency workout for plan {plan.id}: {e}")
            return None
    
    def create_minimal_workout_json(self) -> dict:
        """
        Create a minimal workout JSON for absolute emergencies
        When even database operations fail
        """
        return {
            "workout_name": "Emergency Bodyweight Circuit",
            "exercises": [
                {
                    "name": "Push-ups",
                    "description": "Classic upper body exercise",
                    "sets": 2,
                    "reps": "5-10",
                    "rest_seconds": 60
                },
                {
                    "name": "Squats", 
                    "description": "Lower body strength exercise",
                    "sets": 2,
                    "reps": "8-15",
                    "rest_seconds": 60
                },
                {
                    "name": "Plank",
                    "description": "Core stability exercise", 
                    "sets": 2,
                    "reps": "15-30 seconds",
                    "rest_seconds": 45
                }
            ],
            "total_time": "10-15 minutes",
            "confidence_task": "You're taking care of yourself - that's what matters!",
            "emergency": True,
            "message": "This is an emergency workout. Our system will be back to normal soon!"
        }


class VideoFallbackService:
    """Handles video fallback scenarios"""
    
    @staticmethod
    def get_text_instructions(exercise_slug: str) -> dict:
        """
        Get basic text instructions when videos fail
        Fallback for when video playlist builder fails
        """
        # Basic instructions for common exercises
        instructions = {
            'push_ups': {
                'setup': 'Start in plank position with hands under shoulders',
                'execution': 'Lower body until chest nearly touches ground, push back up',
                'tips': 'Keep core tight, body in straight line',
                'common_mistakes': 'Sagging hips, partial range of motion'
            },
            'squats': {
                'setup': 'Stand with feet shoulder-width apart',
                'execution': 'Lower by pushing hips back, knees track over toes, return to standing',
                'tips': 'Keep chest up, weight in heels',
                'common_mistakes': 'Knees caving in, not going low enough'
            },
            'plank': {
                'setup': 'Start in push-up position on forearms',
                'execution': 'Hold position, maintaining straight line from head to heels',
                'tips': 'Engage core, breathe normally',
                'common_mistakes': 'Sagging hips, holding breath'
            },
            'jumping_jacks': {
                'setup': 'Stand with feet together, arms at sides',
                'execution': 'Jump feet apart while raising arms overhead, reverse',
                'tips': 'Land softly, maintain rhythm',
                'common_mistakes': 'Landing hard, irregular timing'
            },
            'lunges': {
                'setup': 'Stand tall with feet hip-width apart',
                'execution': 'Step forward, lower until both knees at 90 degrees, return',
                'tips': 'Keep front knee over ankle, chest up',
                'common_mistakes': 'Knee going past toes, leaning forward'
            }
        }
        
        return instructions.get(exercise_slug, {
            'setup': 'Follow proper form as best you can',
            'execution': 'Perform the movement with control',
            'tips': 'Focus on quality over quantity',
            'common_mistakes': 'Rushing through the movement'
        })
    
    @staticmethod
    def get_emergency_playlist() -> list:
        """
        Get emergency playlist with text-only content
        When video system completely fails
        """
        return [
            {
                'type': 'welcome',
                'content': 'Welcome to your emergency workout! Videos are temporarily unavailable, but we have text instructions to guide you.',
                'duration': 'Read as needed'
            },
            {
                'type': 'safety',
                'content': 'Safety first: Stop if you feel pain, work within your limits, and focus on proper form over speed.',
                'duration': 'Important reminder'
            },
            {
                'type': 'motivation',
                'content': 'You showed up today despite technical difficulties - that shows real commitment to your fitness journey!',
                'duration': 'Quick motivation'
            }
        ]