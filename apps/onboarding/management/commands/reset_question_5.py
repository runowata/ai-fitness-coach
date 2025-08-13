from django.core.management.base import BaseCommand

from apps.onboarding.models import AnswerOption, OnboardingQuestion


class Command(BaseCommand):
    help = 'Reset question 5 to single_choice with proper answer options'

    def handle(self, *args, **options):
        try:
            # Update question 5 back to single_choice
            question = OnboardingQuestion.objects.get(pk=5)
            question.question_type = 'single_choice'
            question.is_block_separator = False
            question.separator_text = ''
            question.save()
            
            # Ensure answer options exist
            answer_options = [
                {'pk': 123, 'text': 'Я понял, теперь я спокоен', 'value': 'understood_calm', 'order': 1},
                {'pk': 124, 'text': 'Понятно, продолжим', 'value': 'understood_continue', 'order': 2},
                {'pk': 125, 'text': 'Хорошо, я буду честен', 'value': 'understood_honest', 'order': 3},
            ]
            
            created_count = 0
            for option_data in answer_options:
                option, created = AnswerOption.objects.get_or_create(
                    pk=option_data['pk'],
                    defaults={
                        'question': question,
                        'option_text': option_data['text'],
                        'option_value': option_data['value'],
                        'order': option_data['order']
                    }
                )
                if created:
                    created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully reset question 5 to single_choice and created {created_count} answer options'
                )
            )
            
        except OnboardingQuestion.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Question 5 not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )