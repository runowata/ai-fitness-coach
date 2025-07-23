import json
import logging
from typing import Dict, List, Optional

from django.utils import timezone

from .prompt_manager import PromptManager, OnboardingDataProcessor
from .ai_client import AIClientFactory, AIClientError

logger = logging.getLogger(__name__)


def create_workout_plan_from_onboarding(user):
    """
    Main function to create workout plan from onboarding data
    Called from onboarding views
    """
    from apps.workouts.models import WorkoutPlan, DailyWorkout
    
    # Use data processor to collect user data
    user_data = OnboardingDataProcessor.collect_user_data(user)
    
    # Create workout plan using dedicated service
    plan_generator = WorkoutPlanGenerator()
    return plan_generator.create_plan(user, user_data)


class WorkoutPlanGenerator:
    """Service for generating workout plans using AI"""
    
    def __init__(self):
        self.ai_client = AIClientFactory.create_client()
        self.prompt_manager = PromptManager()
    
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
            
            logger.info(f"Creating WorkoutPlan object...")
            # Create workout plan
            workout_plan = WorkoutPlan.objects.create(
                user=user,
                name=plan_data.get('plan_name', 'Персональный план'),
                duration_weeks=plan_data.get('duration_weeks', 6),
                goal=user_data.get('primary_goal', 'general_fitness'),
                plan_data=plan_data,
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
        """Create daily workout records from plan data"""
        from apps.workouts.models import DailyWorkout
        
        logger.info(f"_create_daily_workouts called with plan_data type: {type(plan_data)}")
        weeks_data = plan_data.get('weeks', [])
        logger.info(f"Found {len(weeks_data)} weeks in plan_data")
        
        for week_index, week in enumerate(weeks_data):
            logger.info(f"Processing week {week_index}: type={type(week)}")
            if not isinstance(week, dict):
                logger.error(f"Week {week_index} is not dict: {type(week)} = {week}")
                continue
                
            days_data = week.get('days', [])
            logger.info(f"Week {week_index} has {len(days_data)} days")
            
            for day_index, day in enumerate(days_data):
                logger.info(f"Processing week {week_index} day {day_index}: type={type(day)}")
                if not isinstance(day, dict):
                    logger.error(f"Day {day_index} is not dict: {type(day)} = {day}")
                    continue
                
                # Safe access to confidence_task
                confidence_task = day.get('confidence_task', '')
                if isinstance(confidence_task, dict):
                    confidence_task_str = confidence_task.get('description', '')
                else:
                    confidence_task_str = str(confidence_task)
                
                # Use reliable index-based numbers instead of AI-generated values
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
    
    def generate_plan(self, user_data: Dict) -> Dict:
        """Generate a complete workout plan based on user onboarding data"""
        prompt = self._build_prompt(user_data)
        archetype = user_data.get('archetype', 'bro')
        
        try:
            # Get system prompt for archetype
            system_prompt = self._get_system_prompt(archetype)
            
            # Use AI client to generate response (returns Dict directly)
            plan_data = self.ai_client.generate_completion(
                f"{system_prompt}\n\n{prompt}",
                max_tokens=4096,
                temperature=0.7
            )
            
            # LOG AI RESPONSE FOR DEBUGGING
            logger.warning(f"### AI RAW RESPONSE ### Type: {type(plan_data)}")
            logger.warning(f"### AI RESPONSE KEYS ### {list(plan_data.keys()) if isinstance(plan_data, dict) else 'NOT_DICT'}")
            if isinstance(plan_data, dict):
                weeks = plan_data.get('weeks', [])
                logger.warning(f"### AI WEEKS COUNT ### {len(weeks)}")
                if weeks and len(weeks) > 0:
                    first_week = weeks[0]
                    logger.warning(f"### FIRST WEEK KEYS ### {list(first_week.keys()) if isinstance(first_week, dict) else 'NOT_DICT'}")
                    if isinstance(first_week, dict):
                        days = first_week.get('days', [])
                        logger.warning(f"### FIRST WEEK DAYS COUNT ### {len(days)}")
                        if days and len(days) > 0:
                            first_day = days[0]
                            logger.warning(f"### FIRST DAY KEYS ### {list(first_day.keys()) if isinstance(first_day, dict) else 'NOT_DICT'}")
                            if isinstance(first_day, dict):
                                exercises = first_day.get('exercises', [])
                                logger.warning(f"### FIRST DAY EXERCISES COUNT ### {len(exercises)}")
            
            validated_plan = self._validate_and_enhance_plan(plan_data, user_data)
            
            # LOG VALIDATION RESULT
            logger.warning(f"### POST-VALIDATION WEEKS COUNT ### {len(validated_plan.get('weeks', []))}")
            
            return validated_plan
            
        except AIClientError as e:
            logger.error(f"AI client error generating workout plan: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating workout plan: {str(e)}")
            raise
    
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
        
        # Map archetype to specific prompt file
        prompt_files = {
            'bro': 'workout_plan_bro',
            'sergeant': 'workout_plan_sergeant', 
            'intellectual': 'workout_plan_intellectual'
        }
        
        prompt_name = prompt_files.get(archetype, 'workout_plan_bro')
        
        try:
            prompt_template = self.prompt_manager.get_workout_plan_prompt(archetype)
            logger.warning(f"### USING PROMPT FILE ### for archetype: {archetype}")
            return self.prompt_manager.format_prompt(prompt_template, **user_data)
        except (FileNotFoundError, ValueError) as e:
            # Fallback to built-in prompt if file has formatting issues
            logger.warning(f"### USING FALLBACK PROMPT ### Prompt file has formatting issues: {e}")
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
        if hasattr(user, "profile"):
            user.profile.onboarding_completed = True
            user.profile.save(update_fields=["onboarding_completed"])
        else:
            user.completed_onboarding = True  # если поле у самого User
            user.save(update_fields=["completed_onboarding"])
        
        # 2) любая незакрытая сессия
        OnboardingSession.objects.filter(
            user=user, is_completed=False
        ).update(is_completed=True, completed_at=timezone.now())