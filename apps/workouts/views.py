import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import logging
from django.shortcuts import get_object_or_404, redirect, render

logger = logging.getLogger(__name__)
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import generics, permissions
from rest_framework.response import Response


from django.db import models
from .models import CSVExercise, DailyWorkout, WeeklyNotification
from .serializers import WeeklyNotificationSerializer
# OLD SYSTEM REMOVED: VideoPlaylistBuilder replaced with PlaylistGeneratorV2
# from .video_services import VideoPlaylistBuilder


@login_required
def daily_workout_view(request, workout_id):
    """Display today's workout with video playlist (NEW SYSTEM)"""
    workout = get_object_or_404(DailyWorkout, id=workout_id, plan__user=request.user)
    
    # Get user's archetype
    archetype = getattr(request.user.profile, 'archetype', 'mentor')
    if not archetype:
        messages.error(request, 'Пожалуйста, выберите архетип тренера в настройках')
        return redirect('users:profile_settings')
    
    # NEW SYSTEM: Use pre-generated playlist items from PlaylistGeneratorV2
    playlist_items = workout.playlist_items.all().order_by('order')
    
    # Convert playlist items to format expected by template
    video_playlist = []
    exercise_details = {}
    
    if not playlist_items:
        # Fallback: Generate playlist if it doesn't exist
        try:
            from apps.workouts.services import PlaylistGeneratorV2
            generator = PlaylistGeneratorV2(request.user, archetype)
            playlist_items = generator.generate_playlist_for_day(workout.day_number, workout)
        except Exception as e:
            logger.error(f"Failed to generate playlist for workout {workout_id}: {e}")
            playlist_items = []
    
    # Convert DailyPlaylistItem objects to template format
    for item in playlist_items:
        try:
            # Get R2Video object via ForeignKey
            video = item.video
            if not video:
                continue  # Skip if video not found
                
            # Get R2 URL for video 
            signed_url = video.r2_url
            
            # Create video entry in expected format
            video_entry = {
                'url': signed_url,
                'title': _get_video_title(item),
                'role': item.role,
                'duration': item.duration_seconds or 30,
                'video_code': video.code,  # Get code from video object
                'order': item.order,
                # Exercise-specific data for exercises
                'sets': _get_sets_from_role(item.role),
                'reps': _get_reps_from_role(item.role), 
                'rest': _get_rest_from_role(item.role),
            }
            
            video_playlist.append(video_entry)
            
            # Add exercise details for exercise videos
            if item.role in ['warmup', 'main', 'cooldown']:
                exercise_key = video.code
                exercise_details[exercise_key] = {
                    'id': exercise_key,
                    'name_ru': _get_exercise_name(video.code),
                    'name_en': '',
                    'description': f'{item.role.title()} упражнение',
                    'muscle_group': _get_muscle_group_from_code(video.code),
                    'level': 'intermediate',
                    'exercise_type': 'strength',
                    'sets': _get_sets_from_role(item.role),
                    'reps': _get_reps_from_role(item.role),
                    'rest_seconds': _get_rest_from_role(item.role),
                    'duration_seconds': item.duration_seconds or 30,
                }
                
        except Exception as e:
            logger.error(f"Error processing playlist item {item.id}: {e}")
            continue
    
    # Check if workout is already started
    if not workout.started_at and not workout.is_rest_day:
        workout.started_at = timezone.now()
        workout.save()
    
    context = {
        'workout': workout,
        'video_playlist': video_playlist,
        'video_playlist_json': json.dumps(video_playlist),
        'substitutions': {},  # TODO: Implement substitutions for new system
        'exercise_details': exercise_details,
        'exercise_details_json': json.dumps(exercise_details),
        'is_completed': workout.completed_at is not None,
        'can_substitute': False  # TODO: Implement substitutions for new system
    }
    
    return render(request, 'workouts/daily_workout.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def complete_workout_view(request, workout_id):
    """Mark workout as completed and handle feedback"""
    workout = get_object_or_404(DailyWorkout, id=workout_id, plan__user=request.user)
    
    if workout.completed_at:
        return JsonResponse({'error': 'Тренировка уже завершена'}, status=400)
    
    try:
        data = json.loads(request.body)
        feedback_rating = data.get('feedback_rating')
        feedback_note = data.get('feedback_note', '')
        
        # Complete workout
        workout.completed_at = timezone.now()
        workout.feedback_rating = feedback_rating
        workout.feedback_note = feedback_note
        workout.save()
        
        # Update user profile progress
        profile = request.user.profile
        profile.total_workouts_completed = (profile.total_workouts_completed or 0) + 1
        profile.save()

        return JsonResponse({
            'success': True,
            'message': 'Тренировка успешно завершена!',
            'workouts_completed': profile.total_workouts_completed
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def substitute_exercise_view(request, workout_id):
    """Substitute an exercise in the workout"""
    workout = get_object_or_404(DailyWorkout, id=workout_id, plan__user=request.user)
    
    try:
        data = json.loads(request.body)
        original_slug = data.get('original_exercise')
        substitute_slug = data.get('substitute_exercise')
        
        # Verify substitute is valid
        original_exercise = CSVExercise.objects.get(id=original_slug)
        substitute_exercise = CSVExercise.objects.get(id=substitute_slug)
        
        # Note: alternatives relationship was removed in Phase 5.6
        # For now, allow any active exercise as substitute
        if not substitute_exercise.is_active:
            return JsonResponse({'error': 'Недопустимая замена'}, status=400)
        
        # TODO: Implement substitution for new playlist system
        # For now, return error as substitution is not yet implemented for new system
        return JsonResponse({
            'error': 'Замена упражнений временно недоступна. Функция будет добавлена в следующем обновлении.'
        }, status=501)  # 501 Not Implemented
        
    except CSVExercise.DoesNotExist:
        return JsonResponse({'error': 'Упражнение не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def workout_history_view(request):
    """Show user's workout history"""
    workouts = DailyWorkout.objects.filter(
        plan__user=request.user,
        completed_at__isnull=False
    ).order_by('-completed_at')[:30]  # Last 30 workouts
    
    context = {
        'workouts': workouts,
        'total_completed': request.user.profile.total_workouts_completed,
        'current_streak': request.user.profile.current_streak
    }
    
    return render(request, 'workouts/history.html', context)


@login_required
def plan_overview_view(request):
    """Show full workout plan overview"""
    # Get active workout plan
    plan = request.user.workout_plans.filter(is_active=True).first()
    if not plan:
        messages.error(request, 'У вас нет активного плана тренировок')
        return redirect('users:dashboard')
    
    # Group workouts by week
    workouts_by_week = {}
    for workout in plan.daily_workouts.all().order_by('week_number', 'day_number'):
        week_num = workout.week_number
        if week_num not in workouts_by_week:
            workouts_by_week[week_num] = []
        workouts_by_week[week_num].append(workout)
    
    # Calculate progress
    total_workouts = plan.daily_workouts.count()
    completed_workouts = plan.daily_workouts.filter(completed_at__isnull=False).count()
    progress_percentage = (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0
    
    context = {
        'plan': plan,
        'workouts_by_week': workouts_by_week,
        'total_workouts': total_workouts,
        'completed_workouts': completed_workouts,
        'progress_percentage': progress_percentage,
        'current_week': plan.get_current_week()
    }
    
    return render(request, 'workouts/plan_overview.html', context)


# УДАЛЕНО: ExplainerVideoView - ExplainerVideo заменен на R2Video с category='exercises'
# Использовать R2Video.objects.filter(category='exercises', archetype=user_archetype)


class WeeklyCurrentView(generics.RetrieveAPIView):
    """
    GET /api/weekly/current/ 
    Возвращает непрочитанный еженедельный урок для пользователя и помечает его как прочитанный.
    
    Optimized for high-load scenarios (1k+ concurrent users):
    - Redis caching with 5-minute TTL
    - Database connection pooling with select_for_update
    - Bulk operations support
    - Performance monitoring
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WeeklyNotificationSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .performance import OptimizedWeeklyCurrentService
        self.optimized_service = OptimizedWeeklyCurrentService()
    
    def get(self, request):
        """
        Optimized GET handler with caching and performance monitoring
        """
        import time
        start_time = time.time()
        
        try:
            # Use optimized service for getting weekly lesson
            lesson_data = self.optimized_service.get_current_weekly_lesson(request.user)
            
            if not lesson_data:
                # Track analytics for no lesson found
                try:
                    from apps.analytics.services import AnalyticsService
                    analytics = AnalyticsService()
                    analytics.track_event(
                        event_type='weekly_lesson_viewed',
                        user=request.user,
                        properties={'status': 'no_lesson_found'},
                        request=request,
                        send_to_amplitude=False  # Async to avoid blocking
                    )
                except ImportError:
                    pass  # Analytics not available
                
                return Response({'error': 'No unread weekly lesson found'}, status=404)
            
            # Track successful lesson access
            try:
                from apps.analytics.services import AnalyticsService
                analytics = AnalyticsService()
                analytics.track_event(
                    event_type='weekly_lesson_viewed',
                    user=request.user,
                    properties={
                        'status': 'success',
                        'lesson_week': lesson_data.get('week'),
                        'archetype': lesson_data.get('archetype'),
                        'lesson_title': lesson_data.get('lesson_title')
                    },
                    request=request,
                    send_to_amplitude=False  # Async to avoid blocking
                )
            except ImportError:
                pass  # Analytics not available
            
            # Add performance metadata to response (for monitoring)
            response_time_ms = (time.time() - start_time) * 1000
            lesson_data['_meta'] = {
                'response_time_ms': round(response_time_ms, 2),
                'cached': lesson_data.get('_cached', False),
                'timestamp': timezone.now().isoformat()
            }
            
            return Response(lesson_data)
            
        except Exception as e:
            # Log error and return fallback response
            logger.error(f"WeeklyCurrentView error for user {request.user.id}: {e}")
            
            # Fallback to original implementation
            try:
                notification = WeeklyNotification.objects.filter(
                    user=request.user,
                    is_read=False
                ).first()
                
                if not notification:
                    return Response({'error': 'No unread weekly lesson found'}, status=404)
                
                notification.mark_as_read()
                serializer = self.serializer_class(notification)
                return Response(serializer.data)
                
            except Exception as fallback_e:
                logger.error(f"Fallback failed for user {request.user.id}: {fallback_e}")
                return Response(
                    {'error': 'Service temporarily unavailable'}, 
                    status=503
                )


class WeeklyUnreadView(generics.RetrieveAPIView):
    """
    GET /api/weekly/unread/
    Возвращает {"unread": true/false} - есть ли непрочитанный урок недели.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        unread_exists = WeeklyNotification.objects.filter(
            user=request.user,
            is_read=False
        ).exists()
        
        return Response({'unread': unread_exists})


# УДАЛЕНО: WeeklyLessonView - WeeklyLesson заменен на R2Video с category='weekly'
# Использовать R2Video.objects.filter(category='weekly', archetype=user_archetype)


class WeeklyLessonHealthView(generics.RetrieveAPIView):
    """
    GET /api/weekly/health/ - Health check for weekly lesson system
    Provides performance metrics and optimization recommendations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Return health metrics for weekly lesson system
        Includes database performance, cache status, and recommendations
        """
        from .performance import OptimizedWeeklyCurrentService, WeeklyLessonHealthChecker
        
        try:
            # Check if user is staff for detailed metrics
            include_detailed = request.user.is_staff
            
            health_checker = WeeklyLessonHealthChecker()
            service = OptimizedWeeklyCurrentService()
            
            # Get health metrics
            health_data = health_checker.get_system_health()
            cache_stats = service.get_cache_stats()
            
            # Response structure
            response_data = {
                'status': health_data['overall_status'],
                'timestamp': health_data['timestamp'],
                'cache_enabled': cache_stats.get('cache_enabled', False),
                'recommendations': health_data['recommendations']
            }
            
            # Add detailed metrics for staff users
            if include_detailed:
                response_data['detailed'] = {
                    'database': health_data['database'],
                    'cache': health_data['cache'],
                    'cache_stats': cache_stats
                }
            else:
                # Simplified metrics for regular users
                db_status = health_data['database'].get('status', 'unknown')
                cache_status = health_data['cache'].get('status', 'unknown')
                
                response_data['performance'] = {
                    'database_status': db_status,
                    'cache_status': cache_status,
                    'response_time_category': self._categorize_performance(
                        health_data['database'].get('query_time_ms', 0)
                    )
                }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"WeeklyLessonHealthView error: {e}")
            return Response({
                'status': 'error',
                'error': 'Health check failed',
                'timestamp': timezone.now().isoformat()
            }, status=500)
    
    def _categorize_performance(self, query_time_ms: float) -> str:
        """Categorize performance based on query time"""
        if query_time_ms < 50:
            return 'excellent'
        elif query_time_ms < 100:
            return 'good'
        elif query_time_ms < 500:
            return 'acceptable'
        else:
            return 'poor'


# Demo plan views for Phase 4.2
@login_required
def my_plan(request):
    """Страница с текущим планом пользователя"""
    from apps.workouts.models import WorkoutPlan, DailyWorkout
    
    plan = WorkoutPlan.objects.filter(user=request.user, status='CONFIRMED').first()
    if not plan:
        return render(request, "workouts/no_plan.html")

    daily_workouts = DailyWorkout.objects.filter(plan=plan).order_by("week_number", "day_number")
    return render(request, "workouts/my_plan.html", {
        "plan": plan,
        "daily_workouts": daily_workouts,
    })


@login_required
def workout_day(request, day_id):
    from apps.workouts.models import DailyWorkout
    day = get_object_or_404(DailyWorkout, pk=day_id, plan__user=request.user)

    # ВАЖНО: берём позиции плейлиста, вместе с R2Video
    playlist = day.playlist_items.select_related("video").order_by("order")
    
    # Для совместимости с шаблоном добавляем переменную exercises
    exercises = day.exercises if day.exercises else []

    return render(request, "workouts/workout_day.html", {
        "day": day,
        "playlist": playlist,
        "exercises": exercises,  # Добавлено для совместимости с шаблоном
    })


# Helper functions for new playlist system
def _get_video_title(playlist_item):
    """Generate human-readable title for video"""
    role = playlist_item.role
    video_code = playlist_item.video.code
    
    if role == 'motivation':
        if 'opening' in video_code or 'intro' in video_code:
            return "Вступление"
        elif 'closing' in video_code:
            return "Заключение"
        elif 'main' in video_code:
            return "Мотивация"
        else:
            return "Мотивационное видео"
    elif role == 'warmup':
        return f"Разминка: {_get_exercise_name(video_code)}"
    elif role == 'main':
        return f"Упражнение: {_get_exercise_name(video_code)}"
    elif role == 'cooldown':
        return f"Заминка: {_get_exercise_name(video_code)}"
    else:
        return video_code.replace('_', ' ').title()


def _get_exercise_name(video_code):
    """Extract exercise name from video code"""
    # Try to get from CSVExercise database first
    try:
        from apps.workouts.models import CSVExercise
        # Extract exercise slug from video code (e.g., 'main_042_technique_m01' -> find exercise with similar name)
        parts = video_code.split('_')
        if len(parts) >= 2 and parts[0] in ['warmup', 'main', 'endurance', 'relaxation']:
            exercise_num = parts[1]
            # Try to find exercise by partial match
            exercise = CSVExercise.objects.filter(
                models.Q(name_ru__icontains=exercise_num) |
                models.Q(id__icontains=exercise_num)
            ).first()
            if exercise:
                return exercise.name_ru
    except:
        pass
    
    # Fallback: clean up video code
    clean_name = video_code.replace('_technique_m01', '').replace('_', ' ')
    return clean_name.title()


def _get_muscle_group_from_code(video_code):
    """Extract muscle group from video code"""
    code_lower = video_code.lower()
    
    if any(term in code_lower for term in ['push', 'chest', 'bench']):
        return 'Грудь'
    elif any(term in code_lower for term in ['pull', 'back', 'row']):
        return 'Спина' 
    elif any(term in code_lower for term in ['squat', 'leg', 'quad']):
        return 'Ноги'
    elif any(term in code_lower for term in ['shoulder', 'press']):
        return 'Плечи'
    elif any(term in code_lower for term in ['arm', 'bicep', 'tricep']):
        return 'Руки'
    elif any(term in code_lower for term in ['core', 'abs', 'plank']):
        return 'Корпус'
    else:
        return 'Общие'


def _get_sets_from_role(role):
    """Get typical sets count for exercise role"""
    if role == 'warmup':
        return 1
    elif role == 'main':
        return 3
    elif role == 'cooldown':
        return 1
    else:
        return None


def _get_reps_from_role(role):
    """Get typical reps count for exercise role"""
    if role == 'warmup':
        return 10
    elif role == 'main':
        return 12
    elif role == 'cooldown':
        return 8
    else:
        return None


def _get_rest_from_role(role):
    """Get typical rest time for exercise role"""
    if role == 'warmup':
        return 30
    elif role == 'main':
        return 90
    elif role == 'cooldown':
        return 30
    else:
        return 0