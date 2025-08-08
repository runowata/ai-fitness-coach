"""
Exercise validation and coverage services for v2 clean implementation
"""
import logging
from typing import Set, Dict, List, Optional
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Q

logger = logging.getLogger(__name__)


class ExerciseValidationService:
    """Service for validating exercise coverage in workout plans"""
    
    REQUIRED_KINDS = ["instruction", "technique", "mistake"]
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    def get_allowed_exercise_slugs() -> Set[str]:
        """
        Get set of exercise slugs that have complete video coverage
        Uses clean ORM queries instead of raw SQL
        
        Returns:
            Set of exercise slugs that can be safely used in workout plans
        """
        cache_key = 'allowed_exercise_slugs_v2'
        cached_slugs = cache.get(cache_key)
        
        if cached_slugs is not None:
            return cached_slugs
            
        try:
            from apps.workouts.models import VideoClip
            
            # Find exercises that have all 3 required video types
            slugs_with_coverage = (VideoClip.objects
                .filter(
                    r2_file__isnull=False,
                    r2_kind__in=ExerciseValidationService.REQUIRED_KINDS,
                    is_active=True,
                    exercise__is_active=True
                )
                .values('exercise__slug')
                .annotate(
                    kinds_count=Count(
                        'r2_kind', 
                        filter=Q(r2_kind__in=ExerciseValidationService.REQUIRED_KINDS),
                        distinct=True
                    )
                )
                .filter(kinds_count=len(ExerciseValidationService.REQUIRED_KINDS))
                .values_list('exercise__slug', flat=True)
            )
            
            slugs = set(slugs_with_coverage)
                
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
            with connection.cursor() as cursor:
                # Get coverage breakdown using SQLite-compatible syntax
                cursor.execute("""
                    SELECT 
                        e.slug,
                        e.name,
                        COUNT(DISTINCT v.r2_kind) as kinds_covered,
                        GROUP_CONCAT(DISTINCT v.r2_kind) as available_kinds,
                        CASE 
                            WHEN COUNT(DISTINCT v.r2_kind) >= 3 THEN 'complete'
                            WHEN COUNT(DISTINCT v.r2_kind) >= 1 THEN 'partial'
                            ELSE 'none'
                        END as coverage_status
                    FROM exercises e
                    LEFT JOIN video_clips v ON (
                        v.exercise_id = e.id 
                        AND v.r2_file IS NOT NULL 
                        AND v.r2_file != ''
                        AND v.r2_kind IN ('instruction', 'technique', 'mistake')
                        AND v.is_active = TRUE
                    )
                    WHERE e.is_active = TRUE
                    GROUP BY e.slug, e.name
                    ORDER BY kinds_covered DESC, e.name
                """)
                
                exercises = []
                stats = {'complete': 0, 'partial': 0, 'none': 0}
                
                for row in cursor.fetchall():
                    slug, name, kinds_covered, available_kinds, status = row
                    exercises.append({
                        'slug': slug,
                        'name': name,
                        'kinds_covered': kinds_covered or 0,
                        'available_kinds': available_kinds or '',
                        'status': status
                    })
                    stats[status] += 1
                
                return {
                    'total_exercises': len(exercises),
                    'statistics': stats,
                    'coverage_percentage': round(stats['complete'] / len(exercises) * 100, 1) if exercises else 0,
                    'exercises': exercises
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
                        e.muscle_groups && %s  -- Overlapping muscle groups
                        OR e.difficulty = %s   -- Same difficulty
                    )
                    ORDER BY 
                        CASE WHEN e.muscle_groups && %s THEN 1 ELSE 2 END,  -- Prefer muscle group match
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
        logger.info("Invalidated allowed exercise slugs cache")