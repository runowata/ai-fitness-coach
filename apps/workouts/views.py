from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

from .models import DailyWorkout, Exercise, WeeklyFeedback, WorkoutPlan
from .services import VideoPlaylistBuilder
from .cycle_service import ProgramCycleService
from apps.achievements.services import WorkoutCompletionService


@login_required
def daily_workout_view(request, workout_id):
    """Display today's workout with video playlist"""
    workout = get_object_or_404(DailyWorkout, id=workout_id, plan__user=request.user)
    
    # Get user's archetype
    archetype = request.user.archetype
    if not archetype:
        messages.error(request, 'Пожалуйста, выберите архетип тренера в настройках')
        return redirect('users:profile_settings')
    
    # Build video playlist
    playlist_builder = VideoPlaylistBuilder()
    video_playlist = playlist_builder.build_workout_playlist(workout, archetype)
    
    # Get substitution options for each exercise
    substitutions = {}
    user_equipment = request.user.goals.get('equipment', [])
    
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
        
        # Get final video for "see you tomorrow" message
        from .services import VideoPlaylistBuilder
        playlist_builder = VideoPlaylistBuilder()
        final_video = playlist_builder.get_final_video(
            workout=workout,
            user_archetype=request.user.archetype or 'bro'
        )
        
        # Check if user completed the 6-week program after this workout
        cycle_service = ProgramCycleService()
        completion_data = cycle_service.check_program_completion(request.user)
        program_completed = completion_data is not None
        
        response_data = {
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
            'final_video': final_video,
            'program_completed': program_completed
        }
        
        # If program is completed, add cycle completion video
        if program_completed:
            cycle_completion_video = playlist_builder.get_cycle_completion_video(
                plan=workout.plan,
                user_archetype=request.user.archetype or 'bro',
                completion_stats=completion_data['completion_stats']
            )
            response_data['cycle_completion_video'] = cycle_completion_video
            response_data['program_completion_url'] = '/workouts/program-completion/'
        
        return JsonResponse(response_data)
        
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
        
        # Verify exercises exist
        original_exercise = Exercise.objects.get(slug=original_slug)
        substitute_exercise = Exercise.objects.get(slug=substitute_slug)
        
        # Allow any exercise substitution - validation handled on frontend
        
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
            request.user.archetype
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
        'total_completed': request.user.total_workouts_completed,
        'current_streak': request.user.current_streak
    }
    
    return render(request, 'workouts/history.html', context)


@login_required
def weekly_feedback_view(request, plan_id, week_number):
    """Collect weekly feedback from user"""
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    week_number = int(week_number)
    
    # Check if week is valid
    if week_number < 1 or week_number > plan.duration_weeks:
        messages.error(request, 'Неверный номер недели')
        return redirect('users:dashboard')
    
    # Get existing feedback or create new
    feedback, created = WeeklyFeedback.objects.get_or_create(
        user=request.user,
        plan=plan,
        week_number=week_number
    )
    
    if request.method == 'POST':
        # Update feedback with form data
        feedback.overall_difficulty = request.POST.get('overall_difficulty', 'just_right')
        feedback.energy_level = request.POST.get('energy_level', 'medium')
        feedback.motivation_level = request.POST.get('motivation_level', 'medium')
        feedback.strength_progress = int(request.POST.get('strength_progress', 5))
        feedback.confidence_progress = int(request.POST.get('confidence_progress', 5))
        
        # Handle checkboxes
        feedback.wants_more_cardio = 'wants_more_cardio' in request.POST
        feedback.wants_more_strength = 'wants_more_strength' in request.POST
        feedback.wants_shorter_workouts = 'wants_shorter_workouts' in request.POST
        feedback.wants_longer_workouts = 'wants_longer_workouts' in request.POST
        
        # Handle text fields
        feedback.what_worked_well = request.POST.get('what_worked_well', '')
        feedback.what_needs_improvement = request.POST.get('what_needs_improvement', '')
        feedback.additional_notes = request.POST.get('additional_notes', '')
        
        # Handle exercise lists (JSON)
        challenging_exercises = request.POST.getlist('challenging_exercises')
        favorite_exercises = request.POST.getlist('favorite_exercises')
        feedback.most_challenging_exercises = challenging_exercises
        feedback.favorite_exercises = favorite_exercises
        
        feedback.save()
        
        messages.success(request, 'Спасибо за отзыв! Ваш план будет адаптирован.')
        return redirect('users:dashboard')
    
    # Get exercises from the completed week for selection
    week_workouts = plan.daily_workouts.filter(week_number=week_number)
    all_exercises = []
    for workout in week_workouts:
        for exercise in workout.exercises:
            exercise_slug = exercise.get('exercise_slug')
            exercise_name = exercise.get('exercise_name', exercise_slug)
            if exercise_slug not in [ex['slug'] for ex in all_exercises]:
                all_exercises.append({
                    'slug': exercise_slug,
                    'name': exercise_name
                })
    
    context = {
        'plan': plan,
        'week_number': week_number,
        'feedback': feedback,
        'all_exercises': all_exercises,
        'archetype': request.user.archetype or 'bro'
    }
    
    return render(request, 'workouts/weekly_feedback.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def submit_weekly_feedback(request, plan_id, week_number):
    """AJAX endpoint for submitting weekly feedback"""
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    week_number = int(week_number)
    
    try:
        data = json.loads(request.body)
        
        # Get or create feedback
        feedback, created = WeeklyFeedback.objects.get_or_create(
            user=request.user,
            plan=plan,
            week_number=week_number
        )
        
        # Update feedback with submitted data
        feedback.overall_difficulty = data.get('overall_difficulty', 'just_right')
        feedback.energy_level = data.get('energy_level', 'medium')
        feedback.motivation_level = data.get('motivation_level', 'medium')
        feedback.strength_progress = int(data.get('strength_progress', 5))
        feedback.confidence_progress = int(data.get('confidence_progress', 5))
        
        # Handle preferences
        feedback.wants_more_cardio = data.get('wants_more_cardio', False)
        feedback.wants_more_strength = data.get('wants_more_strength', False)
        feedback.wants_shorter_workouts = data.get('wants_shorter_workouts', False)
        feedback.wants_longer_workouts = data.get('wants_longer_workouts', False)
        
        # Handle text fields
        feedback.what_worked_well = data.get('what_worked_well', '')
        feedback.what_needs_improvement = data.get('what_needs_improvement', '')
        feedback.additional_notes = data.get('additional_notes', '')
        
        # Handle exercise lists
        feedback.most_challenging_exercises = data.get('challenging_exercises', [])
        feedback.favorite_exercises = data.get('favorite_exercises', [])
        
        feedback.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Отзыв сохранен! Ваш план будет адаптирован.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def check_program_completion(request):
    """Check if user has completed their 6-week program and show cycle options"""
    cycle_service = ProgramCycleService()
    completion_data = cycle_service.check_program_completion(request.user)
    
    if not completion_data:
        # User hasn't completed 6 weeks yet
        return redirect('users:dashboard')
    
    # Generate cycle options
    cycle_options = cycle_service.generate_new_cycle_options(request.user, completion_data)
    
    context = {
        'completion_data': completion_data,
        'cycle_options': cycle_options,
        'archetype': request.user.archetype or 'bro',
        'user': request.user
    }
    
    return render(request, 'workouts/program_completion.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_new_cycle(request):
    """Create a new 6-week cycle based on user's selection"""
    try:
        data = json.loads(request.body)
        selected_option = data.get('selected_option')
        
        if not selected_option:
            return JsonResponse({'error': 'Не выбрана опция'}, status=400)
        
        # Get completion data
        cycle_service = ProgramCycleService()
        completion_data = cycle_service.check_program_completion(request.user)
        
        if not completion_data:
            return JsonResponse({'error': 'Программа еще не завершена'}, status=400)
        
        # Create new cycle
        new_plan = cycle_service.create_new_cycle(
            user=request.user,
            selected_option=selected_option,
            previous_completion_data=completion_data
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Новый цикл создан!',
            'plan_id': new_plan.id,
            'redirect_url': f'/onboarding/plan-preview/{new_plan.id}/'
        })
        
    except Exception as e:
        logger.error(f"Error creating new cycle for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)