from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# Story models removed - functionality not used and causing deployment issues
# Story, StoryChapter, UserStoryAccess classes removed


class MediaAsset(models.Model):
    ASSET_TYPE_CHOICES = [
        ('video', 'Video'),
        ('image', 'Image'),
        ('audio', 'Audio'),
    ]
    
    CATEGORY_CHOICES = [
        ('exercise_technique', 'Exercise Technique'),
        ('exercise_mistake', 'Exercise Mistake'),
        ('exercise_instruction', 'Exercise Instruction'),
        ('exercise_reminder', 'Exercise Reminder'),
        ('motivation_weekly', 'Weekly Motivation'),
        ('motivation_final', 'Final Congratulation'),
        ('card_background', 'Motivational Card Background'),
        ('avatar', 'Trainer Avatar'),
        ('story_cover', 'Story Cover'),
        ('story_chapter', 'Story Chapter Image'),
    ]
    
    # File information
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPE_CHOICES)
    
    # Categorization
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    tags = models.JSONField(default=list)
    
    # Relations
    exercise = models.ForeignKey(
        'workouts.Exercise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='media_assets'
    )
    archetype = models.CharField(
        max_length=20,
        choices=[
            ('peer', 'Лучший друг'),
            ('professional', 'Профессиональный тренер'),
            ('mentor', 'Мудрый наставник'),
        ],
        blank=True
    )
    
    # Metadata
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="For videos/audio")
    width = models.PositiveIntegerField(null=True, blank=True, help_text="For images/videos")
    height = models.PositiveIntegerField(null=True, blank=True, help_text="For images/videos")
    
    # Management
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_media'
    )
    is_active = models.BooleanField(default=True)
    
    # CDN information
    cdn_url = models.URLField(blank=True)
    cdn_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('ready', 'Ready'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    
    class Meta:
        db_table = 'media_assets'
        indexes = [
            models.Index(fields=['category', 'asset_type']),
            models.Index(fields=['exercise', 'category']),
        ]
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.file_name}"
    
    def get_serving_url(self):
        return self.cdn_url if self.cdn_url else self.file_url


class TrainerPersona(models.Model):
    """Model for trainer archetypes/personas"""
    ARCHETYPE_CHOICES = [
        ('peer', 'Ровесник'),
        ('professional', 'Успешный профессионал'),
        ('mentor', 'Мудрый наставник'),
        # Old archetypes for backward compatibility
        ('bro', 'Бро (Legacy)'),
        ('sergeant', 'Сержант (Legacy)'),
        ('intellectual', 'Интеллектуал (Legacy)'),
    ]
    
    slug = models.SlugField(unique=True, max_length=50)
    archetype = models.CharField(max_length=20, choices=ARCHETYPE_CHOICES, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    
    # Personality traits
    tone_guidelines = models.TextField(help_text='Guidelines for AI tone and communication style')
    motivational_style = models.TextField(help_text='How this trainer motivates users')
    
    # Visual assets
    avatar = models.ImageField(
        upload_to='images/avatars/',
        blank=True,
        null=True,
        help_text='Trainer avatar image'
    )
    
    # Order for display
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trainer_personas'
        ordering = ['display_order', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.archetype})"
    
    @property
    def avatar_cdn(self):
        """Get CDN URL for avatar"""
        if self.avatar:
            from apps.core.services import MediaService
            return MediaService.get_public_cdn_url(self.avatar)
        return ''


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