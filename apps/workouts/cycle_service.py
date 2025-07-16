import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db.models import Q, Count

from .models import WorkoutPlan, DailyWorkout, WeeklyFeedback
from .services import VideoPlaylistBuilder
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.users.models import User
from apps.achievements.services import AchievementChecker

logger = logging.getLogger(__name__)


class ProgramCycleService:
    """Service to handle completion of 6-week programs and cycle to new ones"""
    
    def __init__(self):
        self.generator = WorkoutPlanGenerator()
        self.achievement_checker = AchievementChecker()
        self.video_builder = VideoPlaylistBuilder()
    
    def check_program_completion(self, user: User) -> Optional[Dict]:
        """
        Check if user has completed their 6-week program
        Returns completion data if completed, None otherwise
        """
        # Get user's current active plan
        current_plan = WorkoutPlan.objects.filter(
            user=user,
            is_active=True,
            is_confirmed=True
        ).first()
        
        if not current_plan:
            return None
        
        # Check if 6 weeks are completed
        if current_plan.is_6_weeks_completed():
            completion_stats = current_plan.get_program_completion_stats()
            
            # Get user progress data
            progress_data = self._analyze_user_progress(user, current_plan)
            
            return {
                'plan': current_plan,
                'completion_stats': completion_stats,
                'progress_data': progress_data,
                'completion_detected_at': timezone.now()
            }
        
        return None
    
    def _analyze_user_progress(self, user: User, plan: WorkoutPlan) -> Dict:
        """Analyze user's progress over the 6 weeks"""
        
        # Get all feedback for the plan
        feedbacks = WeeklyFeedback.objects.filter(
            user=user,
            plan=plan
        ).order_by('week_number')
        
        # Calculate average ratings
        avg_strength_progress = 0
        avg_confidence_progress = 0
        total_feedback_weeks = feedbacks.count()
        
        if total_feedback_weeks > 0:
            avg_strength_progress = sum(f.strength_progress for f in feedbacks) / total_feedback_weeks
            avg_confidence_progress = sum(f.confidence_progress for f in feedbacks) / total_feedback_weeks
        
        # Get workout completion consistency
        completion_by_week = []
        for week in range(1, 7):
            week_workouts = plan.daily_workouts.filter(week_number=week, is_rest_day=False)
            completed_workouts = week_workouts.filter(completed_at__isnull=False)
            completion_by_week.append({
                'week': week,
                'total': week_workouts.count(),
                'completed': completed_workouts.count(),
                'rate': (completed_workouts.count() / week_workouts.count() * 100) if week_workouts.count() > 0 else 0
            })
        
        # Analyze exercise preferences from feedback
        challenging_exercises = []
        favorite_exercises = []
        
        for feedback in feedbacks:
            challenging_exercises.extend(feedback.most_challenging_exercises)
            favorite_exercises.extend(feedback.favorite_exercises)
        
        # Count exercise mentions
        challenging_count = {}
        favorite_count = {}
        
        for exercise in challenging_exercises:
            challenging_count[exercise] = challenging_count.get(exercise, 0) + 1
        
        for exercise in favorite_exercises:
            favorite_count[exercise] = favorite_count.get(exercise, 0) + 1
        
        # Get top mentioned exercises
        top_challenging = sorted(challenging_count.items(), key=lambda x: x[1], reverse=True)[:5]
        top_favorites = sorted(favorite_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'avg_strength_progress': round(avg_strength_progress, 1),
            'avg_confidence_progress': round(avg_confidence_progress, 1),
            'total_feedback_weeks': total_feedback_weeks,
            'completion_by_week': completion_by_week,
            'top_challenging_exercises': top_challenging,
            'top_favorite_exercises': top_favorites,
            'total_workouts_completed': plan.daily_workouts.filter(completed_at__isnull=False).count(),
            'workout_streak': self._calculate_workout_streak(user),
        }
    
    def _calculate_workout_streak(self, user: User) -> int:
        """Calculate current workout streak"""
        # This would ideally be stored in user profile, for now calculate basic version
        recent_workouts = DailyWorkout.objects.filter(
            plan__user=user,
            completed_at__isnull=False
        ).order_by('-completed_at')[:30]
        
        if not recent_workouts:
            return 0
        
        # Simple streak calculation - consecutive days
        streak = 1
        current_date = recent_workouts[0].completed_at.date()
        
        for workout in recent_workouts[1:]:
            workout_date = workout.completed_at.date()
            days_diff = (current_date - workout_date).days
            
            if days_diff == 1:
                streak += 1
                current_date = workout_date
            else:
                break
        
        return streak
    
    def generate_new_cycle_options(self, user: User, completion_data: Dict) -> Dict:
        """
        Generate options for the next 6-week cycle based on user's progress
        """
        progress_data = completion_data['progress_data']
        current_plan = completion_data['plan']
        
        # Determine user's evolved goals based on progress
        evolved_goals = self._determine_evolved_goals(user, progress_data)
        
        # Generate 3 different cycle options
        cycle_options = []
        
        option_templates = [
            {
                'name': 'Интенсивность++',
                'description': 'Увеличиваем нагрузку и сложность упражнений',
                'focus': 'intensity_increase',
                'archetype_message': {
                    'bro': 'Братан, пора поднять планку! Готов к более серьезным вызовам?',
                    'sergeant': 'Боец, базовая подготовка завершена! Переходим к продвинутому тренингу!',
                    'intellectual': 'Анализ показывает готовность к прогрессивной перегрузке!'
                }
            },
            {
                'name': 'Новые горизонты',
                'description': 'Добавляем новые типы упражнений и тренировочные методики',
                'focus': 'variety_expansion',
                'archetype_message': {
                    'bro': 'Давай попробуем что-то новенькое! Разнообразие - это круто!',
                    'sergeant': 'Пора освоить новые боевые навыки! Расширяем арсенал!',
                    'intellectual': 'Время для экспериментов с новыми тренировочными протоколами!'
                }
            },
            {
                'name': 'Персональная настройка',
                'description': 'Фокусируемся на ваших любимых упражнениях и улучшаем слабые места',
                'focus': 'personalized_optimization',
                'archetype_message': {
                    'bro': 'Братан, давай сделаем программу идеально под тебя!',
                    'sergeant': 'Устраняем слабые места и усиливаем преимущества!',
                    'intellectual': 'Оптимизируем программу на основе собранных данных!'
                }
            }
        ]
        
        for template in option_templates:
            # Generate preview for this option
            cycle_preview = self._generate_cycle_preview(
                user, 
                current_plan, 
                progress_data, 
                template['focus']
            )
            
            cycle_options.append({
                'name': template['name'],
                'description': template['description'],
                'focus': template['focus'],
                'message': template['archetype_message'].get(user.archetype or 'bro'),
                'preview': cycle_preview
            })
        
        # Get cycle completion video
        completion_video = self.video_builder.get_cycle_completion_video(
            plan=current_plan,
            user_archetype=user.archetype or 'bro',
            completion_stats=completion_data['completion_stats']
        )
        
        return {
            'evolved_goals': evolved_goals,
            'cycle_options': cycle_options,
            'completion_celebration': self._get_completion_celebration(user, progress_data),
            'completion_video': completion_video
        }
    
    def _determine_evolved_goals(self, user: User, progress_data: Dict) -> Dict:
        """Determine how user's goals have evolved based on their progress"""
        
        # Base goals evolution on progress and feedback
        evolved_goals = {
            'strength_focused': progress_data['avg_strength_progress'] >= 7,
            'confidence_gained': progress_data['avg_confidence_progress'] >= 7,
            'consistency_built': progress_data['total_workouts_completed'] >= 20,
            'ready_for_advanced': progress_data['avg_strength_progress'] >= 6 and progress_data['avg_confidence_progress'] >= 6
        }
        
        return evolved_goals
    
    def _generate_cycle_preview(self, user: User, current_plan: WorkoutPlan, progress_data: Dict, focus: str) -> Dict:
        """Generate a preview of what the new cycle would look like"""
        
        preview = {
            'focus_area': focus,
            'estimated_difficulty': 'intermediate',
            'key_changes': [],
            'sample_week_structure': {}
        }
        
        if focus == 'intensity_increase':
            preview['key_changes'] = [
                'Увеличение количества подходов на 20-30%',
                'Добавление суперсетов и дропсетов',
                'Сокращение времени отдыха между упражнениями',
                'Введение продвинутых вариаций упражнений'
            ]
            preview['estimated_difficulty'] = 'advanced'
            
        elif focus == 'variety_expansion':
            preview['key_changes'] = [
                'Новые функциональные упражнения',
                'Круговые тренировки',
                'Плиометрические элементы',
                'Упражнения на координацию и баланс'
            ]
            
        elif focus == 'personalized_optimization':
            top_favorites = [ex[0] for ex in progress_data['top_favorite_exercises'][:3]]
            top_challenging = [ex[0] for ex in progress_data['top_challenging_exercises'][:3]]
            
            preview['key_changes'] = [
                f'Больше любимых упражнений: {", ".join(top_favorites)}',
                f'Адаптация сложных упражнений: {", ".join(top_challenging)}',
                'Персональные модификации под ваш прогресс',
                'Фокус на слабых группах мышц'
            ]
        
        return preview
    
    def _get_completion_celebration(self, user: User, progress_data: Dict) -> Dict:
        """Get celebration message for completing 6 weeks"""
        
        archetype = user.archetype or 'bro'
        
        celebration_messages = {
            'bro': {
                'title': '🔥 Братан, ты сделал это!',
                'message': f'6 недель позади! Ты завершил {progress_data["total_workouts_completed"]} тренировок и твой прогресс просто огонь! Готов к следующему уровню?',
                'achievement_highlight': 'Ты показал, что такое настоящая сила воли!'
            },
            'sergeant': {
                'title': '🎖️ Миссия выполнена, боец!',
                'message': f'6 недель интенсивной подготовки завершены! {progress_data["total_workouts_completed"]} тренировок в активе. Вы готовы к новым вызовам!',
                'achievement_highlight': 'Дисциплина и упорство - ваши главные достижения!'
            },
            'intellectual': {
                'title': '📊 Цикл успешно завершен!',
                'message': f'Статистика впечатляет: {progress_data["total_workouts_completed"]} тренировок, средний прогресс силы {progress_data["avg_strength_progress"]}/10. Данные показывают отличную готовность к следующему этапу!',
                'achievement_highlight': 'Методичный подход принес отличные результаты!'
            }
        }
        
        return celebration_messages.get(archetype, celebration_messages['bro'])
    
    def create_new_cycle(self, user: User, selected_option: str, previous_completion_data: Dict) -> WorkoutPlan:
        """
        Create a new 6-week workout plan based on selected option and previous progress
        """
        try:
            # Deactivate previous plan
            previous_plan = previous_completion_data['plan']
            previous_plan.is_active = False
            previous_plan.completed_at = timezone.now()
            previous_plan.save()
            
            # Prepare context for AI generation
            context = self._prepare_new_cycle_context(user, selected_option, previous_completion_data)
            
            # Generate new plan using AI with evolution context
            new_plan_data = self.generator.generate_evolved_plan(
                user=user,
                evolution_context=context,
                archetype=user.archetype or 'bro'
            )
            
            # Create new WorkoutPlan
            new_plan = WorkoutPlan.objects.create(
                user=user,
                name=f"{new_plan_data.get('plan_name', 'Эволюционная программа')} - Цикл 2",
                duration_weeks=6,
                goal=new_plan_data.get('goal', context['evolved_goal']),
                plan_data=new_plan_data,
                is_active=True,
                is_confirmed=False  # User will need to confirm
            )
            
            # Create daily workouts from the plan
            self._create_daily_workouts_from_plan(new_plan, new_plan_data)
            
            # Award achievement for completing first cycle
            self.achievement_checker.check_cycle_completion_achievements(user, cycle_number=2)
            
            logger.info(f"Created new cycle for user {user.id}: {new_plan.id}")
            return new_plan
            
        except Exception as e:
            logger.error(f"Error creating new cycle for user {user.id}: {str(e)}")
            raise
    
    def _prepare_new_cycle_context(self, user: User, selected_option: str, completion_data: Dict) -> Dict:
        """Prepare context for AI to generate evolved workout plan"""
        
        progress_data = completion_data['progress_data']
        
        context = {
            'previous_plan_summary': completion_data['plan'].plan_data,
            'completion_stats': completion_data['completion_stats'],
            'user_progress': progress_data,
            'selected_evolution': selected_option,
            'evolved_goal': self._get_evolved_goal_description(selected_option),
            'cycle_number': 2,
            'user_preferences': {
                'favorite_exercises': [ex[0] for ex in progress_data['top_favorite_exercises']],
                'challenging_exercises': [ex[0] for ex in progress_data['top_challenging_exercises']],
                'avg_strength_progress': progress_data['avg_strength_progress'],
                'avg_confidence_progress': progress_data['avg_confidence_progress']
            }
        }
        
        return context
    
    def _get_evolved_goal_description(self, selected_option: str) -> str:
        """Get goal description for the evolved plan"""
        goal_descriptions = {
            'intensity_increase': 'Прогрессивное увеличение интенсивности и сложности тренировок',
            'variety_expansion': 'Расширение тренировочного арсенала и освоение новых методик',
            'personalized_optimization': 'Персонализированная оптимизация на основе индивидуального прогресса'
        }
        return goal_descriptions.get(selected_option, 'Эволюционное развитие фитнес программы')
    
    def _create_daily_workouts_from_plan(self, plan: WorkoutPlan, plan_data: Dict):
        """Create DailyWorkout records from AI-generated plan data"""
        weeks = plan_data.get('weeks', [])
        
        for week_index, week_data in enumerate(weeks):
            week_number = week_index + 1
            days = week_data.get('days', [])
            
            for day_data in days:
                DailyWorkout.objects.create(
                    plan=plan,
                    day_number=day_data.get('day_number'),
                    week_number=week_number,
                    name=day_data.get('name', f'День {day_data.get("day_number")}'),
                    exercises=day_data.get('exercises', []),
                    is_rest_day=day_data.get('is_rest_day', False),
                    confidence_task=day_data.get('confidence_task', '')
                )