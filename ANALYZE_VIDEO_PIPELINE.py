#!/usr/bin/env python3
"""
Полный анализ пайплайна работы с видео в AI Fitness Coach
"""

import os
import sys
import django
import csv
from typing import Dict, List, Set

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.workouts.models import VideoClip, Exercise, WorkoutPlan, DailyWorkout
from apps.content.models import MediaAsset
from django.db.models import Count
import requests

class VideoAnalyzer:
    def __init__(self):
        self.r2_base = 'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev'
        self.analysis_results = {}
        
    def analyze_models_structure(self):
        """Этап 1: Анализ структуры моделей"""
        print("=" * 60)
        print("🔍 ЭТАП 1: АНАЛИЗ СТРУКТУРЫ МОДЕЛЕЙ")
        print("=" * 60)
        
        # VideoClip анализ
        print("\n📹 VideoClip модель:")
        video_types = VideoClip.objects.values('type').annotate(count=Count('type')).order_by('type')
        
        for vtype in video_types:
            print(f"  {vtype['type']}: {vtype['count']} записей")
        
        # По архетипам
        print("\n👥 По архетипам:")
        archetypes = VideoClip.objects.values('archetype').annotate(count=Count('archetype')).order_by('archetype')
        
        for arch in archetypes:
            print(f"  {arch['archetype']}: {arch['count']} видео")
        
        # MediaAsset анализ
        print("\n📁 MediaAsset модель:")
        categories = MediaAsset.objects.values('category').annotate(count=Count('category')).order_by('category')
        
        for cat in categories:
            print(f"  {cat['category']}: {cat['count']} файлов")
        
        # Связи с упражнениями
        print("\n🔗 Связи с упражнениями:")
        exercise_videos = VideoClip.objects.filter(exercise__isnull=False).count()
        motivation_videos = VideoClip.objects.filter(exercise__isnull=True).count()
        
        print(f"  Привязанные к упражнениям: {exercise_videos}")
        print(f"  Мотивационные (без упражнений): {motivation_videos}")
        
        # URL анализ
        print("\n🌐 URL структура:")
        r2_videos = VideoClip.objects.filter(url__contains=self.r2_base).count()
        other_videos = VideoClip.objects.exclude(url__contains=self.r2_base).count()
        
        print(f"  R2 storage URLs: {r2_videos}")
        print(f"  Другие URLs: {other_videos}")
        
        self.analysis_results['models'] = {
            'video_types': dict(video_types.values_list('type', 'count')),
            'archetypes': dict(archetypes.values_list('archetype', 'count')),
            'categories': dict(categories.values_list('category', 'count')),
            'exercise_videos': exercise_videos,
            'motivation_videos': motivation_videos,
            'r2_videos': r2_videos,
            'other_videos': other_videos
        }

    def analyze_video_playlist_builder(self):
        """Этап 2: Анализ VideoPlaylistBuilder"""
        print("\n=" * 60)
        print("🔍 ЭТАП 2: АНАЛИЗ VideoPlaylistBuilder")
        print("=" * 60)
        
        from apps.workouts.services import VideoPlaylistBuilder
        
        print("\n📋 Методы VideoPlaylistBuilder:")
        methods = [method for method in dir(VideoPlaylistBuilder) if not method.startswith('_')]
        for method in methods:
            print(f"  - {method}")
        
        print("\n🎬 Приватные методы (логика видео):")
        private_methods = [method for method in dir(VideoPlaylistBuilder) if method.startswith('_') and 'video' in method]
        for method in private_methods:
            print(f"  - {method}")
        
        # Анализируем каждый приватный метод
        builder = VideoPlaylistBuilder()
        
        print("\n🔍 Анализ методов получения видео:")
        
        # Тестируем intro видео
        try:
            intro_result = builder._get_intro_video(1, 'bro')
            print(f"  _get_intro_video(1, 'bro'): {'✅ работает' if intro_result else '❌ нет данных'}")
        except Exception as e:
            print(f"  _get_intro_video: ❌ ошибка - {e}")
        
        # Тестируем weekly видео
        try:
            weekly_result = builder._get_weekly_motivation_video(1, 'bro')
            print(f"  _get_weekly_motivation_video(1, 'bro'): {'✅ работает' if weekly_result else '❌ нет данных'}")
        except Exception as e:
            print(f"  _get_weekly_motivation_video: ❌ ошибка - {e}")
        
        # Тестируем progress видео
        try:
            progress_result = builder._get_progress_video(2, 'bro')
            print(f"  _get_progress_video(2, 'bro'): {'✅ работает' if progress_result else '❌ нет данных'}")
        except Exception as e:
            print(f"  _get_progress_video: ❌ ошибка - {e}")
        
        # Тестируем final видео
        try:
            final_result = builder._get_final_video('bro')
            print(f"  _get_final_video('bro'): {'✅ работает' if final_result else '❌ нет данных'}")
        except Exception as e:
            print(f"  _get_final_video: ❌ ошибка - {e}")

    def check_r2_correspondence(self):
        """Этап 3: Проверка соответствия с R2 хранилищем"""
        print("\n=" * 60)
        print("🔍 ЭТАП 3: СООТВЕТСТВИЕ С R2 ХРАНИЛИЩЕМ")
        print("=" * 60)
        
        # Читаем CSV файлы
        csv_files = {
            'exercises': '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv',
            'motivation': '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MOTIVATION_345_VIDEOS.csv'
        }
        
        csv_data = {}
        
        for file_type, file_path in csv_files.items():
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    csv_data[file_type] = list(reader)
                print(f"📊 {file_type.upper()}: {len(csv_data[file_type])} записей в CSV")
            else:
                print(f"❌ Файл {file_path} не найден")
                csv_data[file_type] = []
        
        # Сравниваем с базой данных
        print("\n🔍 Сравнение с базой данных:")
        
        if csv_data.get('exercises'):
            # Упражнения
            csv_exercises = {row['exercise_slug'] for row in csv_data['exercises']}
            db_exercises = set(Exercise.objects.values_list('slug', flat=True))
            
            print(f"\n💪 Упражнения:")
            print(f"  CSV: {len(csv_exercises)} упражнений")
            print(f"  БД: {len(db_exercises)} упражнений")
            print(f"  Совпадения: {len(csv_exercises & db_exercises)}")
            print(f"  Только в CSV: {len(csv_exercises - db_exercises)}")
            print(f"  Только в БД: {len(db_exercises - csv_exercises)}")
        
        if csv_data.get('motivation'):
            # Мотивационные видео
            csv_motivation_files = {row['file_name'] for row in csv_data['motivation']}
            db_motivation_files = set(MediaAsset.objects.filter(
                category__startswith='motivation'
            ).values_list('file_name', flat=True))
            
            print(f"\n🎯 Мотивационные видео:")
            print(f"  CSV: {len(csv_motivation_files)} файлов")
            print(f"  БД: {len(db_motivation_files)} файлов")
            print(f"  Совпадения: {len(csv_motivation_files & db_motivation_files)}")
            print(f"  Только в CSV: {len(csv_motivation_files - db_motivation_files)}")
            print(f"  Только в БД: {len(db_motivation_files - csv_motivation_files)}")

    def find_placeholders_and_test_data(self):
        """Этап 4: Поиск заглушек и тестовых данных"""
        print("\n=" * 60)
        print("🔍 ЭТАП 4: ПОИСК ЗАГЛУШЕК И ТЕСТОВЫХ ДАННЫХ")
        print("=" * 60)
        
        # Ищем подозрительные URL
        suspicious_patterns = [
            'test', 'demo', 'placeholder', 'temp', 'example', 'sample', 'mock'
        ]
        
        print("\n🔍 Анализ URL на наличие заглушек:")
        
        for pattern in suspicious_patterns:
            video_count = VideoClip.objects.filter(url__icontains=pattern).count()
            media_count = MediaAsset.objects.filter(file_url__icontains=pattern).count()
            
            if video_count > 0 or media_count > 0:
                print(f"  '{pattern}': VideoClip={video_count}, MediaAsset={media_count}")
        
        # Ищем локальные файлы или некорректные URL
        print("\n🌐 Анализ типов URL:")
        
        # URL не из R2
        non_r2_videos = VideoClip.objects.exclude(url__contains=self.r2_base)[:10]
        if non_r2_videos:
            print(f"\n⚠️ Видео не из R2 хранилища ({non_r2_videos.count()} всего):")
            for video in non_r2_videos:
                print(f"  - {video.type}/{video.archetype}: {video.url[:100]}...")
        
        # Проверяем доступность URL (первые 5)
        print("\n🌍 Проверка доступности URL (тест первых 5):")
        test_videos = VideoClip.objects.filter(url__contains=self.r2_base)[:5]
        
        for video in test_videos:
            try:
                response = requests.head(video.url, timeout=5)
                status = f"✅ {response.status_code}" if response.status_code == 200 else f"❌ {response.status_code}"
                print(f"  {video.type}: {status}")
            except Exception as e:
                print(f"  {video.type}: ❌ ошибка - {str(e)[:50]}...")

    def find_count_mismatches(self):
        """Этап 5: Выявление несоответствий количества"""
        print("\n=" * 60)
        print("🔍 ЭТАП 5: НЕСООТВЕТСТВИЯ КОЛИЧЕСТВА И НАЗВАНИЙ")
        print("=" * 60)
        
        # Ожидаемые количества по типам видео
        expected_counts = {
            'intro': 315,  # 105 дней × 3 архетипа
            'weekly': 24,  # 8 недель × 3 архетипа (изначально было 18)
            'progress': 9,  # 3 этапа × 3 архетипа
            'final': 3,    # 3 архетипа
            'technique': 271,  # По количеству упражнений
            'instruction': 271 * 3 * 3,  # упражнения × архетипы × модели
            'reminder': 271 * 3 * 3,     # упражнения × архетипы × модели
            'mistake': 271  # По количеству упражнений
        }
        
        print("\n📊 Сравнение ожидаемого и фактического количества:")
        print("-" * 60)
        
        for video_type, expected in expected_counts.items():
            actual = VideoClip.objects.filter(type=video_type, is_active=True).count()
            status = "✅" if actual == expected else "❌"
            diff = actual - expected
            diff_str = f"({diff:+d})" if diff != 0 else ""
            
            print(f"  {video_type:12}: {actual:4d} / {expected:4d} {status} {diff_str}")
        
        # Проверяем по архетипам
        print("\n👥 Распределение по архетипам:")
        print("-" * 60)
        
        archetypes = ['bro', 'sergeant', 'intellectual']
        for archetype in archetypes:
            count = VideoClip.objects.filter(archetype=archetype, is_active=True).count()
            print(f"  {archetype:12}: {count:4d} видео")
        
        # Проверяем отсутствующие связи
        print("\n🔗 Проверка связей:")
        print("-" * 60)
        
        exercises_without_videos = Exercise.objects.filter(video_clips__isnull=True).count()
        total_exercises = Exercise.objects.count()
        
        print(f"  Упражнения без видео: {exercises_without_videos} из {total_exercises}")
        
        # Ищем дубликаты
        print("\n🔄 Поиск дубликатов:")
        print("-" * 60)
        
        # Дубликаты URL
        from django.db.models import Count
        duplicate_urls = VideoClip.objects.values('url').annotate(
            count=Count('url')
        ).filter(count__gt=1)
        
        print(f"  Дублирующиеся URL: {duplicate_urls.count()}")
        
        if duplicate_urls.exists():
            print("  Примеры дубликатов:")
            for dup in duplicate_urls[:3]:
                print(f"    {dup['url'][:60]}... ({dup['count']} раз)")

    def generate_final_report(self):
        """Этап 6: Финальный отчет с рекомендациями"""
        print("\n" + "=" * 60)
        print("📋 ФИНАЛЬНЫЙ ОТЧЕТ И РЕКОМЕНДАЦИИ")
        print("=" * 60)
        
        # Подсчитываем общую статистику
        total_videos = VideoClip.objects.count()
        total_media = MediaAsset.objects.count()
        active_videos = VideoClip.objects.filter(is_active=True).count()
        
        print(f"\n📊 Общая статистика:")
        print(f"  Всего VideoClip: {total_videos}")
        print(f"  Активных VideoClip: {active_videos}")
        print(f"  Всего MediaAsset: {total_media}")
        
        # Проблемы и рекомендации
        print(f"\n⚠️ Выявленные проблемы:")
        
        issues = []
        
        # Проверяем критические проблемы
        if VideoClip.objects.filter(type='technique').count() < 100:
            issues.append("Мало видео с техникой выполнения упражнений")
        
        if VideoClip.objects.filter(type='instruction').count() == 0:
            issues.append("Отсутствуют инструкционные видео")
        
        if VideoClip.objects.filter(type='reminder').count() == 0:
            issues.append("Отсутствуют видео-напоминания")
        
        non_r2_count = VideoClip.objects.exclude(url__contains=self.r2_base).count()
        if non_r2_count > 0:
            issues.append(f"{non_r2_count} видео не используют R2 хранилище")
        
        if not issues:
            print("  ✅ Критических проблем не обнаружено")
        else:
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        print(f"\n💡 Рекомендации:")
        print("  1. Создать недостающие видео для упражнений (technique, instruction, reminder)")
        print("  2. Убедиться, что все URL указывают на R2 хранилище")
        print("  3. Проверить доступность всех видео файлов в R2")
        print("  4. Добавить fallback механизмы для отсутствующих видео")
        print("  5. Реализовать автоматическую проверку целостности видео")

def main():
    """Главная функция анализа"""
    print("🚀 ПОЛНЫЙ АНАЛИЗ РАБОТЫ С ВИДЕО В AI FITNESS COACH")
    print("=" * 60)
    
    analyzer = VideoAnalyzer()
    
    try:
        # Выполняем все этапы анализа
        analyzer.analyze_models_structure()
        analyzer.analyze_video_playlist_builder()
        analyzer.check_r2_correspondence()
        analyzer.find_placeholders_and_test_data()
        analyzer.find_count_mismatches()
        analyzer.generate_final_report()
        
        print(f"\n✅ АНАЛИЗ ЗАВЕРШЕН!")
        print("Подробная информация о работе с видео в системе получена.")
        
    except Exception as e:
        print(f"\n❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()