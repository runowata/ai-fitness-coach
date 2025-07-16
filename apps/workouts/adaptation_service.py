import logging
from typing import Dict, List
from django.utils import timezone
from django.db.models import Q

from .models import WorkoutPlan, DailyWorkout, WeeklyFeedback
from apps.ai_integration.services import WorkoutPlanGenerator

logger = logging.getLogger(__name__)


class WeeklyAdaptationService:
    """Service to handle weekly plan adaptation based on user feedback"""
    
    def __init__(self):
        self.generator = WorkoutPlanGenerator()
    
    def adapt_plan_for_week(self, user, plan: WorkoutPlan, week_number: int) -> bool:
        """
        Adapt the workout plan for the upcoming week based on user feedback
        Returns True if adaptation was successful, False otherwise
        """
        try:
            # Get user feedback for previous weeks
            feedback_data = self._collect_feedback_data(user, plan, week_number)
            
            if not feedback_data:
                logger.info(f"No feedback data available for user {user.id} week {week_number}")
                return False
            
            # Generate adaptation using AI
            current_plan_data = plan.plan_data
            adaptation = self.generator.adapt_weekly_plan(
                current_plan=current_plan_data,
                user_feedback=feedback_data,
                week_number=week_number,
                user_archetype=user.archetype or 'bro'
            )
            
            # Apply the adaptation to the plan
            updated_plan = self._apply_adaptation_to_plan(plan, adaptation, week_number)
            
            if updated_plan:
                # Save the updated plan
                plan.plan_data = updated_plan
                plan.last_adaptation_date = timezone.now()
                plan.adaptation_count += 1
                plan.save()
                
                # Update individual DailyWorkout records
                self._update_daily_workouts(plan, updated_plan, week_number)
                
                logger.info(f"Successfully adapted plan for user {user.id} week {week_number}")
                return True
            
        except Exception as e:
            logger.error(f"Error adapting plan for user {user.id} week {week_number}: {str(e)}")
            return False
        
        return False
    
    def _collect_feedback_data(self, user, plan: WorkoutPlan, week_number: int) -> List[Dict]:
        """Collect and format user feedback for AI processing"""
        feedback_data = []
        
        # Get feedback from previous weeks (up to 3 weeks back)
        start_week = max(1, week_number - 3)
        feedbacks = WeeklyFeedback.objects.filter(
            user=user,
            plan=plan,
            week_number__gte=start_week,
            week_number__lt=week_number
        ).order_by('week_number')
        
        for feedback in feedbacks:
            # Get completion data for that week
            week_workouts = DailyWorkout.objects.filter(
                plan=plan,
                week_number=feedback.week_number
            )
            
            completed_workouts = week_workouts.filter(completed_at__isnull=False).count()
            total_workouts = week_workouts.count()
            
            feedback_data.append({
                'week_number': feedback.week_number,
                'completion_rate': (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0,
                'overall_difficulty': feedback.overall_difficulty,
                'energy_level': feedback.energy_level,
                'motivation_level': feedback.motivation_level,
                'strength_progress': feedback.strength_progress,
                'confidence_progress': feedback.confidence_progress,
                'challenging_exercises': feedback.most_challenging_exercises,
                'favorite_exercises': feedback.favorite_exercises,
                'wants_more_cardio': feedback.wants_more_cardio,
                'wants_more_strength': feedback.wants_more_strength,
                'wants_shorter_workouts': feedback.wants_shorter_workouts,
                'wants_longer_workouts': feedback.wants_longer_workouts,
                'what_worked_well': feedback.what_worked_well,
                'what_needs_improvement': feedback.what_needs_improvement,
                'additional_notes': feedback.additional_notes
            })
        
        return feedback_data
    
    def _apply_adaptation_to_plan(self, plan: WorkoutPlan, adaptation: Dict, week_number: int) -> Dict:
        """Apply the AI-generated adaptation to the workout plan"""
        current_plan = plan.plan_data.copy()
        
        # Find the week to adapt
        if week_number <= len(current_plan.get('weeks', [])):
            week_index = week_number - 1
            week_data = current_plan['weeks'][week_index]
            
            # Apply intensity adjustments
            intensity_adjustment = adaptation.get('intensity_adjustment', 'maintain')
            if intensity_adjustment == 'increase':
                week_data['intensity_level'] = 'high'
            elif intensity_adjustment == 'decrease':
                week_data['intensity_level'] = 'low'
            
            # Apply exercise swaps
            exercise_swaps = adaptation.get('exercise_swaps', [])
            for swap in exercise_swaps:
                self._swap_exercise_in_week(week_data, swap['from'], swap['to'])
            
            # Apply volume changes
            volume_changes = adaptation.get('volume_changes', {})
            for exercise_slug, changes in volume_changes.items():
                self._update_exercise_volume(week_data, exercise_slug, changes)
            
            # Add adaptation notes
            archetype = plan.user.archetype or 'bro'
            adaptation_notes = {
                'bro_motivation': adaptation.get('bro_motivation'),
                'sergeant_orders': adaptation.get('sergeant_orders'),
                'research_insights': adaptation.get('research_insights'),
                'additional_notes': adaptation.get('additional_notes')
            }
            
            week_data['adaptation_notes'] = adaptation_notes
            week_data['adapted_at'] = timezone.now().isoformat()
            
            return current_plan
        
        return None
    
    def _swap_exercise_in_week(self, week_data: Dict, from_exercise: str, to_exercise: str):
        """Swap an exercise in all workouts of a week"""
        for day in week_data.get('days', []):
            if not day.get('is_rest_day', False):
                exercises = day.get('exercises', [])
                for exercise in exercises:
                    if exercise.get('exercise_slug') == from_exercise:
                        exercise['exercise_slug'] = to_exercise
                        exercise['exercise_name'] = to_exercise.replace('-', ' ').title()
    
    def _update_exercise_volume(self, week_data: Dict, exercise_slug: str, changes: Dict):
        """Update volume (sets/reps) for an exercise in a week"""
        for day in week_data.get('days', []):
            if not day.get('is_rest_day', False):
                exercises = day.get('exercises', [])
                for exercise in exercises:
                    if exercise.get('exercise_slug') == exercise_slug:
                        if 'sets' in changes:
                            exercise['sets'] = changes['sets']
                        if 'reps' in changes:
                            exercise['reps'] = changes['reps']
    
    def _update_daily_workouts(self, plan: WorkoutPlan, updated_plan: Dict, week_number: int):
        """Update DailyWorkout records with the adapted plan"""
        if week_number <= len(updated_plan.get('weeks', [])):
            week_data = updated_plan['weeks'][week_number - 1]
            
            # Update existing DailyWorkout records
            for day_data in week_data.get('days', []):
                try:
                    daily_workout = DailyWorkout.objects.get(
                        plan=plan,
                        week_number=week_number,
                        day_number=day_data.get('day_number')
                    )
                    
                    # Update exercises
                    daily_workout.exercises = day_data.get('exercises', [])
                    daily_workout.save()
                    
                except DailyWorkout.DoesNotExist:
                    logger.warning(f"DailyWorkout not found for plan {plan.id} week {week_number} day {day_data.get('day_number')}")
    
    def should_adapt_plan(self, user, plan: WorkoutPlan, week_number: int) -> bool:
        """
        Check if the plan should be adapted for the given week
        Returns True if adaptation is needed and possible
        """
        # Check if we have feedback for previous weeks
        has_feedback = WeeklyFeedback.objects.filter(
            user=user,
            plan=plan,
            week_number__lt=week_number
        ).exists()
        
        if not has_feedback:
            return False
        
        # Check if already adapted recently
        if plan.last_adaptation_date:
            days_since_last = (timezone.now() - plan.last_adaptation_date).days
            if days_since_last < 7:  # Don't adapt more than once per week
                return False
        
        # Check if week is valid for adaptation
        if week_number < 2 or week_number > plan.duration_weeks:
            return False
        
        return True
    
    def get_adaptation_summary(self, plan: WorkoutPlan, week_number: int) -> Dict:
        """Get a summary of adaptations made to the plan"""
        if week_number <= len(plan.plan_data.get('weeks', [])):
            week_data = plan.plan_data['weeks'][week_number - 1]
            adaptation_notes = week_data.get('adaptation_notes', {})
            
            if adaptation_notes:
                return {
                    'week_number': week_number,
                    'adapted_at': week_data.get('adapted_at'),
                    'adaptation_count': plan.adaptation_count,
                    'notes': adaptation_notes
                }
        
        return None