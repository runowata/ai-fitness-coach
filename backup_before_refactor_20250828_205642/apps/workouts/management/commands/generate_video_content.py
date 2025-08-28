#!/usr/bin/env python3
"""
Management command to generate VideoClip records based on reference materials
Creates rich contextual video content structure from trainer scripts
"""

import random
from typing import Dict, List

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.workouts.constants import VideoKind
from apps.workouts.models import VideoClip, VideoProvider


class Command(BaseCommand):
    help = 'Generate VideoClip records based on reference trainer scripts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--archetype',
            choices=['mentor', 'professional', 'peer', 'all'],
            default='all',
            help='Generate content for specific archetype'
        )
        parser.add_argument(
            '--content-type',
            choices=['intro', 'outro', 'mid_workout', 'weekly', 'all'],
            default='all',
            help='Generate specific type of content'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of variations to generate'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.archetype_filter = options['archetype']
        self.content_type_filter = options['content_type']
        self.limit = options['limit']

        self.stdout.write("🎬 GENERATE VIDEO CONTENT FROM SCRIPTS")
        self.stdout.write("=" * 50)
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Define trainer content based on reference materials
        trainer_scripts = self._load_trainer_scripts()
        
        created_count = 0
        
        # Generate content for each archetype
        archetypes = ['mentor', 'professional', 'peer'] if self.archetype_filter == 'all' else [self.archetype_filter]
        
        for archetype in archetypes:
            self.stdout.write(f"\n🎯 Generating content for {archetype} archetype")
            
            if self.content_type_filter in ['intro', 'all']:
                created_count += self._generate_contextual_intros(archetype, trainer_scripts[archetype]['intros'])
            
            if self.content_type_filter in ['outro', 'all']:
                created_count += self._generate_contextual_outros(archetype, trainer_scripts[archetype]['outros'])
            
            if self.content_type_filter in ['mid_workout', 'all']:
                created_count += self._generate_mid_workout_content(archetype, trainer_scripts[archetype]['mid_workout'])
            
            if self.content_type_filter in ['weekly', 'all']:
                created_count += self._generate_weekly_content(archetype, trainer_scripts[archetype]['weekly'])

        self.stdout.write(f"\n✅ Generated {created_count} VideoClip records")

    def _load_trainer_scripts(self) -> Dict:
        """Load trainer scripts from reference materials"""
        
        # Based on the analyzed reference files
        return {
            'mentor': {
                'intros': [
                    {
                        'script': 'Здравствуйте. Рад, что вы здесь и готовы уделить время себе. Сегодня мы посвятим нашу практику ногам — нашему фундаменту.',
                        'mood_type': 'calm',
                        'content_theme': 'week_start'
                    },
                    {
                        'script': 'Приветствую вас. Сегодняшняя тренировка — это возможность вернуться в свое тело, особенно если ваш день был полон мыслей и стресса.',
                        'mood_type': 'calm',
                        'content_theme': 'recovery'
                    },
                    {
                        'script': 'Добрый день. Сегодня мы будем искать баланс. Баланс между силой и гибкостью, напряжением и расслаблением.',
                        'mood_type': 'philosophical',
                        'content_theme': 'balance'
                    },
                    # Add more mentor intros...
                ],
                'outros': [
                    {
                        'script': 'Практика на сегодня завершена. Поблагодарите свое тело за этот труд. Та энергия и спокойствие, которые вы сейчас чувствуете, — это ваше.',
                        'mood_type': 'calm',
                        'content_theme': 'gratitude'
                    },
                    {
                        'script': 'Работа окончена. Но настоящая практика только начинается. Постарайтесь сохранить эту осознанность и связь с телом в течение всего дня.',
                        'mood_type': 'philosophical',
                        'content_theme': 'integration'
                    },
                    # Add more mentor outros...
                ],
                'mid_workout': [
                    {
                        'script': 'Пауза. Почувствуйте это жжение. Это не враг. Это энергия трансформации. Прислушайтесь к нему, дышите в него.',
                        'mood_type': 'encouraging',
                        'content_theme': 'overcoming'
                    },
                    {
                        'script': 'Отдых. Вернитесь к дыханию. Оно — наш якорь в настоящем моменте. Глубокий, спокойный вдох... и полный, освобождающий выдох.',
                        'mood_type': 'calm',
                        'content_theme': 'breathing'
                    },
                    # Add more mentor mid-workout...
                ],
                'weekly': [
                    {
                        'script': 'Неделя 1: Фундамент удовольствия. Начнем с самого важного - умения слышать свое тело и дышать осознанно.',
                        'week_context': 1,
                        'content_theme': 'foundation'
                    },
                    # Add more weekly content...
                ]
            },
            'professional': {
                'intros': [
                    {
                        'script': 'Доброе утро. Рад видеть вас. Сегодня наша задача — силовая тренировка на верх тела. Цель — не просто усталость, а точечная стимуляция мышечных волокон.',
                        'mood_type': 'business',
                        'content_theme': 'efficiency'
                    },
                    {
                        'script': 'Приветствую. Время — наш самый ценный ресурс. Эти 30 минут мы инвестируем в вашу производительность на весь день.',
                        'mood_type': 'business',
                        'content_theme': 'investment'
                    },
                    # Add more professional intros...
                ],
                'outros': [
                    {
                        'script': 'Работа на сегодня завершена. Протокол выполнен. Вы инвестировали в свое здоровье, и это усилие принесет свои дивиденды.',
                        'mood_type': 'business',
                        'content_theme': 'achievement'
                    },
                    # Add more professional outros...
                ],
                'mid_workout': [
                    {
                        'script': 'Пауза. Ощущение жжения в мышцах — это сигнал о метаболическом стрессе, который запускает адаптационные процессы.',
                        'mood_type': 'business',
                        'content_theme': 'efficiency'
                    },
                    # Add more professional mid-workout...
                ],
                'weekly': [
                    {
                        'script': 'Неделя 1 - базовая настройка системы. Изучаем анатомию и физиологию для максимального КПД.',
                        'week_context': 1,
                        'content_theme': 'optimization'
                    },
                ]
            },
            'peer': {
                'intros': [
                    {
                        'script': 'Привет! У меня сегодня был тот еще денек... Голова кругом. Знаешь, что лучше всего помогает? Вот это. Полчаса, чтобы выключить мозг и включить тело.',
                        'mood_type': 'energetic',
                        'content_theme': 'stress_relief'
                    },
                    {
                        'script': 'Здорово! Готов поработать? Сегодня у нас силовая на все тело. Создаем тот самый тонус и энергию, которых так не хватает к вечеру.',
                        'mood_type': 'energetic',
                        'content_theme': 'energy'
                    },
                    # Add more peer intros...
                ],
                'outros': [
                    {
                        'script': 'Есть! Сделано! Красавчик! Просто остановись на секунду и почувствуй это. Это гордость. Ты сделал это для себя.',
                        'mood_type': 'energetic',
                        'content_theme': 'achievement'
                    },
                    # Add more peer outros...
                ],
                'mid_workout': [
                    {
                        'script': 'Пауза! Чувствуешь, как мышцы горят? Отлично! Это не боль, это слабость уходит из тела. Мы буквально переплавляем "не могу" в "могу".',
                        'mood_type': 'energetic',
                        'content_theme': 'motivation'
                    },
                    # Add more peer mid-workout...
                ],
                'weekly': [
                    {
                        'script': 'Привет! Начинаем наше путешествие. На этой неделе учимся чувствовать свое тело и правильно дышать.',
                        'week_context': 1,
                        'content_theme': 'journey_start'
                    },
                ]
            }
        }

    def _generate_contextual_intros(self, archetype: str, intro_scripts: List[Dict]) -> int:
        """Generate contextual intro videos"""
        created_count = 0
        
        limit = min(len(intro_scripts), self.limit or len(intro_scripts))
        
        for i, script_data in enumerate(intro_scripts[:limit]):
            if self.dry_run:
                self.stdout.write(f"  [DRY RUN] Would create contextual intro {i+1} for {archetype}")
                created_count += 1
                continue
            
            with transaction.atomic():
                clip_data = {
                    'r2_kind': VideoKind.CONTEXTUAL_INTRO,
                    'r2_archetype': archetype,
                    'model_name': f'contextual_intro_{i+1}',
                    'script_text': script_data['script'],
                    'provider': VideoProvider.R2,
                    'duration_seconds': random.randint(45, 90),  # Realistic intro duration
                    'mood_type': script_data.get('mood_type', 'calm'),
                    'content_theme': script_data.get('content_theme', 'motivation'),
                    'position_in_workout': 'intro',
                    'variation_number': i + 1,
                    'week_context': script_data.get('week_context'),
                    'is_active': True,
                }
                
                clip = VideoClip.objects.create(**clip_data)
                created_count += 1
                
                self.stdout.write(f"  ✅ Created contextual intro {i+1} for {archetype}: {clip.id}")
        
        return created_count

    def _generate_contextual_outros(self, archetype: str, outro_scripts: List[Dict]) -> int:
        """Generate contextual outro videos"""
        created_count = 0
        
        limit = min(len(outro_scripts), self.limit or len(outro_scripts))
        
        for i, script_data in enumerate(outro_scripts[:limit]):
            if self.dry_run:
                self.stdout.write(f"  [DRY RUN] Would create contextual outro {i+1} for {archetype}")
                created_count += 1
                continue
            
            with transaction.atomic():
                clip_data = {
                    'r2_kind': VideoKind.CONTEXTUAL_OUTRO,
                    'r2_archetype': archetype,
                    'model_name': f'contextual_outro_{i+1}',
                    'script_text': script_data['script'],
                    'provider': VideoProvider.R2,
                    'duration_seconds': random.randint(60, 120),  # Realistic outro duration
                    'mood_type': script_data.get('mood_type', 'calm'),
                    'content_theme': script_data.get('content_theme', 'gratitude'),
                    'position_in_workout': 'outro',
                    'variation_number': i + 1,
                    'week_context': script_data.get('week_context'),
                    'is_active': True,
                }
                
                clip = VideoClip.objects.create(**clip_data)
                created_count += 1
                
                self.stdout.write(f"  ✅ Created contextual outro {i+1} for {archetype}: {clip.id}")
        
        return created_count

    def _generate_mid_workout_content(self, archetype: str, mid_scripts: List[Dict]) -> int:
        """Generate mid-workout motivational videos"""
        created_count = 0
        
        limit = min(len(mid_scripts), self.limit or len(mid_scripts))
        
        for i, script_data in enumerate(mid_scripts[:limit]):
            if self.dry_run:
                self.stdout.write(f"  [DRY RUN] Would create mid-workout {i+1} for {archetype}")
                created_count += 1
                continue
            
            with transaction.atomic():
                clip_data = {
                    'r2_kind': VideoKind.MID_WORKOUT,
                    'r2_archetype': archetype,
                    'model_name': f'mid_workout_{i+1}',
                    'script_text': script_data['script'],
                    'provider': VideoProvider.R2,
                    'duration_seconds': random.randint(30, 60),  # Short motivational clips
                    'mood_type': script_data.get('mood_type', 'encouraging'),
                    'content_theme': script_data.get('content_theme', 'motivation'),
                    'position_in_workout': 'mid',
                    'variation_number': i + 1,
                    'is_active': True,
                }
                
                clip = VideoClip.objects.create(**clip_data)
                created_count += 1
                
                self.stdout.write(f"  ✅ Created mid-workout {i+1} for {archetype}: {clip.id}")
        
        return created_count

    def _generate_weekly_content(self, archetype: str, weekly_scripts: List[Dict]) -> int:
        """Generate weekly theme-based videos"""
        created_count = 0
        
        limit = min(len(weekly_scripts), self.limit or len(weekly_scripts))
        
        for i, script_data in enumerate(weekly_scripts[:limit]):
            if self.dry_run:
                self.stdout.write(f"  [DRY RUN] Would create weekly content {i+1} for {archetype}")
                created_count += 1
                continue
            
            with transaction.atomic():
                clip_data = {
                    'r2_kind': VideoKind.THEME_BASED,
                    'r2_archetype': archetype,
                    'model_name': f'weekly_theme_{script_data.get("week_context", i+1)}',
                    'script_text': script_data['script'],
                    'provider': VideoProvider.R2,
                    'duration_seconds': random.randint(120, 180),  # Longer for weekly lessons
                    'content_theme': script_data.get('content_theme', 'weekly_lesson'),
                    'week_context': script_data.get('week_context', i + 1),
                    'is_active': True,
                }
                
                clip = VideoClip.objects.create(**clip_data)
                created_count += 1
                
                self.stdout.write(f"  ✅ Created weekly content week {clip.week_context} for {archetype}: {clip.id}")
        
        return created_count