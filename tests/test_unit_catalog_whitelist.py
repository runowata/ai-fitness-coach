"""
Unit tests for exercise catalog and whitelist functionality
"""

from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.test import TestCase

from apps.core.services.exercise_validation import ExerciseValidationService
from apps.workouts.catalog import ExerciseCatalog, get_catalog
from apps.workouts.constants import EXERCISE_FALLBACK_PRIORITY
from tests.factories import CSVExerciseFactory, VideoClipFactory


@pytest.mark.unit
class TestExerciseCatalog(TestCase):
    """Test exercise catalog similarity and caching"""
    
    def setUp(self):
        self.catalog = ExerciseCatalog()
        self.catalog.invalidate_cache()
        
        # Create test exercises with different attributes
        self.exercises = [
            CSVExerciseFactory(
                slug='push-ups',
                muscle_group='chest',
                equipment='none',
                difficulty='beginner'
            ),
            CSVExerciseFactory(
                slug='bench-press',
                muscle_group='chest', 
                equipment='barbell',
                difficulty='intermediate'
            ),
            CSVExerciseFactory(
                slug='squats',
                muscle_group='legs',
                equipment='none',
                difficulty='beginner'
            ),
            CSVExerciseFactory(
                slug='dumbbell-press',
                muscle_group='chest',
                equipment='dumbbell',
                difficulty='beginner'
            ),
        ]
    
    def test_find_similar_respects_priority(self):
        """Test similarity search respects EXERCISE_FALLBACK_PRIORITY"""
        allowed = {'bench-press', 'squats', 'dumbbell-press'}
        
        # Find similar to push-ups (chest, none, beginner)
        similar = self.catalog.find_similar('push-ups', allowed, EXERCISE_FALLBACK_PRIORITY)
        
        # Should prefer same muscle group (chest) over same equipment (none)
        # dumbbell-press: chest + beginner (2 matches) vs squats: none + beginner (2 matches)
        # But muscle_group has higher priority (weight 1 vs 2)
        first_result = similar[0] if similar else None
        self.assertIn(first_result, ['bench-press', 'dumbbell-press'])  # Both are chest
    
    def test_catalog_caching_behavior(self):
        """Test catalog caching and invalidation"""
        # First call should hit database
        with self.assertNumQueries(1):
            attrs1 = self.catalog.get_attributes('push-ups')
        
        # Second call should use cache
        with self.assertNumQueries(0):
            attrs2 = self.catalog.get_attributes('push-ups')
        
        self.assertEqual(attrs1.slug, attrs2.slug)
        
        # Invalidate cache
        self.catalog.invalidate_cache()
        
        # Next call should hit database again
        with self.assertNumQueries(1):
            attrs3 = self.catalog.get_attributes('push-ups')
    
    def test_similarity_score_calculation(self):
        """Test similarity score follows priority weights"""
        from apps.workouts.catalog import ExerciseAttributes
        
        push_ups = ExerciseAttributes(
            slug='push-ups',
            name='Push-ups',
            muscle_group='chest',
            equipment='none', 
            difficulty='beginner'
        )
        
        # Same muscle group, different equipment
        bench_press = ExerciseAttributes(
            slug='bench-press',
            name='Bench Press',
            muscle_group='chest',
            equipment='barbell',
            difficulty='intermediate'
        )
        
        # Different muscle group, same equipment
        squats = ExerciseAttributes(
            slug='squats',
            name='Squats',
            muscle_group='legs',
            equipment='none',
            difficulty='beginner'
        )
        
        score1 = push_ups.similarity_score(bench_press, EXERCISE_FALLBACK_PRIORITY)
        score2 = push_ups.similarity_score(squats, EXERCISE_FALLBACK_PRIORITY)
        
        # Lower score = more similar
        # bench_press should be more similar (same muscle group)
        self.assertLess(score1, score2)
    
    def test_get_by_muscle_group_with_allowed_filter(self):
        """Test filtering by muscle group and allowed set"""
        allowed = {'push-ups', 'squats'}
        
        chest_exercises = self.catalog.get_by_muscle_group('chest', allowed)
        
        # Should only return allowed chest exercises
        self.assertEqual(chest_exercises, ['push-ups'])
        self.assertNotIn('bench-press', chest_exercises)  # Not in allowed
        self.assertNotIn('squats', chest_exercises)  # Not chest


@pytest.mark.unit
class TestExerciseValidationService(TestCase):
    """Test exercise validation and whitelist generation"""
    
    def setUp(self):
        cache.clear()
        
        # Create exercises with video clips
        self.exercise_with_videos = CSVExerciseFactory(slug='push-ups')
        self.exercise_without_videos = CSVExerciseFactory(slug='no-videos')
        
        # Create required video clips for push-ups
        from apps.workouts.constants import VideoKind
        for kind in [VideoKind.TECHNIQUE, VideoKind.INSTRUCTION, VideoKind.MISTAKE]:
            VideoClipFactory(
                exercise=self.exercise_with_videos,
                r2_kind=kind,
                r2_archetype='professional'
            )
    
    def test_whitelist_cache_key_includes_archetype(self):
        """Test cache key includes archetype parameter"""
        with patch('apps.core.services.exercise_validation.cache') as mock_cache:
            mock_cache.get.return_value = None  # Cache miss
            mock_cache.set.return_value = None
            
            # Call with archetype
            ExerciseValidationService.get_allowed_exercise_slugs(archetype='professional')
            
            # Verify cache key includes archetype
            call_args = mock_cache.get.call_args[0][0]
            self.assertIn('arch_professional', call_args)
    
    def test_whitelist_repeated_call_uses_cache(self):
        """Test repeated calls use cache without SQL"""
        # First call
        slugs1 = ExerciseValidationService.get_allowed_exercise_slugs()
        
        # Second call should use cache
        with self.assertNumQueries(0):
            slugs2 = ExerciseValidationService.get_allowed_exercise_slugs()
        
        self.assertEqual(slugs1, slugs2)
    
    @patch('apps.core.metrics.incr')
    def test_whitelist_tracks_metrics(self, mock_incr):
        """Test whitelist generation tracks metrics"""
        cache.clear()  # Force cache miss
        
        ExerciseValidationService.get_allowed_exercise_slugs()
        
        # Should track whitelist size
        mock_incr.assert_any_call('ai.whitelist.exercises_count', 1)  # push-ups has coverage
    
    def test_whitelist_archetype_filtering(self):
        """Test whitelist filters by archetype"""
        # Create videos only for mentor archetype
        VideoClipFactory(
            exercise=self.exercise_without_videos,
            r2_kind='instruction',
            r2_archetype='mentor'
        )
        VideoClipFactory(
            exercise=self.exercise_without_videos,
            r2_kind='technique', 
            r2_archetype='mentor'
        )
        VideoClipFactory(
            exercise=self.exercise_without_videos,
            r2_kind='mistake',
            r2_archetype='mentor'
        )
        
        # Should find exercise when filtering by mentor
        mentor_slugs = ExerciseValidationService.get_allowed_exercise_slugs(archetype='mentor')
        self.assertIn('no-videos', mentor_slugs)
        
        # Should not find when filtering by different archetype
        peer_slugs = ExerciseValidationService.get_allowed_exercise_slugs(archetype='peer')
        self.assertNotIn('no-videos', peer_slugs)


@pytest.mark.integration
class TestCacheInvalidation(TestCase):
    """Test cache invalidation signals"""
    
    def test_exercise_save_invalidates_catalog(self):
        """Test exercise save triggers catalog cache invalidation"""
        catalog = get_catalog()
        
        # Prime cache
        catalog.get_attributes('test-slug')
        
        with patch.object(catalog, 'invalidate_cache') as mock_invalidate:
            # Create new exercise (should trigger signal)
            CSVExerciseFactory(slug='new-exercise')
            
            # Should have called invalidate_cache
            mock_invalidate.assert_called()
    
    def test_video_clip_save_invalidates_whitelist(self):
        """Test video clip save invalidates whitelist cache"""
        exercise = CSVExerciseFactory()
        
        # Prime whitelist cache
        ExerciseValidationService.get_allowed_exercise_slugs()
        
        with patch('django.core.cache.cache.delete') as mock_delete:
            # Create new video clip (should trigger signal)
            VideoClipFactory(exercise=exercise)
            
            # Should have deleted cache keys
            mock_delete.assert_called()


@pytest.mark.unit
def test_catalog_stats_generation():
    """Test catalog statistics generation"""
    # Create exercises in different muscle groups
    CSVExerciseFactory(slug='chest1', muscle_group='chest')
    CSVExerciseFactory(slug='chest2', muscle_group='chest') 
    CSVExerciseFactory(slug='legs1', muscle_group='legs')
    
    catalog = ExerciseCatalog()
    catalog.invalidate_cache()  # Ensure fresh load
    
    stats = catalog.get_stats()
    
    assert stats['total_exercises'] == 3
    assert stats['muscle_groups'] >= 2
    assert stats['muscle_group_distribution']['chest'] == 2
    assert stats['muscle_group_distribution']['legs'] == 1


@pytest.mark.unit
@patch('apps.core.metrics.incr')
def test_whitelist_metrics_integration(mock_incr, standard_exercises):
    """Test whitelist metrics are properly tracked"""
    cache.clear()
    
    # Generate whitelist (should trigger metrics)
    slugs = ExerciseValidationService.get_allowed_exercise_slugs(archetype='professional')
    
    # Should track count
    expected_count = len([ex for ex in standard_exercises])  # All have coverage
    mock_incr.assert_any_call('ai.whitelist.exercises_count', expected_count)