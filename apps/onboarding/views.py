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
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    question = get_object_or_404(OnboardingQuestion, id=question_id, is_active=True)
    data = json.loads(request.body)
    
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
    
    # Handle different question types
    if question.question_type == 'single_choice':
        option_id = data.get('answer')
        if option_id:
            option = get_object_or_404(AnswerOption, id=option_id, question=question)
            response.answer_options.add(option)
            
            # Get motivational card
            motivational_card = option.motivational_card
            
    elif question.question_type == 'multiple_choice':
        option_ids = data.get('answers', [])
        for option_id in option_ids:
            option = get_object_or_404(AnswerOption, id=option_id, question=question)
            response.answer_options.add(option)
        motivational_card = None
        
    elif question.question_type == 'number':
        response.answer_number = data.get('answer')
        response.save()
        motivational_card = None
        
    else:  # text
        response.answer_text = data.get('answer', '')
        response.save()
        motivational_card = None
    
    # Get next question
    next_question = OnboardingQuestion.objects.filter(
        order__gt=question.order,
        is_active=True
    ).first()
    
    result = {
        'success': True,
        'next_question_url': f'/onboarding/question/{next_question.id}/' if next_question else None,
        'motivational_card': None
    }
    
    if motivational_card:
        result['motivational_card'] = {
            'title': motivational_card.title,
            'message': motivational_card.message,
            'image_url': motivational_card.image_url
        }
    
    # If last question, generate workout plan
    if not next_question:
        result['redirect_to_archetype'] = True
    
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
            
            # Redirect to AI analysis first
            return redirect('onboarding:ai_analysis')
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
def ai_analysis_view(request):
    """Show AI analysis of user responses"""
    profile = request.user.profile
    
    if not profile.archetype:
        messages.error(request, 'Сначала выберите архетип тренера')
        return redirect('onboarding:select_archetype')
    
    # Use existing AI infrastructure to analyze user responses
    from apps.ai_integration.services import analyze_user_responses
    
    try:
        analysis_data = analyze_user_responses(request.user)
    except Exception as e:
        logger.error(f"Failed to analyze user responses for user {request.user.id}: {e}")
        messages.error(request, 'Ошибка при анализе ваших данных. Попробуйте еще раз.')
        return redirect('onboarding:select_archetype')
    
    context = {
        'analysis': analysis_data,
        'archetype': profile.archetype
    }
    
    return render(request, 'onboarding/ai_analysis.html', context)


@login_required
def generate_plan(request):
    """Generate AI workout plan"""
    from apps.workouts.models import WorkoutPlan
    
    # ГАРД: если план уже существует, не генерируем повторно
    existing_plan = WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
    if existing_plan:
        messages.info(request, 'У вас уже есть активный план тренировок')
        return redirect('users:dashboard')
    
    # Check if user confirmed analysis
    if request.method == 'POST' and not request.POST.get('analysis_confirmed'):
        messages.error(request, 'Сначала подтвердите анализ')
        return redirect('onboarding:ai_analysis')
    
    # Show loading page for GET request or confirmed analysis
    if request.method == 'GET' or request.POST.get('analysis_confirmed'):
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
        return redirect('users:dashboard')
        
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
            'redirect_url': reverse('onboarding:plan_confirmation'),
            'plan_id': workout_plan.id
        })
        
    except Exception as e:
        logger.error(f"Plan generation failed for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@login_required
def plan_confirmation(request):
    """Show plan confirmation page before starting"""
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
    
    # Extract plan summary
    plan_data = latest_plan.plan_data
    total_exercises = 0
    for week in plan_data.get('weeks', []):
        for day in week.get('days', []):
            if not day.get('is_rest_day'):
                total_exercises += len(day.get('exercises', []))
    
    context = {
        'plan': latest_plan,
        'plan_data': plan_data,
        'total_exercises': total_exercises,
        'archetype': request.user.profile.archetype
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