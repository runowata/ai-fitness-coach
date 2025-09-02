"""
Service for materializing confirmed workout plans into daily workouts
"""
import logging
from typing import Dict, List, Any

from django.db import transaction
from django.utils import timezone

from apps.workouts.models import DailyWorkout, WorkoutPlan

logger = logging.getLogger(__name__)


def materialize_daily_workouts(plan: WorkoutPlan) -> List[DailyWorkout]:
    """
    Create DailyWorkout instances from a confirmed WorkoutPlan
    
    Args:
        plan: A WorkoutPlan instance with status='CONFIRMED'
        
    Returns:
        List of created DailyWorkout instances
    """
    if plan.status != 'CONFIRMED':
        logger.warning(f"Attempting to materialize non-confirmed plan {plan.id}")
        return []
    
    try:
        plan_data = plan.plan_data
        
        # Handle both new format (with report) and direct plan format
        if 'plan' in plan_data:
            weeks_data = plan_data['plan'].get('weeks', [])
        else:
            weeks_data = plan_data.get('weeks', [])
        
        if not weeks_data:
            logger.error(f"No weeks data found in plan {plan.id}")
            return []
        
        created_workouts = []
        
        with transaction.atomic():
            # Clear any existing daily workouts for this plan
            DailyWorkout.objects.filter(plan=plan).delete()
            
            # Track overall day number
            overall_day = 0
            
            for week_idx, week in enumerate(weeks_data, start=1):
                days_data = week.get('days', [])
                
                for day_idx, day in enumerate(days_data, start=1):
                    overall_day += 1
                    
                    # Extract exercise data
                    exercise_slugs = day.get('exercise_slugs', [])
                    is_rest_day = day.get('is_rest_day', False)
                    confidence_task = day.get('confidence_task', '')
                    
                    # Build exercises list with structure expected by frontend
                    exercises_list = []
                    if not is_rest_day and exercise_slugs:
                        for slug in exercise_slugs:
                            exercises_list.append({
                                'exercise_id': slug,
                                'sets': 3,  # Default sets
                                'reps': '8-12',  # Default reps
                                'rest': 60,  # Default rest in seconds
                            })
                    
                    # Determine workout name
                    if is_rest_day:
                        workout_name = 'Rest Day'
                    else:
                        workout_name = f'Week {week_idx} Day {day_idx}'
                    
                    # Create the daily workout
                    daily_workout = DailyWorkout.objects.create(
                        plan=plan,
                        day_number=overall_day,
                        week_number=week_idx,
                        name=workout_name,
                        exercises=exercises_list,
                        is_rest_day=is_rest_day,
                        confidence_task=confidence_task
                    )
                    
                    created_workouts.append(daily_workout)
                    logger.info(
                        f"Created DailyWorkout day {overall_day} "
                        f"(Week {week_idx} Day {day_idx}) for plan {plan.id}"
                    )
            
            # Update plan status to ACTIVE and set started_at
            plan.status = 'ACTIVE'
            plan.started_at = timezone.now()
            plan.save(update_fields=['status', 'started_at'])
            
            logger.info(
                f"Successfully materialized {len(created_workouts)} daily workouts "
                f"for plan {plan.id}"
            )
            
        return created_workouts
        
    except Exception as e:
        logger.error(f"Error materializing daily workouts for plan {plan.id}: {e}")
        return []


def get_plan_report(plan: WorkoutPlan) -> Dict[str, Any]:
    """
    Extract the AI-generated report from a workout plan
    
    Args:
        plan: A WorkoutPlan instance
        
    Returns:
        Dict containing the report data, or empty dict if no report
    """
    try:
        plan_data = plan.plan_data
        
        # Check for report in new format
        if 'report' in plan_data:
            return plan_data['report']
        
        # Check for legacy AI analysis
        if plan.ai_analysis and 'report' in plan.ai_analysis:
            return plan.ai_analysis['report']
        
        # No report found
        return {}
        
    except Exception as e:
        logger.error(f"Error extracting report from plan {plan.id}: {e}")
        return {}