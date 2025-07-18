"""
Management command to restore essential app data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.onboarding.models import OnboardingQuestion, AnswerOption, MotivationalCard
from apps.workouts.models import Exercise


class Command(BaseCommand):
    help = 'Restore essential app data for onboarding and workouts'

    def handle(self, *args, **options):
        self.stdout.write('Starting data restoration...')
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        OnboardingQuestion.objects.all().delete()
        AnswerOption.objects.all().delete() 
        MotivationalCard.objects.all().delete()
        Exercise.objects.all().delete()
        
        # Create onboarding questions
        self.stdout.write('Creating onboarding questions...')
        self.create_onboarding_questions()
        
        # Create exercises
        self.stdout.write('Creating exercises...')
        self.create_exercises()
        
        # Create motivational cards
        self.stdout.write('Creating motivational cards...')
        self.create_motivational_cards()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Data restoration complete!\n'
                f'- Questions: {OnboardingQuestion.objects.count()}\n'
                f'- Answer options: {AnswerOption.objects.count()}\n'
                f'- Exercises: {Exercise.objects.count()}\n'  
                f'- Motivational cards: {MotivationalCard.objects.count()}'
            )
        )

    def create_onboarding_questions(self):
        # Question 1: Primary Goal
        q1 = OnboardingQuestion.objects.create(
            order=1,
            question_text='Какова ваша основная цель?',
            question_type='single_choice',
            help_text='Выберите наиболее важную для вас цель',
            is_required=True,
            is_active=True,
            ai_field_name='primary_goal'
        )

        AnswerOption.objects.create(question=q1, option_text='Набрать мышечную массу', option_value='bulk', order=1)
        AnswerOption.objects.create(question=q1, option_text='Похудеть и убрать жир', option_value='cut', order=2)
        AnswerOption.objects.create(question=q1, option_text='Улучшить общую физическую форму', option_value='fitness', order=3)
        AnswerOption.objects.create(question=q1, option_text='Повысить уверенность в себе', option_value='confidence', order=4)

        # Question 2: Experience Level
        q2 = OnboardingQuestion.objects.create(
            order=2,
            question_text='Каков ваш уровень опыта в фитнесе?',
            question_type='single_choice',
            help_text='Выберите вариант, который лучше всего описывает ваш опыт',
            is_required=True,
            is_active=True,
            ai_field_name='experience_level'
        )

        AnswerOption.objects.create(question=q2, option_text='Новичок (меньше 6 месяцев)', option_value='beginner', order=1)
        AnswerOption.objects.create(question=q2, option_text='Средний (6 месяцев - 2 года)', option_value='intermediate', order=2)
        AnswerOption.objects.create(question=q2, option_text='Продвинутый (больше 2 лет)', option_value='advanced', order=3)

        # Question 3: Equipment
        q3 = OnboardingQuestion.objects.create(
            order=3,
            question_text='Какое оборудование у вас есть?',
            question_type='multiple_choice',
            help_text='Выберите все доступные варианты',
            is_required=True,
            is_active=True,
            ai_field_name='equipment'
        )

        AnswerOption.objects.create(question=q3, option_text='Только собственный вес', option_value='bodyweight', order=1)
        AnswerOption.objects.create(question=q3, option_text='Гантели', option_value='dumbbells', order=2)
        AnswerOption.objects.create(question=q3, option_text='Турник', option_value='pullup_bar', order=3)
        AnswerOption.objects.create(question=q3, option_text='Полный тренажерный зал', option_value='full_gym', order=4)

        # Question 4: Training Days
        q4 = OnboardingQuestion.objects.create(
            order=4,
            question_text='Сколько дней в неделю вы можете тренироваться?',
            question_type='single_choice',
            help_text='Выберите реалистичное количество дней',
            is_required=True,
            is_active=True,
            ai_field_name='days_per_week'
        )

        AnswerOption.objects.create(question=q4, option_text='2-3 дня', option_value='2-3', order=1)
        AnswerOption.objects.create(question=q4, option_text='3-4 дня', option_value='3-4', order=2)
        AnswerOption.objects.create(question=q4, option_text='4-5 дней', option_value='4-5', order=3)
        AnswerOption.objects.create(question=q4, option_text='6+ дней', option_value='6+', order=4)

        # Question 5: Trainer Archetype
        q5 = OnboardingQuestion.objects.create(
            order=5,
            question_text='Какой стиль тренера вам нравится?',
            question_type='single_choice',
            help_text='Выберите тренера, который больше всего мотивирует',
            is_required=True,
            is_active=True,
            ai_field_name='trainer_archetype'
        )

        AnswerOption.objects.create(question=q5, option_text='Бро - дружелюбный и поддерживающий', option_value='bro', order=1)
        AnswerOption.objects.create(question=q5, option_text='Сержант - строгий и требовательный', option_value='sergeant', order=2)
        AnswerOption.objects.create(question=q5, option_text='Интеллектуал - научный подход', option_value='intellectual', order=3)

    def create_exercises(self):
        exercises = [
            {'id': 'push_ups', 'slug': 'push-ups', 'name': 'Отжимания', 'difficulty': 'beginner', 'equipment': 'bodyweight'},
            {'id': 'squats', 'slug': 'squats', 'name': 'Приседания', 'difficulty': 'beginner', 'equipment': 'bodyweight'},
            {'id': 'plank', 'slug': 'plank', 'name': 'Планка', 'difficulty': 'beginner', 'equipment': 'bodyweight'},
            {'id': 'lunges', 'slug': 'lunges', 'name': 'Выпады', 'difficulty': 'beginner', 'equipment': 'bodyweight'},
            {'id': 'burpees', 'slug': 'burpees', 'name': 'Берпи', 'difficulty': 'intermediate', 'equipment': 'bodyweight'},
            {'id': 'mountain_climbers', 'slug': 'mountain-climbers', 'name': 'Горолаз', 'difficulty': 'beginner', 'equipment': 'bodyweight'},
            {'id': 'jumping_jacks', 'slug': 'jumping-jacks', 'name': 'Прыжки-звёздочки', 'difficulty': 'beginner', 'equipment': 'bodyweight'},
            {'id': 'bicycle_crunches', 'slug': 'bicycle-crunches', 'name': 'Велосипед', 'difficulty': 'beginner', 'equipment': 'bodyweight'},
        ]

        for ex_data in exercises:
            Exercise.objects.create(
                id=ex_data['id'],
                slug=ex_data['slug'],
                name=ex_data['name'],
                description=f'Упражнение {ex_data["name"]} - отличное упражнение для развития силы и выносливости',
                difficulty=ex_data['difficulty'],
                equipment=ex_data['equipment'],
                muscle_groups='Основные группы мышц'
            )

    def create_motivational_cards(self):
        cards_data = [
            {'category': 'general', 'archetype': 'bro', 'title': 'Поехали, бро!', 'message': 'Время показать всем, на что ты способен! Твоя тренировка - твоя сила!'},
            {'category': 'general', 'archetype': 'sergeant', 'title': 'К бою готов!', 'message': 'Дисциплина и упорство - вот что отличает победителей от остальных!'},
            {'category': 'general', 'archetype': 'intellectual', 'title': 'Научный подход', 'message': 'Каждое повторение приближает вас к цели. Прогресс - это результат постоянства.'},
            {'category': 'goal', 'archetype': 'bro', 'title': 'Цель в деле!', 'message': 'Отличный выбор цели! Теперь пошагово идем к результату.'},
            {'category': 'experience', 'archetype': 'sergeant', 'title': 'Опыт - сила!', 'message': 'Ваш уровень подготовки учтен. Программа адаптирована под вас!'},
            {'category': 'equipment', 'archetype': 'intellectual', 'title': 'Оборудование учтено', 'message': 'Программа адаптирована под ваше доступное оборудование.'},
        ]

        for card_data in cards_data:
            MotivationalCard.objects.create(
                category=card_data['category'],
                title=card_data['title'],
                message=card_data['message'],
                image_url=f'/static/images/{card_data["archetype"]}-avatar.png',
                is_active=True
            )