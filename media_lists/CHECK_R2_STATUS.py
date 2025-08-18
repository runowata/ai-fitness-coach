#!/usr/bin/env python3
"""
Проверка статуса загрузки в Cloudflare R2
"""

import boto3
from collections import defaultdict
from datetime import datetime

s3 = boto3.client('s3',
    endpoint_url='https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
    aws_access_key_id='3a9fd5a6b38ec994e057e33c1096874e',
    aws_secret_access_key='0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
)

print('🔍 ПРОВЕРКА ЗАГРУЖЕННЫХ ФАЙЛОВ В CLOUDFLARE R2')
print('=' * 50)

# Получаем все объекты
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket='ai-fitness-media')

files_by_category = defaultdict(list)
total_size = 0
total_count = 0

for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            key = obj['Key']
            size = obj['Size']
            total_size += size
            total_count += 1
            
            # Категоризируем
            if key.startswith('videos/exercises/'):
                files_by_category['exercises'].append(key)
            elif key.startswith('videos/motivation/'):
                files_by_category['motivation'].append(key)
            elif key.startswith('videos/weekly/'):
                files_by_category['weekly'].append(key)
            elif key.startswith('videos/progress/'):
                files_by_category['progress'].append(key)
            elif key.startswith('videos/final/'):
                files_by_category['final'].append(key)
            elif key.startswith('images/'):
                files_by_category['images'].append(key)
            else:
                files_by_category['other'].append(key)

# Выводим статистику
print(f'📊 ВСЕГО ФАЙЛОВ: {total_count}')
print(f'💾 ОБЩИЙ РАЗМЕР: {total_size / (1024**3):.2f} GB')
print()

# Детали по категориям видео
video_categories = {
    'exercises': 271,
    'motivation': 315,
    'weekly': 18,
    'progress': 9,
    'final': 3
}

print('📁 ВИДЕО ПО КАТЕГОРИЯМ:')
print('-' * 40)
total_videos = 0
for category, expected in video_categories.items():
    actual = len(files_by_category.get(category, []))
    total_videos += actual
    status = '✅' if actual == expected else '🔄' if actual > 0 else '❌'
    print(f'{status} {category:15} {actual:3}/{expected:3} файлов')

print('-' * 40)
print(f'   ИТОГО ВИДЕО:    {total_videos}/616')

# Проверяем процент загрузки
percent = (total_videos / 616) * 100
print(f'\n📊 ПРОГРЕСС ЗАГРУЗКИ: {percent:.1f}%')

if percent < 100:
    remaining = 616 - total_videos
    print(f'⏳ Осталось загрузить: {remaining} видео')

# Другие файлы
if files_by_category['images']:
    print(f'\n📷 Изображения: {len(files_by_category["images"])} файлов')
    
if files_by_category['other']:
    print(f'\n📄 Другие файлы: {len(files_by_category["other"])} файлов')
    for f in files_by_category['other'][:5]:
        print(f'  - {f}')

# Проверяем конкретные файлы
print('\n🔍 ПРИМЕРЫ ЗАГРУЖЕННЫХ ВИДЕО:')
examples = [
    'videos/exercises/warmup_01_technique_m01.mp4',
    'videos/exercises/main_001_technique_m01.mp4',
    'videos/exercises/endurance_01_technique_m01.mp4',
    'videos/exercises/relaxation_01_technique_m01.mp4',
    'videos/motivation/intro_bro_day01.mp4',
    'videos/weekly/weekly_bro_week1.mp4',
    'videos/progress/progress_bro_1.mp4',
    'videos/final/final_bro.mp4'
]

for example in examples:
    exists = any(f == example for cat in files_by_category.values() for f in cat)
    status = '✅' if exists else '❌'
    category = example.split('/')[1]
    name = example.split('/')[-1]
    print(f'{status} {category:10} {name}')

# Детальная проверка по категориям упражнений
if files_by_category['exercises']:
    print('\n📋 ДЕТАЛИ УПРАЖНЕНИЙ:')
    exercise_types = {'warmup': 0, 'main': 0, 'endurance': 0, 'relaxation': 0}
    
    for file in files_by_category['exercises']:
        filename = file.split('/')[-1]
        for ex_type in exercise_types:
            if filename.startswith(ex_type):
                exercise_types[ex_type] += 1
                break
    
    expected_ex = {'warmup': 42, 'main': 145, 'endurance': 42, 'relaxation': 42}
    for ex_type, count in exercise_types.items():
        expected = expected_ex[ex_type]
        status = '✅' if count == expected else '🔄'
        print(f'  {status} {ex_type:12} {count:3}/{expected:3}')

print('\n' + '=' * 50)
print(f'📝 Отчет создан: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')