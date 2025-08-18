from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

from .models import DailyWorkout, Exercise
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
            'current_streak': result['current_streak']
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
def weekly_feedback_view(request, plan_id, week_number):
    """Show weekly feedback form and handle submission"""
    from .models import WorkoutPlan
    
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    week_number = int(week_number)
    
    # Get archetype for display
    archetype = request.user.profile.archetype_name
    
    if request.method == 'POST':
        # Handle feedback submission
        try:
            # Import AI integration service
            from apps.ai_integration.services import WorkoutPlanGenerator
            
            # Collect feedback data
            feedback_data = {
                'overall_difficulty': request.POST.get('overall_difficulty'),
                'workout_frequency': request.POST.get('workout_frequency'),
                'energy_level': request.POST.get('energy_level'),
                'enjoyed_exercises': request.POST.getlist('enjoyed_exercises'),
                'challenging_exercises': request.POST.getlist('challenging_exercises'),
                'equipment_issues': request.POST.getlist('equipment_issues'),
                'time_management': request.POST.get('time_management'),
                'motivation_level': request.POST.get('motivation_level'),
                'body_response': request.POST.get('body_response'),
                'confidence_tasks': request.POST.get('confidence_tasks'),
                'weekly_comments': request.POST.get('weekly_comments', ''),
                'goals_progress': request.POST.get('goals_progress'),
                'week_number': week_number
            }
            
            # Use AI service to adapt plan based on feedback
            generator = WorkoutPlanGenerator()
            adapted_plan = generator.adapt_weekly_plan(plan, feedback_data)
            
            # Update plan with adaptations
            if adapted_plan:
                plan.plan_data = adapted_plan
                plan.save()
                
                messages.success(request, 'Спасибо за отзыв! Ваш план обновлен на основе вашего опыта.')
            else:
                messages.success(request, 'Спасибо за отзыв! Ваш план отлично подходит - продолжайте в том же духе.')
            
            # Redirect to dashboard
            return redirect('users:dashboard')
            
        except Exception as e:
            messages.error(request, f'Ошибка при обработке отзыва: {str(e)}')
    
    # GET request - show feedback form
    
    # Get workouts for this week
    week_workouts = DailyWorkout.objects.filter(
        plan=plan,
        week_number=week_number
    ).order_by('day_number')
    
    # Check if user has existing feedback for this week
    existing_feedback = {}  # Could be implemented later if needed
    
    context = {
        'plan': plan,
        'week_number': week_number,
        'archetype': archetype,
        'week_workouts': week_workouts,
        'feedback': existing_feedback,
    }
    
    return render(request, 'workouts/weekly_feedback.html', context)