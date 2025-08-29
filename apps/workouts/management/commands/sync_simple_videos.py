"""
Management command для синхронизации упрощенной модели видео с R2 хранилищем
"""
import requests
from django.core.management.base import BaseCommand
from apps.workouts.models_simple import Video, ArchetypeType


class Command(BaseCommand):
    help = 'Синхронизация упрощенной модели видео с данными из R2 хранилища'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет создано, не создавать записи',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать все записи (очистить и загрузить заново)',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔄 Синхронизация упрощенной модели видео...")
        
        if options['force']:
            Video.objects.all().delete()
            self.stdout.write("🗑️ Удалены все существующие записи Video")
        
        # Определяем структуру видео согласно идеальному плейлисту
        video_data = self.get_video_structure()
        
        created_count = 0
        for video_info in video_data:
            if not options['dry_run']:
                video, created = Video.objects.get_or_create(
                    code=video_info['code'],
                    defaults=video_info
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"✅ Создано: {video}")
                else:
                    self.stdout.write(f"⏭️ Уже существует: {video}")
            else:
                self.stdout.write(f"🔍 Будет создано: {video_info['code']} - {video_info['name']}")
        
        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Создано {created_count} новых видео записей")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"🔍 DRY RUN: Будет создано {len(video_data)} записей")
            )

    def get_video_structure(self):
        """Возвращает структуру всех видео согласно идеальному плейлисту"""
        videos = []
        
        # 1. УПРАЖНЕНИЯ (Модель) - без привязки к архетипу
        exercise_types = [
            ('warmup', 'Разминка', 20),  # Достаточно упражнений для 3 недель
            ('main', 'Основные упражнения', 100),  # Много основных упражнений 
            ('endurance', 'Сексуальная выносливость', 30),
            ('relaxation', 'Расслабление', 30),
        ]
        
        for video_type, type_name, count in exercise_types:
            for i in range(1, count + 1):
                videos.append({
                    'code': f'{video_type}_{i:03d}',
                    'name': f'{type_name} упражнение {i}',
                    'description': f'Видео упражнения {type_name.lower()} #{i}',
                    'video_type': video_type,
                    'archetype': '',  # Упражнения не привязаны к архетипу
                    'sequence_number': i,
                    'is_active': True
                })
        
        # 2. МОТИВАЦИОННЫЕ ВИДЕО (Тренер) - для каждого архетипа и каждого дня
        motivational_types = [
            'intro',
            'warmup_motivation', 
            'main_motivation',
            'trainer_speech',
            'closing'
        ]
        
        # Для каждого архетипа создаем мотивационные видео на каждый день (1-21)
        for archetype_code, archetype_display in ArchetypeType.choices:
            for day in range(1, 22):  # Дни 1-21
                for video_type in motivational_types:
                    videos.append({
                        'code': f'{video_type}_{archetype_code}_day{day:02d}',
                        'name': f'{video_type.replace("_", " ").title()} - День {day}',
                        'description': f'Мотивационное видео {archetype_display} для дня {day}',
                        'video_type': video_type,
                        'archetype': archetype_code,
                        'sequence_number': day,
                        'is_active': True
                    })
        
        return videos

    def test_r2_access(self):
        """Тестирует доступ к R2 хранилищу"""
        self.stdout.write("🔗 Тестирование доступа к R2...")
        
        base_url = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
        test_urls = [
            f"{base_url}/videos/exercises/warmup_001.mp4",
            f"{base_url}/videos/motivation/intro_bro_day01.mp4"
        ]
        
        for url in test_urls:
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    self.stdout.write(f"✅ Доступно: {url}")
                else:
                    self.stdout.write(f"❌ Недоступно ({response.status_code}): {url}")
            except Exception as e:
                self.stdout.write(f"❌ Ошибка доступа к {url}: {e}")