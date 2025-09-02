"""
Dynamic exercise whitelist generator for AI prompts
Ensures AI only returns exercises that exist in our catalog
"""
import logging
from typing import List, Dict, Set
from django.core.cache import cache

from apps.workouts.models import CSVExercise, VideoClip
from apps.core.utils.slug import normalize_exercise_slug, normalize_slug_with_aliases

logger = logging.getLogger(__name__)


def get_available_exercise_slugs() -> List[str]:
    """
    Get list of all available exercise slugs that have video coverage
    Cached for performance
    """
    cache_key = 'available_exercise_slugs_v2'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    # Get exercises with at least one video
    exercises_with_videos = CSVExercise.objects.filter(
        is_active=True,
        video_clips__isnull=False
    ).distinct().values_list('id', flat=True)
    
    # Normalize slugs
    slugs = []
    for exercise_id in exercises_with_videos:
        normalized = normalize_exercise_slug(exercise_id)
        slugs.append(normalized)
    
    # Remove duplicates and sort
    slugs = sorted(list(set(slugs)))
    
    # Cache for 1 hour
    cache.set(cache_key, slugs, 3600)
    
    logger.info(f"Generated whitelist with {len(slugs)} exercise slugs")
    return slugs


def get_exercise_catalog_for_prompt() -> str:
    """
    Generate exercise catalog text for AI prompt
    Returns formatted list of exercises with descriptions
    """
    exercises = CSVExercise.objects.filter(
        is_active=True,
        video_clips__isnull=False
    ).distinct().values('id', 'name_ru', 'muscle_group', 'level')
    
    catalog_lines = ["Available exercises (use exact slugs):"]
    
    for ex in exercises:
        slug = normalize_exercise_slug(ex['id'])
        name = ex['name_ru']
        muscle = ex.get('muscle_group', 'general')
        level = ex.get('level', 'all')
        
        catalog_lines.append(
            f"- {slug}: {name} ({muscle}, {level})"
        )
    
    return "\n".join(catalog_lines)


def validate_exercise_slugs(plan_data: Dict) -> Dict[str, List[str]]:
    """
    Validate all exercise slugs in a workout plan
    Returns dict with 'valid', 'invalid', and 'normalized' lists
    """
    available_slugs = set(get_available_exercise_slugs())
    
    result = {
        'valid': [],
        'invalid': [],
        'normalized': []
    }
    
    # Extract all exercise slugs from plan
    slugs_in_plan = set()
    
    # Handle both old format (weeks) and new format (cycles)
    if 'weeks' in plan_data:
        for week in plan_data.get('weeks', []):
            for day in week.get('days', []):
                # Old format: exercises directly on day
                for exercise in day.get('exercises', []):
                    if 'exercise_slug' in exercise:
                        slugs_in_plan.add(exercise['exercise_slug'])
                
                # New format: exercises in blocks
                for block in day.get('blocks', []):
                    for exercise in block.get('exercises', []):
                        if 'exercise_slug' in exercise:
                            slugs_in_plan.add(exercise['exercise_slug'])
    
    # Validate each slug
    for slug in slugs_in_plan:
        normalized = normalize_exercise_slug(slug)
        
        if normalized in available_slugs:
            result['valid'].append(slug)
            if slug != normalized:
                result['normalized'].append(f"{slug} → {normalized}")
        else:
            result['invalid'].append(slug)
    
    return result


def fix_exercise_slugs_in_plan(plan_data: Dict) -> Dict:
    """
    Normalize all exercise slugs in a workout plan
    Returns modified plan with normalized slugs and alias mapping
    """
    import copy
    fixed_plan = copy.deepcopy(plan_data)
    
    def normalize_exercise(exercise: Dict) -> Dict:
        if 'exercise_slug' in exercise:
            original_slug = exercise['exercise_slug']
            normalized_slug = normalize_slug_with_aliases(original_slug)
            exercise['exercise_slug'] = normalized_slug
            if normalized_slug != original_slug:
                logger.info(f"Normalized exercise slug: {original_slug} → {normalized_slug}")
        return exercise
    
    # Fix in both formats
    if 'weeks' in fixed_plan:
        for week in fixed_plan.get('weeks', []):
            for day in week.get('days', []):
                # Fix old format
                if 'exercises' in day:
                    day['exercises'] = [
                        normalize_exercise(ex) for ex in day['exercises']
                    ]
                
                # Fix new format
                if 'blocks' in day:
                    for block in day['blocks']:
                        if 'exercises' in block:
                            block['exercises'] = [
                                normalize_exercise(ex) for ex in block['exercises']
                            ]
    
    return fixed_plan