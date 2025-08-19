#!/usr/bin/env python3
"""
Создание тестовых данных для демонстрации работы с Cloudflare R2
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.workouts.models import Exercise, VideoClip
from apps.content.models import MediaAsset
from django.db import transaction

# Конфигурация R2
R2_PUBLIC_BASE = 'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev'

def create_sample_exercises():
    """
    Создает примеры упражнений на основе наших видео
    """
    print("\n💪 Создание примеров упражнений...")
    
    # Примеры упражнений на основе загруженных видео
    exercises_data = [
        {
            'id': 'warmup_01',
            'slug': 'warmup-breathing',
            'name': 'Дыхательная разминка',
            'description': 'Подготовительное дыхательное упражнение',
            'difficulty': 'beginner',
            'muscle_groups': ['breathing'],
            'is_active': True
        },
        {
            'id': 'main_001',
            'slug': 'basic-pushups',
            'name': 'Базовые отжимания',
            'description': 'Классические отжимания для укрепления груди и рук',
            'difficulty': 'beginner',
            'muscle_groups': ['chest', 'arms'],
            'is_active': True
        },
        {
            'id': 'endurance_01',
            'slug': 'cardio-burst',
            'name': 'Кардио взрыв',
            'description': 'Высокоинтенсивное кардио упражнение',
            'difficulty': 'intermediate',
            'muscle_groups': ['cardio'],
            'is_active': True
        },
        {
            'id': 'relaxation_01',
            'slug': 'cool-down-stretch',
            'name': 'Расслабляющая растяжка',
            'description': 'Завершающая растяжка для восстановления',
            'difficulty': 'beginner',
            'muscle_groups': ['flexibility'],
            'is_active': True
        }
    ]
    
    created = 0
    with transaction.atomic():
        for ex_data in exercises_data:
            exercise, created_flag = Exercise.objects.get_or_create(
                id=ex_data['id'],
                defaults=ex_data
            )
            if created_flag:
                created += 1
                print(f"  ✅ Создано: {exercise.name}")
    
    print(f"  📊 Создано {created} новых упражнений")
    return created

def create_sample_video_clips():
    """
    Создает VideoClip записи для наших видео в R2
    """
    print("\n🎬 Создание VideoClip записей...")
    
    # Примеры VideoClip на основе наших загруженных видео
    video_clips_data = [
        # Разминка
        {
            'exercise_id': 'warmup_01',
            'type': 'technique',
            'archetype': 'bro',
            'model_name': 'mod1',
            'url': f'{R2_PUBLIC_BASE}/videos/exercises/warmup_01_technique_m01.mp4',
            'duration_seconds': 45
        },
        # Основное упражнение
        {
            'exercise_id': 'main_001',
            'type': 'technique',
            'archetype': 'bro',
            'model_name': 'mod1',
            'url': f'{R2_PUBLIC_BASE}/videos/exercises/main_001_technique_m01.mp4',
            'duration_seconds': 60
        },
        {
            'exercise_id': 'main_001',
            'type': 'technique',
            'archetype': 'bro',
            'model_name': 'mod2',
            'url': f'{R2_PUBLIC_BASE}/videos/exercises/main_001_technique_m02.mp4',
            'duration_seconds': 60
        },
        # Выносливость
        {
            'exercise_id': 'endurance_01',
            'type': 'technique',
            'archetype': 'bro',
            'model_name': 'mod1',
            'url': f'{R2_PUBLIC_BASE}/videos/exercises/endurance_01_technique_m01.mp4',
            'duration_seconds': 90
        },
        # Расслабление
        {
            'exercise_id': 'relaxation_01',
            'type': 'technique',
            'archetype': 'bro',
            'model_name': 'mod1',
            'url': f'{R2_PUBLIC_BASE}/videos/exercises/relaxation_01_technique_m01.mp4',
            'duration_seconds': 120
        }
    ]
    
    created = 0
    with transaction.atomic():
        for clip_data in video_clips_data:
            try:
                exercise = Exercise.objects.get(id=clip_data['exercise_id'])
                clip, created_flag = VideoClip.objects.get_or_create(
                    exercise=exercise,
                    type=clip_data['type'],
                    archetype=clip_data['archetype'],
                    model_name=clip_data['model_name'],
                    defaults={
                        'url': clip_data['url'],
                        'duration_seconds': clip_data['duration_seconds'],
                        'is_active': True
                    }
                )
                if created_flag:
                    created += 1
                    print(f"  ✅ Создано: {exercise.name} - {clip_data['type']} ({clip_data['model_name']})")
            except Exercise.DoesNotExist:
                print(f"  ⚠️ Упражнение {clip_data['exercise_id']} не найдено")
    
    print(f"  📊 Создано {created} новых VideoClip")
    return created

def create_sample_media_assets():
    """
    Создает MediaAsset записи для мотивационных видео
    """
    print("\n🎭 Создание MediaAsset записей...")
    
    # Примеры MediaAsset для мотивационных видео
    media_assets_data = [
        {
            'file_name': 'intro_bro_day01.mp4',
            'file_url': f'{R2_PUBLIC_BASE}/videos/motivation/intro_bro_day01.mp4',
            'asset_type': 'video',
            'category': 'motivation_intro',
            'archetype': 'bro',
            'tags': ['intro', 'day1']
        },
        {
            'file_name': 'weekly_bro_week1.mp4',
            'file_url': f'{R2_PUBLIC_BASE}/videos/weekly/weekly_bro_week1.mp4',
            'asset_type': 'video',
            'category': 'motivation_weekly',
            'archetype': 'bro',
            'tags': ['weekly', 'week1']
        },
        {
            'file_name': 'progress_bro_check1.mp4',
            'file_url': f'{R2_PUBLIC_BASE}/videos/progress/progress_bro_check1.mp4',
            'asset_type': 'video',
            'category': 'motivation_progress',
            'archetype': 'bro',
            'tags': ['progress', 'check1']
        },
        {
            'file_name': 'final_bro_congratulations.mp4',
            'file_url': f'{R2_PUBLIC_BASE}/videos/final/final_bro_congratulations.mp4',
            'asset_type': 'video',
            'category': 'motivation_final',
            'archetype': 'bro',
            'tags': ['final', 'congratulations']
        }
    ]
    
    created = 0
    with transaction.atomic():
        for asset_data in media_assets_data:
            asset, created_flag = MediaAsset.objects.get_or_create(
                file_name=asset_data['file_name'],
                defaults={
                    'file_url': asset_data['file_url'],
                    'cdn_url': asset_data['file_url'],  # Используем тот же URL для CDN
                    'file_size': 1024 * 1024,  # Примерный размер 1MB
                    'asset_type': asset_data['asset_type'],
                    'category': asset_data['category'],
                    'archetype': asset_data['archetype'],
                    'tags': asset_data['tags']
                }
            )
            if created_flag:
                created += 1
                print(f"  ✅ Создано: {asset_data['file_name']}")
    
    print(f"  📊 Создано {created} новых MediaAsset")
    return created

def verify_r2_urls():
    """
    Проверяет доступность созданных URL
    """
    print("\n🔍 Проверка созданных URL...")
    
    # Проверяем VideoClip URL
    video_clips = VideoClip.objects.all()[:3]
    for clip in video_clips:
        try:
            import requests
            response = requests.head(clip.url, timeout=5)
            status = "✅ доступен" if response.status_code == 200 else f"❌ код {response.status_code}"
            print(f"  {clip.url.split('/')[-1]} - {status}")
        except Exception as e:
            print(f"  {clip.url.split('/')[-1]} - ❌ ошибка: {str(e)[:50]}")
    
    # Проверяем MediaAsset URL
    media_assets = MediaAsset.objects.all()[:3]
    for asset in media_assets:
        try:
            import requests
            response = requests.head(asset.file_url, timeout=5)
            status = "✅ доступен" if response.status_code == 200 else f"❌ код {response.status_code}"
            print(f"  {asset.file_name} - {status}")
        except Exception as e:
            print(f"  {asset.file_name} - ❌ ошибка: {str(e)[:50]}")

def main():
    """
    Основная функция
    """
    print("🚀 СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ AI FITNESS COACH")
    print("=" * 55)
    
    try:
        exercises_created = create_sample_exercises()
        clips_created = create_sample_video_clips()
        assets_created = create_sample_media_assets()
        
        print("\n" + "=" * 55)
        print("✅ СОЗДАНИЕ ДАННЫХ ЗАВЕРШЕНО!")
        print(f"\n📊 Статистика:")
        print(f"   💪 Упражнения: {exercises_created}")
        print(f"   🎬 VideoClip: {clips_created}")
        print(f"   🎭 MediaAsset: {assets_created}")
        
        # Проверяем URL
        verify_r2_urls()
        
        print("\n🎯 Следующие шаги:")
        print("1. Запустите Django сервер: python manage.py runserver")
        print("2. Создайте суперпользователя: python manage.py createsuperuser")
        print("3. Проверьте админ панель: /admin/")
        print("4. Протестируйте видео в приложении")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()