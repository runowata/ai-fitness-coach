"""Signal handlers for core app"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.workouts.models import Exercise, VideoClip

from .services.exercise_validation import ExerciseValidationService

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=VideoClip)
def invalidate_exercise_cache_on_video_change(sender, **kwargs):
    """Invalidate exercise validation cache when VideoClip changes"""
    ExerciseValidationService.invalidate_cache()
    logger.info("Invalidated exercise validation cache due to VideoClip change")


@receiver([post_save, post_delete], sender=Exercise) 
def invalidate_exercise_cache_on_exercise_change(sender, **kwargs):
    """Invalidate exercise validation cache when Exercise changes"""
    ExerciseValidationService.invalidate_cache()
    logger.info("Invalidated exercise validation cache due to Exercise change")