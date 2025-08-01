import logging
import json
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
        logger.info(f"=== WORKOUT COMPLETION START === User: {user.id}, Workout: {workout.id}")
        
        try:
            from apps.workouts.models import WorkoutExecution
            
            # Create or update workout execution
            logger.info("Creating workout execution...")
            execution, created = WorkoutExecution.objects.get_or_create(
                user=user,
                workout=workout,
                defaults={'started_at': timezone.now()}
            )
            logger.info(f"Workout execution {'created' if created else 'found'}: {execution.id}")
        except Exception as e:
            logger.error(f"Error creating workout execution: {str(e)}")
            raise
        
        try:
            execution.completed_at = timezone.now()
            execution.save()
            logger.info("Workout execution updated")
            
            # Update workout with feedback
            logger.info("Updating workout with feedback...")
            workout.completed_at = timezone.now()
            workout.feedback_rating = feedback_rating
            workout.feedback_note = feedback_note
            workout.save()
            
            # Update user profile stats
            logger.info("Updating user profile stats...")
            profile = user.profile
            profile.last_workout_at = timezone.now()
            profile.total_workouts_completed += 1
            profile.save()
            
            # Calculate and award XP
            logger.info("Calculating XP...")
            base_xp = 50  # Base XP for completing workout
            if not workout.is_rest_day:
                base_xp = 100
            
            # Bonus XP for perfect execution
            if feedback_rating == 'fire':
                base_xp += 25
            
            logger.info(f"Creating XP transaction: {base_xp} XP")
            XPTransaction.objects.create(
                user=user,
                amount=base_xp,
                transaction_type='workout_completed',
                description=f'Тренировка завершена: {workout.name}',
                workout_execution=execution
            )
            
            logger.info("Adding XP to profile...")
            profile.add_xp(base_xp)
            
            # Update daily progress
            logger.info("Updating daily progress...")
            progress = DailyProgress.update_for_user(user)
            progress.workouts_completed += 1
            progress.xp_earned += base_xp
            progress.save()
            
            # Check achievements
            logger.info("Checking achievements...")
            checker = AchievementChecker()
            new_achievements = checker.check_user_achievements(user)
            logger.info(f"Found {len(new_achievements)} new achievements")
        except Exception as e:
            logger.error(f"Error in workout completion process: {str(e)}")
            raise
        
        # 🔍 AI ANALYSIS - добавляем анализ тренировки
        ai_analysis = None
        try:
            logger.info("🔍 GPT-analysis started for workout %s user %s", workout.id, user.id)
            ai_analysis = self._analyze_workout_with_ai(user, workout, feedback_rating, feedback_note)
            logger.info("🔍 GPT analysis completed for workout %s", workout.id)
        except Exception as e:
            logger.error("🔍 GPT analysis failed for workout %s: %s", workout.id, str(e))
            # AI анализ не должен ломать весь процесс завершения тренировки
            ai_analysis = {
                'feedback': 'Отличная тренировка! Продолжайте в том же духе!',
                'fatigue_score': 5,
                'next_focus': 'Продолжайте развивать силу и выносливость!'
            }
        
        logger.info("=== WORKOUT COMPLETION SUCCESSFUL ===")
        return {
            'execution': execution,
            'xp_earned': base_xp,
            'new_achievements': new_achievements,
            'current_streak': profile.current_streak,
            'ai_analysis': ai_analysis
        }
    
    def _analyze_workout_with_ai(self, user, workout, feedback_rating, feedback_note):
        """Анализ тренировки с помощью AI"""
        from apps.ai_integration.ai_client import AIClientFactory
        
        # Создаем AI клиент
        ai_client = AIClientFactory.create_client()
        
        # Собираем данные о тренировке
        workout_data = {
            'workout_name': workout.name,
            'is_rest_day': workout.is_rest_day,
            'exercises': workout.exercises,
            'feedback_rating': feedback_rating,
            'feedback_note': feedback_note,
            'confidence_task': workout.confidence_task
        }
        
        # Создаем промпт для анализа
        prompt = f"""
        Analyze this completed workout and provide feedback:
        
        WORKOUT DETAILS:
        - Name: {workout.name}
        - Rest Day: {workout.is_rest_day}
        - Exercises: {len(workout.exercises if workout.exercises else [])} exercises
        - User Rating: {feedback_rating} (fire=great, smile=good, neutral=ok, tired=hard)
        - User Note: {feedback_note}
        - Confidence Task: {workout.confidence_task}
        
        USER PROFILE:
        - Total Workouts: {user.profile.total_workouts_completed}
        - Current Streak: {user.profile.current_streak}
        - Experience Level: {user.profile.experience_points} XP
        
        Please provide:
        1. Brief motivational feedback (2-3 sentences)
        2. Fatigue assessment (1-10 scale)
        3. Suggested focus for next workout
        
        Return JSON with keys: feedback, fatigue_score, next_focus
        """
        
        logger.info("🔍 GPT analysis prompt for workout %s: %s", workout.id, prompt[:200])
        
        # Вызываем AI
        response = ai_client.generate_completion(
            prompt,
            max_tokens=300,
            temperature=0.7
        )
        
        logger.info("🔍 GPT response for workout %s: %s", workout.id, str(response)[:400])
        
        # Если response это dict, возвращаем как есть
        if isinstance(response, dict):
            return response
        
        # Если строка, пытаемся парсить JSON
        if isinstance(response, str):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.warning("🔍 Failed to parse AI response as JSON: %s", response[:200])
                return {
                    'feedback': response[:200],
                    'fatigue_score': 5,
                    'next_focus': 'Continue your great progress!'
                }
        
        # Fallback
        return {
            'feedback': 'Great job completing your workout!',
            'fatigue_score': 5,
            'next_focus': 'Keep up the momentum!'
        }