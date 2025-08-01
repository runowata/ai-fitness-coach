from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
import json
import logging

from .models import OnboardingQuestion, AnswerOption, UserOnboardingResponse, OnboardingSession, MotivationalCard
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.workouts.models import WorkoutPlan

logger = logging.getLogger(__name__)


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
    logger.info(f"=== SAVE_ANSWER DEBUG START ===")
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
    
    if motivational_card:
        # Replace [Имя] placeholder with actual name
        message = motivational_card.message
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
        
        result['motivational_card'] = {
            'title': motivational_card.title or '',
            'message': message,
            'image_url': motivational_card.image_url or ''
        }
    
    # If last question, generate workout plan
    if not next_question:
        result['redirect_to_archetype'] = True
    
    logger.info(f"Final result: {result}")
    logger.info(f"=== SAVE_ANSWER DEBUG END ===")
    
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
    """Generate AI workout plan"""
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
    
    try:
        # Use centralized service for plan creation
        from apps.ai_integration.services import create_workout_plan_from_onboarding
        
        workout_plan = create_workout_plan_from_onboarding(request.user)
        
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
    
    from apps.workouts.models import WorkoutPlan
    from apps.ai_integration.services import create_workout_plan_from_onboarding
    
    # Check if plan already exists
    existing_plan = WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
    if existing_plan:
        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('users:dashboard')
        })
    
    try:
        # Generate plan
        workout_plan = create_workout_plan_from_onboarding(request.user)
        
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
    
    # Count total exercises from new structure
    total_exercises = 0
    archetype = request.user.profile.archetype
    
    # Handle different archetype structures
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
    else:
        # Fallback to old weeks structure
        for week in plan_data.get('weeks', []):
            for day in week.get('days', []):
                if not day.get('is_rest_day'):
                    total_exercises += len(day.get('exercises', []))
    
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