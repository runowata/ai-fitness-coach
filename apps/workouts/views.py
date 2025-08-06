from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
import json

from .models import DailyWorkout, Exercise, ExplainerVideo
from .services import VideoPlaylistBuilder
from apps.achievements.services import WorkoutCompletionService
from apps.users.models import UserProfile


@login_required
def daily_workout_view(request, workout_id):
    """Display today's workout with video playlist"""
    workout = get_object_or_404(DailyWorkout, id=workout_id, plan__user=request.user)
    
    # Get user's archetype
    archetype = request.user.profile.archetype
    if not archetype:
        messages.error(request, 'Пожалуйста, выберите архетип тренера в настройках')
        return redirect('users:profile_settings')
    
    # Build video playlist
    playlist_builder = VideoPlaylistBuilder()
    video_playlist = playlist_builder.build_workout_playlist(workout, archetype)
    
    # Get substitution options for each exercise
    substitutions = {}
    user_equipment = request.user.profile.goals.get('equipment', [])
    
    for exercise_data in workout.exercises:
        exercise_slug = exercise_data.get('exercise_slug')
        alternatives = playlist_builder.get_substitution_options(exercise_slug, user_equipment)
        if alternatives:
            substitutions[exercise_slug] = alternatives
    
    # Check if workout is already started
    if not workout.started_at and not workout.is_rest_day:
        workout.started_at = timezone.now()
        workout.save()
    
    context = {
        'workout': workout,
        'video_playlist': video_playlist,
        'substitutions': substitutions,
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
        original_exercise = Exercise.objects.get(slug=original_slug)
        substitute_exercise = Exercise.objects.get(slug=substitute_slug)
        
        if substitute_exercise not in original_exercise.alternatives.all():
            return JsonResponse({'error': 'Недопустимая замена'}, status=400)
        
        # Update workout substitutions
        substitutions = workout.substitutions or {}
        substitutions[original_slug] = substitute_slug
        workout.substitutions = substitutions
        workout.save()
        
        # Rebuild playlist with substitution
        playlist_builder = VideoPlaylistBuilder()
        
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
    
    # Map user archetype to video archetype
    ARCHETYPE_MAP = {
        'bro': '333',           # Ровесник
        'sergeant': '222',      # Профессионал
        'intellectual': '111',  # Наставник
    }
    
    def get(self, request, exercise_id):
        user_archetype = request.user.profile.archetype
        if not user_archetype:
            return Response({'error': 'User archetype not set'}, status=400)
        
        # Map user archetype to video archetype
        video_archetype = self.ARCHETYPE_MAP.get(user_archetype)
        if not video_archetype:
            return Response({'error': 'Invalid user archetype'}, status=400)
        
        try:
            video = ExplainerVideo.objects.get(
                exercise_id=exercise_id,
                archetype=video_archetype,
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