import logging
from django.db import transaction
from django.utils import timezone
from .models import Achievement, UserAchievement, XPTransaction, DailyProgress

logger = logging.getLogger(__name__)


class AchievementChecker:
    """Service to check and unlock user achievements"""
    
    def check_user_achievements(self, user):
        """Check all possible achievements for a user"""
        new_achievements = []
        profile = user.profile
        
        # Get all achievements not yet unlocked by user
        unlocked_ids = user.achievements.values_list('achievement_id', flat=True)
        available_achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(id__in=unlocked_ids)
        
        for achievement in available_achievements:
            if self._check_single_achievement(user, achievement):
                new_achievement = self._unlock_achievement(user, achievement)
                new_achievements.append(new_achievement)
        
        return new_achievements
    
    def _check_single_achievement(self, user, achievement):
        """Check if user meets criteria for a specific achievement"""
        profile = user.profile
        
        if achievement.trigger_type == 'workout_count':
            return profile.total_workouts_completed >= achievement.trigger_value
            
        elif achievement.trigger_type == 'streak_days':
            return profile.current_streak >= achievement.trigger_value
            
        elif achievement.trigger_type == 'xp_earned':
            return profile.experience_points >= achievement.trigger_value
            
        elif achievement.trigger_type == 'plan_completed':
            completed_plans = user.workout_plans.filter(
                completed_at__isnull=False
            ).count()
            return completed_plans >= achievement.trigger_value
            
        elif achievement.trigger_type == 'perfect_week':
            # Check if user completed all workouts in the last week
            week_ago = timezone.now() - timezone.timedelta(days=7)
            daily_progress = DailyProgress.objects.filter(
                user=user,
                date__gte=week_ago.date(),
                workouts_completed__gt=0
            ).count()
            return daily_progress >= 7
            
        elif achievement.trigger_type == 'confidence_tasks':
            # Count completed confidence tasks
            completed_tasks = user.workout_executions.filter(
                workout__confidence_task__isnull=False,
                completed_at__isnull=False
            ).count()
            return completed_tasks >= achievement.trigger_value
            
        return False
    
    @transaction.atomic
    def _unlock_achievement(self, user, achievement):
        """Unlock achievement and grant rewards"""
        # Create achievement record
        user_achievement = UserAchievement.objects.create(
            user=user,
            achievement=achievement
        )
        
        # Grant XP reward
        if achievement.xp_reward > 0:
            XPTransaction.objects.create(
                user=user,
                amount=achievement.xp_reward,
                transaction_type='achievement_unlocked',
                description=f'Достижение разблокировано: {achievement.name}',
                achievement=achievement
            )
            user.profile.add_xp(achievement.xp_reward)
        
        # Unlock story chapter if applicable
        if achievement.unlocks_story_chapter:
            from apps.content.models import UserStoryAccess
            UserStoryAccess.objects.get_or_create(
                user=user,
                chapter=achievement.unlocks_story_chapter,
                defaults={'unlocked_by_achievement': achievement}
            )
        
        logger.info(f"Achievement unlocked: {achievement.name} for user {user.email}")
        return user_achievement


class WorkoutCompletionService:
    """Service to handle workout completion logic"""
    
    @transaction.atomic
    def complete_workout(self, user, workout, feedback_rating=None, feedback_note=''):
        """Mark workout as completed and update all related data"""
        from apps.workouts.models import WorkoutExecution
        
        # Create or update workout execution
        execution, created = WorkoutExecution.objects.get_or_create(
            user=user,
            workout=workout,
            defaults={'started_at': timezone.now()}
        )
        
        execution.completed_at = timezone.now()
        execution.save()
        
        # Update workout with feedback
        workout.completed_at = timezone.now()
        workout.feedback_rating = feedback_rating
        workout.feedback_note = feedback_note
        workout.save()
        
        # Update user profile stats
        profile = user.profile
        profile.last_workout_at = timezone.now()
        profile.total_workouts_completed += 1
        profile.save()
        
        # Calculate and award XP
        base_xp = 50  # Base XP for completing workout
        if not workout.is_rest_day:
            base_xp = 100
        
        # Bonus XP for perfect execution
        if feedback_rating == 'fire':
            base_xp += 25
        
        XPTransaction.objects.create(
            user=user,
            amount=base_xp,
            transaction_type='workout_completed',
            description=f'Тренировка завершена: {workout.name}',
            workout_execution=execution
        )
        profile.add_xp(base_xp)
        
        # Update daily progress
        progress = DailyProgress.update_for_user(user)
        progress.workouts_completed += 1
        progress.xp_earned += base_xp
        progress.save()
        
        # Check achievements
        checker = AchievementChecker()
        new_achievements = checker.check_user_achievements(user)
        
        return {
            'execution': execution,
            'xp_earned': base_xp,
            'new_achievements': new_achievements,
            'current_streak': profile.current_streak
        }