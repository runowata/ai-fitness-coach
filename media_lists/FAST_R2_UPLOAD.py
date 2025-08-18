#!/usr/bin/env python3
"""
Быстрая загрузка видео на Cloudflare R2
"""

import boto3
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Конфигурация
config = {
    'access_key': '3a9fd5a6b38ec994e057e33c1096874e',
    'secret_key': '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13',
    'endpoint': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
    'bucket': 'ai-fitness-media'
}

def create_s3_client():
    return boto3.client(
        's3',
        endpoint_url=config['endpoint'],
        aws_access_key_id=config['access_key'],
        aws_secret_access_key=config['secret_key']
    )

def upload_single_file(file_info, progress_counter):
    try:
        s3_client = create_s3_client()
        local_path = file_info['local_path']
        s3_key = file_info['s3_key']
        
        if not os.path.exists(local_path):
            return {'status': 'error', 'file': s3_key, 'error': 'File not found'}
        
        # Загружаем
        s3_client.upload_file(
            local_path,
            config['bucket'],
            s3_key,
            ExtraArgs={'ContentType': 'video/mp4'}
        )
        
        progress_counter[0] += 1
        return {'status': 'success', 'file': s3_key}
        
    except Exception as e:
        return {'status': 'error', 'file': s3_key, 'error': str(e)}

def get_upload_list():
    files_to_upload = []
    
    # Exercises
    try:
        df = pd.read_csv('/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv')
        for _, row in df.iterrows():
            files_to_upload.append({
                'local_path': row['target_path'],
                's3_key': f"videos/exercises/{row['new_name']}"
            })
    except Exception as e:
        print(f"Ошибка загрузки exercises CSV: {e}")
    
    # Motivational
    try:
        df = pd.read_csv('/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MOTIVATIONAL_345_VIDEOS.csv')
        for _, row in df.iterrows():
            # Определяем категорию по пути
            if '/motivation/' in row['target_path']:
                category = 'motivation'
            elif '/weekly/' in row['target_path']:
                category = 'weekly'
            elif '/progress/' in row['target_path']:
                category = 'progress'
            elif '/final/' in row['target_path']:
                category = 'final'
            else:
                category = 'motivation'
            
            files_to_upload.append({
                'local_path': row['target_path'],
                's3_key': f"videos/{category}/{row['new_name']}"
            })
    except Exception as e:
        print(f"Ошибка загрузки motivational CSV: {e}")
    
    return files_to_upload

def main():
    print("🚀 БЫСТРАЯ ЗАГРУЗКА НА CLOUDFLARE R2")
    print("=" * 50)
    
    # Получаем список файлов
    files_to_upload = get_upload_list()
    total_files = len(files_to_upload)
    print(f"📊 Файлов к загрузке: {total_files}")
    
    if total_files == 0:
        print("❌ Нет файлов для загрузки")
        return
    
    # Прогресс-счетчик
    progress_counter = [0]  # Используем список для изменяемости
    start_time = time.time()
    
    print(f"\n🔄 Загружаем {total_files} файлов...")
    print("Прогресс:")
    
    # Загружаем параллельно
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(upload_single_file, file_info, progress_counter): file_info
            for file_info in files_to_upload
        }
        
        results = {'success': 0, 'error': 0, 'errors': []}
        
        for future in as_completed(futures):
            result = future.result()
            
            if result['status'] == 'success':
                results['success'] += 1
                print(f"✅ {results['success']:3d}/{total_files}: {result['file']}")
            else:
                results['error'] += 1
                results['errors'].append(result)
                print(f"❌ {results['error']:3d}: {result['file']} - {result['error']}")
            
            # Показываем прогресс каждые 10 файлов
            if (results['success'] + results['error']) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (results['success'] + results['error']) / elapsed * 60
                print(f"📊 Обработано: {results['success'] + results['error']}/{total_files} ({rate:.1f} файлов/мин)")
    
    # Итоговый отчет
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print("🎉 ЗАГРУЗКА ЗАВЕРШЕНА!")
    print(f"✅ Успешно: {results['success']}")
    print(f"❌ Ошибок: {results['error']}")
    print(f"⏱️ Время: {elapsed/60:.1f} минут")
    print(f"🚀 Скорость: {results['success']/(elapsed/60):.1f} файлов/мин")
    
    if results['errors']:
        print(f"\n❌ Первые 5 ошибок:")
        for error in results['errors'][:5]:
            print(f"  {error['file']}: {error['error']}")

if __name__ == '__main__':
    main()