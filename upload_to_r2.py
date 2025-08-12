#!/usr/bin/env python3
"""
upload_to_r2.py
---------------
Загружает медиатеку selected_media в Cloudflare R2.
Использует boto3 для S3-совместимого API.
"""

import os
import sys
import time
import hashlib
import json
from pathlib import Path
from datetime import datetime
import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Конфигурация R2
R2_ACCESS_KEY_ID = "3a9fd5a6b38ec994e057e33c1096874e"
R2_SECRET_ACCESS_KEY = "0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13"
R2_ENDPOINT = "https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com"
R2_BUCKET = "ai-fitness-media"

# Пути
PROJECT_ROOT = Path.cwd()
SELECTED_MEDIA = PROJECT_ROOT / "selected_media"
UPLOAD_LOG = PROJECT_ROOT / "r2_upload_log.json"
UPLOAD_STATE = PROJECT_ROOT / "r2_upload_state.json"

# Параметры загрузки
MAX_WORKERS = 10  # Количество параллельных потоков (увеличено для ускорения)
CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks для multipart upload
MULTIPART_THRESHOLD = 50 * 1024 * 1024  # Файлы > 50MB загружаем по частям

def get_s3_client():
    """Создает S3 клиент для R2."""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            retries={'max_attempts': 3}
        ),
        region_name='auto'
    )

def load_upload_state():
    """Загружает состояние предыдущей загрузки."""
    if UPLOAD_STATE.exists():
        with open(UPLOAD_STATE, 'r') as f:
            return set(json.load(f))
    return set()

def save_upload_state(uploaded_files):
    """Сохраняет состояние загрузки."""
    with open(UPLOAD_STATE, 'w') as f:
        json.dump(list(uploaded_files), f, indent=2)

def calculate_file_hash(file_path):
    """Вычисляет MD5 хеш файла для проверки целостности."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()

def get_all_files():
    """Собирает все файлы для загрузки."""
    files = []
    for file_path in SELECTED_MEDIA.rglob('*'):
        if file_path.is_file():
            # Относительный путь от selected_media
            relative_path = file_path.relative_to(SELECTED_MEDIA)
            # Преобразуем в S3 key (используем / даже на Windows)
            s3_key = str(relative_path).replace('\\', '/')
            files.append((file_path, s3_key))
    return files

def upload_file(s3_client, file_path, s3_key, pbar=None):
    """Загружает один файл в R2."""
    try:
        file_size = file_path.stat().st_size
        
        # Метаданные (только ASCII символы для S3)
        import unicodedata
        safe_name = unicodedata.normalize('NFKD', file_path.name).encode('ascii', 'ignore').decode('ascii')
        metadata = {
            'original-name': safe_name or 'unknown',
            'upload-date': datetime.now().isoformat(),
            'file-hash': calculate_file_hash(file_path)
        }
        
        # Определяем content-type
        if file_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            content_type = 'video/mp4'
        elif file_path.suffix.lower() in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif file_path.suffix.lower() == '.png':
            content_type = 'image/png'
        elif file_path.suffix.lower() == '.gif':
            content_type = 'image/gif'
        else:
            content_type = 'application/octet-stream'
        
        # Загружаем файл
        with open(file_path, 'rb') as f:
            s3_client.put_object(
                Bucket=R2_BUCKET,
                Key=s3_key,
                Body=f,
                ContentType=content_type,
                Metadata=metadata
            )
        
        if pbar:
            pbar.update(1)
            pbar.set_postfix({'current': file_path.name[:30]})
        
        return {
            'status': 'success',
            'file': str(file_path),
            's3_key': s3_key,
            'size': file_size,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'file': str(file_path),
            's3_key': s3_key,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def verify_bucket_access(s3_client):
    """Проверяет доступ к бакету."""
    try:
        # Пробуем получить список объектов (может быть пустым)
        s3_client.list_objects_v2(Bucket=R2_BUCKET, MaxKeys=1)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ Bucket '{R2_BUCKET}' не найден")
        elif error_code == '403':
            print(f"❌ Нет доступа к bucket '{R2_BUCKET}'")
        else:
            print(f"❌ Ошибка доступа к bucket: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def main():
    print("🚀 Загрузка медиатеки в Cloudflare R2")
    print("=" * 60)
    
    # Проверяем существование папки
    if not SELECTED_MEDIA.exists():
        print(f"❌ Папка {SELECTED_MEDIA} не найдена")
        return 1
    
    # Создаем S3 клиент
    print("📡 Подключение к R2...")
    s3_client = get_s3_client()
    
    # Проверяем доступ
    if not verify_bucket_access(s3_client):
        return 1
    
    print(f"✅ Подключено к bucket: {R2_BUCKET}")
    print(f"   Endpoint: {R2_ENDPOINT}")
    
    # Собираем файлы
    print("\n📂 Сканирование файлов...")
    all_files = get_all_files()
    print(f"   Найдено файлов: {len(all_files)}")
    
    # Загружаем состояние
    uploaded_files = load_upload_state()
    files_to_upload = [(f, k) for f, k in all_files if k not in uploaded_files]
    
    if not files_to_upload:
        print("✅ Все файлы уже загружены!")
        return 0
    
    print(f"   К загрузке: {len(files_to_upload)} файлов")
    
    # Подсчет общего размера
    total_size = sum(f.stat().st_size for f, _ in files_to_upload)
    print(f"   Общий размер: {total_size / (1024**3):.2f} GB")
    
    # Автоматически начинаем загрузку (можно добавить флаг --auto)
    import sys
    if '--auto' in sys.argv:
        print("\n" + "=" * 60)
        print("🚀 Автоматический режим - начинаем загрузку...")
    else:
        print("\n" + "=" * 60)
        try:
            response = input("Начать загрузку? (y/n): ")
            if response.lower() != 'y':
                print("Отменено")
                return 0
        except EOFError:
            print("🚀 Неинтерактивный режим - начинаем загрузку...")
    
    # Загружаем файлы
    print("\n📤 Загрузка файлов...")
    results = []
    errors = []
    
    with tqdm(total=len(files_to_upload), unit='файлов') as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(upload_file, s3_client, file_path, s3_key, pbar): (file_path, s3_key)
                for file_path, s3_key in files_to_upload
            }
            
            for future in as_completed(futures):
                file_path, s3_key = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['status'] == 'success':
                        uploaded_files.add(s3_key)
                        save_upload_state(uploaded_files)
                    else:
                        errors.append(result)
                        
                except Exception as e:
                    errors.append({
                        'status': 'error',
                        'file': str(file_path),
                        's3_key': s3_key,
                        'error': str(e)
                    })
    
    # Сохраняем лог
    log_data = {
        'upload_date': datetime.now().isoformat(),
        'total_files': len(all_files),
        'uploaded': len(uploaded_files),
        'errors': len(errors),
        'results': results
    }
    
    with open(UPLOAD_LOG, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ЗАГРУЗКИ")
    print("-" * 60)
    print(f"✅ Успешно загружено: {len(uploaded_files)}/{len(all_files)}")
    
    if errors:
        print(f"❌ Ошибок: {len(errors)}")
        print("\nПервые 5 ошибок:")
        for err in errors[:5]:
            print(f"  • {err['file']}: {err.get('error', 'Unknown error')}")
    
    print(f"\n📝 Лог сохранен: {UPLOAD_LOG}")
    print(f"📌 Состояние сохранено: {UPLOAD_STATE}")
    
    if len(uploaded_files) == len(all_files):
        print("\n🎉 Все файлы успешно загружены в R2!")
        
        # Генерируем примеры URL
        print("\n🔗 Примеры URL для доступа:")
        example_keys = list(uploaded_files)[:3]
        for key in example_keys:
            # Публичный URL (если bucket настроен как публичный)
            public_url = f"https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/{key}"
            print(f"  • {public_url}")
        
        return 0
    else:
        print(f"\n⚠️  Не все файлы загружены. Запустите скрипт повторно для докачки.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Загрузка прервана. Состояние сохранено.")
        print("Запустите скрипт повторно для продолжения.")
        sys.exit(1)