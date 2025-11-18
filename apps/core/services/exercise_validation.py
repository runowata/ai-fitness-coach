"""
Exercise validation and coverage services for v2 clean implementation
"""
import logging
from typing import Dict, List, Optional, Set

from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Q

from apps.workouts.constants import REQUIRED_VIDEO_KINDS
from apps.workouts.models import VideoProvider

logger = logging.getLogger(__name__)


class ExerciseValidationService:
    """Service for validating exercise coverage in workout plans"""
    
    REQUIRED_KINDS = REQUIRED_VIDEO_KINDS
    CACHE_TIMEOUT = 300  # 5 minutes

    @staticmethod
    def get_allowed_exercise_slugs(archetype: Optional[str] = None, locale: Optional[str] = None) -> Set[str]:
        """
        Get set of exercise slugs that can be safely used in workout plans

        Note: Videos in R2 are universal (warmup, main, endurance, cooldown types),
        not linked to specific exercises. This method returns all active exercises
        since video availability is determined by exercise type, not individual exercise.

        Args:
            archetype: Ignored (kept for API compatibility)
            locale: Ignored (kept for API compatibility)

        Returns:
            Set of all active exercise IDs from CSVExercise
        """
        # Build cache key
        cache_key = 'allowed_exercise_slugs_v6_all_active'

        cached_slugs = cache.get(cache_key)
        if cached_slugs is not None:
            return cached_slugs

        try:
            from apps.core.metrics import MetricNames, incr
            from apps.workouts.models import CSVExercise

            # Return all exercises - videos are universal by type, not linked to individual exercises
            # Note: CSVExercise has no is_active field (only id, name_ru, description)
            # All exercises in DB are available for use
            slugs = set(
                CSVExercise.objects.all()
                .values_list('id', flat=True)
            )

            # Track metrics
            incr(MetricNames.AI_WHITELIST_COUNT, len(slugs))

            # Cache results
            cache.set(cache_key, slugs, ExerciseValidationService.CACHE_TIMEOUT)

            logger.info(f"Returning {len(slugs)} exercises from database (videos are type-based, not exercise-specific)")
            return slugs

        except Exception as e:
            logger.error(f"Error getting allowed exercise slugs: {e}")
            # Return empty set on error
            return set()
    
    @staticmethod
    def get_coverage_report() -> Dict[str, any]:
        """
        Generate simplified coverage report for all exercises

        Note: In current architecture, videos in R2 are type-based (warmup/main/endurance),
        not linked to individual exercises. This report shows basic exercise counts.

        Returns:
            Dict with coverage statistics and details
        """
        try:
            from apps.workouts.models import CSVExercise, R2Video

            # Count exercises by type
            exercises = list(CSVExercise.objects.all())
            exercises_data = []

            for exercise in exercises:
                # Determine exercise type from ID prefix
                exercise_type = 'unknown'
                if exercise.id.startswith('warmup_'):
                    exercise_type = 'warmup'
                elif exercise.id.startswith('main_'):
                    exercise_type = 'main'
                elif exercise.id.startswith('endurance_'):
                    exercise_type = 'endurance'
                elif exercise.id.startswith('relaxation_'):
                    exercise_type = 'cooldown'

                exercises_data.append({
                    'slug': exercise.id,
                    'name': exercise.name_ru,
                    'type': exercise_type,
                    'status': 'available'  # Simplified: all exercises available
                })

            # Count R2 videos by category
            video_counts = {}
            for category in ['exercises', 'motivation', 'final', 'progress', 'weekly']:
                video_counts[category] = R2Video.objects.filter(category=category).count()

            return {
                'total_exercises': len(exercises_data),
                'exercises': exercises_data,
                'video_counts_by_category': video_counts,
                'note': 'Simplified report: videos are type-based, not exercise-specific'
            }

        except Exception as e:
            logger.error(f"Error generating coverage report: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def find_exercise_alternatives(slug: str, required_equipment: List[str] = None) -> List[str]:
        """
        Find alternative exercises for a given slug

        Simplified version: CSVExercise has only id, name_ru, description fields.
        Returns random alternatives from same exercise type (warmup/main/endurance).

        Args:
            slug: Exercise slug to find alternatives for
            required_equipment: List of available equipment (currently unused)

        Returns:
            List of alternative exercise slugs (up to 5)
        """
        try:
            allowed_slugs = ExerciseValidationService.get_allowed_exercise_slugs()

            # Don't suggest the same exercise
            if slug in allowed_slugs:
                allowed_slugs.remove(slug)

            if not allowed_slugs:
                return []

            # Determine exercise type from slug prefix
            exercise_type = None
            if slug.startswith('warmup_'):
                exercise_type = 'warmup_'
            elif slug.startswith('main_'):
                exercise_type = 'main_'
            elif slug.startswith('endurance_'):
                exercise_type = 'endurance_'
            elif slug.startswith('relaxation_'):
                exercise_type = 'relaxation_'

            # Filter alternatives by same type if possible
            if exercise_type:
                same_type_alternatives = [s for s in allowed_slugs if s.startswith(exercise_type)]
                if same_type_alternatives:
                    import random
                    alternatives = random.sample(
                        same_type_alternatives,
                        min(5, len(same_type_alternatives))
                    )
                    logger.debug(f"Found {len(alternatives)} same-type alternatives for {slug}")
                    return alternatives

            # Fallback: return random alternatives
            import random
            alternatives = random.sample(list(allowed_slugs), min(5, len(allowed_slugs)))
            logger.debug(f"Found {len(alternatives)} random alternatives for {slug}")
            return alternatives

        except Exception as e:
            logger.error(f"Error finding alternatives for {slug}: {e}")
            return []
    
    @staticmethod
    def invalidate_cache():
        """Invalidate the allowed exercises cache"""
        # Clear all cache versions and archetype combinations
        cache_patterns = [
            'allowed_exercise_slugs_v2',
            'allowed_exercise_slugs_v3', 
            'allowed_exercise_slugs_v4',
            'allowed_exercise_slugs_v4:arch_mentor',
            'allowed_exercise_slugs_v4:arch_professional',
            'allowed_exercise_slugs_v4:arch_peer'
        ]
        for pattern in cache_patterns:
            cache.delete(pattern)
        logger.info("Invalidated allowed exercise slugs cache")