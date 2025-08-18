#!/usr/bin/env python3
"""
Скрипт для обновления всех видео URL в системе на Cloudflare R2
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

# Конфигурация Cloudflare R2
R2_CONFIG = {
    'private_endpoint': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
    'public_base': 'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev',
    'bucket': 'ai-fitness-media'
}

def convert_to_r2_url(old_url):
    """
    Конвертирует старый URL в новый Cloudflare R2 URL
    """
    if not old_url:
        return old_url
    
    # Если это уже R2 URL, ничего не делаем
    if R2_CONFIG['public_base'] in old_url:
        return old_url
    
    # Если это приватный R2 endpoint, меняем на публичный
    if R2_CONFIG['private_endpoint'] in old_url:
        return old_url.replace(R2_CONFIG['private_endpoint'], R2_CONFIG['public_base'])
    
    # Извлекаем путь к файлу
    if 'videos/' in old_url:
        # Находим путь начиная с videos/
        video_path = old_url[old_url.find('videos/'):]
        return f"{R2_CONFIG['public_base']}/{video_path}"
    
    # Для локальных URL (/media/...)
    if old_url.startswith('/media/'):
        path = old_url.replace('/media/', '')
        return f"{R2_CONFIG['public_base']}/{path}"
    
    # Для S3 URL
    if 's3.amazonaws.com' in old_url:
        # Извлекаем путь после media/
        if '/media/' in old_url:
            path = old_url.split('/media/')[-1]
        else:
            path = old_url.split('.com/')[-1]
        return f"{R2_CONFIG['public_base']}/{path}"
    
    # Если не можем определить формат, возвращаем как есть
    print(f"  ⚠️ Не могу конвертировать URL: {old_url}")
    return old_url

def update_video_clips():
    """
    Обновляет URL в VideoClip
    """
    print("\n📹 Обновление VideoClip...")
    
    clips = VideoClip.objects.all()
    total = clips.count()
    
    if total == 0:
        print("  Нет записей VideoClip")
        return
    
    updated = 0
    with transaction.atomic():
        for clip in clips:
            old_url = clip.url
            new_url = convert_to_r2_url(old_url)
            
            if old_url != new_url:
                clip.url = new_url
                clip.save(update_fields=['url'])
                updated += 1
                
                if updated % 10 == 0:
                    print(f"  Обновлено: {updated}/{total}")
    
    print(f"  ✅ Обновлено {updated} из {total} записей")

def update_exercises():
    """
    Обновляет видео URL в Exercise
    """
    print("\n🏋️ Обновление Exercise...")
    
    exercises = Exercise.objects.all()
    total = exercises.count()
    
    if total == 0:
        print("  Нет записей Exercise")
        return
    
    updated = 0
    with transaction.atomic():
        for exercise in exercises:
            changed = False
            
            # Обновляем technique_video_url
            if exercise.technique_video_url:
                old_url = exercise.technique_video_url
                new_url = convert_to_r2_url(old_url)
                if old_url != new_url:
                    exercise.technique_video_url = new_url
                    changed = True
            
            # Обновляем mistake_video_url
            if exercise.mistake_video_url:
                old_url = exercise.mistake_video_url
                new_url = convert_to_r2_url(old_url)
                if old_url != new_url:
                    exercise.mistake_video_url = new_url
                    changed = True
            
            if changed:
                exercise.save(update_fields=['technique_video_url', 'mistake_video_url'])
                updated += 1
                
                if updated % 10 == 0:
                    print(f"  Обновлено: {updated}/{total}")
    
    print(f"  ✅ Обновлено {updated} из {total} записей")

def update_media_assets():
    """
    Обновляет URL в MediaAsset
    """
    print("\n🎬 Обновление MediaAsset...")
    
    assets = MediaAsset.objects.filter(asset_type='video')
    total = assets.count()
    
    if total == 0:
        print("  Нет видео в MediaAsset")
        return
    
    updated = 0
    with transaction.atomic():
        for asset in assets:
            changed = False
            
            # Обновляем file_url
            old_file_url = asset.file_url
            new_file_url = convert_to_r2_url(old_file_url)
            if old_file_url != new_file_url:
                asset.file_url = new_file_url
                changed = True
            
            # Устанавливаем cdn_url если его нет
            if not asset.cdn_url or asset.cdn_url != new_file_url:
                asset.cdn_url = new_file_url
                changed = True
            
            if changed:
                asset.save(update_fields=['file_url', 'cdn_url'])
                updated += 1
                
                if updated % 10 == 0:
                    print(f"  Обновлено: {updated}/{total}")
    
    print(f"  ✅ Обновлено {updated} из {total} записей")

def update_settings():
    """
    Показывает, какие настройки нужно обновить в settings.py
    """
    print("\n⚙️ Рекомендуемые изменения в settings.py:")
    print("""
# Cloudflare R2 Configuration
USE_R2_STORAGE = os.getenv('USE_R2_STORAGE', 'True') == 'True'

if USE_R2_STORAGE:
    R2_ENDPOINT = os.getenv('R2_ENDPOINT', 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com')
    R2_PUBLIC_BASE = os.getenv('R2_PUBLIC_BASE', 'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev')
    R2_BUCKET = os.getenv('R2_BUCKET', 'ai-fitness-media')
    
    # Override MEDIA_URL for R2
    MEDIA_URL = f'{R2_PUBLIC_BASE}/'
    
    # Video base URLs
    VIDEO_BASE_URL = f'{R2_PUBLIC_BASE}/videos/'
else:
    # Fallback to local or S3
    if DEBUG:
        MEDIA_URL = '/media/'
    else:
        AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
        AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
""")

def verify_urls():
    """
    Проверяет несколько URL для подтверждения
    """
    print("\n🔍 Проверка примеров URL...")
    
    test_urls = [
        'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev/videos/exercises/warmup_01_technique_m01.mp4',
        'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev/videos/motivation/intro_bro_day01.mp4',
        'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev/videos/weekly/weekly_bro_week1.mp4'
    ]
    
    import requests
    
    for url in test_urls:
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {url.split('/')[-1]} - доступен")
            else:
                print(f"  ❌ {url.split('/')[-1]} - код {response.status_code}")
        except Exception as e:
            print(f"  ❌ {url.split('/')[-1]} - ошибка: {e}")

def main():
    """
    Основная функция
    """
    print("🔄 ОБНОВЛЕНИЕ ВИДЕО URL НА CLOUDFLARE R2")
    print("=" * 50)
    
    # Проверяем доступность R2
    print("\n🌐 Проверка доступности Cloudflare R2...")
    verify_urls()
    
    # Обновляем базу данных
    print("\n📊 Обновление базы данных...")
    
    try:
        update_video_clips()
    except Exception as e:
        print(f"  ❌ Ошибка обновления VideoClip: {e}")
    
    try:
        update_exercises()
    except Exception as e:
        print(f"  ❌ Ошибка обновления Exercise: {e}")
    
    try:
        update_media_assets()
    except Exception as e:
        print(f"  ❌ Ошибка обновления MediaAsset: {e}")
    
    # Показываем рекомендации по настройкам
    update_settings()
    
    print("\n" + "=" * 50)
    print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print("\nСледующие шаги:")
    print("1. Обновите settings.py согласно рекомендациям выше")
    print("2. Перезапустите Django сервер")
    print("3. Проверьте воспроизведение видео в приложении")

if __name__ == "__main__":
    main()