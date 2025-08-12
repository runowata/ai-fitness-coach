import json
import logging
import os
from typing import Dict, List, Optional, Set, Tuple

from django.conf import settings
from django.utils import timezone
from openai import OpenAI

from .prompt_manager_v2 import PromptManagerV2
from .ai_client_gpt5 import AIClientFactory, AIClientError
from .fallback_service import FallbackService
from .validators import WorkoutPlanValidator
from apps.onboarding.services import OnboardingDataProcessor
from apps.core.services.exercise_validation import ExerciseValidationService
from apps.core.metrics import incr, MetricNames
from apps.workouts.catalog import get_catalog
from apps.workouts.constants import EXERCISE_FALLBACK_PRIORITY

logger = logging.getLogger(__name__)

# Real OpenAI client
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def create_workout_plan_from_onboarding(user):
    """
    Main function to create workout plan from onboarding data
    Called from onboarding views
    """
    from apps.workouts.models import WorkoutPlan, DailyWorkout
    
    logger.info("🔍 PLAN GENERATION: Starting for user %s", user.id)
    
    try:
        # Use data processor to collect user data
        logger.info("🔍 PLAN GENERATION: Collecting user data...")
        user_data = OnboardingDataProcessor.collect_user_data(user)
        logger.info("🔍 PLAN GENERATION: User data collected, keys: %s", list(user_data.keys()))
        
        # Check if comprehensive analysis should be used (default to True)
        use_comprehensive = user_data.get('use_comprehensive', True)
        
        # Create workout plan using dedicated service
        logger.info("🔍 PLAN GENERATION: Creating plan with WorkoutPlanGenerator...")
        plan_generator = WorkoutPlanGenerator()
        result = plan_generator.create_plan(user, user_data, use_comprehensive)
        logger.info("🔍 PLAN GENERATION: Plan created successfully, plan ID: %s", result.id)
        return result
        
    except Exception as e:
        logger.error("🔍 PLAN GENERATION: FAILED for user %s: %s", user.id, str(e))
        logger.exception("🔍 PLAN GENERATION: Full traceback:")
        raise


class WorkoutPlanGenerator:
    """Service for generating workout plans using AI"""
    
    def __init__(self):
        self.ai_client = AIClientFactory.create_client()
        self.prompt_manager = PromptManagerV2()
    
    def create_plan(self, user, user_data: Dict) -> 'WorkoutPlan':
        """Create a complete workout plan for user"""
        from apps.workouts.models import WorkoutPlan, DailyWorkout
        from apps.onboarding.models import OnboardingSession
        from django.db import transaction
        
        # Prevent race condition - check if plan generation is already in progress
        existing_active_plan = WorkoutPlan.objects.filter(
            user=user, 
            is_active=True,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=10)  # Recent plan
        ).first()
        
        if existing_active_plan:
            logger.info(f"User {user.id} already has a recent active plan, returning existing")
            return existing_active_plan
        
        try:
            logger.info(f"Starting plan generation for user {user.id}")
            logger.info(f"User data type: {type(user_data)}, keys: {list(user_data.keys()) if isinstance(user_data, dict) else 'not dict'}")
            
            # Generate plan with AI
            plan_data = self.generate_plan(user_data)
            logger.info(f"Plan generation completed, type: {type(plan_data)}")
            
            # Validate that plan_data is a dictionary
            if not isinstance(plan_data, dict):
                logger.error(f"Expected dict from generate_plan, got {type(plan_data)}: {plan_data}")
                raise ValueError(f"Invalid plan data type: {type(plan_data)}")
            
            # Post-validate and fix the AI plan
            validator = WorkoutPlanValidator()
            plan_data, validation_report = validator.validate_and_fix_plan(plan_data)
            logger.info(f"Plan validation: {validation_report['fixes_applied']} fixes applied, {validation_report['issues_found']} issues found")
            
            logger.info(f"Creating WorkoutPlan object...")
            
            # Extract analysis and plan from new structure
            analysis_data = plan_data.get('analysis', {})
            plan_details = plan_data.get('plan', plan_data)  # Fallback for old structure
            
            # Create workout plan
            workout_plan = WorkoutPlan.objects.create(
                user=user,
                name=plan_details.get('plan_name', plan_details.get('operation_name', plan_details.get('study_name', 'Персональный план'))),
                duration_weeks=12,  # 90 days ≈ 12 weeks  
                goal=user_data.get('primary_goal', 'general_fitness'),
                plan_data=plan_data,  # Store full AI response including analysis
                ai_analysis=analysis_data,  # Store analysis separately for easier access
                started_at=timezone.now()
            )
            logger.info(f"WorkoutPlan created successfully with id: {workout_plan.id}")
            
            logger.info(f"Creating daily workouts...")
            # Create daily workouts
            self._create_daily_workouts(workout_plan, plan_data)
            logger.info(f"Daily workouts created successfully")
            
            logger.info(f"Updating user completion status...")
            # Mark onboarding as completed
            user.onboarding_completed_at = timezone.now()
            user.completed_onboarding = True  # Set the boolean flag that dashboard checks
            user.save()
            
            logger.info(f"Updating onboarding session...")
            # Update session
            self._update_onboarding_session(user, user_data, plan_data)
            
            # === NEW: окончательно помечаем онбординг как завершённый ===
            self._mark_onboarding_complete(user)
            
            logger.info(f"Plan creation completed successfully")
            return workout_plan
            
        except AIClientError as e:
            logger.error(f"AI client error creating plan for user {user.id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating plan for user {user.id}: {str(e)}")
            raise
    
    def _create_daily_workouts(self, workout_plan, plan_data: Dict):
        """Create daily workout records from plan data (supports both old weeks and new cycles/phases)"""
        from apps.workouts.models import DailyWorkout
        
        logger.info(f"_create_daily_workouts called with plan_data type: {type(plan_data)}")
        
        # Extract plan details (support new structure with analysis)
        plan_details = plan_data.get('plan', plan_data)
        
        # Check for new structure first (cycles/phases), then fall back to old (weeks)
        cycles_data = plan_details.get('cycles', plan_details.get('phases', []))
        
        if cycles_data:
            logger.info(f"Found {len(cycles_data)} cycles/phases in new format")
            self._process_cycles_structure(workout_plan, cycles_data)
        else:
            # Fallback to old weeks structure
            weeks_data = plan_details.get('weeks', [])
            logger.info(f"Found {len(weeks_data)} weeks in old format")
            self._process_weeks_structure(workout_plan, weeks_data)
    
    def _process_cycles_structure(self, workout_plan, cycles_data):
        """Process new cycles/phases structure for 90-day plans"""
        from apps.workouts.models import DailyWorkout
        
        for cycle in cycles_data:
            if not isinstance(cycle, dict):
                logger.error(f"Cycle is not dict: {type(cycle)} = {cycle}")
                continue
            
            # Get daily workouts from cycle (different key names for different archetypes)
            daily_workouts = cycle.get('daily_workouts', cycle.get('daily_operations', cycle.get('training_sessions', [])))
            
            for workout in daily_workouts:
                if not isinstance(workout, dict):
                    logger.error(f"Workout is not dict: {type(workout)} = {workout}")
                    continue
                
                day_number = workout.get('day_number')
                if not day_number:
                    logger.error(f"No day_number in workout: {workout}")
                    continue
                
                # Calculate week number from day number (day 1-7 = week 1, day 8-14 = week 2, etc.)
                week_number = ((day_number - 1) // 7) + 1
                
                # Get confidence task (different key names for different archetypes)
                confidence_task = workout.get('confidence_task', 
                                            workout.get('character_mission', 
                                                      workout.get('behavioral_intervention', '')))
                
                if isinstance(confidence_task, dict):
                    confidence_task_str = confidence_task.get('description', str(confidence_task))
                else:
                    confidence_task_str = str(confidence_task) if confidence_task else ''
                
                # Get workout name (different key names for different archetypes)
                workout_name = workout.get('workout_name', 
                                         workout.get('operation_name', 
                                                   workout.get('session_name', f'День {day_number}')))
                
                logger.info(f"Creating DailyWorkout for day {day_number} (week {week_number})")
                DailyWorkout.objects.create(
                    plan=workout_plan,
                    day_number=day_number,
                    week_number=week_number,
                    name=workout_name,
                    exercises=workout.get('exercises', []),
                    is_rest_day=workout.get('is_rest_day', False),
                    confidence_task=confidence_task_str
                )
    
    def _process_weeks_structure(self, workout_plan, weeks_data):
        """Process old weeks structure (fallback)"""
        from apps.workouts.models import DailyWorkout
        
        for week_index, week in enumerate(weeks_data):
            if not isinstance(week, dict):
                logger.error(f"Week {week_index} is not dict: {type(week)} = {week}")
                continue
                
            days_data = week.get('days', [])
            
            for day_index, day in enumerate(days_data):
                if not isinstance(day, dict):
                    logger.error(f"Day {day_index} is not dict: {type(day)} = {day}")
                    continue
                
                confidence_task = day.get('confidence_task', '')
                if isinstance(confidence_task, dict):
                    confidence_task_str = confidence_task.get('description', '')
                else:
                    confidence_task_str = str(confidence_task)
                
                actual_week_number = week_index + 1  
                actual_day_number = day_index + 1
                
                logger.info(f"Creating DailyWorkout for week {actual_week_number} day {actual_day_number}")
                DailyWorkout.objects.create(
                    plan=workout_plan,
                    day_number=actual_day_number,
                    week_number=actual_week_number,
                    name=day.get('workout_name', f'День {actual_day_number}'),
                    exercises=day.get('exercises', []),
                    is_rest_day=day.get('is_rest_day', False),
                    confidence_task=confidence_task_str
                )
    
    def _update_onboarding_session(self, user, user_data: Dict, plan_data: Dict):
        """Update onboarding session with AI data"""
        from apps.onboarding.models import OnboardingSession
        
        session = OnboardingSession.objects.filter(
            user=user,
            is_completed=False
        ).first()
        
        if session:
            session.is_completed = True
            session.completed_at = timezone.now()
            session.ai_request_data = user_data
            session.ai_response_data = plan_data
            session.save()
    
    def generate_plan(self, user_data: Dict, use_comprehensive: bool = True) -> Dict:
        """Generate a complete workout plan based on user onboarding data"""
        # Check for legacy flow fallback
        if settings.FALLBACK_TO_LEGACY_FLOW:
            logger.warning("Using legacy flow for plan generation")
            return self._generate_plan_legacy(user_data)
        
        archetype = user_data.get('archetype', 'bro')
        
        # Get allowed exercises for this archetype
        allowed_slugs = ExerciseValidationService.get_allowed_exercise_slugs(archetype=archetype)
        incr(MetricNames.AI_WHITELIST_COUNT, len(allowed_slugs))
        logger.info(f"Whitelist for {archetype}: {len(allowed_slugs)} exercises")
        
        # Check if we should use comprehensive 4-block structure
        if use_comprehensive:
            logger.info(f"Using comprehensive 4-block report generation")
            return self._generate_comprehensive_plan(user_data, archetype, allowed_slugs)
        
        # Build prompt with whitelist (legacy method)
        prompt = self._build_prompt_with_whitelist(user_data, allowed_slugs)
        
        # Reprompt cycle with limits
        max_attempts = settings.AI_REPROMPT_MAX_ATTEMPTS
        
        for attempt in range(max_attempts + 1):
            try:
                # Get system prompt for archetype  
                system_prompt = self._get_system_prompt(archetype)
                
                # Use new method with strict validation
                if hasattr(self.ai_client, 'generate_workout_plan'):
                    logger.info(f"Attempt {attempt + 1}/{max_attempts + 1}: Using strict validation")
                    validated_plan = self.ai_client.generate_workout_plan(
                        f"{system_prompt}\n\n{prompt}",
                        max_tokens=4096,
                        temperature=0.7
                    )
                    
                    # Convert Pydantic model to dict for downstream compatibility
                    plan_data = validated_plan.model_dump()
                    logger.info(f"Validated plan: {validated_plan.plan_name}, {validated_plan.duration_weeks} weeks")
                else:
                    # Fallback to old method
                    logger.warning("Falling back to old AI client method without validation")
                    plan_data = self.ai_client.generate_completion(
                        f"{system_prompt}\n\n{prompt}",
                        max_tokens=4096,
                        temperature=0.7
                    )
                
                # Post-process and enforce allowed exercises
                plan_data, substitutions, unresolved = self._enforce_allowed_exercises(
                    plan_data, allowed_slugs
                )
                
                # Track metrics
                if substitutions > 0:
                    incr(MetricNames.AI_SUBSTITUTIONS, substitutions)
                    logger.info(f"Made {substitutions} exercise substitutions")
                
                # Check if we have unresolved exercises
                if not unresolved:
                    # Success - all exercises are valid
                    return self._validate_and_enhance_plan(plan_data, user_data)
                
                # Need to reprompt if we have unresolved and haven't exceeded attempts
                if attempt < max_attempts:
                    incr(MetricNames.AI_REPROMPTED)
                    logger.warning(f"Reprompting due to {len(unresolved)} unresolved exercises")
                    prompt = self._build_reprompt(prompt, unresolved, allowed_slugs)
                    continue
                else:
                    # Final attempt failed
                    logger.error(f"Failed to resolve exercises after {max_attempts} attempts")
                    incr(MetricNames.AI_VALIDATION_FAILED)
                    raise ValueError(f"Unable to generate valid plan with available exercises")
            
            except AIClientError as e:
                logger.error(f"AI client error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts:
                    logger.warning("AI generation failed completely, using fallback service")
                    fallback_service = FallbackService()
                    fallback_plan = fallback_service.generate_default_workout_plan(
                        user_data, 
                        f"AI_CLIENT_ERROR: {str(e)}"
                    )
                    return fallback_plan.dict()
                continue
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts:
                    logger.warning("All attempts failed, using fallback service")
                    fallback_service = FallbackService()
                    fallback_plan = fallback_service.generate_default_workout_plan(
                        user_data,
                        f"GENERAL_ERROR: {str(e)}"
                    )
                    return fallback_plan.dict()
                continue
        
        # Should not reach here, but provide fallback just in case
        logger.error("Unexpected fallthrough in generate_plan")
        fallback_service = FallbackService()
        fallback_plan = fallback_service.generate_default_workout_plan(
            user_data,
            "UNEXPECTED_FALLTHROUGH"
        )
        return fallback_plan.dict()
    
    def _generate_comprehensive_plan(self, user_data: Dict, archetype: str, allowed_slugs: Set[str]) -> Dict:
        """Generate comprehensive 4-block AI report with full analysis and plan"""
        try:
            # Normalize archetype for prompt system
            normalized_archetype = self.prompt_manager.normalize_archetype(archetype)
            logger.info(f"Generating comprehensive report for archetype: {normalized_archetype}")
            
            # Build comprehensive prompt
            prompt = self._build_comprehensive_prompt(user_data, allowed_slugs)
            
            # Get comprehensive system and user prompts
            system_prompt, user_prompt = self.prompt_manager.get_prompt_pair(
                'comprehensive', 
                normalized_archetype, 
                with_intro=True
            )
            
            # Render user prompt with data
            rendered_user_prompt = user_prompt.format(**user_data)
            full_prompt = f"{system_prompt}\n\n{rendered_user_prompt}\n\n{prompt}"
            
            # Generate comprehensive report
            if hasattr(self.ai_client, 'generate_comprehensive_report'):
                logger.info("Using comprehensive report generation")
                validated_report = self.ai_client.generate_comprehensive_report(
                    full_prompt,
                    user_id=str(user_data.get('user_id', 'anonymous')),
                    archetype=normalized_archetype,
                    max_tokens=12288,
                    temperature=0.7
                )
                
                # Convert ComprehensiveAIReport to dict format expected by downstream code
                report_data = validated_report.model_dump()
                
                # Extract the training program for legacy compatibility
                plan_data = report_data.get('training_program', {})
                
                # Add the full report as analysis data
                analysis_data = {
                    'user_analysis': report_data.get('user_analysis'),
                    'motivation_system': report_data.get('motivation_system'),
                    'long_term_strategy': report_data.get('long_term_strategy'),
                    'meta': report_data.get('meta')
                }
                
                # Post-process and enforce allowed exercises on training program
                plan_data, substitutions, unresolved = self._enforce_allowed_exercises(
                    plan_data, allowed_slugs
                )
                
                # Track metrics
                if substitutions > 0:
                    incr(MetricNames.AI_SUBSTITUTIONS, substitutions)
                    logger.info(f"Made {substitutions} exercise substitutions in comprehensive plan")
                
                if unresolved:
                    logger.warning(f"Comprehensive plan has {len(unresolved)} unresolved exercises")
                    # For comprehensive reports, we'll be more forgiving and allow some unresolved
                
                # Enhance and return combined structure
                enhanced_plan = self._validate_and_enhance_plan(plan_data, user_data)
                
                # Add the analysis back to the enhanced plan
                enhanced_plan['analysis'] = analysis_data
                enhanced_plan['comprehensive'] = True
                
                logger.info(f"Successfully generated comprehensive report with {len(plan_data.get('weeks', []))} weeks")
                return enhanced_plan
                
            else:
                # Fallback to legacy method if comprehensive not available
                logger.warning("Comprehensive report method not available, falling back to legacy")
                return self._generate_plan_legacy(user_data)
                
        except Exception as e:
            logger.error(f"Comprehensive plan generation failed: {str(e)}")
            # Try legacy method first
            try:
                logger.info("Falling back to legacy plan generation")
                return self._generate_plan_legacy(user_data)
            except Exception as legacy_error:
                logger.error(f"Legacy plan generation also failed: {legacy_error}")
                # Ultimate fallback to FallbackService
                logger.warning("Using fallback service for comprehensive plan failure")
                fallback_service = FallbackService()
                fallback_plan = fallback_service.generate_default_workout_plan(
                    user_data,
                    f"COMPREHENSIVE_AND_LEGACY_FAILED: {str(e)}, {str(legacy_error)}"
                )
                return fallback_plan.dict()
    
    def _build_comprehensive_prompt(self, user_data: Dict, allowed_slugs: Set[str]) -> str:
        """Build comprehensive prompt with exercise whitelist"""
        
        # Fallback to real exercises from CSV/Cloudflare if allowed_slugs is empty
        if not allowed_slugs:
            logger.warning("No allowed exercises found, loading from CSV and Cloudflare")
            # Get exercises that have video coverage from database
            from apps.workouts.models import CSVExercise
            try:
                # Get all exercises with video clips (using proper codes from CSV)
                video_exercises = set(
                    CSVExercise.objects.filter(video_clips__isnull=False)
                    .distinct()
                    .values_list('id', flat=True)
                )
                
                if video_exercises:
                    logger.info(f"Loaded {len(video_exercises)} exercises with video coverage from database")
                    allowed_slugs = video_exercises
                else:
                    # Fallback to CSV exercises if no video links found
                    logger.warning("No video exercises found, using all CSV exercises")
                    all_csv_exercises = set(
                        CSVExercise.objects.values_list('id', flat=True)
                    )
                    allowed_slugs = all_csv_exercises
                    logger.info(f"Using {len(allowed_slugs)} exercises from CSV")
                    
            except Exception as e:
                logger.error(f"Failed to load exercises from database: {e}")
                # Ultimate fallback - use technical names from R2 Cloudflare
                import json
                import os
                from django.conf import settings
                try:
                    # Load R2 upload state to get real exercise names
                    r2_state_path = os.path.join(settings.BASE_DIR, 'r2_upload_state.json')
                    if os.path.exists(r2_state_path):
                        with open(r2_state_path, 'r') as f:
                            uploaded_files = json.load(f)
                        
                        # Extract technical exercise names from video files
                        exercise_names = set()
                        for file_path in uploaded_files:
                            if 'videos/exercises/' in file_path and '_technique_' in file_path:
                                filename = file_path.split('/')[-1]  # knee-to-elbow_technique_m01.mp4
                                exercise_name = filename.split('_technique_')[0]  # knee-to-elbow
                                exercise_names.add(exercise_name)
                        
                        allowed_slugs = exercise_names
                        logger.info(f"Loaded {len(allowed_slugs)} exercise names from R2 upload state")
                    else:
                        # Hard-coded R2 exercise names as last resort  
                        allowed_slugs = {
                            'push-ups', 'squats', 'planks', 'burpees', 'lunges', 'mountain-climbers',
                            'crunches', 'wall-sits', 'calf-raises', 'diamond-push-ups', 'jump-squats', 
                            'bicycle-crunches', 'glute-bridges', 'russian-twists', 'dead-bugs',
                            'archer-push-ups', 'atlas-stone-lifts', 'barbell-curls', 'battle-ropes',
                            'bear-crawls', 'bench-press', 'bent-over-rows', 'bicep-curls', 'bird-dogs'
                        }
                        logger.info(f"Using hardcoded R2 exercise names: {len(allowed_slugs)} exercises")
                        
                except Exception as r2_error:
                    logger.error(f"R2 fallback also failed: {r2_error}")
                    # Final emergency fallback
                    allowed_slugs = {
                        'push-ups', 'squats', 'planks', 'burpees', 'lunges', 'crunches'
                    }
        
        # Build comprehensive whitelist instruction  
        whitelist_instruction = f"""
КРИТИЧЕСКИ ВАЖНО - УПРАЖНЕНИЯ:
Используйте ТОЛЬКО упражнения из этого списка в тренировочных планах:
{', '.join(sorted(allowed_slugs))}

ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
1. Каждое упражнение ДОЛЖНО быть из списка выше
2. Используйте точное название (exercise_slug)
3. НЕ изобретайте новые упражнения
4. Если нужно упражнение не из списка - выберите похожее из списка

ПАРАМЕТРЫ rest_seconds (СТРОГО):
- Силовые упражнения: 60-90 секунд
- Кардио упражнения: 30-60 секунд  
- Упражнения на гибкость: 15-30 секунд
- Все значения должны быть от 10 до 600 секунд

ВИДЕО-СИСТЕМА:
- Каждое упражнение имеет предзаписанные видео
- Включает: технику, типичные ошибки, инструкции по архетипам
- Система автоматически генерирует плейлисты с мотивационными вставками
- Используются только упражнения с полным видео-покрытием

СТРУКТУРА ПЛЕЙЛИСТА (автоматически создается):
- Вводное мотивационное видео
- Инструкции по технике для каждого упражнения  
- Видео разборов типичных ошибок
- Промежуточная мотивация между упражнениями
- Заключительное мотивационное видео

ЗАДАЧА: Создать план используя ТОЛЬКО упражнения из whitelist выше!
"""

        return whitelist_instruction
    
    def _generate_plan_legacy(self, user_data: Dict) -> Dict:
        """Legacy plan generation without strict validation"""
        prompt = self._build_prompt(user_data)
        archetype = user_data.get('archetype', 'bro')
        
        try:
            system_prompt = self._get_system_prompt(archetype)
            plan_data = self.ai_client.generate_completion(
                f"{system_prompt}\n\n{prompt}",
                max_tokens=4096,
                temperature=0.7
            )
            return self._validate_and_enhance_plan(plan_data, user_data)
        except Exception as e:
            logger.error(f"Legacy plan generation failed: {str(e)}")
            raise
    
    def _build_prompt_with_whitelist(self, user_data: Dict, allowed_slugs: Set[str]) -> str:
        """Build prompt with exercise whitelist"""
        base_prompt = self._build_prompt(user_data)
        
        # Add whitelist instruction
        whitelist_instruction = f"""
IMPORTANT: You MUST use ONLY exercises from this allowed list:
{', '.join(sorted(allowed_slugs))}

If you cannot find a suitable exercise from the list, choose the closest alternative based on:
1. Same muscle group
2. Similar equipment requirements  
3. Similar difficulty level

DO NOT use any exercises not in this list.
"""
        
        return f"{base_prompt}\n\n{whitelist_instruction}"
    
    def _enforce_allowed_exercises(
        self, 
        plan_data: Dict, 
        allowed_slugs: Set[str]
    ) -> Tuple[Dict, int, List[str]]:
        """
        Enforce that all exercises in plan are from allowed set
        
        Returns:
            (modified_plan, substitution_count, unresolved_exercises)
        """
        catalog = get_catalog()
        substitutions = 0
        unresolved = []
        
        # Process each week and day
        for week in plan_data.get('weeks', []):
            for day in week.get('days', []):
                fixed_exercises = []
                
                for exercise in day.get('exercises', []):
                    exercise_slug = exercise.get('exercise_slug', '')
                    
                    if exercise_slug in allowed_slugs:
                        # Exercise is allowed, keep as-is
                        fixed_exercises.append(exercise)
                    else:
                        # Need to find substitute
                        substitutes = catalog.find_similar(
                            exercise_slug,
                            allowed_slugs,
                            priority=EXERCISE_FALLBACK_PRIORITY,
                            max_results=1
                        )
                        
                        if substitutes:
                            # Found replacement
                            replacement_slug = substitutes[0]
                            exercise['exercise_slug'] = replacement_slug
                            exercise['_substituted'] = True
                            exercise['_original'] = exercise_slug
                            fixed_exercises.append(exercise)
                            substitutions += 1
                            logger.info(f"Substituted {exercise_slug} -> {replacement_slug}")
                        else:
                            # No valid substitute found
                            exercise['_unresolved'] = True
                            fixed_exercises.append(exercise)
                            unresolved.append(exercise_slug)
                            logger.warning(f"No substitute found for {exercise_slug}")
                
                day['exercises'] = fixed_exercises
        
        return plan_data, substitutions, unresolved
    
    def _build_reprompt(
        self, 
        original_prompt: str, 
        unresolved: List[str], 
        allowed_slugs: Set[str]
    ) -> str:
        """Build reprompt for unresolved exercises"""
        reprompt = f"""
{original_prompt}

CORRECTION NEEDED: The following exercises are not available and need replacement:
{', '.join(unresolved)}

Please regenerate the plan using ONLY exercises from the allowed list.
Focus especially on finding good substitutes for the exercises listed above.
Consider muscle groups, equipment, and difficulty when selecting alternatives.

Allowed exercises: {', '.join(sorted(allowed_slugs))}
"""
        return reprompt

    def adapt_weekly_plan(self, current_plan: Dict, user_feedback: List[Dict], week_number: int, user_archetype: str = 'bro') -> Dict:
        """Adapt the plan for the upcoming week based on user feedback"""
        adaptation_prompt = self._build_adaptation_prompt(current_plan, user_feedback, week_number, user_archetype)
        
        try:
            # Get system prompt for adaptation
            system_prompt = self._get_adaptation_system_prompt(user_archetype)
            
            # Use AI client to generate response (returns Dict directly)
            adaptation = self.ai_client.generate_completion(
                f"{system_prompt}\n\n{adaptation_prompt}",
                max_tokens=1000,
                temperature=0.5
            )
            
            return self._apply_adaptation(current_plan, adaptation, week_number)
            
        except AIClientError as e:
            logger.error(f"AI client error adapting workout plan: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error adapting workout plan: {str(e)}")
            raise ValueError(f"Failed to adapt workout plan: {str(e)}")
    
    def _build_prompt(self, user_data: Dict) -> str:
        """Build the prompt for plan generation using archetype-specific template"""
        archetype = user_data.get('archetype', 'bro')
        
        # Normalize archetype from legacy to new naming
        archetype = self.prompt_manager.normalize_archetype(archetype)
        
        try:
            # Get v2 prompts (system + user)
            system_prompt, user_prompt = self.prompt_manager.get_prompt_pair('master', archetype, with_intro=True)
            
            # Format user prompt with user data
            formatted_user_prompt = user_prompt.format(**user_data)
            
            logger.info(f"### USING V2 PROMPTS ### for archetype: {archetype}")
            return f"{system_prompt}\n\n{formatted_user_prompt}"
            
        except Exception as e:
            # Fallback to built-in prompt if v2 prompts have issues
            logger.warning(f"### USING FALLBACK PROMPT ### V2 prompt error: {e}")
            return self._build_fallback_prompt(user_data)
    
    def _build_fallback_prompt(self, user_data: Dict) -> str:
        """Fallback prompt when file template has issues"""
        prompt = f"""
        You are an expert fitness coach creating a personalized workout program.
        
        USER PROFILE:
        - Age: {user_data.get('age', 25)} years
        - Height: {user_data.get('height', 175)} cm
        - Weight: {user_data.get('weight', 70)} kg
        - Primary Goal: {user_data.get('primary_goal', 'general_fitness')}
        - Experience Level: {user_data.get('experience_level', 'beginner')}
        - Days per Week: {user_data.get('days_per_week', 3)}
        - Workout Duration: {user_data.get('workout_duration', 45)} minutes
        - Available Equipment: {user_data.get('available_equipment', 'bodyweight_only')}
        - Health Limitations: {user_data.get('health_limitations', 'none')}
        - Trainer Archetype: {user_data.get('archetype', 'bro')}
        
        Create a {user_data.get('duration_weeks', 6)}-week progressive workout plan.
        
        Return a JSON object with this structure:
        {{
            "plan_name": "string",
            "duration_weeks": {user_data.get('duration_weeks', 6)},
            "weeks": [
                {{
                    "week_number": 1,
                    "days": [
                        {{
                            "day_number": 1,
                            "workout_name": "string",
                            "is_rest_day": false,
                            "exercises": [
                                {{
                                    "exercise_slug": "push_ups",
                                    "sets": 3,
                                    "reps": "8-12",
                                    "rest_seconds": 60
                                }}
                            ],
                            "confidence_task": "string"
                        }}
                    ]
                }}
            ]
        }}
        
        Available exercise slugs: push-ups, squats, plank, pull-ups, lunges, deadlifts, shoulder-press, burpees, bicycle-crunches, mountain-climbers, jumping-jacks
        """
        return prompt
    
    def _get_system_prompt(self, archetype: str = 'bro') -> str:
        """Get system prompt based on trainer archetype"""
        
        archetype_prompts = {
            'bro': """You are a friendly, supportive fitness coach who speaks in a casual, encouraging way. 
            You're like a workout buddy who motivates with positivity and enthusiasm. Use simple language, 
            celebrate progress, and make fitness fun. Always be encouraging and approachable.""",
            
            'sergeant': """You are a disciplined military-style fitness instructor who emphasizes structure, 
            discipline, and clear commands. You push for excellence while maintaining respect. Use direct, 
            precise language and focus on building mental toughness alongside physical strength.""",
            
            'intellectual': """You are a scientifically-minded fitness coach who applies evidence-based 
            principles to training. You explain the 'why' behind exercises using research and data. 
            Your approach is methodical, educational, and backed by sports science."""
        }
        
        base_prompt = """You are an expert fitness coach specializing in creating personalized workout plans 
        for men. You understand the importance of building both physical strength and self-confidence. 
        Your plans are progressive, safe, and engaging. Always include appropriate rest days and 
        confidence-building tasks that help users feel more comfortable in their bodies and social situations."""
        
        archetype_specific = archetype_prompts.get(archetype, archetype_prompts['bro'])
        
        return f"{base_prompt}\n\nYour coaching style: {archetype_specific}"
    
    def _get_adaptation_system_prompt(self, archetype: str = 'bro') -> str:
        """Get adaptation system prompt based on trainer archetype"""
        
        archetype_prompts = {
            'bro': """You are a friendly, supportive fitness coach reviewing your buddy's progress. 
            You speak in a casual, encouraging way and focus on keeping workouts fun and engaging. 
            Make adjustments that maintain motivation while respecting their limits. Use simple, friendly language.""",
            
            'sergeant': """You are a disciplined military fitness instructor reviewing a soldier's performance. 
            You maintain high standards while being fair and strategic. Make tactical adjustments based on 
            performance data to ensure optimal training progression. Use direct, precise language.""",
            
            'intellectual': """You are a scientifically-minded fitness coach analyzing training data. 
            You make evidence-based adjustments using sports science principles. Focus on explaining 
            the rationale behind changes with research-backed reasoning. Use methodical, educational language."""
        }
        
        base_prompt = """You are an expert fitness coach reviewing a user's progress to make weekly adjustments. 
        Based on their feedback, you will suggest minor modifications to maintain optimal challenge and engagement. 
        Only suggest changes that improve the experience without completely restructuring the plan."""
        
        archetype_specific = archetype_prompts.get(archetype, archetype_prompts['bro'])
        
        return f"{base_prompt}\n\nYour coaching style: {archetype_specific}"
    
    def _validate_and_enhance_plan(self, plan_data: Dict, user_data: Dict) -> Dict:
        """Validate the generated plan and add any missing elements"""
        # Ensure plan_data is actually a dict
        if not isinstance(plan_data, dict):
            logger.error(f"plan_data is not a dict: {type(plan_data)} = {plan_data}")
            raise ValueError(f"Invalid plan data type: {type(plan_data)}")
        
        # Clean the plan data to ensure it only has expected fields with correct types
        cleaned_plan = {
            'plan_name': str(plan_data.get('plan_name', 'Персональный план тренировок')),
            'duration_weeks': int(plan_data.get('duration_weeks', 6)),  # Force int
            'goal': str(plan_data.get('goal', user_data.get('primary_goal', 'general_fitness'))),
            'weeks': []
        }
        
        # Clean weeks data
        for week in plan_data.get('weeks', []):
            # Ensure week is a dict
            if not isinstance(week, dict):
                logger.error(f"Week is not a dict: {type(week)} = {week}")
                continue
                
            cleaned_week = {
                'week_number': int(week.get('week_number', 1)),  # Force int
                'week_focus': str(week.get('week_focus', week.get('theme', 'Тренировочная неделя'))),
                'days': []
            }
            
            # Clean days data
            for day in week.get('days', []):
                # Ensure day is a dict
                if not isinstance(day, dict):
                    logger.error(f"Day is not a dict: {type(day)} = {day}")
                    continue
                    
                day_number = int(day.get('day_number', 1))
                cleaned_day = {
                    'day_number': day_number,  # Already int
                    'workout_name': str(day.get('workout_name', f'День {day_number}')),
                    'is_rest_day': bool(day.get('is_rest_day', False)),  # Force bool
                    'exercises': [],
                    'confidence_task': str(day.get('confidence_task', ''))
                }
                
                # Clean exercises data
                for exercise in day.get('exercises', []):
                    # Ensure exercise is a dict
                    if not isinstance(exercise, dict):
                        logger.error(f"Exercise is not a dict: {type(exercise)} = {exercise}")
                        continue
                        
                    cleaned_exercise = {
                        'exercise_slug': str(exercise.get('exercise_slug', '')),
                        'sets': int(exercise.get('sets', 3)),  # Force int
                        'reps': str(exercise.get('reps', '8-12')),
                        'rest_seconds': int(exercise.get('rest_seconds', 60))  # Force int
                    }
                    cleaned_day['exercises'].append(cleaned_exercise)
                
                # Handle confidence_task if it's a dict (already converted to string above, but double-check)
                confidence_task = day.get('confidence_task', '')
                if isinstance(confidence_task, dict):
                    cleaned_day['confidence_task'] = str(confidence_task.get('description', ''))
                else:
                    cleaned_day['confidence_task'] = str(confidence_task)
                
                cleaned_week['days'].append(cleaned_day)
            
            # Ensure all weeks have proper rest days
            rest_days = sum(1 for day in cleaned_week['days'] if day.get('is_rest_day', False))
            if rest_days == 0:
                # Add a rest day if none exists
                cleaned_week['days'].append({
                    'day_number': len(cleaned_week['days']) + 1,
                    'workout_name': 'Active Recovery',
                    'is_rest_day': True,
                    'exercises': [],
                    'confidence_task': 'Take a relaxing walk and practice positive self-talk'
                })
            
            cleaned_plan['weeks'].append(cleaned_week)
        
        # Add metadata
        cleaned_plan['generated_at'] = timezone.now().isoformat()
        cleaned_plan['user_archetype'] = user_data.get('archetype', 'bro')
        
        return cleaned_plan
    
    
    def _build_adaptation_prompt(self, current_plan: Dict, user_feedback: List[Dict], week_number: int, user_archetype: str = 'bro') -> str:
        """Build prompt for weekly adaptation based on archetype"""
        feedback_summary = self._summarize_feedback(user_feedback)
        
        # Archetype-specific prompt introductions
        archetype_intros = {
            'bro': f"Эй, братан! Давай посмотрим как прошла неделя {week_number - 1} и адаптируем план для недели {week_number}.",
            'sergeant': f"Рапорт по неделе {week_number - 1} получен. Анализируем результаты и корректируем план для недели {week_number}.",
            'intellectual': f"Анализируем данные по неделе {week_number - 1} для оптимизации протокола недели {week_number}."
        }
        
        # Archetype-specific response formats
        archetype_responses = {
            'bro': """
            Верни JSON с адаптациями в дружелюбном стиле:
            {{
                "intensity_adjustment": "increase|maintain|decrease",
                "exercise_swaps": [
                    {{"from": "exercise_slug", "to": "exercise_slug", "reason": "Понятное объяснение почему меняем"}}
                ],
                "volume_changes": {{"exercise_slug": {{"sets": number, "reps": "string"}}}},
                "bro_motivation": "Мотивирующее сообщение от бро-тренера",
                "additional_notes": "Дружеские советы и объяснения"
            }}
            """,
            
            'sergeant': """
            Верни JSON с тактическими корректировками:
            {{
                "intensity_adjustment": "increase|maintain|decrease",
                "exercise_swaps": [
                    {{"from": "exercise_slug", "to": "exercise_slug", "reason": "Тактическое обоснование замены"}}
                ],
                "volume_changes": {{"exercise_slug": {{"sets": number, "reps": "string"}}}},
                "sergeant_orders": "Приказы и указания на неделю",
                "additional_notes": "Стратегические рекомендации"
            }}
            """,
            
            'intellectual': """
            Верни JSON с научно обоснованными корректировками:
            {{
                "intensity_adjustment": "increase|maintain|decrease",
                "exercise_swaps": [
                    {{"from": "exercise_slug", "to": "exercise_slug", "reason": "Научное обоснование замены"}}
                ],
                "volume_changes": {{"exercise_slug": {{"sets": number, "reps": "string"}}}},
                "research_insights": "Научные инсайты и данные",
                "additional_notes": "Методологические рекомендации"
            }}
            """
        }
        
        intro = archetype_intros.get(user_archetype, archetype_intros['bro'])
        response_format = archetype_responses.get(user_archetype, archetype_responses['bro'])
        
        return f"""
        {intro}
        
        Анализ обратной связи:
        - Процент завершения: {feedback_summary['completion_rate']}%
        - Средняя сложность: {feedback_summary['avg_difficulty']}
        - Самые сложные упражнения: {', '.join(feedback_summary['challenging_exercises'])}
        - Количество замен: {feedback_summary['substitution_count']}
        
        Текущий план для недели {week_number}:
        {json.dumps(current_plan['weeks'][week_number - 1], indent=2)}
        
        {response_format}
        """
    
    def _summarize_feedback(self, user_feedback: List[Dict]) -> Dict:
        """Summarize user feedback for the adaptation prompt"""
        total_workouts = len(user_feedback)
        completed_workouts = sum(1 for f in user_feedback if f.get('completed'))
        
        difficulty_map = {'fire': 1, 'smile': 2, 'neutral': 3, 'tired': 4}
        difficulties = [difficulty_map.get(f.get('feedback_rating', 'neutral'), 3) for f in user_feedback]
        
        return {
            'completion_rate': int((completed_workouts / total_workouts * 100) if total_workouts > 0 else 0),
            'avg_difficulty': sum(difficulties) / len(difficulties) if difficulties else 3,
            'challenging_exercises': [],  # Would need to analyze exercise-level feedback
            'substitution_count': sum(len(f.get('substitutions', {})) for f in user_feedback)
        }
    
    
    def _apply_adaptation(self, current_plan: Dict, adaptation: Dict, week_number: int) -> Dict:
        """Apply the suggested adaptations to the plan"""
        logger.info(f"Applying adaptations for week {week_number}: {adaptation}")
        
        # Create a deep copy to avoid modifying the original
        import copy
        adapted_plan = copy.deepcopy(current_plan)
        
        adaptations = adaptation.get('adaptations', {})
        
        # Apply intensity adjustments
        intensity_adj = adaptations.get('intensity_adjustment', 0)
        if intensity_adj != 0:
            self._adjust_plan_intensity(adapted_plan, intensity_adj, week_number)
        
        # Apply volume adjustments  
        volume_adj = adaptations.get('volume_adjustment', 0)
        if volume_adj != 0:
            self._adjust_plan_volume(adapted_plan, volume_adj, week_number)
        
        # Apply exercise substitutions
        substitutions = adaptations.get('exercise_substitutions', {})
        if substitutions:
            self._apply_exercise_substitutions(adapted_plan, substitutions, week_number)
        
        # Apply rest day adjustments
        if adaptations.get('rest_day_adjustment', False):
            self._adjust_rest_days(adapted_plan, week_number)
        
        return adapted_plan
    
    def _adjust_plan_intensity(self, plan: Dict, intensity_change: int, week_number: int):
        """Adjust workout intensity for specific week"""
        weeks = plan.get('weeks', [])
        for week in weeks:
            if week.get('week_number') == week_number:
                for day in week.get('days', []):
                    if not day.get('is_rest_day', False):
                        for exercise in day.get('exercises', []):
                            # Increase/decrease rest time inversely to intensity
                            current_rest = exercise.get('rest_seconds', 60)
                            if intensity_change > 0:
                                # Higher intensity = less rest
                                new_rest = max(30, current_rest - (intensity_change * 2))
                            else:
                                # Lower intensity = more rest
                                new_rest = min(120, current_rest + (abs(intensity_change) * 2))
                            exercise['rest_seconds'] = new_rest
    
    def _adjust_plan_volume(self, plan: Dict, volume_change: int, week_number: int):
        """Adjust workout volume (sets/reps) for specific week"""
        weeks = plan.get('weeks', [])
        for week in weeks:
            if week.get('week_number') == week_number:
                for day in week.get('days', []):
                    if not day.get('is_rest_day', False):
                        for exercise in day.get('exercises', []):
                            # Adjust sets
                            current_sets = exercise.get('sets', 3)
                            if volume_change > 0:
                                new_sets = min(5, current_sets + 1)
                            else:
                                new_sets = max(2, current_sets - 1)
                            exercise['sets'] = new_sets
    
    def _apply_exercise_substitutions(self, plan: Dict, substitutions: Dict, week_number: int):
        """Apply exercise substitutions for specific week"""
        weeks = plan.get('weeks', [])
        for week in weeks:
            if week.get('week_number') == week_number:
                for day in week.get('days', []):
                    if not day.get('is_rest_day', False):
                        exercises = day.get('exercises', [])
                        for i, exercise in enumerate(exercises):
                            old_slug = exercise.get('exercise_slug')
                            if old_slug in substitutions:
                                new_slug = substitutions[old_slug]
                                exercise['exercise_slug'] = new_slug
                                logger.info(f"Substituted {old_slug} with {new_slug} in week {week_number}")
    
    def _adjust_rest_days(self, plan: Dict, week_number: int):
        """Adjust rest day placement for specific week"""
        weeks = plan.get('weeks', [])
        for week in weeks:
            if week.get('week_number') == week_number:
                days = week.get('days', [])
                # Find current rest days
                rest_days = [i for i, day in enumerate(days) if day.get('is_rest_day', False)]
                workout_days = [i for i, day in enumerate(days) if not day.get('is_rest_day', False)]
                
                # If user needs more recovery, add a rest day
                if len(rest_days) < 2 and len(workout_days) > 3:
                    # Convert the last workout day to rest day
                    if workout_days:
                        last_workout_idx = workout_days[-1]
                        days[last_workout_idx]['is_rest_day'] = True
                        days[last_workout_idx]['exercises'] = []
                        days[last_workout_idx]['workout_name'] = 'День отдыха'
    
    def generate_evolved_plan(self, user, evolution_context: Dict, archetype: str = 'bro') -> Dict:
        """Generate an evolved workout plan for a new 6-week cycle"""
        evolution_prompt = self._build_evolution_prompt(user, evolution_context, archetype)
        
        try:
            # Get system prompt for evolution
            system_prompt = self._get_evolution_system_prompt(archetype)
            
            # Use AI client to generate response (returns Dict directly)
            evolved_plan = self.ai_client.generate_completion(
                f"{system_prompt}\n\n{evolution_prompt}",
                max_tokens=2000,
                temperature=0.7
            )
            
            return self._validate_and_enhance_evolved_plan(evolved_plan, evolution_context)
            
        except AIClientError as e:
            logger.error(f"AI client error generating evolved workout plan: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating evolved workout plan: {str(e)}")
            raise ValueError(f"Failed to generate evolved workout plan: {str(e)}")
    
    def _build_evolution_prompt(self, user, evolution_context: Dict, archetype: str) -> str:
        """Build prompt for evolved plan generation"""
        
        previous_plan = evolution_context['previous_plan_summary']
        progress_data = evolution_context['user_progress']
        selected_evolution = evolution_context['selected_evolution']
        
        # Archetype-specific introductions
        archetype_intros = {
            'bro': f"Братан, ты завершил свой первый 6-недельный цикл! Время перейти на следующий уровень!",
            'sergeant': f"Боец, базовая подготовка завершена! Пора переходить к продвинутому тренингу!",
            'intellectual': f"Первый цикл успешно завершен. Анализируем данные для оптимизации следующего этапа."
        }
        
        intro = archetype_intros.get(archetype, archetype_intros['bro'])
        
        prompt = f"""
        {intro}
        
        СТАТИСТИКА ПЕРВОГО ЦИКЛА:
        - Общее завершение: {evolution_context['completion_stats']['overall_completion_rate']:.1f}%
        - Тренировок завершено: {progress_data['total_workouts_completed']}
        - Средний прогресс силы: {progress_data['avg_strength_progress']}/10
        - Средний прогресс уверенности: {progress_data['avg_confidence_progress']}/10
        - Любимые упражнения: {', '.join([ex[0] for ex in progress_data['top_favorite_exercises'][:3]])}
        - Сложные упражнения: {', '.join([ex[0] for ex in progress_data['top_challenging_exercises'][:3]])}
        
        ВЫБРАННОЕ НАПРАВЛЕНИЕ ЭВОЛЮЦИИ: {selected_evolution}
        
        ПРЕДЫДУЩИЙ ПЛАН (краткое содержание):
        - Название: {previous_plan.get('plan_name', 'Базовая программа')}
        - Длительность: {previous_plan.get('duration_weeks', 6)} недель
        - Основные упражнения: {self._extract_main_exercises(previous_plan)}
        
        ЗАДАЧА: Создай новый 6-недельный план, который:
        1. Учитывает прогресс пользователя из первого цикла
        2. Увеличивает сложность и/или разнообразие
        3. Сохраняет любимые упражнения пользователя
        4. Адаптирует/заменяет сложные упражнения
        5. Реализует выбранное направление эволюции
        
        НАПРАВЛЕНИЯ ЭВОЛЮЦИИ:
        - intensity_increase: Увеличить интенсивность, добавить суперсеты, дропсеты
        - variety_expansion: Добавить новые упражнения и методики тренировок
        - personalized_optimization: Персонализировать под прогресс и предпочтения
        
        Создай JSON план со следующей структурой:
        {{
            "plan_name": "Название нового плана",
            "goal": "Описание цели на этот цикл",
            "evolution_notes": "Что изменилось по сравнению с первым циклом",
            "duration_weeks": 6,
            "cycle_number": 2,
            "weeks": [
                {{
                    "week_number": 1,
                    "week_focus": "Фокус недели",
                    "intensity_level": "medium|high|advanced",
                    "days": [
                        {{
                            "day_number": 1,
                            "name": "Название тренировки",
                            "is_rest_day": false,
                            "exercises": [
                                {{
                                    "exercise_slug": "exercise_name",
                                    "exercise_name": "Человеческое название",
                                    "sets": 3,
                                    "reps": "8-12",
                                    "rest_seconds": 60,
                                    "notes": "Особые указания"
                                }}
                            ],
                            "confidence_task": "Задача на уверенность"
                        }}
                    ]
                }}
            ]
        }}
        
        Доступные упражнения: push_ups, squats, plank, pull_ups, lunges, deadlifts, shoulder_press, 
        burpees, mountain_climbers, jumping_jacks, dips, pike_push_ups, glute_bridges, calf_raises,
        russian_twists, bicycle_crunches, superman, wall_sit, high_knees, butt_kicks
        """
        
        return prompt
    
    def _extract_main_exercises(self, plan_data: Dict) -> str:
        """Extract main exercises from previous plan for context"""
        exercises = set()
        weeks = plan_data.get('weeks', [])
        
        for week in weeks[:2]:  # Look at first 2 weeks
            for day in week.get('days', []):
                for exercise in day.get('exercises', []):
                    exercise_slug = exercise.get('exercise_slug')
                    if exercise_slug:
                        exercises.add(exercise_slug)
        
        return ', '.join(list(exercises)[:8])  # Top 8 exercises
    
    def _get_evolution_system_prompt(self, archetype: str = 'bro') -> str:
        """Get system prompt for evolved plan generation"""
        
        archetype_prompts = {
            'bro': """Ты дружелюбный фитнес-тренер, который помогает своему бро перейти на следующий уровень! 
            Ты видишь его прогресс и готов бросить ему новые вызовы. Говори просто и мотивирующе, 
            как лучший друг который хочет видеть результаты.""",
            
            'sergeant': """Ты военный инструктор, который видит что новобранец готов к продвинутой подготовке. 
            Время перейти от базовых упражнений к серьезному тренингу. Будь требовательным но справедливым, 
            создавай программы которые формируют характер.""",
            
            'intellectual': """Ты ученый-тренер, который анализирует данные первого цикла для создания оптимального 
            второго этапа. Используй принципы прогрессивной перегрузки и адаптации на основе собранной статистики. 
            Объясняй логику изменений."""
        }
        
        base_prompt = """Ты создаешь второй 6-недельный цикл тренировок на основе данных первого цикла. 
        Твоя задача - прогрессивно развить программу, учитывая успехи и предпочтения пользователя. 
        Новый план должен быть сложнее, но достижимым. Включи элементы которые понравились, адаптируй сложности."""
        
        archetype_specific = archetype_prompts.get(archetype, archetype_prompts['bro'])
        
        return f"{base_prompt}\n\nТвой стиль: {archetype_specific}"
    
    def _validate_and_enhance_evolved_plan(self, plan_data: Dict, evolution_context: Dict) -> Dict:
        """Validate and enhance the evolved plan"""
        # Add evolution metadata
        plan_data['generated_at'] = timezone.now().isoformat()
        plan_data['evolution_context'] = {
            'previous_completion_rate': evolution_context['completion_stats']['overall_completion_rate'],
            'selected_evolution': evolution_context['selected_evolution'],
            'cycle_number': evolution_context['cycle_number']
        }
        
        # Ensure proper progression
        for week_index, week in enumerate(plan_data.get('weeks', [])):
            week_number = week_index + 1
            
            # Add progressive intensity
            if week_number <= 2:
                week['intensity_level'] = 'medium'
            elif week_number <= 4:
                week['intensity_level'] = 'high'
            else:
                week['intensity_level'] = 'advanced'
            
            # Ensure rest days
            rest_days = sum(1 for day in week.get('days', []) if day.get('is_rest_day', False))
            if rest_days == 0:
                # Add rest day
                week['days'].append({
                    'day_number': len(week['days']) + 1,
                    'name': 'Активное восстановление',
                    'is_rest_day': True,
                    'exercises': [],
                    'confidence_task': 'Практикуй глубокое дыхание и визуализацию успеха'
                })
        
        return plan_data
    
    def _mark_onboarding_complete(self, user):
        """Окончательно помечает онбординг как завершённый"""
        from apps.onboarding.models import OnboardingSession
        
        # 1) пользовательский флаг
        # Mark onboarding as completed in User model (critical for dashboard redirect)
        user.completed_onboarding = True
        user.save(update_fields=["completed_onboarding"])
        
        # Also update profile timestamp
        if hasattr(user, "profile"):
            user.profile.onboarding_completed_at = timezone.now()
            user.profile.save(update_fields=["onboarding_completed_at"])
        
        # 2) любая незакрытая сессия
        OnboardingSession.objects.filter(
            user=user, is_completed=False
        ).update(is_completed=True, completed_at=timezone.now())