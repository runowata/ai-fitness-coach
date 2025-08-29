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
        """Get QuerySet of R2Videos that have available video content"""
        from apps.workouts.models import R2Video
        
        # All R2Videos are available by definition (they exist in R2 storage)
        return R2Video.objects.all()
    
    @staticmethod
    def get_allowed_exercise_slugs(archetype: Optional[str] = None, locale: Optional[str] = None) -> Set[str]:
        """
        Get set of exercise slugs that have complete video coverage
        
        Note: Exercise videos are archetype-agnostic (all users see same exercises).
        Archetype is used only for motivational/speech videos, not exercises.
        
        Args:
            archetype: Ignored for exercises (kept for API compatibility)
            locale: Filter by locale (default: all locales)
        
        Returns:
            Set of exercise slugs that can be safely used in workout plans
        """
        # Build cache key (archetype doesn't affect exercise availability)
        cache_key = 'allowed_exercise_slugs_v5_unified'
        if locale:
            cache_key += f'_loc_{locale}'
        
        cached_slugs = cache.get(cache_key)
        if cached_slugs is not None:
            return cached_slugs
            
        try:
            from apps.core.metrics import MetricNames, incr

            # Get all exercise videos regardless of archetype
            # Exercises are universal - archetype affects only motivational videos
            query = ExerciseValidationService.get_clips_with_video().filter(
                r2_kind__in=ExerciseValidationService.REQUIRED_KINDS,
                exercise__is_active=True
            )
            
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
            
            logger.info(f"Found {len(slugs)} exercises with complete video coverage (archetype-agnostic)")
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
            
            # Add required kinds info
            from apps.workouts.constants import REQUIRED_VIDEO_KINDS
            required_kinds = [k.value if hasattr(k, 'value') else str(k) for k in REQUIRED_VIDEO_KINDS]
            
            # Add by_archetype breakdown
            by_archetype = {}
            for archetype in ['mentor', 'peer', 'professional']:
                # Get clips for this archetype only
                archetype_clips = ExerciseValidationService.get_clips_with_video().filter(
                    archetype=archetype,
                    r2_kind__in=ExerciseValidationService.REQUIRED_KINDS
                )
                
                # Count exercises that have ALL required kinds for this archetype
                exercise_coverage = {}
                for clip in archetype_clips:
                    if clip.exercise_id not in exercise_coverage:
                        exercise_coverage[clip.exercise_id] = set()
                    exercise_coverage[clip.exercise_id].add(clip.r2_kind)
                
                # Count complete exercises (have all required kinds)
                required_kinds_set = set(k.value if hasattr(k, 'value') else str(k) for k in REQUIRED_VIDEO_KINDS)
                complete_exercises = sum(1 for kinds in exercise_coverage.values() 
                                       if required_kinds_set.issubset(kinds))
                
                total_exercises = len(exercise_coverage)
                coverage_pct = round(complete_exercises / total_exercises * 100, 1) if total_exercises else 0
                
                by_archetype[archetype] = {
                    'total': total_exercises,
                    'complete': complete_exercises,
                    'coverage_percentage': coverage_pct
                }
                
            return {
                'total_exercises': len(exercises_data),
                'statistics': stats,
                'coverage_percentage': round(stats['complete'] / len(exercises_data) * 100, 1) if exercises_data else 0,
                'required_kinds': required_kinds,
                'by_archetype': by_archetype,
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
                    SELECT ai_tags, level
                    FROM csv_exercises 
                    WHERE id = %s AND is_active = TRUE
                """, [slug])
                
                result = cursor.fetchone()
                if not result:
                    return []
                
                original_muscle_groups, original_difficulty = result
                
                # Ensure muscle_groups is a valid list for PostgreSQL
                if original_muscle_groups is None or not original_muscle_groups:
                    muscle_groups_list = []
                elif isinstance(original_muscle_groups, str):
                    try:
                        import json
                        muscle_groups_list = json.loads(original_muscle_groups)
                    except (json.JSONDecodeError, TypeError):
                        muscle_groups_list = [original_muscle_groups]  # Single string
                elif isinstance(original_muscle_groups, list):
                    muscle_groups_list = original_muscle_groups
                else:
                    muscle_groups_list = []
                
                # Skip JSONb operator if no muscle groups to compare
                if not muscle_groups_list:
                    # Simpler query without muscle group matching
                    cursor.execute("""
                        SELECT e.id
                        FROM csv_exercises e
                        WHERE e.id = ANY(%s)
                        AND e.is_active = TRUE
                        AND e.level = %s
                        ORDER BY e.id
                        LIMIT 5
                    """, [list(allowed_slugs), original_difficulty])
                else:
                    # Full query with muscle group matching
                    cursor.execute("""
                        SELECT e.id
                        FROM csv_exercises e
                        WHERE e.id = ANY(%s)
                        AND e.is_active = TRUE
                        AND (
                            (e.ai_tags IS NOT NULL AND e.ai_tags::jsonb ?| %s)  -- Overlapping AI tags
                            OR e.level = %s   -- Same difficulty
                        )
                        ORDER BY 
                            CASE WHEN (e.ai_tags IS NOT NULL AND e.ai_tags::jsonb ?| %s) THEN 1 ELSE 2 END,  -- Prefer tag match
                            CASE WHEN e.level = %s THEN 1 ELSE 2 END      -- Then level match
                        LIMIT 5
                    """, [
                        list(allowed_slugs), 
                        muscle_groups_list,
                        original_difficulty,
                        muscle_groups_list,
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