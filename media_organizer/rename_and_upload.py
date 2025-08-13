#!/usr/bin/env python3
"""
Скрипт для категоризации медиафайлов с диска 'fitnes ai' 
и загрузки на Google Drive.
"""

import argparse
import csv
import mimetypes
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("❌ PyYAML не установлен. Установите: pip install pyyaml")
    sys.exit(1)

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("❌ Google API библиотеки не установлены.")
    print("Установите: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Константы
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
CATEGORIES_FILE = 'categories.yml'
LOG_FILE = 'rename_log.csv'
GDRIVE_FOLDER = 'ai_fitness_media'
TEMP_DIR = 'temp_media'

# Поддерживаемые форматы
VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def authenticate_gdrive():
    """Аутентификация в Google Drive API."""
    creds = None
    
    # Загружаем существующий токен
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE, SCOPES
        )
    
    # Если токен недействителен, обновляем
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ Файл {CREDENTIALS_FILE} не найден!")
                print("Скачайте OAuth credentials с Google Cloud Console")
                sys.exit(1)
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Сохраняем токен для будущего использования
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)


def load_categories(file_path: str) -> Dict[str, str]:
    """Загрузка правил категоризации из YAML."""
    if not os.path.exists(file_path):
        print(f"⚠️  Файл {file_path} не найден, создаю пример...")
        
        # Создаём пример файла
        example = {
            'pushup': 'chest',
            'squat': 'legs', 
            'plank': 'core',
            'workout': 'general',
            'alex': 'models',
            'selfie': 'progress',
            'motivation': 'quotes'
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(example, f, allow_unicode=True)
        
        return example
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def categorize_file(filename: str, rules: Dict[str, str]) -> str:
    """Определение категории файла по имени."""
    name_lower = filename.lower()
    
    for keyword, category in rules.items():
        if keyword.lower() in name_lower:
            return category
    
    return 'uncategorized'


def scan_media_files(source_dir: str) -> Tuple[List[Path], List[Path]]:
    """Сканирование директории для поиска медиафайлов."""
    videos = []
    photos = []
    
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"❌ Директория {source_dir} не найдена!")
        sys.exit(1)
    
    print(f"📂 Сканирую {source_dir}...")
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            
            if ext in VIDEO_EXTS:
                videos.append(file_path)
            elif ext in PHOTO_EXTS:
                photos.append(file_path)
    
    print(f"✓ Найдено: {len(videos)} видео, {len(photos)} фото")
    return videos, photos


def create_gdrive_folder(service, name: str, parent_id=None):
    """Создание папки на Google Drive."""
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    # Проверяем существование папки
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    else:
        query += " and 'root' in parents"
    
    results = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()
    
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        return folder.get('id')


def upload_to_gdrive(service, local_path: str, 
                     gdrive_path: str, parent_id: str):
    """Загрузка файла на Google Drive."""
    file_name = os.path.basename(gdrive_path)
    
    # Определяем MIME-тип
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    file_metadata = {
        'name': file_name,
        'parents': [parent_id]
    }
    
    # Проверяем существование файла
    query = f"name='{file_name}' and '{parent_id}' in parents"
    results = service.files().list(
        q=query,
        fields="files(id)"
    ).execute()
    
    items = results.get('files', [])
    
    media = MediaFileUpload(
        local_path,
        mimetype=mime_type,
        resumable=True
    )
    
    if items:
        # Обновляем существующий файл
        file_id = items[0]['id']
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
    else:
        # Создаём новый файл
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()


def process_media(source_dir: str, rules: Dict[str, str], 
                  service, dry_run: bool = False):
    """Основная функция обработки медиафайлов."""
    
    # Сканируем файлы
    videos, photos = scan_media_files(source_dir)
    
    # Подготавливаем временную директорию
    temp_path = Path(TEMP_DIR)
    if not dry_run:
        temp_path.mkdir(exist_ok=True)
    
    # Создаём корневую папку на GDrive
    if not dry_run and service:
        root_folder_id = create_gdrive_folder(service, GDRIVE_FOLDER)
        videos_folder_id = create_gdrive_folder(
            service, 'videos', root_folder_id
        )
        photos_folder_id = create_gdrive_folder(
            service, 'photos', root_folder_id
        )
    
    # Счётчики для категорий
    category_counters = defaultdict(lambda: {'video': 0, 'photo': 0})
    category_folders = {}
    
    # Лог переименований
    rename_log = []
    
    # Обработка видео
    print("\n📹 Обработка видео...")
    for i, video_path in enumerate(videos[:50]):  # Ограничиваем для теста
        filename = video_path.name
        category = categorize_file(filename, rules)
        
        # Увеличиваем счётчик
        category_counters[category]['video'] += 1
        counter = category_counters[category]['video']
        
        # Новое имя
        new_name = f"{category}_{counter:03d}{video_path.suffix}"
        new_rel_path = f"videos/{category}/{new_name}"
        
        # Создаём папку категории на GDrive
        if not dry_run and service and category not in category_folders:
            cat_folder_id = create_gdrive_folder(
                service, category, videos_folder_id
            )
            category_folders[f"video_{category}"] = cat_folder_id
        
        # Копируем во временную папку
        temp_file = temp_path / new_rel_path
        if not dry_run:
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(video_path, temp_file)
                
                # Загружаем на GDrive
                if service:
                    upload_to_gdrive(
                        service, 
                        str(temp_file),
                        new_name,
                        category_folders[f"video_{category}"]
                    )
            except Exception as e:
                print(f"  ❌ Ошибка с файлом {filename}: {e}")
                continue
        
        # Добавляем в лог
        rename_log.append({
            'old_name': str(video_path),
            'new_name': new_rel_path,
            'category': category,
            'type': 'video'
        })
        
        print(f"  ✓ {filename} → {new_rel_path}")
        
        if i > 0 and i % 10 == 0:
            print(f"    Обработано {i+1} из {len(videos)} видео...")
    
    # Обработка фото
    print(f"\n📸 Обработка фото...")
    for i, photo_path in enumerate(photos[:100]):  # Ограничиваем для теста
        filename = photo_path.name
        category = categorize_file(filename, rules)
        
        # Увеличиваем счётчик
        category_counters[category]['photo'] += 1
        counter = category_counters[category]['photo']
        
        # Новое имя
        new_name = f"{category}_{counter:03d}{photo_path.suffix}"
        new_rel_path = f"photos/{category}/{new_name}"
        
        # Создаём папку категории на GDrive
        if not dry_run and service and f"photo_{category}" not in category_folders:
            cat_folder_id = create_gdrive_folder(
                service, category, photos_folder_id
            )
            category_folders[f"photo_{category}"] = cat_folder_id
        
        # Копируем во временную папку
        temp_file = temp_path / new_rel_path
        if not dry_run:
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(photo_path, temp_file)
                
                # Загружаем на GDrive
                if service:
                    upload_to_gdrive(
                        service,
                        str(temp_file),
                        new_name,
                        category_folders[f"photo_{category}"]
                    )
            except Exception as e:
                print(f"  ❌ Ошибка с файлом {filename}: {e}")
                continue
        
        # Добавляем в лог
        rename_log.append({
            'old_name': str(photo_path),
            'new_name': new_rel_path,
            'category': category,
            'type': 'photo'
        })
        
        print(f"  ✓ {filename} → {new_rel_path}")
        
        if i > 0 and i % 20 == 0:
            print(f"    Обработано {i+1} из {len(photos)} фото...")
    
    # Сохраняем лог
    print(f"\n💾 Сохраняю лог в {LOG_FILE}...")
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['old_name', 'new_name', 'category', 'type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rename_log)
    
    # Статистика
    print("\n📊 Статистика по категориям:")
    for category in sorted(category_counters.keys()):
        counts = category_counters[category]
        print(f"  {category:20} - "
              f"видео: {counts['video']:4}, "
              f"фото: {counts['photo']:4}")
    
    # Очищаем временную папку
    if not dry_run and temp_path.exists():
        shutil.rmtree(temp_path)
        print(f"\n🧹 Временная папка {TEMP_DIR} очищена")
    
    if not dry_run and service:
        print(f"\n✅ Готово! Файлы загружены в GDrive/{GDRIVE_FOLDER}/")
    else:
        print(f"\n✅ Сухой прогон завершён. Создан лог {LOG_FILE}")


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='Категоризация и загрузка медиа на Google Drive'
    )
    parser.add_argument(
        '--source',
        default='/Volumes/fitnes ai/',
        help='Путь к диску с медиафайлами'
    )
    parser.add_argument(
        '--categories',
        default=CATEGORIES_FILE,
        help='Файл с правилами категоризации'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Тестовый запуск без загрузки'
    )
    
    args = parser.parse_args()
    
    print("🚀 AI Fitness Media Organizer")
    print("=" * 50)
    
    # Загружаем правила
    print(f"📋 Загружаю правила из {args.categories}...")
    rules = load_categories(args.categories)
    print(f"✓ Загружено {len(rules)} правил")
    
    if args.dry_run:
        print("\n⚠️  ТЕСТОВЫЙ РЕЖИМ - файлы не будут загружены")
        service = None
    else:
        try:
            # Аутентификация
            print("\n🔐 Подключаюсь к Google Drive...")
            service = authenticate_gdrive()
            print("✓ Подключение установлено")
        except Exception as e:
            print(f"❌ Ошибка подключения к Google Drive: {e}")
            print("Запускаю в тестовом режиме...")
            service = None
    
    # Обработка
    process_media(args.source, rules, service, args.dry_run or service is None)


if __name__ == '__main__':
    main()