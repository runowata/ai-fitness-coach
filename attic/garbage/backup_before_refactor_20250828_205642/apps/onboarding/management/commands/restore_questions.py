"""
Management command to restore all onboarding questions and answer options from fixtures
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.onboarding.models import OnboardingQuestion, AnswerOption


class Command(BaseCommand):
    help = 'Restore all onboarding questions and answer options from fixtures'

    def handle(self, *args, **options):
        self.stdout.write('Starting questions restoration...')
        
        # Load questions
        questions_file = os.path.join(settings.BASE_DIR, 'fixtures', 'onboarding_questions.json')
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        # Load answer options
        options_file = os.path.join(settings.BASE_DIR, 'fixtures', 'answer_options.json')
        with open(options_file, 'r', encoding='utf-8') as f:
            options_data = json.load(f)
        
        # Clear existing data
        self.stdout.write('Clearing existing questions and options...')
        AnswerOption.objects.all().delete()
        OnboardingQuestion.objects.all().delete()
        
        # Create questions
        self.stdout.write('Creating questions...')
        question_map = {}
        for item in questions_data:
            if item['model'] == 'onboarding.onboardingquestion':
                fields = item['fields']
                question = OnboardingQuestion.objects.create(
                    id=item['pk'],
                    order=fields['order'],
                    question_text=fields['question_text'],
                    question_type=fields['question_type'],
                    block_name=fields.get('block_name', ''),
                    block_order=fields.get('block_order', 1),
                    is_block_separator=fields.get('is_block_separator', False),
                    separator_text=fields.get('separator_text', ''),
                    help_text=fields.get('help_text', ''),
                    is_required=fields.get('is_required', True),
                    ai_field_name=fields.get('ai_field_name', ''),
                    scale_min_label=fields.get('scale_min_label', ''),
                    scale_max_label=fields.get('scale_max_label', ''),
                    min_value=fields.get('min_value'),
                    max_value=fields.get('max_value'),
                    is_active=fields.get('is_active', True)
                )
                question_map[item['pk']] = question
                self.stdout.write(f'  Created question {question.order}: {question.question_text[:50]}...')
        
        # Create answer options
        self.stdout.write('Creating answer options...')
        for item in options_data:
            if item['model'] == 'onboarding.answeroption':
                fields = item['fields']
                question_id = fields['question']
                if question_id in question_map:
                    option = AnswerOption.objects.create(
                        question=question_map[question_id],
                        option_text=fields['option_text'],
                        option_value=fields['option_value'],
                        order=fields['order']
                    )
                    self.stdout.write(f'  Added option for Q{question_id}: {option.option_text}')
        
        # Fix question 5 specifically (ensure it has simple options)
        q5 = OnboardingQuestion.objects.filter(order=5).first()
        if q5:
            q5.is_block_separator = False
            q5.question_type = 'single_choice'
            q5.save()
            
            # Clear and recreate simple options for Q5
            q5.answer_options.all().delete()
            AnswerOption.objects.create(
                question=q5,
                option_text="Понятно, продолжаем",
                option_value="continue",
                order=1
            )
            AnswerOption.objects.create(
                question=q5,
                option_text="Хочу узнать больше о безопасности",
                option_value="more_info",
                order=2
            )
            self.stdout.write(self.style.SUCCESS('✓ Fixed question 5 with simple options'))
        
        # Summary
        total_questions = OnboardingQuestion.objects.count()
        total_options = AnswerOption.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Restoration complete!'))
        self.stdout.write(f'  Total questions: {total_questions}')
        self.stdout.write(f'  Total answer options: {total_options}')
        
        # List questions with their option counts
        self.stdout.write('\nQuestions summary:')
        for q in OnboardingQuestion.objects.order_by('order'):
            opt_count = q.answer_options.count()
            if q.question_type in ['single_choice', 'multiple_choice', 'body_map'] and opt_count == 0:
                self.stdout.write(self.style.WARNING(f'  Q{q.order}: {q.question_type} - {opt_count} options ⚠️'))
            else:
                self.stdout.write(f'  Q{q.order}: {q.question_type} - {opt_count} options')