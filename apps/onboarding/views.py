import json
import logging
import os
import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from apps.workouts.models import WorkoutPlan

from .models import (
    AnswerOption,
    MotivationalCard,
    OnboardingQuestion,
    OnboardingSession,
    UserOnboardingResponse,
)

logger = logging.getLogger(__name__)


def _get_random_motivational_background():
    """Get random motivational background image from R2 using the same mechanism as videos"""
    try:
        from django.core.files.storage import default_storage

        # Read available photos from R2
        r2_state_path = os.path.join(settings.BASE_DIR, 'r2_upload_state.json')
        if os.path.exists(r2_state_path):
            with open(r2_state_path, 'r') as f:
                r2_files = json.load(f)
            
            # Filter quotes photos
            quotes_photos = [
                f for f in r2_files 
                if 'photos/quotes/' in f and f.endswith('.jpg')
            ]
            
            if quotes_photos:
                # Select random photo
                random_photo = random.choice(quotes_photos)
                
                # Use the same mechanism as videos - default_storage.url()
                # This will use signed URLs if USE_R2_STORAGE=True, or return empty in dev
                try:
                    photo_url = default_storage.url(random_photo)
                    # In development (USE_R2_STORAGE=False), this returns /media/path
                    # In production (USE_R2_STORAGE=True), this returns signed R2 URL
                    
                    # Check if it's a local path (dev environment)
                    if photo_url.startswith('/media/'):
                        logger.info("Development environment: using gradient background instead of R2 image")
                        return ''  # Use gradient background in development
                    else:
                        # Production: return signed URL
                        return photo_url
                        
                except Exception as e:
                    logger.warning(f"Failed to get URL for {random_photo}: {e}")
                    return ''
        
        # Fallback: return empty to use gradient background
        return ''
        
    except Exception as e:
        logger.error(f"Error getting random motivational background: {e}")
        return ''


@login_required
def start_onboarding(request):
    """Start or continue onboarding process"""
    profile = request.user.profile
    
    # Check if already completed
    if profile.onboarding_completed_at:
        messages.info(request, 'Вы уже прошли онбординг!')
        return redirect('users:dashboard')
    
    # Get or create session
    session, created = OnboardingSession.objects.get_or_create(
        user=request.user,
        is_completed=False,
        defaults={'started_at': timezone.now()}
    )
    
    # Get first question
    first_question = OnboardingQuestion.objects.filter(is_active=True).first()
    if not first_question:
        messages.error(request, 'Вопросы онбординга не настроены')
        return redirect('users:dashboard')
    
    return redirect('onboarding:question', question_id=first_question.id)


@login_required
def question_view(request, question_id):
    """Display single onboarding question"""
    question = get_object_or_404(OnboardingQuestion, id=question_id, is_active=True)
    
    # Get user's existing response
    try:
        existing_response = UserOnboardingResponse.objects.get(
            user=request.user, 
            question=question
        )
    except UserOnboardingResponse.DoesNotExist:
        existing_response = None
    
    # Get all questions for progress bar
    all_questions = OnboardingQuestion.objects.filter(is_active=True).order_by('order')
    current_index = list(all_questions).index(question) + 1
    total_questions = len(all_questions)
    
    context = {
        'question': question,
        'existing_response': existing_response,
        'progress_percent': int((current_index / total_questions) * 100),
        'current_index': current_index,
        'total_questions': total_questions,
        'is_last_question': current_index == total_questions
    }
    
    return render(request, 'onboarding/question.html', context)


@login_required
@csrf_exempt
def save_answer(request, question_id):
    """Save answer and show motivational card"""
    logger.info("=== SAVE_ANSWER DEBUG START ===")
    logger.info(f"Question ID: {question_id}")
    logger.info(f"User: {request.user}")
    logger.info(f"Method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Request body: {request.body}")
    
    if request.method != 'POST':
        logger.error(f"Invalid method: {request.method}")
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        question = get_object_or_404(OnboardingQuestion, id=question_id, is_active=True)
        logger.info(f"Question found: {question.question_text}")
        logger.info(f"Question type: {question.question_type}")
        logger.info(f"Is block separator: {question.is_block_separator}")
        
        data = json.loads(request.body)
        logger.info(f"Parsed data: {data}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in save_answer: {str(e)}")
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
    
    # Delete existing response
    UserOnboardingResponse.objects.filter(
        user=request.user, 
        question=question
    ).delete()
    
    # Create new response
    response = UserOnboardingResponse.objects.create(
        user=request.user,
        question=question
    )
    
    # Get motivational card for this question
    motivational_card = None
    
    # Handle block separators first
    if question.is_block_separator:
        # Block separators don't need data, just mark as acknowledged
        response.answer_text = 'acknowledged'
        response.save()
        
    # Handle different question types
    elif question.question_type == 'single_choice':
        option_id = data.get('answer')
        if option_id:
            option = get_object_or_404(AnswerOption, id=option_id, question=question)
            response.answer_options.add(option)
            
            # Try to get specific card for this answer option
            motivational_card = MotivationalCard.objects.filter(
                question=question,
                answer_option=option,
                is_active=True
            ).first()
            
    elif question.question_type == 'multiple_choice':
        option_ids = data.get('answers', [])
        for option_id in option_ids:
            option = get_object_or_404(AnswerOption, id=option_id, question=question)
            response.answer_options.add(option)
        
    elif question.question_type == 'number':
        try:
            number_value = int(data.get('answer'))
            # Проверяем границы если они заданы
            if question.min_value is not None and number_value < question.min_value:
                return JsonResponse({'error': f'Значение должно быть не менее {question.min_value}'}, status=400)
            if question.max_value is not None and number_value > question.max_value:
                return JsonResponse({'error': f'Значение должно быть не более {question.max_value}'}, status=400)
            response.answer_number = number_value
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Введите корректное число'}, status=400)
        response.save()
        
    elif question.question_type == 'scale':
        try:
            scale_value = int(data.get('answer'))
            if 1 <= scale_value <= 5:
                response.answer_scale = scale_value
            else:
                return JsonResponse({'error': 'Значение должно быть от 1 до 5'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Введите число от 1 до 5'}, status=400)
        response.save()
        
    elif question.question_type == 'body_map':
        # Body map uses multiple checkbox selections like multiple_choice
        option_ids = data.get('answers', [])
        selected_areas = []
        for option_id in option_ids:
            try:
                option = AnswerOption.objects.get(id=option_id, question=question)
                response.answer_options.add(option)
                selected_areas.append(option.option_value)
            except AnswerOption.DoesNotExist:
                pass
        # Also save as JSON for easier AI processing
        response.answer_body_map = {"areas": selected_areas}
        response.save()
        
    else:  # text
        response.answer_text = data.get('answer', '')
        response.save()
    
    # If no specific card found, get default card for question
    if not motivational_card:
        motivational_card = MotivationalCard.objects.filter(
            question=question,
            is_default_for_question=True,
            is_active=True
        ).first()
    
    # Get next question
    next_question = OnboardingQuestion.objects.filter(
        order__gt=question.order,
        is_active=True
    ).first()
    
    logger.info(f"Next question: {next_question.id if next_question else 'None'}")
    
    result = {
        'success': True,
        'next_question_url': f'/onboarding/question/{next_question.id}/' if next_question else None,
        'motivational_card': None
    }
    
    logger.info(f"Result before motivational card: {result}")
    
    # Always show motivational card (either specific or default)
    if motivational_card:
        # Replace [Имя] placeholder with actual name
        message = motivational_card.message
        title = motivational_card.title or ''
        image_url = motivational_card.cdn_url
    else:
        # Default motivational message
        title = "Отлично! 🎯"
        message = "Ваш ответ сохранен. Каждый шаг приближает нас к созданию идеальной программы специально для вас!"
        image_url = ''
    
    # Replace name placeholder
    if '[Имя]' in message and hasattr(request.user, 'first_name') and request.user.first_name:
        message = message.replace('[Имя]', request.user.first_name)
    elif '[Имя]' in message:
        # Try to get name from first question response
        name_response = UserOnboardingResponse.objects.filter(
            user=request.user,
            question__ai_field_name='user_name'
        ).first()
        if name_response:
            name = name_response.get_answer_value()
            if name:
                message = message.replace('[Имя]', name)
    
    # Always use random quotes background for motivational cards
    # Override any existing image with quotes photos
    image_url = _get_random_motivational_background()
    
    # Fallback to original if quotes function fails
    if not image_url and motivational_card:
        image_url = motivational_card.cdn_url
    
    result['motivational_card'] = {
        'title': title,
        'message': message,
        'image_url': image_url
    }
    
    # If last question, generate workout plan
    if not next_question:
        result['redirect_to_archetype'] = True
    
    logger.info(f"Final result: {result}")
    logger.info("=== SAVE_ANSWER DEBUG END ===")
    
    return JsonResponse(result)


@login_required
def select_archetype(request):
    """Archetype selection page"""
    if request.method == 'POST':
        archetype = request.POST.get('archetype')
        if archetype in ['bro', 'sergeant', 'intellectual']:
            profile = request.user.profile
            profile.archetype = archetype
            profile.save()
            
            # Generate workout plan with real AI analysis
            return redirect('onboarding:generate_plan')
        else:
            messages.error(request, 'Выберите корректный архетип тренера')
    
    archetypes = [
        {
            'key': 'bro',
            'name': 'Бро',
            'description': 'Дружелюбный и мотивирующий. Всегда поддержит и подскажет. Говорит простым языком.',
            'image': '/static/images/avatars/bro-avatar.png',
            'style': 'Casual и расслабленный'
        },
        {
            'key': 'sergeant',
            'name': 'Сержант',
            'description': 'Строгий и требовательный. Поможет вам превзойти себя. Четкие команды и дисциплина.',
            'image': '/static/images/avatars/sergeant-avatar.png',
            'style': 'Военный стиль'
        },
        {
            'key': 'intellectual',
            'name': 'Интеллектуал',
            'description': 'Научный подход к тренировкам. Детальные объяснения и обоснования.',
            'image': '/static/images/avatars/intellectual-avatar.png',
            'style': 'Научный подход'
        }
    ]
    
    context = {'archetypes': archetypes}
    return render(request, 'onboarding/select_archetype.html', context)




@login_required
def generate_plan(request):
    """Generate AI workout plan (with comprehensive support)"""
    from apps.workouts.models import WorkoutPlan

    # ГАРД: если план уже существует, не генерируем повторно
    existing_plan = WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
    if existing_plan:
        messages.info(request, 'У вас уже есть активный план тренировок')
        return redirect('users:dashboard')
    
    # Show loading page for GET request
    if request.method == 'GET':
        return render(request, 'onboarding/analysis_loading.html')
    
    profile = request.user.profile
    
    if not profile.archetype:
        messages.error(request, 'Сначала выберите архетип тренера')
        return redirect('onboarding:select_archetype')
    
    # Collect all user responses
    responses = UserOnboardingResponse.objects.filter(user=request.user)
    user_data = {
        'archetype': profile.archetype,
        'age': 25,  # Default, will be overridden by responses
        'height': 175,
        'weight': 70,
        'height_unit': 'cm',
        'weight_unit': 'kg',
        'duration_weeks': 6,
        'workout_duration': 45
    }
    
    # Process responses into AI-friendly format
    for response in responses:
        field_name = response.question.ai_field_name
        value = response.get_answer_value()
        user_data[field_name] = value
    
    # Map some common fields
    if 'days_per_week' not in user_data:
        user_data['days_per_week'] = 4
    if 'equipment' not in user_data:
        user_data['equipment'] = ['bodyweight']
    
    # Check if comprehensive analysis was requested
    use_comprehensive = request.POST.get('use_comprehensive') == 'true'
    
    try:
        # Use centralized service for plan creation
        from apps.ai_integration.services import create_workout_plan_from_onboarding

        # Pass comprehensive flag through user_data
        if use_comprehensive:
            user_data['use_comprehensive'] = True
        
        workout_plan = create_workout_plan_from_onboarding(request.user)
        
        # Check if we got comprehensive data
        if hasattr(workout_plan, 'ai_analysis') and workout_plan.ai_analysis:
            # We have comprehensive data, show comprehensive preview
            return redirect('onboarding:ai_analysis_comprehensive')
        else:
            # Standard flow
            messages.success(request, 'Ваш персональный план тренировок готов!')
            return redirect('onboarding:plan_confirmation', plan_id=workout_plan.id)
        
    except Exception as e:
        messages.error(request, f'Ошибка при генерации плана: {str(e)}')
        return render(request, 'onboarding/error.html', {'error': str(e)})


@login_required
def generate_plan_ajax(request):
    """AJAX endpoint for plan generation with progress updates"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    from django.conf import settings

    from apps.ai_integration.services import WorkoutPlanGenerator
    from apps.onboarding.services import OnboardingDataProcessor
    from apps.workouts.models import WorkoutPlan

    # Check if plan already exists
    existing_plan = WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
    if existing_plan:
        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('users:dashboard')
        })
    
    try:
        # Check if we're confirming a previewed plan
        action = request.POST.get('action', 'generate')
        
        if action == 'confirm':
            # User confirmed the plan after preview
            plan_data = request.session.get('pending_plan_data')
            if not plan_data:
                return JsonResponse({
                    'status': 'error',
                    'error': 'No pending plan to confirm'
                }, status=400)
            
            # Create the actual workout plan
            generator = WorkoutPlanGenerator()
            workout_plan = generator.create_plan(request.user, plan_data)
            
            # Clear session data
            request.session.pop('pending_plan_data', None)
            
            # Mark onboarding as complete
            request.user.completed_onboarding = True
            request.user.save()
            
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('onboarding:plan_confirmation', kwargs={'plan_id': workout_plan.id}),
                'plan_id': workout_plan.id
            })
        
        else:
            # Generate new plan
            user_data = OnboardingDataProcessor.collect_user_data(request.user)
            generator = WorkoutPlanGenerator()
            
            # Generate plan data (not saved to DB yet)
            plan_data = generator.generate_plan(user_data)
            
            if settings.SHOW_AI_ANALYSIS and 'analysis' in plan_data:
                # Store plan in session for confirmation
                request.session['pending_plan_data'] = plan_data
                
                # Return analysis for preview
                return JsonResponse({
                    'status': 'needs_confirmation',
                    'analysis': plan_data.get('analysis', {}),
                    'plan_preview': {
                        'plan_name': plan_data.get('plan_name', 'Персональный план'),
                        'duration_weeks': plan_data.get('duration_weeks', 4),
                        'weekly_frequency': plan_data.get('weekly_frequency', 3),
                        'session_duration': plan_data.get('session_duration', 45),
                        'first_week_focus': plan_data.get('weeks', [{}])[0].get('focus', '') if plan_data.get('weeks') else '',
                    }
                })
            else:
                # Direct creation without preview
                workout_plan = generator.create_plan(request.user, plan_data)
                
                # Mark onboarding as complete
                request.user.completed_onboarding = True
                request.user.save()
                
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': reverse('onboarding:plan_confirmation', kwargs={'plan_id': workout_plan.id}),
                    'plan_id': workout_plan.id
                })
        
    except Exception as e:
        logger.error(f"Plan generation failed for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@login_required
def plan_confirmation(request, plan_id=None):
    """Show plan confirmation page before starting"""
    if plan_id:
        latest_plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    else:
        latest_plan = request.user.workout_plans.filter(is_active=True).first()
    
    if not latest_plan:
        messages.error(request, 'План тренировок не найден')
        return redirect('onboarding:generate_plan')
    
    if request.method == 'POST':
        # User confirmed the plan
        latest_plan.is_confirmed = True
        latest_plan.save()
        
        messages.success(request, 'Отлично! Ваш план активирован. Начнем тренироваться!')
        return redirect('users:dashboard')
    
    # Extract plan data and analysis
    plan_data = latest_plan.plan_data
    
    # Extract analysis data (prioritize separate ai_analysis field)
    analysis_data = latest_plan.ai_analysis or plan_data.get('analysis', {})
    
    # Extract plan details (new structure with cycles/phases)
    plan_details = plan_data.get('plan', plan_data.get('protocol', plan_data))
    
    # Count total exercises - check old structure first
    total_exercises = 0
    archetype = request.user.profile.archetype
    
    # First try the old weeks structure (most common case)
    weeks_data = plan_data.get('weeks', [])
    if weeks_data:
        for week in weeks_data:
            for day in week.get('days', []):
                if not day.get('is_rest_day'):
                    total_exercises += len(day.get('exercises', []))
    else:
        # Handle different archetype structures (new structure)
        if archetype == 'bro':
            # Bro uses cycles with daily_workouts
            for cycle in plan_details.get('cycles', []):
                for workout in cycle.get('daily_workouts', []):
                    if not workout.get('is_rest_day'):
                        total_exercises += len(workout.get('exercises', []))
        elif archetype == 'sergeant':
            # Sergeant uses phases with daily_operations
            for phase in plan_details.get('phases', []):
                for operation in phase.get('daily_operations', []):
                    if not operation.get('is_rest_day'):
                        total_exercises += len(operation.get('exercises', []))
        elif archetype == 'intellectual':
            # Intellectual uses phases with training_sessions
            for phase in plan_details.get('phases', []):
                for session in phase.get('training_sessions', []):
                    if not session.get('is_rest_day'):
                        total_exercises += len(session.get('exercises', []))
    
    # Extract AI feedback/analysis from plan data
    ai_feedback = analysis_data.get('profile_insight') or analysis_data.get('profile_assessment') or analysis_data.get('scientific_assessment') or "Персональный анализ готов!"
    
    context = {
        'plan': latest_plan,
        'plan_data': plan_details,
        'analysis_data': analysis_data,
        'ai_feedback': ai_feedback,
        'total_exercises': total_exercises,
        'archetype': archetype,
        'duration_days': plan_details.get('duration_days', 90)
    }
    
    return render(request, 'onboarding/plan_confirmation.html', context)


@login_required
def plan_preview(request):
    """Show generated plan preview"""
    latest_plan = request.user.workout_plans.filter(is_active=True).first()
    
    if not latest_plan:
        messages.error(request, 'План не найден')
        return redirect('users:dashboard')
    
    context = {
        'plan': latest_plan,
        'plan_data': latest_plan.plan_data
    }
    
    return render(request, 'onboarding/plan_preview.html', context)


@login_required
def ai_analysis_comprehensive(request):
    """Display comprehensive AI analysis with 4 blocks"""

    # Get the latest plan with comprehensive analysis
    latest_plan = request.user.workout_plans.filter(is_active=True).first()
    
    if not latest_plan:
        messages.error(request, 'План не найден')
        return redirect('onboarding:select_archetype')
    
    # Extract comprehensive data from ai_analysis
    ai_analysis = latest_plan.ai_analysis or {}
    plan_data = latest_plan.plan_data or {}
    
    # Check if we have comprehensive structure
    has_comprehensive = (
        'user_analysis' in ai_analysis or
        'motivation_system' in ai_analysis or
        'long_term_strategy' in ai_analysis
    )
    
    if not has_comprehensive:
        # Fallback to regular analysis page
        return redirect('onboarding:ai_analysis')
    
    context = {
        'plan': latest_plan,
        'plan_data': plan_data,
        'comprehensive_data': ai_analysis,
        'archetype': request.user.profile.archetype,
        'user_level': 'Персональный'  # Could be determined from analysis
    }
    
    return render(request, 'onboarding/ai_analysis_comprehensive.html', context)


@login_required
def plan_preview_comprehensive(request):
    """Show comprehensive plan preview with 4-block analysis"""
    
    latest_plan = request.user.workout_plans.filter(is_active=True).first()
    
    if not latest_plan:
        messages.error(request, 'План не найден')
        return redirect('users:dashboard')
    
    # Extract data
    ai_analysis = latest_plan.ai_analysis or {}
    plan_data = latest_plan.plan_data or {}
    
    # Check if we have comprehensive structure
    has_comprehensive = (
        'user_analysis' in ai_analysis or
        'motivation_system' in ai_analysis or
        'long_term_strategy' in ai_analysis
    )
    
    if not has_comprehensive:
        # Fallback to regular preview
        return redirect('onboarding:plan_preview')
    
    # Handle form submission
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            # User confirmed the comprehensive plan
            latest_plan.is_confirmed = True
            latest_plan.save()
            
            # Mark onboarding as complete
            request.user.onboarding_completed_at = timezone.now()
            request.user.completed_onboarding = True
            request.user.save()
            
            messages.success(request, 'Ваш comprehensive план активирован!')
            return redirect('users:dashboard')
        
        elif action == 'regenerate':
            # Delete current plan and start over
            latest_plan.delete()
            messages.info(request, 'Генерируем новый comprehensive план...')
            return redirect('onboarding:generate_plan')
    
    # Extract training program from comprehensive structure
    training_program = plan_data
    if 'training_program' in plan_data:
        training_program = plan_data['training_program']
    
    context = {
        'plan': latest_plan,
        'plan_data': plan_data,
        'training_program': training_program,
        'comprehensive_data': ai_analysis,
        'archetype': request.user.profile.archetype,
        'user_level': 'Comprehensive'
    }
    
    return render(request, 'onboarding/plan_preview_comprehensive.html', context)


@login_required
def ai_analysis(request):
    """Regular AI analysis (fallback for non-comprehensive)"""
    
    latest_plan = request.user.workout_plans.filter(is_active=True).first()
    
    if not latest_plan:
        messages.error(request, 'План не найден')
        return redirect('onboarding:select_archetype')
    
    # Extract data for regular analysis template
    plan_data = latest_plan.plan_data or {}
    ai_analysis = latest_plan.ai_analysis or {}
    
    # Create compatibility data for old template
    analysis_data = {
        'age': 25,  # Default values
        'height': 175,
        'weight': 70,
        'primary_goal': 'general_fitness',
        'experience_level': 'Начинающий',
        'days_per_week': '3-4',
        'workout_duration': '45-60',
        'equipment': 'Вес тела',
        'preferred_time': 'Вечер'
    }
    
    # Override with actual data if available
    if 'user_data' in ai_analysis:
        user_data = ai_analysis['user_data']
        analysis_data.update(user_data)
    
    context = {
        'plan': latest_plan,
        'plan_data': plan_data,
        'analysis': analysis_data,  # For template compatibility
        'archetype': request.user.profile.archetype
    }
    
    return render(request, 'onboarding/ai_analysis.html', context)