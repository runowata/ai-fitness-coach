"""
Exercise catalog service for fast lookups and similarity matching
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from django.core.cache import cache

from .constants import EXERCISE_FALLBACK_PRIORITY
from .models import CSVExercise

logger = logging.getLogger(__name__)


@dataclass
class ExerciseAttributes:
    """Exercise attributes for similarity matching"""
    slug: str
    name: str
    muscle_group: str
    equipment: str
    difficulty: str
    is_compound: bool = False
    is_cardio: bool = False
    
    def similarity_score(self, other: 'ExerciseAttributes', priority: Dict[str, int]) -> int:
        """
        Calculate similarity score based on priority weights
        Lower score = more similar
        """
        score = 0
        
        # Apply weights based on priority
        if self.muscle_group != other.muscle_group:
            score += priority.get('muscle_group', 1) * 100
            
        if self.equipment != other.equipment:
            score += priority.get('equipment', 2) * 50
            
        if self.difficulty != other.difficulty:
            score += priority.get('difficulty', 3) * 25
            
        # Bonus points for matching compound/cardio status
        if self.is_compound != other.is_compound:
            score += 10
            
        if self.is_cardio != other.is_cardio:
            score += 10
            
        return score


class ExerciseCatalog:
    """
    Fast exercise catalog for lookups and substitutions
    Uses database as source of truth, with smart caching
    """
    
    CACHE_TIMEOUT = 900  # 15 minutes
    CACHE_KEY_PREFIX = 'exercise_catalog'
    
    def __init__(self):
        self._catalog: Optional[Dict[str, ExerciseAttributes]] = None
        self._by_muscle_group: Optional[Dict[str, List[str]]] = None
        self._by_equipment: Optional[Dict[str, List[str]]] = None
        self._by_difficulty: Optional[Dict[str, List[str]]] = None
    
    def _load_catalog(self) -> Dict[str, ExerciseAttributes]:
        """Load exercise catalog from database with caching"""
        cache_key = f'{self.CACHE_KEY_PREFIX}:full_catalog'
        catalog = cache.get(cache_key)
        
        if catalog is not None:
            logger.debug("Loaded exercise catalog from cache")
            return catalog
        
        # Build catalog from database
        catalog = {}
        # Use actual CSVExercise fields that exist in the model and CSV
        exercises = CSVExercise.objects.filter(is_active=True).values(
            'id', 'name_ru', 'muscle_group', 'exercise_type', 'level', 'ai_tags'
        )
        
        for ex in exercises:
            # Map level to difficulty for backward compatibility
            raw_level = (ex.get('level') or '').strip().lower()
            difficulty = {
                'начальный': 'beginner',
                'средний': 'intermediate', 
                'продвинутый': 'advanced',
                'beginner': 'beginner',
                'intermediate': 'intermediate',
                'advanced': 'advanced'
            }.get(raw_level, raw_level or 'beginner')
            
            # Derive missing fields from available data
            ai_tags = ex.get('ai_tags') or []
            exercise_type = (ex.get('exercise_type') or '').strip().lower()
            
            # Safe defaults for fields that don't exist in CSVExercise
            equipment = 'none'  # No equipment field in CSV/model
            is_compound = 'compound' in str(ai_tags).lower()
            is_cardio = exercise_type == 'cardio'
            
            catalog[ex['id']] = ExerciseAttributes(
                slug=ex['id'],  # Use id as slug
                name=ex['name_ru'],  # Use Russian name
                muscle_group=(ex['muscle_group'] or 'general').strip().lower(),
                equipment=equipment,
                difficulty=difficulty,
                is_compound=is_compound,
                is_cardio=is_cardio
            )
        
        # Cache the catalog
        cache.set(cache_key, catalog, self.CACHE_TIMEOUT)
        logger.info(f"Loaded {len(catalog)} exercises into catalog")
        
        return catalog
    
    def _build_indices(self):
        """Build indices for fast lookups by attributes"""
        if self._catalog is None:
            self._catalog = self._load_catalog()
        
        self._by_muscle_group = {}
        self._by_equipment = {}
        self._by_difficulty = {}
        
        for slug, attrs in self._catalog.items():
            # Index by muscle group
            if attrs.muscle_group not in self._by_muscle_group:
                self._by_muscle_group[attrs.muscle_group] = []
            self._by_muscle_group[attrs.muscle_group].append(slug)
            
            # Index by equipment
            if attrs.equipment not in self._by_equipment:
                self._by_equipment[attrs.equipment] = []
            self._by_equipment[attrs.equipment].append(slug)
            
            # Index by difficulty
            if attrs.difficulty not in self._by_difficulty:
                self._by_difficulty[attrs.difficulty] = []
            self._by_difficulty[attrs.difficulty].append(slug)
    
    def get_attributes(self, slug: str) -> Optional[ExerciseAttributes]:
        """Get attributes for a specific exercise"""
        if self._catalog is None:
            self._catalog = self._load_catalog()
        
        return self._catalog.get(slug)
    
    def find_similar(
        self, 
        source_slug: str,
        allowed: Set[str],
        priority: Optional[Dict[str, int]] = None,
        max_results: int = 5
    ) -> List[str]:
        """
        Find similar exercises from allowed set
        
        Args:
            source_slug: Exercise to find substitutes for
            allowed: Set of allowed exercise slugs
            priority: Priority weights for attributes (default: EXERCISE_FALLBACK_PRIORITY)
            max_results: Maximum number of results to return
            
        Returns:
            List of similar exercise slugs, sorted by similarity
        """
        if priority is None:
            priority = EXERCISE_FALLBACK_PRIORITY
        
        if self._catalog is None:
            self._catalog = self._load_catalog()
        
        source = self.get_attributes(source_slug)
        if not source:
            logger.warning(f"Source exercise {source_slug} not found in catalog")
            return []
        
        # Calculate similarity scores for all allowed exercises
        candidates = []
        for slug in allowed:
            if slug == source_slug:
                continue
                
            target = self.get_attributes(slug)
            if not target:
                continue
            
            score = source.similarity_score(target, priority)
            candidates.append((slug, score))
        
        # Sort by score (lower is better) and return top results
        candidates.sort(key=lambda x: x[1])
        
        results = [slug for slug, _ in candidates[:max_results]]
        
        if results:
            logger.debug(f"Found {len(results)} similar exercises for {source_slug}: {results[:3]}")
        else:
            logger.warning(f"No similar exercises found for {source_slug} in allowed set")
        
        return results
    
    def get_by_muscle_group(self, muscle_group: str, allowed: Optional[Set[str]] = None) -> List[str]:
        """Get exercises by muscle group, optionally filtered by allowed set"""
        if self._by_muscle_group is None:
            self._build_indices()
        
        exercises = self._by_muscle_group.get(muscle_group, [])
        
        if allowed:
            exercises = [ex for ex in exercises if ex in allowed]
        
        return exercises
    
    def get_by_equipment(self, equipment: str, allowed: Optional[Set[str]] = None) -> List[str]:
        """Get exercises by equipment, optionally filtered by allowed set"""
        if self._by_equipment is None:
            self._build_indices()
        
        exercises = self._by_equipment.get(equipment, [])
        
        if allowed:
            exercises = [ex for ex in exercises if ex in allowed]
        
        return exercises
    
    def get_by_difficulty(self, difficulty: str, allowed: Optional[Set[str]] = None) -> List[str]:
        """Get exercises by difficulty, optionally filtered by allowed set"""
        if self._by_difficulty is None:
            self._build_indices()
        
        exercises = self._by_difficulty.get(difficulty, [])
        
        if allowed:
            exercises = [ex for ex in exercises if ex in allowed]
        
        return exercises
    
    def invalidate_cache(self):
        """Clear catalog cache (call on exercise updates)"""
        cache_key = f'{self.CACHE_KEY_PREFIX}:full_catalog'
        cache.delete(cache_key)
        
        # Reset internal state
        self._catalog = None
        self._by_muscle_group = None
        self._by_equipment = None
        self._by_difficulty = None
        
        logger.info("Exercise catalog cache invalidated")
    
    def get_stats(self) -> Dict[str, any]:
        """Get catalog statistics"""
        if self._catalog is None:
            self._catalog = self._load_catalog()
        
        if self._by_muscle_group is None:
            self._build_indices()
        
        return {
            'total_exercises': len(self._catalog),
            'muscle_groups': len(self._by_muscle_group),
            'equipment_types': len(self._by_equipment),
            'difficulty_levels': len(self._by_difficulty),
            'muscle_group_distribution': {
                mg: len(exercises) 
                for mg, exercises in self._by_muscle_group.items()
            }
        }


# Global catalog instance
_catalog = ExerciseCatalog()


def get_catalog() -> ExerciseCatalog:
    """Get global catalog instance"""
    return _catalog