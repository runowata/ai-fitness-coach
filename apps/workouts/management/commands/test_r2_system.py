"""
Тестирование системы на базе реального R2 хранилища
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.workouts.models import R2Video, R2Image
from collections import defaultdict
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the R2-based system: videos, images, playlists, motivational cards'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-videos',
            action='store_true',
            help='Test video system',
        )
        parser.add_argument(
            '--test-images',
            action='store_true',
            help='Test image system',
        )
        parser.add_argument(
            '--test-playlists',
            action='store_true',
            help='Test playlist generation',
        )
        parser.add_argument(
            '--test-cards',
            action='store_true',
            help='Test motivational cards',
        )
        parser.add_argument(
            '--full-test',
            action='store_true',
            help='Run all tests',
        )

    def handle(self, *args, **options):
        self.stdout.write("🧪 ТЕСТИРОВАНИЕ R2 СИСТЕМЫ...")
        
        if options.get('full_test'):
            options.update({
                'test_videos': True,
                'test_images': True,
                'test_playlists': True,
                'test_cards': True
            })
        
        if options.get('test_videos'):
            self._test_videos()
        
        if options.get('test_images'):
            self._test_images()
            
        if options.get('test_playlists'):
            self._test_playlists()
            
        if options.get('test_cards'):
            self._test_cards()
    
    def _test_videos(self):
        """Тестирует видео систему"""
        self.stdout.write("\n🎬 ТЕСТИРОВАНИЕ ВИДЕО СИСТЕМЫ:")
        self.stdout.write("="*50)
        
        total_videos = R2Video.objects.count()
        self.stdout.write(f"📊 Total videos in DB: {total_videos}")
        
        if total_videos == 0:
            self.stdout.write(self.style.ERROR("❌ No videos found! Run 'load_r2_data' first"))
            return
        
        # Проверяем по категориям
        categories = ['exercises', 'motivation', 'final', 'progress', 'weekly']
        for category in categories:
            count = R2Video.objects.filter(category=category).count()
            self.stdout.write(f"  {category}: {count} videos")
        
        # Проверяем типы упражнений
        self.stdout.write("\n📋 Exercise types:")
        exercise_videos = R2Video.objects.filter(category='exercises')
        
        type_counts = defaultdict(int)
        for video in exercise_videos:
            video_type = video.exercise_type
            type_counts[video_type] += 1
        
        for video_type, count in type_counts.items():
            self.stdout.write(f"  {video_type}: {count} videos")
        
        # Тестируем URL генерацию
        self.stdout.write("\n🌐 Testing URL generation:")
        sample_video = R2Video.objects.first()
        if sample_video:
            self.stdout.write(f"Sample URL: {sample_video.r2_url}")
    
    def _test_images(self):
        """Тестирует систему изображений"""
        self.stdout.write("\n🖼️ ТЕСТИРОВАНИЕ ИЗОБРАЖЕНИЙ:")
        self.stdout.write("="*50)
        
        total_images = R2Image.objects.count()
        self.stdout.write(f"📊 Total images in DB: {total_images}")
        
        if total_images == 0:
            self.stdout.write(self.style.ERROR("❌ No images found! Run 'load_r2_data' first"))
            return
        
        # Проверяем по категориям
        categories = ['avatars', 'quotes', 'progress', 'workout']
        for category in categories:
            count = R2Image.objects.filter(category=category).count()
            self.stdout.write(f"  {category}: {count} images")
        
        # Тестируем URL генерацию
        self.stdout.write("\n🌐 Testing image URLs:")
        for category in categories[:2]:  # Тестируем первые 2 категории
            image = R2Image.objects.filter(category=category).first()
            if image:
                self.stdout.write(f"  {category}: {image.r2_url}")
    
    def _test_playlists(self):
        """Тестирует структуру видео для плейлистов"""
        self.stdout.write("\n🎵 ТЕСТИРОВАНИЕ СТРУКТУРЫ ДЛЯ ПЛЕЙЛИСТОВ:")
        self.stdout.write("="*50)
        
        # Проверяем наличие упражнений
        exercise_count = R2Video.objects.filter(category='exercises').count()
        if exercise_count == 0:
            self.stdout.write(self.style.ERROR("❌ No exercise videos found!"))
            return
        
        # Анализируем типы упражнений
        exercise_types = ['warmup', 'main', 'endurance', 'relaxation']
        type_counts = {}
        
        for ex_type in exercise_types:
            if ex_type == 'warmup':
                count = R2Video.objects.filter(category='exercises', code__startswith='warmup_').count()
            elif ex_type == 'main':
                count = R2Video.objects.filter(category='exercises', code__startswith='main_').count()
            elif ex_type == 'endurance':
                count = R2Video.objects.filter(category='exercises', code__startswith='endurance_').count()
            elif ex_type == 'relaxation':
                count = R2Video.objects.filter(category='exercises', code__startswith='relaxation_').count()
            
            type_counts[ex_type] = count
            self.stdout.write(f"  {ex_type}: {count} videos")
        
        # Проверяем структуру для 21-дневного плейлиста
        self.stdout.write(f"\n🎯 АНАЛИЗ ДЛЯ 21-ДНЕВНОЙ ПРОГРАММЫ:")
        
        # Структура дня: 2 warmup + 8 main + 3 endurance + 3 relaxation = 16 видео/день
        videos_per_day = {'warmup': 2, 'main': 8, 'endurance': 3, 'relaxation': 3}
        total_needed = sum(videos_per_day.values()) * 21  # 21 день
        
        self.stdout.write(f"📋 Структура дня: {videos_per_day}")
        self.stdout.write(f"📊 Всего видео на 21 день: {total_needed}")
        
        # Проверяем достаточность видео
        sufficient = True
        for ex_type, needed_per_day in videos_per_day.items():
            needed_total = needed_per_day * 21
            available = type_counts.get(ex_type, 0)
            
            if available < needed_total:
                self.stdout.write(f"⚠️  {ex_type}: нужно {needed_total}, доступно {available} (повторы будут)")
                sufficient = False
            else:
                self.stdout.write(f"✅ {ex_type}: нужно {needed_total}, доступно {available}")
        
        if sufficient:
            self.stdout.write(f"\n🎉 ДОСТАТОЧНО ВИДЕО ДЛЯ 21-ДНЕВНОЙ ПРОГРАММЫ БЕЗ ПОВТОРОВ!")
        else:
            self.stdout.write(f"\n⚠️  Будут повторы в некоторых категориях")
        
        # Тестируем URL генерацию
        self.stdout.write(f"\n🌐 ТЕСТОВЫЕ URL:")
        for ex_type in exercise_types:
            if ex_type == 'warmup':
                video = R2Video.objects.filter(category='exercises', code__startswith='warmup_').first()
            elif ex_type == 'main':
                video = R2Video.objects.filter(category='exercises', code__startswith='main_').first()
            elif ex_type == 'endurance':
                video = R2Video.objects.filter(category='exercises', code__startswith='endurance_').first()
            elif ex_type == 'relaxation':
                video = R2Video.objects.filter(category='exercises', code__startswith='relaxation_').first()
            
            if video:
                self.stdout.write(f"  {ex_type}: {video.r2_url}")
        
        self.stdout.write(f"\n✅ Playlist structure test completed!")
    
    def _test_cards(self):
        """Тестирует структуру мотивационных карточек"""
        self.stdout.write("\n🎯 ТЕСТИРОВАНИЕ МОТИВАЦИОННЫХ КАРТОЧЕК:")
        self.stdout.write("="*50)
        
        # Проверяем наличие изображений для карточек
        quotes_count = R2Image.objects.filter(category='quotes').count()
        if quotes_count == 0:
            self.stdout.write(self.style.ERROR("❌ No quote images found!"))
            return
        
        self.stdout.write(f"📋 Available quote images: {quotes_count}")
        
        # Проверяем другие категории изображений
        categories = ['avatars', 'progress', 'workout']
        for category in categories:
            count = R2Image.objects.filter(category=category).count()
            self.stdout.write(f"  {category}: {count} images")
        
        # Тестируем случайную выборку карточек
        self.stdout.write("\n🎲 Testing random card selection:")
        
        # Получаем 10 случайных карточек
        random_quotes = R2Image.objects.filter(category='quotes').order_by('?')[:10]
        
        for i, image in enumerate(random_quotes, 1):
            self.stdout.write(f"  Card {i}: {image.code} - {image.name}")
            # Тестируем URL
            url = image.r2_url
            if url:
                self.stdout.write(f"    URL: {url}")
        
        # Проверяем достаточность для сессии онбординга
        needed_for_session = 20  # Примерно столько карточек показывается за сессию
        if quotes_count >= needed_for_session:
            self.stdout.write(f"\n✅ Достаточно карточек для онбординга ({quotes_count} >= {needed_for_session})")
        else:
            self.stdout.write(f"\n⚠️  Может не хватить карточек для онбординга ({quotes_count} < {needed_for_session})")
        
        # Тестируем аватары
        self.stdout.write(f"\n👤 ТЕСТИРОВАНИЕ АВАТАРОВ:")
        avatars = R2Image.objects.filter(category='avatars')[:3]
        
        for avatar in avatars:
            self.stdout.write(f"  Avatar: {avatar.code} - {avatar.r2_url}")
        
        self.stdout.write("\n🎯 Motivational cards test completed!")