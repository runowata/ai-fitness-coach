"""
Post-validation and fixing services for AI-generated workout plans
"""
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from apps.core.services.exercise_validation import ExerciseValidationService

logger = logging.getLogger(__name__)


class WorkoutPlanValidator:
    """Post-validator for AI-generated workout plans"""
    
    def __init__(self):
        self.validation_service = ExerciseValidationService()
        self.issues_found = []
        self.fixes_applied = []
    
    def validate_and_fix_plan(self, plan_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Validate and fix a workout plan
        
        Args:
            plan_data: AI-generated plan data
            
        Returns:
            Tuple of (fixed_plan_data, validation_report)
        """
        self.issues_found = []
        self.fixes_applied = []
        
        try:
            # Get allowed exercises
            allowed_slugs = self.validation_service.get_allowed_exercise_slugs()
            logger.info(f"Validating plan against {len(allowed_slugs)} allowed exercises")
            
            # Validate structure
            fixed_plan = self._validate_structure(plan_data)
            
            # Validate and fix exercises
            fixed_plan = self._validate_exercises(fixed_plan, allowed_slugs)
            
            # Generate validation report
            report = {
                'valid': len(self.issues_found) == 0,
                'issues_found': len(self.issues_found),
                'fixes_applied': len(self.fixes_applied),
                'issues': self.issues_found,
                'fixes': self.fixes_applied,
                'allowed_exercises_count': len(allowed_slugs),
                'coverage_ok': len(allowed_slugs) > 10,  # Minimum viable coverage
            }
            
            logger.info(f"Plan validation complete: {report['issues_found']} issues, {report['fixes_applied']} fixes")
            return fixed_plan, report
            
        except Exception as e:
            logger.error(f"Plan validation failed: {e}")
            return plan_data, {
                'valid': False,
                'error': str(e),
                'issues_found': 1,
                'fixes_applied': 0
            }
    
    def _validate_structure(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate basic plan structure"""
        required_fields = ['meta', 'weeks']
        
        for field in required_fields:
            if field not in plan_data:
                self.issues_found.append(f"Missing required field: {field}")
                if field == 'meta':
                    plan_data['meta'] = {'version': 'v2', 'archetype': 'mentor'}
                elif field == 'weeks':
                    plan_data['weeks'] = []
                self.fixes_applied.append(f"Added missing {field}")
        
        # Validate meta structure
        if 'meta' in plan_data:
            meta = plan_data['meta']
            if 'archetype' not in meta:
                meta['archetype'] = 'mentor'
                self.fixes_applied.append("Added default archetype to meta")
            
            if 'version' not in meta:
                meta['version'] = 'v2'
                self.fixes_applied.append("Added version to meta")
        
        return plan_data
    
    def _validate_exercises(self, plan_data: Dict[str, Any], allowed_slugs: set) -> Dict[str, Any]:
        """Validate and fix exercise references in the plan"""
        if 'weeks' not in plan_data:
            return plan_data
        
        for week_idx, week in enumerate(plan_data['weeks']):
            if 'days' not in week:
                continue
                
            for day_idx, day in enumerate(week['days']):
                # Handle both old (blocks) and new (direct exercises) structure
                if 'blocks' in day:
                    # Old structure with blocks
                    for block_idx, block in enumerate(day['blocks']):
                        if 'exercises' not in block:
                            continue
                        
                        # Validate each exercise
                        fixed_exercises = []
                        for exercise in block['exercises']:
                            fixed_exercise = self._validate_single_exercise(
                                exercise, allowed_slugs, week_idx + 1, day_idx + 1
                            )
                            if fixed_exercise:
                                fixed_exercises.append(fixed_exercise)
                        
                        # Update block with fixed exercises
                        block['exercises'] = fixed_exercises
                
                elif 'exercises' in day:
                    # New structure with direct exercises in day
                    fixed_exercises = []
                    for exercise in day['exercises']:
                        fixed_exercise = self._validate_single_exercise(
                            exercise, allowed_slugs, week_idx + 1, day_idx + 1
                        )
                        if fixed_exercise:
                            fixed_exercises.append(fixed_exercise)
                    
                    # Update day with fixed exercises
                    day['exercises'] = fixed_exercises
        
        return plan_data
    
    def _validate_single_exercise(
        self, 
        exercise: Dict[str, Any], 
        allowed_slugs: set, 
        week_num: int, 
        day_num: int
    ) -> Optional[Dict[str, Any]]:
        """
        Validate and fix a single exercise
        
        Returns:
            Fixed exercise dict or None if exercise should be removed
        """
        # Handle both 'slug' and 'exercise_slug' fields
        slug = exercise.get('slug') or exercise.get('exercise_slug')
        if not slug:
            self.issues_found.append(f"Exercise missing slug in week {week_num}, day {day_num}")
            return None
        
        # Ensure exercise_slug field is present for new schema
        if 'exercise_slug' not in exercise:
            exercise['exercise_slug'] = slug
        
        # Check if slug is allowed (has video coverage)
        if slug not in allowed_slugs:
            self.issues_found.append(f"Exercise '{slug}' has no video coverage")
            
            # Try to find alternative
            alternatives = self.validation_service.find_exercise_alternatives(slug)
            if alternatives:
                new_slug = alternatives[0]  # Take best alternative
                exercise['exercise_slug'] = new_slug
                if 'slug' in exercise:
                    exercise['slug'] = new_slug
                self.fixes_applied.append(f"Replaced '{slug}' with '{new_slug}' (week {week_num}, day {day_num})")
                logger.info(f"Substituted {slug} → {new_slug}")
                slug = new_slug  # Update slug for further validation
            else:
                self.issues_found.append(f"No alternatives found for '{slug}' - removing exercise")
                return None  # Remove exercise if no alternatives
        
        # Validate exercise structure
        required_fields = ['sets', 'reps']
        for field in required_fields:
            if field not in exercise:
                if field == 'sets':
                    exercise['sets'] = 3
                elif field == 'reps':
                    exercise['reps'] = '8-12'
                self.fixes_applied.append(f"Added missing {field} to exercise {slug}")
        
        # Ensure sets is integer
        if not isinstance(exercise.get('sets'), int):
            try:
                exercise['sets'] = int(exercise['sets'])
            except (ValueError, TypeError):
                exercise['sets'] = 3
                self.fixes_applied.append(f"Fixed invalid sets value for {slug}")
        
        # Ensure reps is string
        if not isinstance(exercise.get('reps'), str):
            exercise['reps'] = str(exercise['reps'])
            self.fixes_applied.append(f"Fixed reps format for {slug}")
        
        # Fix rest_seconds if invalid
        rest_seconds = exercise.get('rest_seconds')
        if rest_seconds is not None:
            # Ensure it's an integer
            if not isinstance(rest_seconds, int):
                try:
                    rest_seconds = int(rest_seconds)
                except (ValueError, TypeError):
                    rest_seconds = None
            
            # Ensure minimum value
            if rest_seconds is not None and rest_seconds < 10:
                exercise['rest_seconds'] = 30  # Default safe value
                self.fixes_applied.append(f"Fixed rest_seconds for {slug}: {rest_seconds} → 30")
            elif rest_seconds is not None and rest_seconds > 600:
                exercise['rest_seconds'] = 90  # Maximum reasonable value
                self.fixes_applied.append(f"Fixed rest_seconds for {slug}: {rest_seconds} → 90")
            elif rest_seconds is not None:
                exercise['rest_seconds'] = rest_seconds
        
        # Fix duration_seconds if invalid
        duration_seconds = exercise.get('duration_seconds')
        if duration_seconds is not None:
            # Ensure it's an integer
            if not isinstance(duration_seconds, int):
                try:
                    duration_seconds = int(duration_seconds)
                except (ValueError, TypeError):
                    duration_seconds = None
            
            # Ensure minimum value
            if duration_seconds is not None and duration_seconds < 10:
                exercise['duration_seconds'] = 30  # Default safe value
                self.fixes_applied.append(f"Fixed duration_seconds for {slug}: {duration_seconds} → 30")
            elif duration_seconds is not None and duration_seconds > 1800:
                exercise['duration_seconds'] = 300  # Maximum reasonable value (5 min)
                self.fixes_applied.append(f"Fixed duration_seconds for {slug}: {duration_seconds} → 300")
            elif duration_seconds is not None:
                exercise['duration_seconds'] = duration_seconds
        
        return exercise
    
    def dry_run_validation(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform validation without making changes
        
        Returns:
            Validation report only
        """
        original_plan = json.loads(json.dumps(plan_data))  # Deep copy
        _, report = self.validate_and_fix_plan(original_plan)
        return report