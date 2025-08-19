from django.db import models
from django.contrib.auth import get_user_model
from .media_service import public_url

User = get_user_model()


class Story(models.Model):
    slug = models.SlugField(unique=True, db_index=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField()
    cover_image_url = models.URLField()  # This will be migrated to use paths instead of full URLs
    genre = models.CharField(max_length=50, default='romance')
    
    # Story metadata
    total_chapters = models.PositiveIntegerField()
    is_published = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stories'
        verbose_name_plural = 'Stories'
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    def get_cover_image_url(self):
        """Get cover image URL using media_service if it's a path, otherwise return as-is"""
        if self.cover_image_url.startswith('http'):
            return self.cover_image_url  # Already a full URL
        return public_url(self.cover_image_url)  # Convert path to URL


class StoryChapter(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='chapters')
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Video/media URLs
    video_url = models.URLField(blank=True)
    thumbnail_url = models.URLField(blank=True)
    
    # Reading time estimate
    estimated_reading_time = models.PositiveIntegerField(help_text="In minutes", default=5)
    
    # Chapter image (optional)
    image_url = models.URLField(blank=True)
    
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'story_chapters'
        unique_together = [['story', 'order']]
        ordering = ['order']
    
    def __str__(self):
        return f"{self.story.title} - Chapter {self.order}: {self.title}"
    
    def get_image_url(self):
        """Get chapter image URL using media_service if it's a path, otherwise return as-is"""
        if not self.image_url:
            return ''
        if self.image_url.startswith('http'):
            return self.image_url  # Already a full URL
        return public_url(self.image_url)  # Convert path to URL


class UserStoryAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_access')
    chapter = models.ForeignKey(StoryChapter, on_delete=models.CASCADE)
    
    unlocked_at = models.DateTimeField(auto_now_add=True)
    unlocked_by_achievement = models.ForeignKey(
        'achievements.Achievement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Reading tracking
    first_read_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    read_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'user_story_access'
        unique_together = [['user', 'chapter']]
        indexes = [
            models.Index(fields=['user', 'chapter']),
        ]


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
        ('motivation_intro', 'Daily Intro'),
        ('motivation_weekly', 'Weekly Motivation'),
        ('motivation_progress', 'Progress Milestone'),
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
            ('bro', 'Бро'),
            ('sergeant', 'Сержант'),
            ('intellectual', 'Интеллектуал'),
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
        """Get the public URL for this media asset using media_service"""
        if self.cdn_url:
            return self.cdn_url
        # Use media_service to generate URL from stored path
        return public_url(self.file_url)