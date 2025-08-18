#!/usr/bin/env python3
"""
Очистка дубликатов в папке exercises на Cloudflare R2
"""

import boto3
import pandas as pd
from collections import defaultdict

# Настройки R2
s3 = boto3.client('s3',
    endpoint_url='https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
    aws_access_key_id='3a9fd5a6b38ec994e057e33c1096874e',
    aws_secret_access_key='0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
)

bucket_name = 'ai-fitness-media'

print("🔍 ПОИСК ДУБЛИКАТОВ В EXERCISES")
print("=" * 50)

# 1. Получаем список правильных файлов из CSV
print("\n📋 Загружаем эталонный список...")
df = pd.read_csv('/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv')
correct_files = set()
for _, row in df.iterrows():
    correct_files.add(f"videos/exercises/{row['new_name']}")

print(f"✅ Эталонных файлов: {len(correct_files)}")

# 2. Получаем все файлы из R2
print("\n🌐 Получаем список файлов из R2...")
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket_name, Prefix='videos/exercises/')

all_exercise_files = []
for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            all_exercise_files.append(obj['Key'])

print(f"📁 Всего файлов в exercises: {len(all_exercise_files)}")

# 3. Находим дубликаты
duplicates = []
correct_count = 0

for file_key in all_exercise_files:
    if file_key in correct_files:
        correct_count += 1
    else:
        duplicates.append(file_key)

print(f"\n📊 АНАЛИЗ:")
print(f"  ✅ Правильных файлов: {correct_count}")
print(f"  ❌ Дубликатов/лишних: {len(duplicates)}")

if duplicates:
    print(f"\n🗑️ ФАЙЛЫ К УДАЛЕНИЮ ({len(duplicates)}):")
    
    # Группируем по типу
    by_type = defaultdict(list)
    for dup in duplicates:
        filename = dup.split('/')[-1]
        if filename.startswith('warmup'):
            by_type['warmup'].append(dup)
        elif filename.startswith('main'):
            by_type['main'].append(dup)
        elif filename.startswith('endurance') or filename.startswith('sexual'):
            by_type['endurance/sexual'].append(dup)
        elif filename.startswith('relaxation'):
            by_type['relaxation'].append(dup)
        else:
            by_type['other'].append(dup)
    
    # Показываем примеры
    for file_type, files in by_type.items():
        if files:
            print(f"\n  {file_type}: {len(files)} файлов")
            for f in files[:3]:  # Показываем первые 3
                print(f"    - {f.split('/')[-1]}")
            if len(files) > 3:
                print(f"    ... и еще {len(files) - 3}")
    
    # Спрашиваем подтверждение
    print("\n" + "=" * 50)
    print("⚠️ ВНИМАНИЕ! Будут удалены файлы, которых нет в эталонном списке.")
    print("Это действие необратимо!")
    
    response = input("\n🔄 Удалить дубликаты? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🗑️ Удаление дубликатов...")
        deleted_count = 0
        error_count = 0
        
        for i, file_key in enumerate(duplicates, 1):
            try:
                s3.delete_object(Bucket=bucket_name, Key=file_key)
                deleted_count += 1
                if i % 10 == 0:
                    print(f"  Удалено: {deleted_count}/{len(duplicates)}")
            except Exception as e:
                error_count += 1
                print(f"  ❌ Ошибка удаления {file_key}: {e}")
        
        print(f"\n✅ РЕЗУЛЬТАТ:")
        print(f"  Удалено: {deleted_count} файлов")
        if error_count:
            print(f"  Ошибок: {error_count}")
        
        # Проверяем финальное количество
        print("\n🔍 Проверка после очистки...")
        pages = paginator.paginate(Bucket=bucket_name, Prefix='videos/exercises/')
        final_count = sum(len(page.get('Contents', [])) for page in pages)
        
        print(f"📊 Финальный результат:")
        print(f"  Было: {len(all_exercise_files)} файлов")
        print(f"  Стало: {final_count} файлов")
        print(f"  Должно быть: 271 файлов")
        
        if final_count == 271:
            print("\n🎉 УСПЕХ! Папка exercises содержит ровно 271 файл!")
        else:
            print(f"\n⚠️ Количество файлов не совпадает: {final_count} вместо 271")
    else:
        print("\n❌ Очистка отменена")
else:
    print("\n✅ Дубликатов не найдено!")