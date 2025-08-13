#!/usr/bin/env python3
"""
AI-Fitness Media Picker & Uploader v2
Случайно выбирает нужное количество медиафайлов с диска и загружает в Google Drive
"""

import argparse
import csv
import mimetypes
import os
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Импорты для Google API
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

# ───────────────────────────────────────────────────────────────────────────── #
#  1. ГЛОБАЛЬНЫЕ КОНСТАНТЫ
# ───────────────────────────────────────────────────────────────────────────── #

SOURCE_DIR = "/Volumes/fitnes ai/"
GDRIVE_ROOT = "ai_fitness_media"
ARCHETYPES = ["wise_mentor", "best_mate", "pro_coach"]

EXERCISE_FILE = "exercises.csv"

VIDEO_TARGETS = {
    "technique": 147,                               # 1× на упражнение
    "instruction": 147 * len(ARCHETYPES),           # 3× архетип-инструктаж = 441
    "mistake": 147,                                 # 1× «ошибки» (опц.)
    "reminder": 147 * len(ARCHETYPES) * 3,          # 3 варианта напоминаний = 1323
    "weekly": 12 * len(ARCHETYPES),                 # 36
    "final": 1 * len(ARCHETYPES)                    # 3
}

IMAGE_TARGETS = {
    "avatars": 9,                                   # 3 архетипа × 3 варианта
    "cards": 600,                                   # мотивационные карточки
}

# Допустимые расширения
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Google Drive API настройки
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

# Логирование
LOG_FILE = 'rename_log.csv'


def load_exercises(file_path: str) -> List[str]:
    """Загружает slug-и упражнений из CSV файла."""
    exercises = []
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exercises.append(row['slug'])
    
    print(f"✓ Загружено {len(exercises)} упражнений из {file_path}")
    return exercises


def authenticate_gdrive():
    """Аутентификация в Google Drive API."""
    creds = None
    
    # Загружаем существующий токен
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Если токен недействителен, обновляем
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ Файл {CREDENTIALS_FILE} не найден!")
                print("Скачайте OAuth credentials с Google Cloud Console")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Сохраняем токен
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)


# ───────────────────────────────────────────────────────────────────────────── #
#  2. ЛОГИКА ВЫБОРА ФАЙЛОВ
# ───────────────────────────────────────────────────────────────────────────── #

def scan_source_files(source_dir: str) -> Tuple[Dict[str, List[Path]], 
                                                Dict[str, List[Path]]]:
    """Сканирует источник и группирует файлы по типам."""
    video_candidates = defaultdict(list)
    image_candidates = defaultdict(list)
    
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"❌ Директория {source_dir} не найдена!")
        sys.exit(1)
    
    print(f"📂 Сканирую {source_dir}...")
    
    # Рекурсивно обходим все файлы
    for file_path in source_path.rglob('*'):
        if not file_path.is_file():
            continue
            
        ext = file_path.suffix.lower()
        name_lower = file_path.name.lower()
        parent_name_lower = file_path.parent.name.lower()
        
        # Категоризация видео
        if ext in VIDEO_EXTS:
            if any(word in name_lower for word in ['technique', 'tech']):
                video_candidates['technique'].append(file_path)
            elif any(word in name_lower for word in ['instruction', 'instr']):
                video_candidates['instruction'].append(file_path)
            elif any(word in name_lower for word in ['mistake', 'error', 'wrong']):
                video_candidates['mistake'].append(file_path)
            elif any(word in name_lower for word in ['reminder', 'remind']):
                video_candidates['reminder'].append(file_path)
            elif any(word in name_lower for word in ['weekly', 'week']):
                video_candidates['weekly'].append(file_path)
            elif any(word in name_lower for word in ['final', 'complete']):
                video_candidates['final'].append(file_path)
            else:
                # Все остальные видео считаем technique (техника выполнения)
                video_candidates['technique'].append(file_path)
        
        # Категоризация изображений
        elif ext in IMAGE_EXTS:
            if any(word in name_lower for word in ['avatar', 'profile']):
                image_candidates['avatars'].append(file_path)
            elif any(word in parent_name_lower for word in ['avatar', 'profile']):
                image_candidates['avatars'].append(file_path)
            elif any(word in name_lower for word in ['card', 'motivation', 'quote', 'inspire']):
                image_candidates['cards'].append(file_path)
            elif any(word in parent_name_lower for word in ['card', 'motivation', 'quote']):
                image_candidates['cards'].append(file_path)
            elif any(word in name_lower for word in ['story', 'cover']):
                image_candidates['stories'].append(file_path)
            elif any(word in parent_name_lower for word in ['story', 'stories']):
                image_candidates['stories'].append(file_path)
            else:
                # Остальные картинки считаем cards
                image_candidates['cards'].append(file_path)
    
    print(f"📊 Найдено файлов по категориям:")
    for category, files in video_candidates.items():
        print(f"  📹 {category}: {len(files)} видео")
    for category, files in image_candidates.items():
        print(f"  📷 {category}: {len(files)} изображений")
    
    return dict(video_candidates), dict(image_candidates)


def pick_random_files(candidates: Dict[str, List[Path]], 
                     targets: Dict[str, int]) -> Dict[str, List[Path]]:
    """Случайно выбирает нужное количество файлов для каждой категории."""
    selected = {}
    
    for category, target_count in targets.items():
        available = candidates.get(category, [])
        
        if len(available) < target_count:
            print(f"⚠️  {category}: нужно {target_count}, "
                  f"найдено только {len(available)}")
            selected[category] = available
        else:
            # Случайно перемешиваем и берём первые N
            random.shuffle(available)
            selected[category] = available[:target_count]
            print(f"✓ {category}: выбрано {target_count} из {len(available)}")
    
    return selected


# ───────────────────────────────────────────────────────────────────────────── #
#  3. ШАБЛОНЫ НОВЫХ ИМЁН
# ───────────────────────────────────────────────────────────────────────────── #

def generate_new_name(file_path: Path, category: str, 
                     exercises: List[str], counters: Dict) -> str:
    """Генерирует новое имя файла по шаблонам."""
    ext = file_path.suffix.lower()
    
    # Для видео
    if category == "technique":
        slug = random.choice(exercises)
        return f"videos/exercises/{slug}_technique_m01{ext}"
    
    elif category == "instruction":
        slug = random.choice(exercises)
        archetype = random.choice(ARCHETYPES)
        return f"videos/instructions/{slug}_instruction_{archetype}_m01{ext}"
    
    elif category == "mistake":
        slug = random.choice(exercises)
        return f"videos/exercises/{slug}_mistake_m01{ext}"
    
    elif category == "reminder":
        slug = random.choice(exercises)
        archetype = random.choice(ARCHETYPES)
        reminder_num = (counters[f"reminder_{archetype}_{slug}"] % 3) + 1
        return f"videos/reminders/{slug}_reminder_{archetype}_{reminder_num:02d}{ext}"
    
    elif category == "weekly":
        archetype = random.choice(ARCHETYPES)
        week_num = (counters[f"weekly_{archetype}"] % 12) + 1
        return f"videos/motivation/weekly_{archetype}_week{week_num:02d}{ext}"
    
    elif category == "final":
        archetype = random.choice(ARCHETYPES)
        return f"videos/motivation/final_{archetype}{ext}"
    
    # Для изображений
    elif category == "avatars":
        archetype = random.choice(ARCHETYPES)
        avatar_num = (counters[f"avatar_{archetype}"] % 3) + 1
        return f"images/avatars/{archetype}_avatar_{avatar_num:02d}{ext}"
    
    elif category == "cards":
        card_num = counters.get("cards", 0) + 1
        card_category = random.choice(['motivation', 'progress', 'success', 'challenge'])
        return f"images/cards/card_{card_category}_{card_num:05d}{ext}"
    
    elif category == "stories":
        # Для stories сохраняем оригинальное имя
        return f"images/stories/{file_path.name}"
    
    return f"misc/{file_path.name}"


def create_gdrive_folder(service, name: str, parent_id: str = None) -> str:
    """Создаёт папку на Google Drive или возвращает ID существующей."""
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    # Проверяем существование
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    else:
        query += " and 'root' in parents"
    
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')


def upload_to_gdrive(service, local_path: Path, gdrive_path: str, 
                    parent_id: str) -> bool:
    """Загружает файл на Google Drive."""
    file_name = Path(gdrive_path).name
    
    # MIME-тип
    mime_type, _ = mimetypes.guess_type(str(local_path))
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    file_metadata = {
        'name': file_name,
        'parents': [parent_id]
    }
    
    # Проверяем существование
    query = f"name='{file_name}' and '{parent_id}' in parents"
    results = service.files().list(q=query, fields="files(id)").execute()
    items = results.get('files', [])
    
    try:
        media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)
        
        if items:
            # Обновляем существующий файл
            file_id = items[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Создаём новый файл
            service.files().create(body=file_metadata, media_body=media).execute()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки {file_name}: {e}")
        return False


# ───────────────────────────────────────────────────────────────────────────── #
#  4. ОСНОВНАЯ ЛОГИКА
# ───────────────────────────────────────────────────────────────────────────── #

def setup_gdrive_structure(service) -> Dict[str, str]:
    """Создаёт структуру папок на Google Drive."""
    folder_ids = {}
    
    # Корневая папка
    root_id = create_gdrive_folder(service, GDRIVE_ROOT)
    folder_ids['root'] = root_id
    
    # Основные папки
    videos_id = create_gdrive_folder(service, 'videos', root_id)
    images_id = create_gdrive_folder(service, 'images', root_id)
    
    folder_ids['videos'] = videos_id
    folder_ids['images'] = images_id
    
    # Подпапки для видео
    folder_ids['videos/exercises'] = create_gdrive_folder(service, 'exercises', videos_id)
    folder_ids['videos/instructions'] = create_gdrive_folder(service, 'instructions', videos_id)
    folder_ids['videos/reminders'] = create_gdrive_folder(service, 'reminders', videos_id)
    folder_ids['videos/motivation'] = create_gdrive_folder(service, 'motivation', videos_id)
    
    # Подпапки для изображений
    folder_ids['images/avatars'] = create_gdrive_folder(service, 'avatars', images_id)
    folder_ids['images/cards'] = create_gdrive_folder(service, 'cards', images_id)
    folder_ids['images/stories'] = create_gdrive_folder(service, 'stories', images_id)
    
    print("✓ Структура папок на Google Drive создана")
    return folder_ids


def process_files(selected_videos: Dict[str, List[Path]], 
                 selected_images: Dict[str, List[Path]],
                 exercises: List[str], 
                 service=None, 
                 dry_run: bool = False) -> List[Dict]:
    """Обрабатывает выбранные файлы - переименовывает и загружает."""
    
    log_entries = []
    counters = defaultdict(int)
    
    if service and not dry_run:
        folder_ids = setup_gdrive_structure(service)
    else:
        folder_ids = {}
    
    print("\n📹 Обработка видеофайлов...")
    
    # Обработка видео
    for category, files in selected_videos.items():
        print(f"\n  {category.upper()}: обрабатываю {len(files)} файлов")
        
        for i, file_path in enumerate(files):
            # Обновляем счётчики для правильной нумерации
            if category == "reminder":
                slug = random.choice(exercises)
                archetype = random.choice(ARCHETYPES)
                key = f"reminder_{archetype}_{slug}"
                counters[key] += 1
            elif category == "weekly":
                archetype = random.choice(ARCHETYPES)
                counters[f"weekly_{archetype}"] += 1
            
            # Генерируем новое имя
            new_path = generate_new_name(file_path, category, exercises, counters)
            
            # Определяем родительскую папку
            folder_key = str(Path(new_path).parent)
            parent_id = folder_ids.get(folder_key)
            
            # Загружаем на Drive (если не dry-run)
            uploaded = True
            if service and not dry_run and parent_id:
                uploaded = upload_to_gdrive(service, file_path, new_path, parent_id)
            
            # Записываем в лог
            log_entries.append({
                'old_path': str(file_path),
                'new_rel_path': new_path,
                'type': 'video',
                'subtype': category,
                'archetype_slug': 'various',
                'picked': uploaded
            })
            
            if (i + 1) % 50 == 0:
                print(f"    Обработано {i + 1} из {len(files)}")
    
    print("\n📷 Обработка изображений...")
    
    # Обработка изображений
    for category, files in selected_images.items():
        print(f"\n  {category.upper()}: обрабатываю {len(files)} файлов")
        
        for i, file_path in enumerate(files):
            # Обновляем счётчики
            if category == "avatars":
                archetype = random.choice(ARCHETYPES)
                counters[f"avatar_{archetype}"] += 1
            elif category == "cards":
                counters["cards"] += 1
            
            # Генерируем новое имя
            new_path = generate_new_name(file_path, category, exercises, counters)
            
            # Определяем родительскую папку
            folder_key = str(Path(new_path).parent)
            parent_id = folder_ids.get(folder_key)
            
            # Загружаем на Drive (если не dry-run)
            uploaded = True
            if service and not dry_run and parent_id:
                uploaded = upload_to_gdrive(service, file_path, new_path, parent_id)
            
            # Записываем в лог
            log_entries.append({
                'old_path': str(file_path),
                'new_rel_path': new_path,
                'type': 'image',
                'subtype': category,
                'archetype_slug': 'various',
                'picked': uploaded
            })
            
            if (i + 1) % 100 == 0:
                print(f"    Обработано {i + 1} из {len(files)}")
    
    return log_entries


# ───────────────────────────────────────────────────────────────────────────── #
#  5. ЛОГИРОВАНИЕ И ОТЧЁТЫ
# ───────────────────────────────────────────────────────────────────────────── #

def save_log(log_entries: List[Dict], log_file: str = LOG_FILE):
    """Сохраняет лог в CSV."""
    print(f"\n💾 Сохраняю лог в {log_file}...")
    
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['old_path', 'new_rel_path', 'type', 'subtype', 
                     'archetype_slug', 'picked']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_entries)


def print_summary(selected_videos: Dict[str, List[Path]], 
                 selected_images: Dict[str, List[Path]]):
    """Выводит сводную таблицу."""
    print("\n📊 СВОДНАЯ ТАБЛИЦА:")
    print("=" * 50)
    
    # Видео
    total_videos = 0
    for category, target in VIDEO_TARGETS.items():
        selected_count = len(selected_videos.get(category, []))
        total_videos += selected_count
        status = "✓" if selected_count == target else "⚠️"
        print(f"{status} {category:12} {selected_count:4}/{target:4}")
    
    print(f"   {'ВСЕГО ВИДЕО':12} {total_videos:4}")
    print()
    
    # Изображения
    total_images = 0
    for category, target in IMAGE_TARGETS.items():
        selected_count = len(selected_images.get(category, []))
        total_images += selected_count
        status = "✓" if selected_count == target else "⚠️"
        print(f"{status} {category:12} {selected_count:4}/{target:4}")
    
    # Stories отдельно (без целевого количества)
    stories_count = len(selected_images.get('stories', []))
    if stories_count > 0:
        print(f"✓ {'stories':12} {stories_count:4}/все")
    
    total_images += stories_count
    print(f"   {'ВСЕГО ФОТО':12} {total_images:4}")
    print("=" * 50)


# ───────────────────────────────────────────────────────────────────────────── #
#  6. MAIN
# ───────────────────────────────────────────────────────────────────────────── #

def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='AI-Fitness Media Picker & Uploader v2'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Тестовый режим без загрузки на Google Drive'
    )
    parser.add_argument(
        '--source',
        default=SOURCE_DIR,
        help='Путь к источнику медиафайлов'
    )
    
    args = parser.parse_args()
    
    print("🚀 AI-Fitness Media Picker & Uploader v2")
    print("=" * 60)
    
    # Загружаем упражнения
    exercises = load_exercises(EXERCISE_FILE)
    
    # Подключение к Google Drive
    service = None
    if not args.dry_run:
        print("\n🔐 Подключаюсь к Google Drive...")
        service = authenticate_gdrive()
        if service:
            print("✓ Подключение к Google Drive установлено")
        else:
            print("⚠️  Не удалось подключиться к Google Drive, запускаю в тестовом режиме")
            args.dry_run = True
    
    if args.dry_run:
        print("⚠️  ТЕСТОВЫЙ РЕЖИМ - файлы не будут загружены")
    
    # Сканируем исходные файлы
    video_candidates, image_candidates = scan_source_files(args.source)
    
    # Добавляем stories к целям (все что найдём)
    stories_count = len(image_candidates.get('stories', []))
    if stories_count > 0:
        IMAGE_TARGETS['stories'] = stories_count
    
    # Случайный выбор файлов
    print(f"\n🎲 Случайный выбор файлов...")
    random.seed()  # Инициализируем генератор случайных чисел
    
    selected_videos = pick_random_files(video_candidates, VIDEO_TARGETS)
    selected_images = pick_random_files(image_candidates, IMAGE_TARGETS)
    
    # Обработка файлов
    log_entries = process_files(
        selected_videos, selected_images, exercises, service, args.dry_run
    )
    
    # Сохранение лога
    save_log(log_entries)
    
    # Сводная таблица
    print_summary(selected_videos, selected_images)
    
    if args.dry_run:
        print(f"\n✅ Сухой прогон завершён. Лог сохранён в {LOG_FILE}")
    else:
        print(f"\n✅ Загрузка завершена! Файлы в Google Drive/{GDRIVE_ROOT}/")
        print(f"   Лог операций: {LOG_FILE}")


if __name__ == '__main__':
    main()