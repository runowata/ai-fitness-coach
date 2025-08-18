#!/usr/bin/env python3
"""
Загрузка видеофайлов на Cloudflare R2 Storage
"""

import os
import boto3
import pandas as pd
from datetime import datetime
from botocore.config import Config
import hashlib
import time
import concurrent.futures
from pathlib import Path

# Конфигурация Cloudflare R2
CLOUDFLARE_R2_CONFIG = {
    'endpoint_url': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
    'bucket_name': 'ai-fitness-media',
    'public_base': 'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev',
    'region': 'auto',
    'access_key_id': '3a9fd5a6b38ec994e057e33c1096874e',
    'secret_access_key': '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
}

def check_cloudflare_credentials():
    """Проверить наличие учетных данных Cloudflare R2"""
    
    print("🔑 Проверка учетных данных Cloudflare R2...")
    
    # Используем встроенные учетные данные
    access_key = CLOUDFLARE_R2_CONFIG['access_key_id']
    secret_key = CLOUDFLARE_R2_CONFIG['secret_access_key']
    
    if not access_key or not secret_key:
        print("❌ Учетные данные Cloudflare R2 не найдены!")
        return False
    
    print("✅ Учетные данные найдены")
    print(f"📡 Endpoint: {CLOUDFLARE_R2_CONFIG['endpoint_url']}")
    print(f"🪣 Bucket: {CLOUDFLARE_R2_CONFIG['bucket_name']}")
    print(f"🌐 Public URL: {CLOUDFLARE_R2_CONFIG['public_base']}")
    return True

def create_r2_client():
    """Создать клиент для подключения к Cloudflare R2"""
    
    try:
        s3_config = Config(
            region_name='auto',
            signature_version='s3v4',
            s3={
                'addressing_style': 'path'
            }
        )
        
        s3_client = boto3.client(
            's3',
            endpoint_url=CLOUDFLARE_R2_CONFIG['endpoint_url'],
            aws_access_key_id=CLOUDFLARE_R2_CONFIG['access_key_id'],
            aws_secret_access_key=CLOUDFLARE_R2_CONFIG['secret_access_key'],
            config=s3_config
        )
        
        # Тестируем подключение - пробуем список объектов вместо head_bucket
        try:
            response = s3_client.list_objects_v2(Bucket=CLOUDFLARE_R2_CONFIG['bucket_name'], MaxKeys=1)
            print("✅ Подключение к Cloudflare R2 успешно")
        except Exception as list_error:
            print(f"⚠️ Предупреждение при тестировании: {list_error}")
            print("🔄 Продолжаем с существующим подключением...")
        
        return s3_client
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Cloudflare R2: {e}")
        return None

def get_video_files_info():
    """Получить информацию о видеофайлах для загрузки"""
    
    print("📋 Загрузка информации о видеофайлах...")
    
    files_info = {
        'exercises': [],
        'motivation': [],
        'weekly': [],
        'progress': [],
        'final': []
    }
    
    # Загружаем информацию из CSV файлов
    csv_files = {
        'exercises': '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv',
        'motivation': '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MOTIVATIONAL_345_VIDEOS.csv'
    }
    
    # Упражнения
    try:
        df = pd.read_csv(csv_files['exercises'])
        for _, row in df.iterrows():
            files_info['exercises'].append({
                'local_path': row['target_path'],
                'cloudflare_key': f"videos/exercises/{row['new_name']}",
                'cloudflare_url': row['cloudflare_url'],
                'size_mb': row['size_mb'],
                'filename': row['new_name']
            })
        print(f"✅ Exercises: {len(files_info['exercises'])} файлов")
    except Exception as e:
        print(f"❌ Ошибка загрузки exercises: {e}")
    
    # Мотивационные
    try:
        df = pd.read_csv(csv_files['motivation'])
        for _, row in df.iterrows():
            # Определяем категорию по пути
            path_parts = row['target_path'].split('/')
            if 'motivation' in path_parts:
                category = 'motivation'
            elif 'weekly' in path_parts:
                category = 'weekly'
            elif 'progress' in path_parts:
                category = 'progress'
            elif 'final' in path_parts:
                category = 'final'
            else:
                category = 'motivation'
            
            files_info[category].append({
                'local_path': row['target_path'],
                'cloudflare_key': f"videos/{category}/{row['new_name']}",
                'cloudflare_url': row['cloudflare_url'],
                'size_mb': row['size_mb'],
                'filename': row['new_name']
            })
        
        print(f"✅ Motivation: {len(files_info['motivation'])} файлов")
        print(f"✅ Weekly: {len(files_info['weekly'])} файлов")
        print(f"✅ Progress: {len(files_info['progress'])} файлов")
        print(f"✅ Final: {len(files_info['final'])} файлов")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки motivational: {e}")
    
    total_files = sum(len(files_info[category]) for category in files_info)
    total_size = sum(
        sum(file['size_mb'] for file in files_info[category]) 
        for category in files_info
    )
    
    print(f"📊 Всего к загрузке: {total_files} файлов ({total_size:.1f} МБ)")
    
    return files_info

def upload_file_to_r2(s3_client, file_info, progress_callback=None):
    """Загрузить один файл на R2"""
    
    try:
        local_path = file_info['local_path']
        cloudflare_key = file_info['cloudflare_key']
        filename = file_info['filename']
        
        # Проверяем существование файла
        if not os.path.exists(local_path):
            return {
                'status': 'error',
                'filename': filename,
                'error': f'Файл не найден: {local_path}'
            }
        
        # Получаем размер файла
        file_size = os.path.getsize(local_path)
        
        # Загружаем файл
        start_time = time.time()
        
        s3_client.upload_file(
            local_path,
            CLOUDFLARE_R2_CONFIG['bucket_name'],
            cloudflare_key,
            ExtraArgs={
                'ContentType': 'video/mp4',
                'CacheControl': 'max-age=31536000',  # 1 год
                'Metadata': {
                    'original-filename': filename,
                    'upload-date': datetime.now().isoformat()
                }
            }
        )
        
        upload_time = time.time() - start_time
        
        if progress_callback:
            progress_callback(filename, 'success')
        
        return {
            'status': 'success',
            'filename': filename,
            'cloudflare_key': cloudflare_key,
            'size_bytes': file_size,
            'upload_time': upload_time,
            'speed_mbps': (file_size / 1024 / 1024) / upload_time if upload_time > 0 else 0
        }
        
    except Exception as e:
        if progress_callback:
            progress_callback(filename, 'error')
        
        return {
            'status': 'error',
            'filename': filename,
            'error': str(e)
        }

def upload_category_parallel(s3_client, category_files, category_name, max_workers=3):
    """Загрузить файлы категории параллельно"""
    
    print(f"\n🔄 Загрузка {category_name}: {len(category_files)} файлов...")
    
    results = []
    uploaded = 0
    errors = 0
    
    def progress_callback(filename, status):
        nonlocal uploaded, errors
        if status == 'success':
            uploaded += 1
        else:
            errors += 1
        print(f"  {uploaded + errors:3d}/{len(category_files)}: {filename} {'✅' if status == 'success' else '❌'}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(upload_file_to_r2, s3_client, file_info, progress_callback): file_info
            for file_info in category_files
        }
        
        for future in concurrent.futures.as_completed(future_to_file):
            result = future.result()
            results.append(result)
    
    print(f"✅ {category_name}: {uploaded} успешно, {errors} ошибок")
    
    return results

def generate_upload_report(all_results, start_time, end_time):
    """Создать отчет о загрузке"""
    
    total_files = sum(len(results) for results in all_results.values())
    successful = sum(
        len([r for r in results if r['status'] == 'success']) 
        for results in all_results.values()
    )
    failed = total_files - successful
    
    total_size_mb = sum(
        sum(r.get('size_bytes', 0) for r in results if r['status'] == 'success') 
        for results in all_results.values()
    ) / 1024 / 1024
    
    upload_duration = end_time - start_time
    
    report = f"""# 🌐 ОТЧЕТ О ЗАГРУЗКЕ НА CLOUDFLARE R2

## Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 СВОДКА:

### Общие результаты:
- **Всего файлов**: {total_files}
- **Успешно загружено**: {successful} ✅
- **Ошибок**: {failed} ❌
- **Процент успеха**: {(successful/total_files*100):.1f}%
- **Общий размер**: {total_size_mb:.1f} МБ
- **Время загрузки**: {upload_duration/60:.1f} минут
- **Средняя скорость**: {total_size_mb/(upload_duration/60):.1f} МБ/мин

---

## 📁 РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ:

"""
    
    for category, results in all_results.items():
        successful_cat = len([r for r in results if r['status'] == 'success'])
        failed_cat = len([r for r in results if r['status'] == 'error'])
        total_cat = len(results)
        
        if total_cat > 0:
            size_cat = sum(r.get('size_bytes', 0) for r in results if r['status'] == 'success') / 1024 / 1024
            
            report += f"""### {category.title()}:
- Файлов: {total_cat}
- Успешно: {successful_cat} ✅
- Ошибок: {failed_cat} ❌
- Размер: {size_cat:.1f} МБ

"""
    
    report += """---

## 🔗 CLOUDFLARE R2 URLS:

### Базовый URL:
```
https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev
```

### Структура файлов:
```
/videos/exercises/warmup_01_technique_m01.mp4
/videos/exercises/main_001_technique_m01.mp4
/videos/exercises/endurance_01_technique_m01.mp4
/videos/exercises/relaxation_01_technique_m01.mp4
/videos/motivation/intro_bro_m01.mp4
/videos/weekly/weekly_bro_week01.mp4
/videos/progress/progress_bro_week02.mp4
/videos/final/final_bro.mp4
```

---

## ❌ ОШИБКИ ЗАГРУЗКИ:

"""
    
    error_count = 0
    for category, results in all_results.items():
        for result in results:
            if result['status'] == 'error':
                error_count += 1
                report += f"- `{result['filename']}` ({category}): {result.get('error', 'Неизвестная ошибка')}\n"
    
    if error_count == 0:
        report += "Ошибок не было.\n"
    
    report += f"""
---

## 🎯 СЛЕДУЮЩИЕ ШАГИ:

1. ✅ Проверить доступность файлов по URL
2. ✅ Обновить Django модели MediaAsset
3. ✅ Настроить CDN кеширование
4. ✅ Обновить frontend для использования R2 URLs

---

## 🎉 СТАТУС:

"""
    
    if failed == 0:
        report += "**🎉 ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!**\n\n"
        report += "Все 616 видеофайлов успешно загружены на Cloudflare R2.\n"
        report += "Система готова к использованию с CDN.\n"
    else:
        report += "**⚠️ ЗАГРУЗКА ЗАВЕРШЕНА С ОШИБКАМИ**\n\n"
        report += f"Успешно загружено {successful} из {total_files} файлов.\n"
        report += f"Требуется повторная загрузка {failed} файлов.\n"
    
    return report

def main():
    """Основная функция загрузки"""
    
    print("🌐 ЗАГРУЗКА ВИДЕО НА CLOUDFLARE R2")
    print("=" * 60)
    
    # 1. Проверяем учетные данные
    print("\n🔑 Шаг 1: Проверка учетных данных...")
    if not check_cloudflare_credentials():
        print("❌ Настройте учетные данные и запустите снова")
        return
    
    # 2. Создаем клиент R2
    print("\n🔗 Шаг 2: Подключение к Cloudflare R2...")
    s3_client = create_r2_client()
    
    if not s3_client:
        print("❌ Не удалось подключиться к Cloudflare R2")
        return
    
    # 3. Получаем информацию о файлах
    print("\n📋 Шаг 3: Подготовка списка файлов...")
    files_info = get_video_files_info()
    
    if not any(files_info.values()):
        print("❌ Файлы для загрузки не найдены")
        return
    
    # 4. Загружаем файлы по категориям
    print("\n🚀 Шаг 4: Загрузка файлов...")
    start_time = time.time()
    
    all_results = {}
    
    # Порядок загрузки: exercises, motivation, weekly, progress, final
    upload_order = ['exercises', 'motivation', 'weekly', 'progress', 'final']
    
    for category in upload_order:
        if files_info[category]:
            results = upload_category_parallel(s3_client, files_info[category], category)
            all_results[category] = results
    
    end_time = time.time()
    
    # 5. Создаем отчет
    print("\n📄 Шаг 5: Создание отчета...")
    report = generate_upload_report(all_results, start_time, end_time)
    
    # Сохраняем отчет
    report_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/CLOUDFLARE_R2_UPLOAD_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Отчет сохранен: {report_file}")
    
    # Итог
    total_files = sum(len(results) for results in all_results.values())
    successful = sum(
        len([r for r in results if r['status'] == 'success']) 
        for results in all_results.values()
    )
    failed = total_files - successful
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("🎉 ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!")
        print(f"✅ Загружено: {successful} файлов")
        print("🌐 Все видео доступны на Cloudflare R2")
    else:
        print("⚠️ ЗАГРУЗКА ЗАВЕРШЕНА С ОШИБКАМИ")
        print(f"✅ Успешно: {successful} файлов")
        print(f"❌ Ошибок: {failed} файлов")
        print("📄 Проверьте отчет для деталей")

if __name__ == '__main__':
    main()