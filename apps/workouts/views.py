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

from apps.achievements.services import WorkoutCompletionService

from .models import CSVExercise, DailyWorkout, ExplainerVideo, WeeklyLesson, WeeklyNotification
from .serializers import WeeklyLessonSerializer, WeeklyNotificationSerializer
from .video_services import VideoPlaylistBuilder


@login_required
def daily_workout_view(request, workout_id):
    """Display today's workout with video playlist"""
    workout = get_object_or_404(DailyWorkout, id=workout_id, plan__user=request.user)
    
    # Get user's archetype
    archetype = request.user.profile.archetype_name
    if not archetype:
        messages.error(request, 'Пожалуйста, выберите архетип тренера в настройках')
        return redirect('users:profile_settings')
    
    # Build video playlist
    playlist_builder = VideoPlaylistBuilder(archetype=archetype)
    video_playlist = playlist_builder.build_workout_playlist(workout, archetype)
    
    # Get substitution options for each exercise (equipment checking removed)
    substitutions = {}
    
    # Get detailed exercise information for display
    exercise_details = {}
    
    for exercise_data in workout.exercises:
        exercise_slug = exercise_data.get('exercise_slug')
        
        # Get substitution alternatives
        alternatives = playlist_builder.get_substitution_options(exercise_slug, [])
        if alternatives:
            substitutions[exercise_slug] = alternatives
        
        # Get detailed exercise info from database
        try:
            exercise = CSVExercise.objects.get(id=exercise_slug)
            exercise_details[exercise_slug] = {
                'id': exercise.id,
                'name_ru': exercise.name_ru,
                'name_en': exercise.name_en,
                'description': exercise.description,
                'muscle_group': exercise.muscle_group,
                'level': exercise.level,
                'exercise_type': exercise.exercise_type,
                'sets': exercise_data.get('sets'),
                'reps': exercise_data.get('reps'),
                'rest_seconds': exercise_data.get('rest_seconds'),
                'duration_seconds': exercise_data.get('duration_seconds'),
            }
        except CSVExercise.DoesNotExist:
            # Fallback for missing exercises
            exercise_details[exercise_slug] = {
                'id': exercise_slug,
                'name_ru': exercise_slug.replace('_', ' ').replace('-', ' ').title(),
                'name_en': '',
                'description': 'Описание упражнения будет добавлено позже.',
                'muscle_group': '',
                'level': 'beginner',
                'exercise_type': 'strength',
                'sets': exercise_data.get('sets'),
                'reps': exercise_data.get('reps'),
                'rest_seconds': exercise_data.get('rest_seconds'),
                'duration_seconds': exercise_data.get('duration_seconds'),
            }
    
    # Check if workout is already started
    if not workout.started_at and not workout.is_rest_day:
        workout.started_at = timezone.now()
        workout.save()
    
    context = {
        'workout': workout,
        'video_playlist': video_playlist,
        'video_playlist_json': json.dumps(video_playlist),
        'substitutions': substitutions,
        'exercise_details': exercise_details,
        'exercise_details_json': json.dumps(exercise_details),
        'is_completed': workout.completed_at is not None,
        'can_substitute': bool(substitutions)
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
        completion_service = WorkoutCompletionService()
        result = completion_service.complete_workout(
            user=request.user,
            workout=workout,
            feedback_rating=feedback_rating,
            feedback_note=feedback_note
        )
        
        return JsonResponse({
            'success': True,
            'xp_earned': result['xp_earned'],
            'new_achievements': [
                {
                    'name': achievement.achievement.name,
                    'description': achievement.achievement.description
                }
                for achievement in result['new_achievements']
            ],
            'current_streak': result['current_streak'],
            'ai_analysis': result.get('ai_analysis')
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
        
        if substitute_exercise not in original_exercise.alternatives.all():
            return JsonResponse({'error': 'Недопустимая замена'}, status=400)
        
        # Update workout substitutions
        substitutions = workout.substitutions or {}
        substitutions[original_slug] = substitute_slug
        workout.substitutions = substitutions
        workout.save()
        
        # Rebuild playlist with substitution
        user_archetype = request.user.profile.archetype_name_name or 'mentor'
        playlist_builder = VideoPlaylistBuilder(archetype=user_archetype)
        
        # Update exercise in workout data
        updated_exercises = []
        for exercise_data in workout.exercises:
            if exercise_data.get('exercise_slug') == original_slug:
                exercise_data['exercise_slug'] = substitute_slug
                exercise_data['exercise_name'] = substitute_exercise.name
            updated_exercises.append(exercise_data)
        
        workout.exercises = updated_exercises
        workout.save()
        
        # Build new playlist
        video_playlist = playlist_builder.build_workout_playlist(
            workout, 
            request.user.profile.archetype
        )
        
        return JsonResponse({
            'success': True,
            'video_playlist': video_playlist,
            'message': f'Упражнение заменено: {original_exercise.name} → {substitute_exercise.name}'
        })
        
    except Exercise.DoesNotExist:
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


class ExplainerVideoView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, exercise_id):
        user_archetype = request.user.profile.archetype_name
        if not user_archetype:
            return Response({'error': 'User archetype not set'}, status=400)
        
        try:
            video = ExplainerVideo.objects.get(
                exercise_id=exercise_id,
                archetype=user_archetype,
                locale='ru'
            )
            return Response({
                'exercise_id': video.exercise_id,
                'archetype': video.archetype,
                'script': video.script,
                'locale': video.locale
            })
        except ExplainerVideo.DoesNotExist:
            return Response({'error': 'Video not found'}, status=404)


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


class WeeklyLessonView(generics.RetrieveAPIView):
    """
    GET /api/weekly/<int:week>/
    Возвращает урок по номеру недели для архетипа текущего пользователя.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WeeklyLessonSerializer
    lookup_field = 'week'
    
    def get(self, request, week):
        user_archetype = request.user.profile.archetype_name
        if not user_archetype:
            return Response({'error': 'User archetype not set'}, status=400)
        
        try:
            lesson = WeeklyLesson.objects.get(
                week=week,
                archetype=user_archetype,
                locale='ru'
            )
            serializer = self.serializer_class(lesson)
            return Response(serializer.data)
        except WeeklyLesson.DoesNotExist:
            return Response({'error': f'Lesson for week {week} not found'}, status=404)


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