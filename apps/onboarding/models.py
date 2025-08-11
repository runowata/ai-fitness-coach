from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class OnboardingQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('number', 'Number Input'),
        ('text', 'Text Input'),
        ('scale', 'Scale (1-5)'),
        ('body_map', 'Body Map Selection'),
    ]
    
    order = models.PositiveIntegerField(unique=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    
    # Question blocks
    block_name = models.CharField(max_length=100, blank=True)
    block_order = models.PositiveIntegerField(default=1)
    is_block_separator = models.BooleanField(default=False)
    separator_text = models.TextField(blank=True)
    
    # For number inputs
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    
    # For scale questions
    scale_min_label = models.CharField(max_length=50, blank=True)
    scale_max_label = models.CharField(max_length=50, blank=True)
    
    # Additional context
    help_text = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    
    # Conditional logic
    depends_on_question = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dependent_questions'
    )
    depends_on_answer = models.CharField(max_length=100, blank=True)
    
    # AI prompt component
    ai_field_name = models.CharField(max_length=50)  # Field name for AI prompt
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'onboarding_questions'
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."


class AnswerOption(models.Model):
    question = models.ForeignKey(
        OnboardingQuestion, 
        on_delete=models.CASCADE, 
        related_name='answer_options'
    )
    option_text = models.CharField(max_length=200)
    option_value = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    
    # Link to motivational card
    motivational_card = models.ForeignKey(
        'MotivationalCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answer_options'
    )
    
    class Meta:
        db_table = 'answer_options'
        ordering = ['order']
        unique_together = [['question', 'order']]
    
    def __str__(self):
        return self.option_text


class MotivationalCard(models.Model):
    title = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    image_url = models.URLField(blank=True)  # Keep for backward compatibility
    
    # New image field for R2/S3 storage
    image = models.ImageField(
        upload_to='photos/quotes/',
        blank=True,
        null=True,
        help_text='Motivational card image'
    )
    
    # Specific linking to questions and answers
    question = models.ForeignKey(
        'OnboardingQuestion', 
        on_delete=models.CASCADE,
        related_name='motivational_cards',
        null=True,
        blank=True
    )
    answer_option = models.ForeignKey(
        'AnswerOption',
        on_delete=models.CASCADE,
        related_name='motivational_cards',
        null=True,
        blank=True
    )
    
    # For text/number questions without specific answer options
    is_default_for_question = models.BooleanField(default=False)
    
    # Categorization (kept for backward compatibility)
    category = models.CharField(
        max_length=50,
        choices=[
            ('goal', 'Goal-related'),
            ('experience', 'Experience-related'),
            ('limitation', 'Limitation-related'),
            ('general', 'General motivation'),
            ('response', 'Response-specific'),
        ],
        default='response'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'motivational_cards'
        unique_together = [['question', 'answer_option']]
    
    def __str__(self):
        if self.question:
            if self.answer_option:
                return f"Card for Q{self.question.order}: {self.answer_option.option_text}"
            elif self.is_default_for_question:
                return f"Default card for Q{self.question.order}"
        return self.title or self.message[:50]
    
    @property
    def cdn_url(self):
        """Get CDN URL for card image"""
        if self.image:
            from apps.core.services import MediaService
            return MediaService.get_public_cdn_url(self.image)
        
        # For legacy image_url fields, create signed URL since public R2 access not configured
        if self.image_url:
            # If it's already a full URL with pub-*.r2.dev domain, extract path and create signed URL
            if self.image_url.startswith('http'):
                # Extract path from public URL (remove https://pub-xxxxx.r2.dev/)
                import re
                match = re.search(r'https://pub-[^/]+\.r2\.dev/(.+)', self.image_url)
                if match:
                    file_path = match.group(1)  # e.g., "photos/progress/card_progress_0066.jpg"
                    # Create a mock file field with the path for signed URL generation
                    from django.core.files.storage import default_storage
                    try:
                        # Generate signed URL using the file path
                        signed_url = default_storage.url(file_path)
                        return signed_url
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Failed to generate signed URL for {file_path}: {e}")
                        return self.image_url  # Fallback to original URL
                else:
                    return self.image_url  # Return original URL if pattern doesn't match
            
            # If it's a relative path, try to build signed URL
            from apps.core.services import MediaService
            return MediaService.get_public_cdn_url(self.image_url)
        
        return ''  # No image available


class UserOnboardingResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarding_responses')
    question = models.ForeignKey(OnboardingQuestion, on_delete=models.CASCADE)
    
    # Response data (flexible for different question types)
    answer_text = models.TextField(blank=True)
    answer_options = models.ManyToManyField(AnswerOption, blank=True)
    answer_number = models.IntegerField(null=True, blank=True)
    answer_scale = models.IntegerField(null=True, blank=True)  # For 1-5 scale questions
    answer_body_map = models.JSONField(null=True, blank=True)  # For body pain areas
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_onboarding_responses'
        unique_together = [['user', 'question']]
        
    def get_answer_value(self):
        if self.question.question_type == 'single_choice':
            option = self.answer_options.first()
            return option.option_value if option else None
        elif self.question.question_type == 'multiple_choice':
            return [opt.option_value for opt in self.answer_options.all()]
        elif self.question.question_type == 'number':
            return self.answer_number
        elif self.question.question_type == 'scale':
            return self.answer_scale
        elif self.question.question_type == 'body_map':
            return self.answer_body_map
        else:
            return self.answer_text


class OnboardingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarding_sessions')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # AI generation tracking
    ai_request_sent_at = models.DateTimeField(null=True, blank=True)
    ai_response_received_at = models.DateTimeField(null=True, blank=True)
    ai_request_data = models.JSONField(null=True, blank=True)
    ai_response_data = models.JSONField(null=True, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'onboarding_sessions'
        ordering = ['-started_at']