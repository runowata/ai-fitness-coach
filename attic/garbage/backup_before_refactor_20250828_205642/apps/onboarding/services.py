"""
Onboarding data processing services for AI workout plan generation
"""
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OnboardingDataProcessor:
    """Service for processing onboarding data into AI-ready format"""
    
    @staticmethod
    def collect_user_data(user) -> Dict[str, Any]:
        """
        Collect REAL user data from onboarding responses and profile
        
        Args:
            user: User instance with profile and onboarding data
            
        Returns:
            Dict containing structured user data for AI prompts
        """
        try:
            from apps.onboarding.models import UserOnboardingResponse
            
            user_data = {}
            
            # Step 1: Collect actual onboarding responses via ai_field_name
            responses = UserOnboardingResponse.objects.filter(
                user=user
            ).select_related('question')
            
            for response in responses:
                if response.question.ai_field_name:
                    key = response.question.ai_field_name
                    value = response.get_answer_value()
                    user_data[key] = value
            
            # Step 2: Add real UserProfile fields (no fake fields!)
            profile = user.profile
            
            # Basic physical data
            user_data.update({
                'age': profile.age,
                'height': profile.height,
                'weight': profile.weight,
                'archetype': profile.archetype,
            })
            
            # Health data - using REAL fields from UserProfile
            if profile.health_conditions:
                user_data['health_conditions'] = profile.health_conditions
            if profile.chronic_pain_areas:
                user_data['chronic_pain_areas'] = profile.chronic_pain_areas
            if profile.injuries_surgeries:
                user_data['injuries_surgeries'] = profile.injuries_surgeries
            if profile.exercise_limitations:
                user_data['exercise_limitations'] = profile.exercise_limitations
            
            # Lifestyle data
            user_data.update({
                'work_activity_level': profile.work_activity_level,
                'sleep_hours': profile.sleep_hours,
                'sleep_quality': profile.sleep_quality,
                'stress_level': profile.stress_level,
                'alcohol_consumption': profile.alcohol_consumption,
                'is_smoker': profile.is_smoker,
            })
            
            # Sexual health preferences (important for this app's context)
            if profile.sexual_health_goals:
                user_data['sexual_health_goals'] = profile.sexual_health_goals
            user_data.update({
                'sexual_stamina_rating': profile.sexual_stamina_rating,
                'flexibility_importance': profile.flexibility_importance,
                'kegel_exercises_interest': profile.kegel_exercises_interest,
                'intimacy_confidence': profile.intimacy_confidence,
            })
            
            # Goals and limitations
            if profile.goals:
                user_data['goals'] = profile.goals
            if profile.limitations:
                user_data['limitations'] = profile.limitations
            
            # Calculate BMI if height/weight available
            if profile.height and profile.weight:
                height_m = profile.height / 100.0
                bmi = profile.weight / (height_m * height_m)
                user_data['bmi'] = round(bmi, 1)
            
            # Validate and apply minimal defaults only where critical
            OnboardingDataProcessor._validate_user_data(user_data)
            
            logger.info(f"Collected REAL user data for user {user.id}: {list(user_data.keys())}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error collecting user data for user {user.id}: {e}")
            # Return minimal fallback data
            return OnboardingDataProcessor._get_fallback_data(user)
    
    @staticmethod
    def _format_equipment(profile) -> str:
        """Format equipment list into readable string"""
        try:
            equipment = getattr(profile, 'available_equipment', None)
            if isinstance(equipment, list):
                return ', '.join(equipment)
            elif isinstance(equipment, str):
                return equipment
            else:
                return 'dumbbells, bodyweight'
        except:
            return 'dumbbells, bodyweight'
    
    @staticmethod
    def _extract_onboarding_data(profile) -> Optional[Dict[str, Any]]:
        """Extract structured onboarding data from profile"""
        try:
            # Try to get onboarding responses
            onboarding_data = {}
            
            # Add any stored questionnaire responses
            if hasattr(profile, 'questionnaire_responses'):
                onboarding_data['questionnaire'] = profile.questionnaire_responses
            
            # Add motivational preferences
            if hasattr(profile, 'motivational_preferences'):
                onboarding_data['motivation'] = profile.motivational_preferences
                
            # Add workout preferences
            if hasattr(profile, 'workout_preferences'):
                onboarding_data['preferences'] = profile.workout_preferences
            
            return onboarding_data if onboarding_data else None
            
        except Exception as e:
            logger.warning(f"Could not extract onboarding data: {e}")
            return None
    
    @staticmethod
    def _validate_user_data(user_data: Dict[str, Any]) -> None:
        """Validate that essential fields are present and apply defaults"""
        required_fields = {
            'age': 25,
            'height': 175, 
            'weight': 70,
            'archetype': 'mentor'
        }
        
        missing_before_defaults = []
        applied_defaults = []
        
        # First pass: identify truly missing fields
        for field, default_value in required_fields.items():
            current_value = user_data.get(field)
            if not current_value or (isinstance(current_value, (int, float)) and current_value <= 0):
                missing_before_defaults.append(field)
                user_data[field] = default_value
                applied_defaults.append(f"{field}={default_value}")
        
        # Log meaningful information
        if missing_before_defaults:
            logger.warning(f"Applied defaults for missing fields: {applied_defaults}")
        
        # Validate after defaults applied
        missing_after_defaults = []
        for field in required_fields.keys():
            if not user_data.get(field):
                missing_after_defaults.append(field)
        
        if missing_after_defaults:
            logger.error(f"Critical: Fields still missing after defaults: {missing_after_defaults}")
        else:
            logger.info(f"✅ All required fields validated. Defaults applied: {len(applied_defaults)}")
    
    @staticmethod
    def _get_fallback_data(user) -> Dict[str, Any]:
        """Provide fallback data when user data collection fails"""
        return {
            'age': 25,
            'height': 175,
            'weight': 70,
            'biological_sex': 'male',
            'fitness_level': 'beginner',
            'primary_goal': 'general_fitness',
            'archetype': 'mentor',
            'injuries': 'none',
            'medical_conditions': 'none',
            'equipment_list': 'dumbbells, bodyweight',
            'workout_frequency': 3,
            'workout_duration': 45,
            'duration_weeks': 3,
            'preferred_workout_time': 'morning',
            'training_experience': 'beginner',
            'motivation_level': 'medium',
            'onboarding_payload_json': '{}'
        }