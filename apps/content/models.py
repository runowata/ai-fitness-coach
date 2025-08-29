from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# Story models removed - functionality not used and causing deployment issues
# Story, StoryChapter, UserStoryAccess classes removed

# УДАЛЕНО: MediaAsset модель - заменена на R2Video/R2Image через UnifiedMediaService
# Все медиафайлы теперь управляются через apps.workouts.models.R2Video и R2Image
# с унифицированным сервисом apps.core.services.unified_media.UnifiedMediaService

# УДАЛЕНО: TrainerPersona модель - заменена на архетипы в R2Video/R2Image
# Архетипы теперь хранятся прямо в медиафайлах: 'mentor', 'professional', 'peer'


class LandingContent(models.Model):
    """Model for managing landing page content"""
    version = models.CharField(max_length=20, default='2.0', unique=True)
    
    # Hero section
    hero_title = models.CharField(max_length=200)
    hero_subtitle = models.TextField()
    hero_cta_primary = models.CharField(max_length=50)
    hero_cta_secondary = models.CharField(max_length=50, blank=True)
    
    # Main sections
    for_whom = models.TextField(help_text='Who is this app for?')
    how_it_works = models.TextField(help_text='How the app works')
    safety = models.TextField(help_text='Safety and confidence information')
    personalization = models.TextField(help_text='Personalization features')
    
    # Use cases / Success stories
    cases = models.JSONField(
        default=list,
        help_text='List of use cases or success stories'
    )
    
    # Features list
    features = models.JSONField(
        default=list,
        help_text='List of key features'
    )
    
    # Footer
    footer_text = models.TextField(blank=True)
    
    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'landing_content'
        ordering = ['-version']
    
    def __str__(self):
        return f"Landing Content v{self.version}"
    
    @classmethod
    def get_active_content(cls):
        """Получить активный контент для landing page"""
        return cls.objects.filter(is_active=True).first()