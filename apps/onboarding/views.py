import json
import logging
import os
import random
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from apps.workouts.models import WorkoutPlan

logger = logging.getLogger(__name__)

from .models import (
    AnswerOption,
    MotivationalCard,
    OnboardingQuestion,
    OnboardingSession,
    UserOnboardingResponse,
)

logger = logging.getLogger(__name__)


def _get_random_motivational_background():
    """Get random motivational background image using path field (NEW APPROACH)"""
    try:
        from apps.onboarding.models import MotivationalCard
        from apps.onboarding.utils import public_r2_url
        
        # NEW approach: use path field directly with better randomization
        available_cards = list(MotivationalCard.objects.filter(
            is_active=True,
            path__isnull=False
        ).exclude(path='').values_list('id', 'path'))
        
        if available_cards:
            # Use Python's random selection for better distribution
            card_id, card_path = random.choice(available_cards)
            card = MotivationalCard.objects.get(id=card_id)
            
            if card and card.path:
                public_url = public_r2_url(card.path)
                if public_url:
                    logger.info(f"Using path field: {card.path} -> {public_url}")
                    return public_url
        
        # LEGACY fallback: try to find cards with image_url (during migration period)
        available_legacy_cards = list(MotivationalCard.objects.filter(
            is_active=True,
            image_url__isnull=False
        ).exclude(image_url='').values_list('id', flat=True))
        
        legacy_card = None
        if available_legacy_cards:
            # Use Python's random selection instead of order_by('?') for better distribution
            random_id = random.choice(available_legacy_cards)
            legacy_card = MotivationalCard.objects.get(id=random_id)
        
        if legacy_card and legacy_card.image_url:
            if legacy_card.image_url.startswith('https://pub-'):
                logger.warning(f"Using legacy image_url (should be migrated to path): {legacy_card.image_url}")
                return legacy_card.image_url
        
        # Secondary fallback: use r2_upload_state.json for quotes
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
                # Select random photo and create public URL using new helper
                # Use better randomization to avoid patterns
                random_photo = random.choice(quotes_photos)
                public_url = public_r2_url(random_photo)
                if public_url:
                    logger.info(f"Using public URL from state file ({len(quotes_photos)} available): {public_url}")
                    return public_url
        
        # Final fallback: return empty to use gradient background
        logger.info("No motivational images available, using gradient background")
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
        logger.info(f"Received archetype selection: {archetype}")
        # Map UI values to proper archetype names - updated for V2 consistency
        archetype_map = {
            # V2 keys (current form sends these)
            'peer': 'peer',           # Best Mate / Бро
            'professional': 'professional',  # Pro Coach / Сержант
            'mentor': 'mentor',       # Wise Mentor / Интеллектуал
            # Legacy keys for backward compatibility
            'bro': 'peer',           # Best Mate (legacy)
            'sergeant': 'professional',      # Pro Coach (legacy) 
            'intellectual': 'mentor',  # Wise Mentor (legacy)
        }
        
        if archetype in archetype_map:
            from apps.core.utils.archetypes import validate_archetype
            profile = request.user.profile
            # Save normalized archetype name instead of numeric code
            mapped_archetype = archetype_map[archetype]
            validated_archetype = validate_archetype(mapped_archetype)
            profile.archetype = validated_archetype
            profile.save()
            
            logger.info(f"Successfully saved archetype: {archetype} -> {mapped_archetype} -> {validated_archetype} for user {request.user.email}")
            
            # Generate workout plan with real AI analysis
            return redirect('onboarding:generate_plan')
        else:
            logger.error(f"Invalid archetype received: '{archetype}' not in {list(archetype_map.keys())}")
            messages.error(request, f'Выберите корректный архетип тренера. Получен: {archetype}')
    
    archetypes = [
        {
            'key': 'peer',
            'name': 'Близкий по духу ровесник',
            'description': 'Понимающий, дружелюбный и открытый тренер. Идет к цели вместе с вами как равный, поддерживает через искреннее понимание и общие ценности.',
            'image': '/static/images/avatars/bro-avatar.png',  # Сохраняем существующий аватар
            'style': 'Дружелюбный и искренний'
        },
        {
            'key': 'professional', 
            'name': 'Успешный Профессионал',
            'description': 'Результативный, целеориентированный тренер. Ведет к успеху через четкие планы, измеримые результаты и профессиональную поддержку.',
            'image': '/static/images/avatars/sergeant-avatar.png',  # Сохраняем существующий аватар
            'style': 'Результат-ориентированный'
        },
        {
            'key': 'mentor',
            'name': 'Мудрый Наставник',
            'description': 'Опытный, терпеливый и поддерживающий тренер. Ведет к долгосрочному успеху через понимание и постепенные изменения.',
            'image': '/static/images/avatars/intellectual-avatar.png',  # Сохраняем существующий аватар
            'style': 'Мудрый и терпеливый'
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
        'archetype': profile.archetype_name,
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
    request_start = time.time()
    logger.info(f"=== 🚀 GENERATE_PLAN_AJAX START === User: {request.user.email}")
    
    if request.method != 'POST':
        logger.warning(f"❌ Invalid method {request.method} from user {request.user}")
        return JsonResponse({
            'success': False,
            'error_code': 'METHOD_NOT_ALLOWED',
            'message': 'Метод не поддерживается',
            'progress': 100,
            'retry_allowed': False
        }, status=405)
    
    from django.conf import settings

    from apps.ai_integration.services import WorkoutPlanGenerator
    from apps.onboarding.services import OnboardingDataProcessor
    from apps.workouts.models import WorkoutPlan

    # Check if plan already exists
    existing_plan = WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
    if existing_plan:
        logger.info(f"✅ Existing plan found for user {request.user}: {existing_plan.id}")
        return JsonResponse({
            'success': True,
            'progress': 100,
            'redirect_url': reverse('users:dashboard'),
            'plan_id': existing_plan.id
        })
    
    # Progress tracking with detailed timing
    response_sent = False
    milestone_times = {
        'request_start': request_start,
        'prepare_user_data': None,
        'call_openai_start': None,
        'call_openai_finish': None,
        'build_response': None,
        'total_duration': None
    }
    
    try:
        # Parse JSON data if Content-Type is application/json, otherwise use POST data
        logger.info(f"Request content_type: {request.content_type}")
        logger.info(f"Request body: {request.body}")
        
        if request.content_type == 'application/json' and request.body:
            try:
                data = json.loads(request.body)
                action = data.get('action', 'generate')
                logger.info(f"Parsed JSON data: {data}, action: {action}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                action = 'generate'
        else:
            action = request.POST.get('action', 'generate')
            logger.info(f"POST data action: {action}")
        
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
            
            response_sent = True
            return JsonResponse({
                'success': True,
                'progress': 100,
                'redirect_url': reverse('onboarding:plan_confirmation', kwargs={'plan_id': workout_plan.id}),
                'plan_id': workout_plan.id
            })
        
        else:
            # Generate new plan
            milestone_times['prepare_user_data'] = time.time()
            logger.info(f"📊 Collecting user data for {request.user}...")
            
            user_data = OnboardingDataProcessor.collect_user_data(request.user)
            generator = WorkoutPlanGenerator()
            
            logger.info(f"🧠 Starting AI plan generation (archetype: {user_data.get('archetype')})")
            milestone_times['call_openai_start'] = time.time()
            
            # Generate plan data (not saved to DB yet) 
            plan_data = generator.generate_plan(user_data)
            
            milestone_times['call_openai_finish'] = time.time()
            logger.info(f"✅ AI generation completed in {milestone_times['call_openai_finish'] - milestone_times['call_openai_start']:.1f}s")
            
            if settings.SHOW_AI_ANALYSIS and 'analysis' in plan_data:
                # Store plan in session for confirmation
                request.session['pending_plan_data'] = plan_data
                
                # Return analysis for preview
                response_sent = True
                return JsonResponse({
                    'success': True,
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
                milestone_times['build_response'] = time.time()
                workout_plan = generator.create_plan(request.user, plan_data)
                
                # Mark onboarding as complete
                request.user.completed_onboarding = True
                request.user.save()
                
                milestone_times['total_duration'] = time.time() - request_start
                
                result = {
                    'success': True,
                    'message': 'План успешно создан',
                    'progress': 100,
                    'redirect_url': reverse('onboarding:plan_confirmation', kwargs={'plan_id': workout_plan.id}),
                    'plan_id': workout_plan.id,
                    'retry_allowed': False
                }
                
                # Log detailed timing breakdown
                logger.info(f"✅ === GENERATE_PLAN_AJAX SUCCESS ===")
                logger.info(f"📊 Timing breakdown: " + 
                           f"prepare={milestone_times['prepare_user_data'] - request_start:.1f}s, " +
                           f"ai_call={milestone_times['call_openai_finish'] - milestone_times['call_openai_start']:.1f}s, " +
                           f"total={milestone_times['total_duration']:.1f}s")
                logger.info(f"🎯 Result: {result}")
                
                response_sent = True
                return JsonResponse(result)
        
    except Exception as e:
        milestone_times['total_duration'] = time.time() - request_start
        logger.error(f"❌ Plan generation failed for user {request.user.email} after {milestone_times['total_duration']:.1f}s: {str(e)}")
        
        # Handle specific AI client errors with standardized response format
        from apps.ai_integration.ai_client_gpt5 import AIClientError, ServiceTimeoutError, ServiceCallError
        
        # Map exceptions to standardized error codes and messages
        if isinstance(e, ServiceTimeoutError):
            error_code = "AI_TIMEOUT"
            error_message = "Генерация плана заняла слишком много времени. Сервис перегружен, попробуйте через несколько минут."
            status_code = 504  # Gateway timeout
        elif isinstance(e, ServiceCallError):
            if "too large" in str(e).lower():
                error_code = "PAYLOAD_TOO_LARGE"  
                error_message = "Слишком много данных для обработки. Упростите ответы в анкете."
                status_code = 413  # Request Entity Too Large
            else:
                error_code = "AI_UPSTREAM_ERROR"
                error_message = "Ошибка AI-сервиса. Попробуйте еще раз через минуту."
                status_code = 502  # Bad gateway
        elif isinstance(e, AIClientError):
            error_code = "AI_CLIENT_ERROR"
            error_message = "Не удалось сгенерировать план. Попробуйте еще раз."
            status_code = 500
        else:
            error_code = "UNEXPECTED_ERROR"
            error_message = "Неожиданная ошибка. Попробуйте еще раз."
            status_code = 500
        
        # Standardized error response format
        error_result = {
            'success': False,
            'error_code': error_code,
            'message': error_message,
            'progress': 100,  # Always 100 to unblock frontend
            'retry_allowed': True,
            'details': str(e) if settings.DEBUG else None  # Only in debug mode
        }
        
        # Log detailed error breakdown
        logger.error(f"💥 === GENERATE_PLAN_AJAX ERROR ===")
        logger.error(f"📊 Error timing: total={milestone_times['total_duration']:.1f}s")
        logger.error(f"🔍 Error details: {error_code} - {error_result}")
        
        response_sent = True
        return JsonResponse(error_result, status=status_code)
    
    finally:
        # Safety net: ensure we always send a response to prevent frontend hanging
        if not response_sent:
            milestone_times['total_duration'] = time.time() - request_start
            logger.error(f"🚨 CRITICAL: No response sent after {milestone_times['total_duration']:.1f}s, sending fallback error response")
            fallback_result = {
                'success': False,
                'error_code': 'FALLBACK_ERROR',
                'message': 'Неожиданная ошибка при генерации плана. Попробуйте еще раз.',
                'progress': 100,
                'retry_allowed': True
            }
            return JsonResponse(fallback_result, status=500)


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
        # User confirmed the plan - change status from DRAFT to CONFIRMED
        latest_plan.status = 'CONFIRMED'
        latest_plan.is_confirmed = True  # Keep for backward compatibility
        latest_plan.save()
        
        # Create daily workouts from plan
        from apps.workouts.services import materialize_daily_workouts
        try:
            materialize_daily_workouts(latest_plan)
        except Exception as e:
            logger.warning(f"Could not materialize daily workouts: {e}")
        
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
    archetype = request.user.profile.archetype_name  # Convert numeric to string
    
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
    """Show generated plan preview with REPORT first"""
    # Get or create DRAFT plan
    latest_plan = request.user.workout_plans.filter(
        status='DRAFT'
    ).order_by('-created_at').first()
    
    if not latest_plan:
        # Generate new plan if no DRAFT exists
        from apps.onboarding.services import OnboardingDataProcessor
        from apps.ai_integration.services import WorkoutPlanGenerator
        
        try:
            user_data = OnboardingDataProcessor.collect_user_data(request.user)
            latest_plan = WorkoutPlanGenerator(request.user).generate_plan_with_report(user_data)
        except Exception as e:
            messages.error(request, f'Ошибка генерации плана: {str(e)}')
            return redirect('users:dashboard')
    
    # Extract report and plan from plan_data
    report = latest_plan.plan_data.get('report', {}) if latest_plan.plan_data else {}
    plan = latest_plan.plan_data.get('plan', {}) if latest_plan.plan_data else {}
    
    context = {
        'workout_plan': latest_plan,
        'report': report,
        'plan': plan,
        'can_confirm': latest_plan.status == 'DRAFT'
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
        'archetype': request.user.profile.archetype_name,
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
        'archetype': request.user.profile.archetype_name,
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


def sleep_test(request, seconds):
    """Diagnostic endpoint to test timeout handling without external dependencies"""
    import time
    from django.conf import settings
    
    # Security: limit sleep time in production
    max_sleep = 600 if settings.DEBUG else 300
    if seconds > max_sleep:
        return JsonResponse({
            'success': False,
            'error_code': 'SLEEP_TOO_LONG',
            'message': f'Sleep time limited to {max_sleep}s',
            'requested': seconds,
            'max_allowed': max_sleep
        }, status=400)
    
    start_time = time.time()
    logger.info(f"Sleep test starting: {seconds}s requested")
    
    try:
        time.sleep(seconds)
        duration = time.time() - start_time
        
        result = {
            'success': True,
            'slept': seconds,
            'actual_duration': round(duration, 2),
            'message': f'Successfully slept for {seconds}s',
            'timestamp': time.time()
        }
        
        logger.info(f"Sleep test completed: {duration:.1f}s actual duration")
        return JsonResponse(result)
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Sleep test failed after {duration:.1f}s: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'error_code': 'SLEEP_INTERRUPTED',
            'message': f'Sleep interrupted: {str(e)}',
            'actual_duration': round(duration, 2)
        }, status=500)