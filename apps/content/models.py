from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Story(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField()
    cover_image_url = models.URLField()
    
    # Story metadata
    total_chapters = models.PositiveIntegerField()
    is_published = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stories'
        verbose_name_plural = 'Stories'
        ordering = ['title']
    
    def __str__(self):
        return self.title


class StoryChapter(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Reading time estimate
    estimated_reading_time = models.PositiveIntegerField(help_text="In minutes")
    
    # Chapter image (optional)
    image_url = models.URLField(blank=True)
    
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'story_chapters'
        unique_together = [['story', 'chapter_number']]
        ordering = ['chapter_number']
    
    def __str__(self):
        return f"{self.story.title} - Chapter {self.chapter_number}: {self.title}"


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
        return self.cdn_url if self.cdn_url else self.file_url