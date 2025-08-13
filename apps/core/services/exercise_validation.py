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
    def get_clips_with_video():
        """Get QuerySet of VideoClips that have available video content"""
        from apps.workouts.models import VideoClip
        
        return VideoClip.objects.filter(
            is_active=True
        ).filter(
            Q(provider=VideoProvider.R2, r2_file__isnull=False) |
            Q(provider=VideoProvider.STREAM, stream_uid__isnull=False) |
            Q(provider=VideoProvider.STREAM, playback_id__isnull=False)
        )
    
    @staticmethod
    def get_allowed_exercise_slugs(archetype: Optional[str] = None, locale: Optional[str] = None) -> Set[str]:
        """
        Get set of exercise slugs that have complete video coverage
        Uses provider-agnostic video availability check
        
        Args:
            archetype: Filter by specific archetype (peer/professional/mentor)
            locale: Filter by locale (default: all locales)
        
        Returns:
            Set of exercise slugs that can be safely used in workout plans
        """
        # Build cache key with parameters
        cache_parts = ['allowed_exercise_slugs_v4']
        if archetype:
            cache_parts.append(f'arch_{archetype}')
        if locale:
            cache_parts.append(f'loc_{locale}')
        
        cache_key = ':'.join(cache_parts)
        cached_slugs = cache.get(cache_key)
        
        if cached_slugs is not None:
            return cached_slugs
            
        try:
            from apps.core.metrics import MetricNames, incr

            # Build query with optional filters
            query = ExerciseValidationService.get_clips_with_video().filter(
                r2_kind__in=ExerciseValidationService.REQUIRED_KINDS,
                exercise__is_active=True
            )
            
            # Apply archetype filter if specified
            if archetype:
                query = query.filter(r2_archetype=archetype)
            
            # Apply locale filter if specified (future: when locale field exists)
            # if locale:
            #     query = query.filter(locale=locale)
            
            # Find exercises that have all required video types with available content
            slugs_with_coverage = (query
                .values('exercise__id')
                .annotate(
                    kinds_count=Count(
                        'r2_kind', 
                        filter=Q(r2_kind__in=ExerciseValidationService.REQUIRED_KINDS),
                        distinct=True
                    )
                )
                .filter(kinds_count=len(ExerciseValidationService.REQUIRED_KINDS))
                .values_list('exercise__id', flat=True)
            )
            
            slugs = set(slugs_with_coverage)
            
            # Track metrics
            incr(MetricNames.AI_WHITELIST_COUNT, len(slugs))
                
            # Cache results
            cache.set(cache_key, slugs, ExerciseValidationService.CACHE_TIMEOUT)
            
            logger.info(f"Found {len(slugs)} exercises with complete video coverage")
            return slugs
            
        except Exception as e:
            logger.error(f"Error getting allowed exercise slugs: {e}")
            # Return empty set on error - better safe than sorry
            return set()
    
    @staticmethod
    def get_coverage_report() -> Dict[str, any]:
        """
        Generate detailed coverage report for all exercises
        
        Returns:
            Dict with coverage statistics and details
        """
        try:
            from apps.workouts.models import CSVExercise

            # Use Django ORM instead of raw SQL for better database compatibility
            exercises_data = []
            stats = {'complete': 0, 'partial': 0, 'none': 0}
            
            for exercise in CSVExercise.objects.filter(is_active=True):
                # Get available video kinds for this exercise using provider-aware logic
                available_clips = ExerciseValidationService.get_clips_with_video().filter(
                    exercise=exercise,
                    r2_kind__in=ExerciseValidationService.REQUIRED_KINDS
                )
                
                kinds_covered = available_clips.values_list('r2_kind', flat=True).distinct().count()
                available_kinds = list(available_clips.values_list('r2_kind', flat=True).distinct())
                
                if kinds_covered >= len(ExerciseValidationService.REQUIRED_KINDS):
                    status = 'complete'
                elif kinds_covered >= 1:
                    status = 'partial'
                else:
                    status = 'none'
                
                exercises_data.append({
                    'slug': exercise.id,
                    'name': exercise.name_ru,
                    'kinds_covered': kinds_covered,
                    'available_kinds': ','.join(available_kinds),
                    'status': status
                })
                stats[status] += 1
                
            # Sort exercises by coverage
            exercises_data.sort(key=lambda x: (-x['kinds_covered'], x['name']))
                
            return {
                'total_exercises': len(exercises_data),
                'statistics': stats,
                'coverage_percentage': round(stats['complete'] / len(exercises_data) * 100, 1) if exercises_data else 0,
                'exercises': exercises_data
            }
                
        except Exception as e:
            logger.error(f"Error generating coverage report: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def find_exercise_alternatives(slug: str, required_equipment: List[str] = None) -> List[str]:
        """
        Find alternative exercises for a given slug based on muscle groups and equipment
        
        Args:
            slug: Exercise slug to find alternatives for
            required_equipment: List of available equipment
            
        Returns:
            List of alternative exercise slugs with complete coverage
        """
        try:
            allowed_slugs = ExerciseValidationService.get_allowed_exercise_slugs()
            
            # Don't suggest the same exercise
            if slug in allowed_slugs:
                allowed_slugs.remove(slug)
            
            # Get exercise details for filtering
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT muscle_groups, equipment_needed, difficulty
                    FROM exercises 
                    WHERE slug = %s AND is_active = TRUE
                """, [slug])
                
                result = cursor.fetchone()
                if not result:
                    return []
                
                original_muscle_groups, original_equipment, original_difficulty = result
                
                # Find similar exercises
                cursor.execute("""
                    SELECT e.slug
                    FROM exercises e
                    WHERE e.slug = ANY(%s)
                    AND e.is_active = TRUE
                    AND (
                        (e.muscle_groups IS NOT NULL AND e.muscle_groups::jsonb ?| %s)  -- Overlapping muscle groups
                        OR e.difficulty = %s   -- Same difficulty
                    )
                    ORDER BY 
                        CASE WHEN (e.muscle_groups IS NOT NULL AND e.muscle_groups::jsonb ?| %s) THEN 1 ELSE 2 END,  -- Prefer muscle group match
                        CASE WHEN e.difficulty = %s THEN 1 ELSE 2 END      -- Then difficulty match
                    LIMIT 5
                """, [
                    list(allowed_slugs), 
                    original_muscle_groups,
                    original_difficulty,
                    original_muscle_groups,
                    original_difficulty
                ])
                
                alternatives = [row[0] for row in cursor.fetchall()]
                
                logger.debug(f"Found {len(alternatives)} alternatives for {slug}")
                return alternatives
                
        except Exception as e:
            logger.error(f"Error finding alternatives for {slug}: {e}")
            return []
    
    @staticmethod
    def invalidate_cache():
        """Invalidate the allowed exercises cache"""
        cache.delete('allowed_exercise_slugs_v2')
        cache.delete('allowed_exercise_slugs_v3')
        logger.info("Invalidated allowed exercise slugs cache")