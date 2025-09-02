"""
Test catalog building from CSVExercise model
"""

import pytest
from django.test import TestCase

from apps.workouts.catalog import ExerciseCatalog
from apps.workouts.models import CSVExercise


class TestCatalogBuild(TestCase):
    """Test catalog building without crashes and with correct field mapping"""
    
    def setUp(self):
        """Create test CSVExercise instances"""
        # Test with Russian level
        CSVExercise.objects.create(
            id='test_01',
            name_ru='Тест упражнение 1',
            level='средний',
            muscle_group='Грудь',
            exercise_type='strength',
            ai_tags=['Силовая', 'Compound'],
            is_active=True
        )
        
        # Test with English level  
        CSVExercise.objects.create(
            id='test_02',
            name_ru='Тест упражнение 2',
            level='beginner',
            muscle_group='Спина',
            exercise_type='cardio',
            ai_tags='["Кардио", "Выносливость"]',  # String format from CSV
            is_active=True
        )
        
        # Test with missing/empty fields
        CSVExercise.objects.create(
            id='test_03',
            name_ru='Тест упражнение 3',
            level='',  # Empty level
            muscle_group='',  # Empty muscle group
            exercise_type='',
            ai_tags=None,  # None ai_tags
            is_active=True
        )
        
    def test_catalog_builds_without_crashes(self):
        """Test that catalog builds without errors from CSVExercise data"""
        catalog = ExerciseCatalog()
        
        # Should not crash
        exercises = catalog.get_exercises()
        self.assertIsInstance(exercises, dict)
        self.assertEqual(len(exercises), 3)
        
    def test_field_mapping_correct(self):
        """Test that fields are mapped correctly from CSVExercise to ExerciseAttributes"""
        catalog = ExerciseCatalog()
        exercises = catalog.get_exercises()
        
        # Test Russian level mapping
        test_01 = exercises['test_01']
        self.assertEqual(test_01.slug, 'test_01')  # id → slug
        self.assertEqual(test_01.name, 'Тест упражнение 1')  # name_ru → name  
        self.assertEqual(test_01.difficulty, 'intermediate')  # средний → intermediate
        self.assertEqual(test_01.muscle_group, 'грудь')  # Normalized to lowercase
        self.assertTrue(test_01.is_compound)  # 'Compound' in ai_tags
        self.assertEqual(test_01.equipment, 'none')  # Safe default
        
    def test_level_mapping(self):
        """Test level → difficulty mapping with various inputs"""
        catalog = ExerciseCatalog()
        exercises = catalog.get_exercises()
        
        # Russian to English mapping
        test_01 = exercises['test_01']  
        self.assertEqual(test_01.difficulty, 'intermediate')  # средний → intermediate
        
        # English pass-through
        test_02 = exercises['test_02']
        self.assertEqual(test_02.difficulty, 'beginner')  # beginner → beginner
        
        # Empty defaults to beginner
        test_03 = exercises['test_03']  
        self.assertEqual(test_03.difficulty, 'beginner')  # '' → beginner
        
    def test_ai_tags_parsing(self):
        """Test safe parsing of ai_tags in different formats"""
        catalog = ExerciseCatalog() 
        exercises = catalog.get_exercises()
        
        # List format
        test_01 = exercises['test_01']
        self.assertTrue(test_01.is_compound)  # 'Compound' in ['Силовая', 'Compound']
        
        # String format (JSON from CSV)
        test_02 = exercises['test_02'] 
        self.assertTrue(test_02.is_cardio)  # exercise_type='cardio'
        
        # None/empty format
        test_03 = exercises['test_03']
        self.assertFalse(test_03.is_compound)  # No ai_tags
        self.assertFalse(test_03.is_cardio)  # Empty exercise_type
        
    def test_safe_defaults(self):
        """Test that safe defaults are applied for missing fields"""
        catalog = ExerciseCatalog()
        exercises = catalog.get_exercises()
        
        test_03 = exercises['test_03']  # Has empty/None fields
        self.assertEqual(test_03.equipment, 'none')  # No equipment field → 'none'
        self.assertEqual(test_03.muscle_group, 'general')  # Empty muscle_group → 'general'
        self.assertEqual(test_03.difficulty, 'beginner')  # Empty level → 'beginner'