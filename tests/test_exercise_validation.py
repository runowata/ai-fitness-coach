"""Tests for exercise validation service"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from apps.core.services.exercise_validation import ExerciseValidationService
from apps.workouts.models import VideoClip, VideoProvider


class TestExerciseValidationService:
    """Test ExerciseValidationService"""
    
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_clips_with_video')
    @patch('django.core.cache.cache')
    def test_get_allowed_exercise_slugs_from_cache(self, mock_cache, mock_get_clips):
        """Test getting allowed slugs from cache"""
        # Mock cache hit
        mock_cache.get.return_value = {'push-ups', 'squats', 'lunges'}
        
        slugs = ExerciseValidationService.get_allowed_exercise_slugs()
        
        assert slugs == {'push-ups', 'squats', 'lunges'}
        mock_cache.get.assert_called_once_with('allowed_exercise_slugs_v3')
        mock_get_clips.assert_not_called()
    
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_clips_with_video')
    @patch('django.core.cache.cache')
    def test_get_allowed_exercise_slugs_from_db(self, mock_cache, mock_get_clips):
        """Test getting allowed slugs from database"""
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock QuerySet chain
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.values_list.return_value = ['push-ups', 'squats']
        
        mock_get_clips.return_value = mock_queryset
        
        slugs = ExerciseValidationService.get_allowed_exercise_slugs()
        
        assert slugs == {'push-ups', 'squats'}
        mock_cache.set.assert_called_once()
    
    def test_get_clips_with_video_query(self):
        """Test get_clips_with_video builds correct query"""
        with patch('apps.workouts.models.VideoClip.objects') as mock_objects:
            mock_queryset = Mock()
            mock_objects.filter.return_value = mock_queryset
            mock_queryset.filter.return_value = mock_queryset
            
            ExerciseValidationService.get_clips_with_video()
            
            # Verify initial filter for is_active=True
            mock_objects.filter.assert_called_once_with(is_active=True)
            
            # Verify second filter for provider conditions
            mock_queryset.filter.assert_called_once()
    
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_clips_with_video')
    @patch('django.core.cache.cache')
    def test_get_allowed_exercise_slugs_error_handling(self, mock_cache, mock_get_clips):
        """Test error handling in get_allowed_exercise_slugs"""
        mock_cache.get.return_value = None
        mock_get_clips.side_effect = Exception("Database error")
        
        slugs = ExerciseValidationService.get_allowed_exercise_slugs()
        
        # Should return empty set on error
        assert slugs == set()
    
    @patch('django.core.cache.cache')
    def test_invalidate_cache(self, mock_cache):
        """Test cache invalidation"""
        ExerciseValidationService.invalidate_cache()
        
        # Should delete both old and new cache keys
        assert mock_cache.delete.call_count == 2
        mock_cache.delete.assert_any_call('allowed_exercise_slugs_v2')
        mock_cache.delete.assert_any_call('allowed_exercise_slugs_v3')
    
    @patch('django.db.connection')
    def test_get_coverage_report_success(self, mock_connection):
        """Test successful coverage report generation"""
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock database results
        mock_cursor.fetchall.return_value = [
            ('push-ups', 'Push-ups', 3, 'instruction,technique,mistake', 'complete'),
            ('squats', 'Squats', 2, 'instruction,technique', 'partial'),
            ('lunges', 'Lunges', 0, '', 'none')
        ]
        
        report = ExerciseValidationService.get_coverage_report()
        
        assert report['total_exercises'] == 3
        assert report['statistics'] == {'complete': 1, 'partial': 1, 'none': 1}
        assert report['coverage_percentage'] == 33.3  # 1/3 * 100 rounded to 1 decimal
        assert len(report['exercises']) == 3
    
    @patch('django.db.connection')
    def test_get_coverage_report_error(self, mock_connection):
        """Test coverage report error handling"""
        mock_connection.cursor.side_effect = Exception("Database error")
        
        report = ExerciseValidationService.get_coverage_report()
        
        assert 'error' in report
        assert report['error'] == "Database error"
    
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('django.db.connection')
    def test_find_exercise_alternatives_success(self, mock_connection, mock_get_allowed):
        """Test successful exercise alternatives finding"""
        mock_get_allowed.return_value = {'squats', 'lunges', 'leg-press'}
        
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock exercise lookup
        mock_cursor.fetchone.return_value = (
            ['legs', 'glutes'],  # muscle_groups
            ['bodyweight'],      # equipment_needed
            'intermediate'       # difficulty
        )
        
        # Mock alternatives query
        mock_cursor.fetchall.return_value = [
            ('lunges',), 
            ('leg-press',)
        ]
        
        alternatives = ExerciseValidationService.find_exercise_alternatives('push-ups')
        
        assert alternatives == ['lunges', 'leg-press']
    
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('django.db.connection')
    def test_find_exercise_alternatives_not_found(self, mock_connection, mock_get_allowed):
        """Test exercise alternatives when exercise not found"""
        mock_get_allowed.return_value = {'squats', 'lunges'}
        
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Exercise not found
        
        alternatives = ExerciseValidationService.find_exercise_alternatives('nonexistent')
        
        assert alternatives == []
    
    @patch('apps.core.services.exercise_validation.ExerciseValidationService.get_allowed_exercise_slugs')
    @patch('django.db.connection')
    def test_find_exercise_alternatives_error(self, mock_connection, mock_get_allowed):
        """Test exercise alternatives error handling"""
        mock_get_allowed.return_value = {'squats'}
        mock_connection.cursor.side_effect = Exception("Database error")
        
        alternatives = ExerciseValidationService.find_exercise_alternatives('push-ups')
        
        assert alternatives == []


@pytest.mark.django_db
class TestExerciseValidationIntegration:
    """Integration tests with real database models"""
    
    def test_required_kinds_constant(self):
        """Test REQUIRED_KINDS constant is properly defined"""
        assert ExerciseValidationService.REQUIRED_KINDS == ["instruction", "technique", "mistake"]
        assert len(ExerciseValidationService.REQUIRED_KINDS) == 3
    
    def test_cache_timeout_constant(self):
        """Test CACHE_TIMEOUT constant is reasonable"""
        assert ExerciseValidationService.CACHE_TIMEOUT == 300  # 5 minutes
        assert isinstance(ExerciseValidationService.CACHE_TIMEOUT, int)


class TestVideoProviderIntegration:
    """Test integration with VideoProvider choices"""
    
    def test_video_provider_choices(self):
        """Test VideoProvider choices are available"""
        assert VideoProvider.R2 == "r2"
        assert VideoProvider.STREAM == "stream"
        assert VideoProvider.EXTERNAL == "external"
    
    @patch('apps.workouts.models.VideoClip.objects')
    def test_get_clips_with_video_provider_filter(self, mock_objects):
        """Test get_clips_with_video uses correct provider filters"""
        mock_queryset = Mock()
        mock_objects.filter.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        
        ExerciseValidationService.get_clips_with_video()
        
        # Verify the Q objects are constructed correctly
        # The actual Q object construction would be tested in integration tests
        assert mock_objects.filter.called
        assert mock_queryset.filter.called