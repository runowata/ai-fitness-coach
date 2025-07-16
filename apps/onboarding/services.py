"""Service layer for onboarding business logic"""
from django.utils import timezone
from django.contrib import messages
from .models import OnboardingQuestion, OnboardingSession, UserOnboardingResponse, MotivationalCard
import random
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class OnboardingService:
    """Service for managing onboarding flow"""
    
    @staticmethod
    def get_or_create_session(user):
        """Get or create onboarding session for user"""
        session, created = OnboardingSession.objects.get_or_create(
            user=user,
            is_completed=False,
            defaults={'started_at': timezone.now()}
        )
        return session, created
    
    @staticmethod
    def is_onboarding_complete(user) -> bool:
        """Check if user has completed onboarding - simple boolean field check"""
        if not user.is_authenticated:
            return False
            
        # Simple boolean check - no validation that could cause save() during request
        return getattr(user, "completed_onboarding", False)
    
    @staticmethod
    def validate_and_fix_onboarding_status(user) -> bool:
        """Validate and fix onboarding status - call this only when safe to save"""
        if not user.is_authenticated:
            return False
            
        # Check boolean flag first
        if not getattr(user, "completed_onboarding", False):
            return False
            
        # Validate that user actually has required data
        if not user.archetype or not user.workout_plans.filter(is_active=True).exists():
            # User marked as complete but missing required data - reset
            user.completed_onboarding = False
            user.onboarding_completed_at = None
            user.save(update_fields=['completed_onboarding', 'onboarding_completed_at'])
            return False
            
        return True
    
    @staticmethod
    def get_first_question() -> Optional[OnboardingQuestion]:
        """Get the first active onboarding question"""
        return OnboardingQuestion.objects.filter(is_active=True).first()
    
    @staticmethod
    def get_question_progress(question: OnboardingQuestion) -> Dict:
        """Get progress information for a question"""
        all_questions = OnboardingQuestion.objects.filter(is_active=True).order_by('order')
        current_index = list(all_questions).index(question) + 1
        total_questions = len(all_questions)
        
        return {
            'current_index': current_index,
            'total_questions': total_questions,
            'progress_percent': int((current_index / total_questions) * 100),
            'is_last_question': current_index == total_questions
        }
    
    @staticmethod
    def get_next_question(current_question: OnboardingQuestion) -> Optional[OnboardingQuestion]:
        """Get next question in sequence"""
        return OnboardingQuestion.objects.filter(
            order__gt=current_question.order,
            is_active=True
        ).first()
    
    @staticmethod
    def get_existing_response(user, question: OnboardingQuestion) -> Optional[UserOnboardingResponse]:
        """Get user's existing response to a question"""
        try:
            return UserOnboardingResponse.objects.get(user=user, question=question)
        except UserOnboardingResponse.DoesNotExist:
            return None


class AnswerService:
    """Service for managing user answers"""
    
    @staticmethod
    def save_answer(user, question: OnboardingQuestion, answer_data: Dict) -> UserOnboardingResponse:
        """Save user's answer to a question"""
        from .models import AnswerOption
        
        # Delete existing response
        UserOnboardingResponse.objects.filter(user=user, question=question).delete()
        
        # Create new response
        response = UserOnboardingResponse.objects.create(user=user, question=question)
        
        # Handle different question types
        if question.question_type == 'single_choice':
            option_id = answer_data.get('answer')
            if option_id:
                option = AnswerOption.objects.get(id=option_id, question=question)
                response.answer_options.add(option)
                
        elif question.question_type == 'multiple_choice':
            option_ids = answer_data.get('answers', [])
            for option_id in option_ids:
                option = AnswerOption.objects.get(id=option_id, question=question)
                response.answer_options.add(option)
            
        elif question.question_type == 'number':
            response.answer_number = answer_data.get('answer')
            response.save()
            
        else:  # text
            response.answer_text = answer_data.get('answer', '')
            response.save()
        
        return response


class MotivationalCardService:
    """Service for selecting motivational cards"""
    
    @staticmethod
    def get_motivational_card(question: OnboardingQuestion) -> Optional[MotivationalCard]:
        """Get appropriate motivational card for a question"""
        # Map questions to categories
        category = 'general'  # Default
        
        if question.ai_field_name == 'primary_goal':
            category = 'goal'
        elif question.ai_field_name == 'experience_level':
            category = 'experience'
        
        # Get available trainer archetypes for cycling
        archetypes = ['bro', 'sergeant', 'intellectual']
        
        # Cycle through archetypes based on question order
        selected_archetype = archetypes[(question.order - 1) % 3]
        
        # Try to get card for selected archetype and category
        cards = MotivationalCard.objects.filter(
            category=category,
            image_url__contains=f'{selected_archetype}-avatar'
        )
        
        if not cards.exists():
            # Fallback to general cards
            cards = MotivationalCard.objects.filter(
                category='general',
                image_url__contains=f'{selected_archetype}-avatar'
            )
        
        if not cards.exists():
            # Last fallback - any general card
            cards = MotivationalCard.objects.filter(category='general')
        
        return random.choice(cards) if cards.exists() else None


class OnboardingDataService:
    """Service for processing onboarding data"""
    
    @staticmethod
    def collect_user_data(user) -> Dict:
        """Collect all user data from onboarding responses"""
        responses = UserOnboardingResponse.objects.filter(user=user)
        
        user_data = {
            'archetype': user.archetype,
            'age': 25,  # Default values
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
        
        # Set defaults for missing fields
        if 'days_per_week' not in user_data:
            user_data['days_per_week'] = 4
        if 'equipment' not in user_data:
            user_data['equipment'] = ['bodyweight']
        
        return user_data
    
    @staticmethod
    def mark_onboarding_complete(user) -> None:
        """Mark onboarding as completed for user"""
        # Ensure user has required data before marking as complete
        if not user.archetype:
            from apps.users.models import User
            user.archetype = User.DEFAULT_ARCHETYPE
        
        # Create default workout plan if none exists
        if not user.workout_plans.filter(is_active=True).exists():
            from apps.users.services import UserDashboardService
            UserDashboardService.create_default_workout_plan(user)
        
        user.onboarding_completed_at = timezone.now()
        user.completed_onboarding = True
        user.save(update_fields=['onboarding_completed_at', 'completed_onboarding', 'archetype'])
        
        # Update session if exists
        session = OnboardingSession.objects.filter(
            user=user,
            is_completed=False
        ).first()
        
        if session:
            session.is_completed = True
            session.completed_at = timezone.now()
            session.save()

class ArchetypeService:
    """Service for managing trainer archetypes"""
    
    @staticmethod
    def get_archetype_data() -> List[Dict]:
        """Get archetype data for display"""
        return [
            {
                'key': 'bro',
                'name': 'Бро',
                'description': 'Дружелюбный и мотивирующий. Всегда поддержит и подскажет. Говорит простым языком.',
                'image': '/static/images/avatars/bro_avatar_1.jpg',
                'style': 'Casual и расслабленный'
            },
            {
                'key': 'sergeant',
                'name': 'Сержант',
                'description': 'Строгий и требовательный. Поможет вам превзойти себя. Четкие команды и дисциплина.',
                'image': '/static/images/avatars/sergeant_avatar_1.jpg',
                'style': 'Военный стиль'
            },
            {
                'key': 'intellectual',
                'name': 'Интеллектуал',
                'description': 'Научный подход к тренировкам. Детальные объяснения и обоснования.',
                'image': '/static/images/avatars/intellectual_avatar_1.jpg',
                'style': 'Научный подход'
            }
        ]
    
    @staticmethod
    def save_archetype(user, archetype: str) -> bool:
        """Save archetype for user"""
        if archetype in ['bro', 'sergeant', 'intellectual']:
            user.archetype = archetype
            user.save()
            return True
        return False