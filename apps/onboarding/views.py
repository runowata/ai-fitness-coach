from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .models import OnboardingQuestion, AnswerOption, UserOnboardingResponse, OnboardingSession, MotivationalCard
from .services import (
    OnboardingService,
    AnswerService,
    MotivationalCardService,
    OnboardingDataService,
    ArchetypeService
)
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.workouts.models import WorkoutPlan


@login_required
def start_onboarding(request):
    """Start or continue onboarding process"""
    user = request.user
    
    # Check if already completed properly - use same validation as dashboard
    if OnboardingService.validate_and_fix_onboarding_status(user):
        messages.info(request, 'Вы уже прошли онбординг!')
        return redirect('users:dashboard')
    
    # Get or create session
    session, created = OnboardingService.get_or_create_session(user)
    
    # Get first question
    first_question = OnboardingService.get_first_question()
    if not first_question:
        # If no questions exist, mark onboarding as completed
        OnboardingDataService.mark_onboarding_complete(user)
        messages.success(request, 'Онбординг завершен! Добро пожаловать!')
        return redirect('users:dashboard')
    
    return redirect('onboarding:question', question_id=first_question.id)


@login_required
def question_view(request, question_id):
    """Display single onboarding question"""
    question = get_object_or_404(OnboardingQuestion, id=question_id, is_active=True)
    
    # Get user's existing response
    existing_response = OnboardingService.get_existing_response(request.user, question)
    
    # Get progress information
    progress = OnboardingService.get_question_progress(question)
    
    context = {
        'question': question,
        'existing_response': existing_response,
        **progress
    }
    
    return render(request, 'onboarding/question.html', context)


@login_required
@csrf_exempt
def save_answer(request, question_id):
    """Save answer and redirect to motivational card"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    question = get_object_or_404(OnboardingQuestion, id=question_id, is_active=True)
    data = json.loads(request.body)
    
    try:
        # Save answer using service
        AnswerService.save_answer(request.user, question, data)
        
        # Always redirect to motivation card after saving answer
        return JsonResponse({
            'success': True,
            'redirect_url': f'/onboarding/motivation/{question_id}/'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def select_archetype(request):
    """Archetype selection page"""
    if request.method == 'POST':
        archetype = request.POST.get('archetype')
        if ArchetypeService.save_archetype(request.user, archetype):
            # Generate workout plan
            return redirect('onboarding:generate_plan')
        else:
            messages.error(request, 'Выберите корректный архетип тренера')
    
    archetypes = ArchetypeService.get_archetype_data()
    context = {'archetypes': archetypes}
    return render(request, 'onboarding/select_archetype.html', context)


@login_required
def generate_plan(request):
    """Generate AI workout plan"""
    if not request.user.archetype:
        messages.error(request, 'Сначала выберите архетип тренера')
        return redirect('onboarding:select_archetype')
    
    try:
        # Use centralized service for plan creation
        from apps.ai_integration.services import create_workout_plan_from_onboarding
        
        workout_plan = create_workout_plan_from_onboarding(request.user)
        
        messages.success(request, 'Ваш персональный план тренировок готов!')
        return redirect('onboarding:plan_preview')
        
    except Exception as e:
        messages.error(request, f'Ошибка при генерации плана: {str(e)}')
        return render(request, 'onboarding/error.html', {'error': str(e)})


@login_required
def plan_preview(request):
    """Show generated plan preview with confirmation options"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            # User confirms the plan - activate it and redirect to dashboard
            latest_plan = request.user.workout_plans.filter(is_active=True).first()
            if latest_plan:
                latest_plan.is_confirmed = True
                latest_plan.save()
                
                # Mark onboarding as completed
                OnboardingDataService.mark_onboarding_complete(request.user)
                
                messages.success(request, 'Отлично! Ваш план тренировок активирован!')
                return redirect('users:dashboard')
            
        elif action == 'regenerate':
            # User wants to regenerate the plan
            messages.info(request, 'Генерируем новый план тренировок...')
            return redirect('onboarding:generate_plan')
    
    # GET request - show the preview
    latest_plan = request.user.workout_plans.filter(is_active=True).first()
    
    if not latest_plan:
        messages.error(request, 'План не найден')
        return redirect('onboarding:generate_plan')
    
    # Get trainer archetype for UI customization
    archetype = request.user.archetype or 'bro'
    
    context = {
        'plan': latest_plan,
        'plan_data': latest_plan.plan_data,
        'archetype': archetype,
        'user': request.user
    }
    
    return render(request, 'onboarding/plan_preview.html', context)


@login_required
def motivation_card_view(request, question_id):
    """Show motivational card after answering a question"""
    question = get_object_or_404(OnboardingQuestion, id=question_id, is_active=True)
    
    # Get appropriate motivational card
    motivational_card = MotivationalCardService.get_motivational_card(question)
    
    # Get next question
    next_question = OnboardingService.get_next_question(question)
    
    # Get progress
    progress = OnboardingService.get_question_progress(question)
    
    context = {
        'motivational_card': motivational_card,
        'current_question': question,
        'next_question': next_question,
        'progress_percentage': progress['progress_percent']
    }
    
    return render(request, 'onboarding/motivation_card.html', context)