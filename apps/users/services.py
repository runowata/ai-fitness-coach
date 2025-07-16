from django.utils import timezone
from apps.workouts.models import WorkoutPlan, DailyWorkout


class UserDashboardService:
    """Service for user dashboard operations"""
    
    @staticmethod
    def create_default_workout_plan(user):
        """Create a basic default workout plan for user"""
        workout_plan = WorkoutPlan.objects.create(
            user=user,
            name="Базовый план тренировок",
            duration_weeks=6,
            goal="general_fitness",
            plan_data={"plan_name": "Базовый план", "weeks": []},
            is_active=True,
            started_at=timezone.now()
        )
        
        # Create a simple daily workout
        DailyWorkout.objects.create(
            plan=workout_plan,
            week_number=1,
            day_number=1,
            name="Базовая тренировка",
            exercises=[
                {"exercise_slug": "push_ups", "sets": 3, "reps": "8-12", "rest_seconds": 60},
                {"exercise_slug": "squats", "sets": 3, "reps": "10-15", "rest_seconds": 60},
                {"exercise_slug": "plank", "sets": 3, "reps": "30 сек", "rest_seconds": 60}
            ],
            confidence_task="Сделайте 5 глубоких вдохов после тренировки"
        )
        
        return workout_plan
    
    @staticmethod
    def get_dashboard_context(user):
        """Get all context data for dashboard"""
        # Get active workout plan
        workout_plan = user.workout_plans.filter(is_active=True).first()
        
        if not workout_plan:
            # Create a basic default workout plan
            workout_plan = UserDashboardService.create_default_workout_plan(user)
        
        # Get today's workout
        current_week = workout_plan.get_current_week()
        days_since_start = (timezone.now() - workout_plan.started_at).days if workout_plan.started_at else 0
        current_day = (days_since_start % 7) + 1
        
        today_workout = workout_plan.daily_workouts.filter(
            week_number=current_week,
            day_number=current_day
        ).first()
        
        # Check achievements
        from apps.achievements.services import AchievementChecker
        checker = AchievementChecker()
        new_achievements = checker.check_user_achievements(user)
        
        # Check if user has completed 6-week program and should see cycle options
        program_completion_available = False
        from apps.workouts.cycle_service import ProgramCycleService
        cycle_service = ProgramCycleService()
        completion_data = cycle_service.check_program_completion(user)
        if completion_data:
            program_completion_available = True
        
        return {
            'user': user,
            'workout_plan': workout_plan,
            'today_workout': today_workout,
            'current_week': current_week,
            'new_achievements': new_achievements,
            'streak': user.current_streak,
            'xp': user.experience_points,
            'level': user.level,
            'program_completion_available': program_completion_available,
        }