"""Signal handlers for core app"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.workouts.models import CSVExercise, R2Video

from .services.exercise_validation import ExerciseValidationService

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=R2Video)
def invalidate_exercise_cache_on_video_change(sender, **kwargs):
    """Invalidate exercise validation cache when R2Video changes"""
    ExerciseValidationService.invalidate_cache()
    logger.info("Invalidated exercise validation cache due to R2Video change")


@receiver([post_save, post_delete], sender=CSVExercise) 
def invalidate_exercise_cache_on_exercise_change(sender, **kwargs):
    """Invalidate exercise validation cache when Exercise changes"""
    ExerciseValidationService.invalidate_cache()
    logger.info("Invalidated exercise validation cache due to Exercise change")