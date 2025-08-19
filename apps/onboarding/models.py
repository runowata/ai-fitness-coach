from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.content.media_service import public_url

User = get_user_model()


class OnboardingQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('number', 'Number Input'),
        ('text', 'Text Input'),
        ('scale', 'Scale Rating'),
        ('body_map', 'Body Map Selection'),
    ]
    
    order = models.PositiveIntegerField(unique=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    
    # Block organization
    block_name = models.CharField(max_length=200, blank=True)
    block_order = models.PositiveIntegerField(null=True, blank=True)
    is_block_separator = models.BooleanField(default=False)
    separator_text = models.TextField(blank=True)
    
    # For number inputs and scales
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    
    # For scale questions
    scale_min_label = models.CharField(max_length=100, blank=True)
    scale_max_label = models.CharField(max_length=100, blank=True)
    
    # Additional context
    help_text = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    
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
    title = models.CharField(max_length=200)
    message = models.TextField()
    image_url = models.URLField()
    
    # Categorization
    category = models.CharField(
        max_length=50,
        choices=[
            ('goal', 'Goal-related'),
            ('experience', 'Experience-related'),
            ('limitation', 'Limitation-related'),
            ('general', 'General motivation'),
        ]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'motivational_cards'
    
    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Get image URL using media_service if it's a path, otherwise return as-is"""
        if self.image_url.startswith('http'):
            return self.image_url  # Already a full URL
        return public_url(self.image_url)  # Convert path to URL


class UserOnboardingResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarding_responses')
    question = models.ForeignKey(OnboardingQuestion, on_delete=models.CASCADE)
    
    # Response data (flexible for different question types)
    answer_text = models.TextField(blank=True)
    answer_options = models.ManyToManyField(AnswerOption, blank=True)
    answer_number = models.IntegerField(null=True, blank=True)
    
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