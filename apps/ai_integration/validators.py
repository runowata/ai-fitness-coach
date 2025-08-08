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
                if 'blocks' not in day:
                    continue
                    
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
        if 'slug' not in exercise:
            self.issues_found.append(f"Exercise missing slug in week {week_num}, day {day_num}")
            return None
        
        slug = exercise['slug']
        
        # Check if slug is allowed (has video coverage)
        if slug not in allowed_slugs:
            self.issues_found.append(f"Exercise '{slug}' has no video coverage")
            
            # Try to find alternative
            alternatives = self.validation_service.find_exercise_alternatives(slug)
            if alternatives:
                new_slug = alternatives[0]  # Take best alternative
                exercise['slug'] = new_slug
                self.fixes_applied.append(f"Replaced '{slug}' with '{new_slug}' (week {week_num}, day {day_num})")
                logger.info(f"Substituted {slug} → {new_slug}")
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