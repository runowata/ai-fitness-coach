"""
Management command to automatically complete onboarding for testing
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.onboarding.models import OnboardingQuestion, UserOnboardingResponse, AnswerOption

User = get_user_model()

class Command(BaseCommand):
    help = 'Automatically complete onboarding for a test user'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='test@test.com', help='User email')
        parser.add_argument('--archetype', type=str, default='mentor', help='Trainer archetype (mentor/professional/peer)')
        
    def handle(self, *args, **options):
        email = options['email']
        archetype = options['archetype']
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'first_name': 'Test', 'last_name': 'User'}
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created new user: {email}')
        else:
            self.stdout.write(f'Using existing user: {email}')
        
        # Clear existing responses
        UserOnboardingResponse.objects.filter(user=user).delete()
        self.stdout.write('Cleared existing responses')
        
        # Get all questions
        questions = OnboardingQuestion.objects.filter(is_active=True).order_by('order')
        
        # Pre-defined answers for quick completion
        answers = {
            1: {'answer': 'TestUser'},  # name
            2: {'answer': 25},  # age
            3: {'answer': 175},  # height
            4: {'answer': 70},   # weight
            5: {'answer': 128},  # ready question - use first available option
            # Health questions (6-15)
            6: {'answers': [3]},  # cardiovascular - no problems
            7: {'answer': 11},   # diabetes - no
            8: {'answers': [16]},  # pain - no pain
            9: {'answer': 'no'},  # injuries
            10: {'answer': 3},   # flexibility
            11: {'answer': 23},  # HIV - confidential/no
            12: {'answer': 24},  # medications - no
            13: {'answer': 27},  # dizziness - no
            14: {'answer': 'no'},  # other conditions
            15: {'answer': 29},  # smoking - no
            # Goals and motivation (16-27)
            16: {'answer': 'better health'},
            17: {'answer': 34},  # what's important
            18: {'answer': 3},   # muscle definition scale
            19: {'answer': 37},  # size preference
            20: {'answer': 39},  # social pressure
            21: {'answers': [43]},  # barriers
            22: {'answer': 49},  # past experiences
            23: {'answer': 3},   # quick results importance
            24: {'answer': 51},  # after hard day
            25: {'answers': [54]},  # inspiration
            26: {'answer': 3},   # body satisfaction
            27: {'answer': 59},  # main goal
            # Lifestyle (28-37)
            28: {'answer': 63},  # work type
            29: {'answer': 7},   # sleep hours
            30: {'answer': 3},   # sleep quality
            31: {'answer': 2},   # stress level
            32: {'answer': 'oatmeal'},  # breakfast
            33: {'answer': 3},   # meals per day
            34: {'answer': 65},  # fast food frequency
            35: {'answer': 71},  # water intake
            36: {'answer': 74},  # alcohol
            37: {'answers': [83]},  # equipment
            # Sexual health (38-45)
            38: {'answers': [88]},  # sexual fitness goals
            39: {'answer': 3},   # sexual stamina
            40: {'answer': 3},   # flexibility importance
            41: {'answer': 89},  # kegel exercises
            42: {'answer': 93},  # stress impact
            43: {'answer': 95},  # sexual role
            44: {'answer': 3},   # confidence
            45: {'answer': 100}, # main goal in sex
            # Training preferences (46-55)
            46: {'answer': 102}, # best time to train
            47: {'answer': 107}, # training preference
            48: {'answer': 'no'}, # disliked exercises
            49: {'answer': 110}, # cardio attitude
            50: {'answers': [114]}, # app importance
            51: {'answer': 'rest'}, # recovery
            52: {'answer': 117}, # trying new exercises
            53: {'answer': 3},   # music importance
            54: {'answer': 122}, # progress tracking
            55: {'answer': 123}, # ready to start
        }
        
        # Process each question
        for question in questions:
            if question.order in answers:
                answer_data = answers[question.order]
                
                # Create response based on question type
                if question.question_type == 'multiple_choice' and 'answers' in answer_data:
                    # For multiple choice, store as JSON array
                    UserOnboardingResponse.objects.create(
                        user=user,
                        question=question,
                        answer_text=json.dumps(answer_data['answers'])
                    )
                    self.stdout.write(f'Q{question.order}: Multiple choice - {answer_data["answers"]}')
                
                elif 'answer' in answer_data:
                    # For single choice, number, text, scale
                    if question.question_type in ['single_choice', 'scale'] and isinstance(answer_data['answer'], int):
                        # Try to find the answer option
                        try:
                            option = AnswerOption.objects.get(id=answer_data['answer'])
                            response = UserOnboardingResponse.objects.create(
                                user=user,
                                question=question,
                                answer_text=option.option_text
                            )
                            response.answer_options.add(option)
                            self.stdout.write(f'Q{question.order}: Selected option - {option.option_text}')
                        except AnswerOption.DoesNotExist:
                            # Fallback - use first available option
                            first_option = question.answer_options.first()
                            if first_option:
                                response = UserOnboardingResponse.objects.create(
                                    user=user,
                                    question=question,
                                    answer_text=first_option.option_text
                                )
                                response.answer_options.add(first_option)
                                self.stdout.write(f'Q{question.order}: Fallback option - {first_option.option_text}')
                            else:
                                self.stdout.write(f'Q{question.order}: No options available - SKIPPED')
                    else:
                        # Text, number or other types
                        UserOnboardingResponse.objects.create(
                            user=user,
                            question=question,
                            answer_text=str(answer_data['answer'])
                        )
                        self.stdout.write(f'Q{question.order}: Text/Number - {answer_data["answer"]}')
            else:
                # Default to first option or skip
                first_option = question.answer_options.first()
                if first_option:
                    response = UserOnboardingResponse.objects.create(
                        user=user,
                        question=question,
                        answer_text=first_option.option_text
                    )
                    response.answer_options.add(first_option)
                    self.stdout.write(f'Q{question.order}: Default option - {first_option.option_text}')
                else:
                    self.stdout.write(f'Q{question.order}: NO DEFAULT AVAILABLE - SKIPPED')
        
        # Set archetype - create profile if it doesn't exist
        try:
            profile = user.profile
        except User.profile.RelatedObjectDoesNotExist:
            from apps.users.models import UserProfile
            profile = UserProfile.objects.create(user=user)
            
        profile.archetype = archetype
        profile.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Onboarding completed!\n'
                f'User: {email}\n'
                f'Archetype: {archetype}\n'
                f'Responses: {UserOnboardingResponse.objects.filter(user=user).count()}/55\n'
                f'Now run: python manage.py fix_workout_plan_columns\n'
                f'Then test: /onboarding/generate/'
            )
        )