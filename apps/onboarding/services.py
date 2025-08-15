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
        Collect comprehensive user data from onboarding for AI processing
        
        Args:
            user: User instance with profile and onboarding data
            
        Returns:
            Dict containing structured user data for AI prompts
        """
        try:
            profile = user.profile
            
            # Basic profile data
            user_data = {
                'age': getattr(profile, 'age', None),
                'height': getattr(profile, 'height', None),
                'weight': getattr(profile, 'weight', None),
                'biological_sex': getattr(profile, 'biological_sex', 'male'),
                'fitness_level': getattr(profile, 'fitness_level', 'beginner'),
                'primary_goal': getattr(profile, 'primary_goal', 'general_fitness'),
                'archetype': getattr(profile, 'archetype', 'mentor'),
                
                # Onboarding specifics
                'injuries': getattr(profile, 'injuries', 'none'),
                'medical_conditions': getattr(profile, 'medical_conditions', 'none'),
                'equipment_list': OnboardingDataProcessor._format_equipment(profile),
                'workout_frequency': getattr(profile, 'workout_frequency', 3),
                'workout_duration': getattr(profile, 'workout_duration', 45),
                'duration_weeks': getattr(profile, 'duration_weeks', 8),
                
                # Advanced preferences
                'preferred_workout_time': getattr(profile, 'preferred_workout_time', 'morning'),
                'training_experience': getattr(profile, 'training_experience', 'beginner'),
                'motivation_level': getattr(profile, 'motivation_level', 'medium'),
            }
            
            # Add onboarding payload if available
            onboarding_data = OnboardingDataProcessor._extract_onboarding_data(profile)
            if onboarding_data:
                user_data['onboarding_payload_json'] = json.dumps(onboarding_data)
            else:
                user_data['onboarding_payload_json'] = '{}'
            
            # Validate required fields
            OnboardingDataProcessor._validate_user_data(user_data)
            
            logger.info(f"Collected user data for user {user.id}: {list(user_data.keys())}")
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
            'primary_goal': 'general_fitness',
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
            'duration_weeks': 8,
            'preferred_workout_time': 'morning',
            'training_experience': 'beginner',
            'motivation_level': 'medium',
            'onboarding_payload_json': '{}'
        }