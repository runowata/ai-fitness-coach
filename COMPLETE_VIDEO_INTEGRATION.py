#!/usr/bin/env python3
"""
Полная интеграция всех типов видео в соответствии с планом тренировок
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.workouts.models import VideoClip, Exercise
from apps.content.models import MediaAsset
from django.db import transaction

# Конфигурация R2
R2_PUBLIC_BASE = 'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev'

def create_motivation_video_clips():
    """
    Создает VideoClip записи для мотивационных видео из CSV данных
    """
    print("\n🎬 Создание VideoClip для мотивационных видео...")
    
    # Intro видео для каждого дня (дни 1-105)
    intro_videos = []
    for day in range(1, 106):  # 15 недель * 7 дней
        for archetype in ['bro', 'sergeant', 'intellectual']:
            intro_videos.append({
                'type': 'intro',
                'archetype': archetype,
                'day_number': day,
                'url': f'{R2_PUBLIC_BASE}/videos/motivation/intro_{archetype}_day{day:02d}.mp4',
                'duration_seconds': 30
            })
    
    # Weekly видео
    weekly_videos = []
    for week in range(1, 9):  # 8 недель
        for archetype in ['bro', 'sergeant', 'intellectual']:
            weekly_videos.append({
                'type': 'weekly',
                'archetype': archetype,
                'week_number': week,
                'url': f'{R2_PUBLIC_BASE}/videos/weekly/weekly_{archetype}_week{week}.mp4',
                'duration_seconds': 180
            })
    
    # Progress видео
    progress_videos = []
    for progress_num in range(1, 4):  # 3 прогресс-видео
        for archetype in ['bro', 'sergeant', 'intellectual']:
            progress_videos.append({
                'type': 'progress',
                'archetype': archetype,
                'progress_number': progress_num,
                'url': f'{R2_PUBLIC_BASE}/videos/progress/progress_{archetype}_{progress_num}.mp4',
                'duration_seconds': 120
            })
    
    # Final видео
    final_videos = []
    for archetype in ['bro', 'sergeant', 'intellectual']:
        final_videos.append({
            'type': 'final',
            'archetype': archetype,
            'url': f'{R2_PUBLIC_BASE}/videos/final/final_{archetype}.mp4',
            'duration_seconds': 240
        })
    
    all_videos = intro_videos + weekly_videos + progress_videos + final_videos
    
    created = 0
    with transaction.atomic():
        for video_data in all_videos:
            # Используем специальную логику для разных типов
            if video_data['type'] == 'intro':
                reminder_text = f"day_{video_data['day_number']}"
            elif video_data['type'] == 'weekly':
                reminder_text = f"week_{video_data['week_number']}"
            elif video_data['type'] == 'progress':
                reminder_text = f"progress_{video_data['progress_number']}"
            else:  # final
                reminder_text = "completion"
            
            video_clip, created_flag = VideoClip.objects.get_or_create(
                exercise=None,  # Мотивационные видео не связаны с упражнениями
                type=video_data['type'],
                archetype=video_data['archetype'],
                model_name='motivation',
                reminder_text=reminder_text,
                defaults={
                    'url': video_data['url'],
                    'duration_seconds': video_data['duration_seconds'],
                    'is_active': True
                }
            )
            
            if created_flag:
                created += 1
                if created % 20 == 0:
                    print(f"  Создано: {created} мотивационных видео...")
    
    print(f"  ✅ Создано {created} новых мотивационных VideoClip")
    return created

def create_media_assets():
    """
    Создает MediaAsset записи для всех типов видео
    """
    print("\n📁 Создание MediaAsset записей...")
    
    media_assets_data = []
    
    # Intro видео
    for day in range(1, 106):
        for archetype in ['bro', 'sergeant', 'intellectual']:
            media_assets_data.append({
                'file_name': f'intro_{archetype}_day{day:02d}.mp4',
                'file_url': f'{R2_PUBLIC_BASE}/videos/motivation/intro_{archetype}_day{day:02d}.mp4',
                'asset_type': 'video',
                'category': 'motivation_intro',
                'archetype': archetype,
                'tags': ['intro', f'day{day}'],
                'file_size': 5 * 1024 * 1024  # 5MB average
            })
    
    # Weekly видео
    for week in range(1, 9):
        for archetype in ['bro', 'sergeant', 'intellectual']:
            media_assets_data.append({
                'file_name': f'weekly_{archetype}_week{week}.mp4',
                'file_url': f'{R2_PUBLIC_BASE}/videos/weekly/weekly_{archetype}_week{week}.mp4',
                'asset_type': 'video',
                'category': 'motivation_weekly',
                'archetype': archetype,
                'tags': ['weekly', f'week{week}'],
                'file_size': 50 * 1024 * 1024  # 50MB average
            })
    
    # Progress видео
    for progress_num in range(1, 4):
        for archetype in ['bro', 'sergeant', 'intellectual']:
            media_assets_data.append({
                'file_name': f'progress_{archetype}_{progress_num}.mp4',
                'file_url': f'{R2_PUBLIC_BASE}/videos/progress/progress_{archetype}_{progress_num}.mp4',
                'asset_type': 'video',
                'category': 'motivation_progress',
                'archetype': archetype,
                'tags': ['progress', f'milestone{progress_num}'],
                'file_size': 40 * 1024 * 1024  # 40MB average
            })
    
    # Final видео
    for archetype in ['bro', 'sergeant', 'intellectual']:
        media_assets_data.append({
            'file_name': f'final_{archetype}.mp4',
            'file_url': f'{R2_PUBLIC_BASE}/videos/final/final_{archetype}.mp4',
            'asset_type': 'video',
            'category': 'motivation_final',
            'archetype': archetype,
            'tags': ['final', 'completion'],
            'file_size': 60 * 1024 * 1024  # 60MB average
        })
    
    created = 0
    with transaction.atomic():
        for asset_data in media_assets_data:
            asset, created_flag = MediaAsset.objects.get_or_create(
                file_name=asset_data['file_name'],
                defaults={
                    'file_url': asset_data['file_url'],
                    'cdn_url': asset_data['file_url'],
                    'file_size': asset_data['file_size'],
                    'asset_type': asset_data['asset_type'],
                    'category': asset_data['category'],
                    'archetype': asset_data['archetype'],
                    'tags': asset_data['tags']
                }
            )
            if created_flag:
                created += 1
                if created % 30 == 0:
                    print(f"  Создано: {created} MediaAsset...")
    
    print(f"  ✅ Создано {created} новых MediaAsset")
    return created

def update_media_asset_categories():
    """
    Обновляет категории MediaAsset для новых типов мотивационных видео
    """
    print("\n🏷️ Обновление категорий MediaAsset...")
    
    # Добавляем новые категории в модель (это нужно сделать в миграции)
    new_categories = [
        ('motivation_intro', 'Daily Intro'),
        ('motivation_progress', 'Progress Milestone'),
    ]
    
    print("  📝 Новые категории для добавления в модель MediaAsset:")
    for category, description in new_categories:
        print(f"    - {category}: {description}")
    
    return True

def main():
    """
    Основная функция интеграции
    """
    print("🚀 ПОЛНАЯ ИНТЕГРАЦИЯ ВИДЕО В ПЛАН ТРЕНИРОВОК")
    print("=" * 55)
    
    print(f"\n📊 Анализ структуры видео:")
    print(f"  🎬 Intro videos: 315 файлов (105 дней × 3 архетипа)")
    print(f"  📅 Weekly videos: 18 файлов (6 недель × 3 архетипа)")  
    print(f"  📈 Progress videos: 9 файлов (3 этапа × 3 архетипа)")
    print(f"  🏆 Final videos: 3 файла (3 архетипа)")
    print(f"  📁 Total motivation videos: 345 файлов")
    
    try:
        # 1. Создаем VideoClip для мотивационных видео
        video_clips_created = create_motivation_video_clips()
        
        # 2. Создаем MediaAsset записи
        media_assets_created = create_media_assets()
        
        # 3. Обновляем категории
        update_media_asset_categories()
        
        print("\n" + "=" * 55)
        print("✅ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!")
        print(f"\n📊 Создано:")
        print(f"   🎬 VideoClip: {video_clips_created}")
        print(f"   📁 MediaAsset: {media_assets_created}")
        
        print(f"\n🎯 Что это дает:")
        print("   🎬 Intro видео показываются в начале каждого дня")
        print("   📅 Weekly видео - в конце недели и дни отдыха")
        print("   📈 Progress видео - каждые 2 недели")
        print("   🏆 Final видео - при завершении программы")
        
        print(f"\n📝 Следующие шаги:")
        print("1. Обновить модель MediaAsset с новыми категориями")
        print("2. Обновить VideoPlaylistBuilder для новых типов")
        print("3. Добавить логику progress видео в WorkoutPlan")
        print("4. Протестировать полный workflow")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()