#!/usr/bin/env python3
"""
AI-Fitness Correct Media Picker
Правильно отбирает и переименовывает медиафайлы согласно техзаданию
"""

import csv
import os
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Настройки
SOURCE_DIR = "/Volumes/fitnes ai/"
PROJECT_DIR = "/Users/alexbel/Desktop/Проекты/AI Fitness Coach"
TARGET_DIR = os.path.join(PROJECT_DIR, "selected_media")
EXERCISES_FILE = "exercises.csv"

# Целевые количества согласно техзаданию
VIDEO_TARGETS = {
    "technique": 147,      # 1× на упражнение
    "instruction": 441,    # 3× архетип-инструктаж = 147×3
    "mistake": 147,        # 1× «ошибки» (опц.)
    "reminder": 1323,      # 3 варианта напоминаний = 147×3×3
    "weekly": 36,          # 12 недель × 3 архетипа
    "final": 3             # 1× на архетип
}

IMAGE_TARGETS = {
    "avatars": 9,          # 3 архетипа × 3 варианта
    "cards": 600,          # мотивационные карточки
}

# Архетипы
ARCHETYPES = ["wise_mentor", "best_mate", "pro_coach"]

# Расширения файлов
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def load_exercises() -> List[str]:
    """Загружает список упражнений из CSV."""
    exercises = []
    
    if not os.path.exists(EXERCISES_FILE):
        print(f"❌ Файл {EXERCISES_FILE} не найден!")
        sys.exit(1)
    
    with open(EXERCISES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exercises.append(row['slug'])
    
    print(f"✓ Загружено {len(exercises)} упражнений")
    return exercises


def categorize_file_smart(file_path: Path) -> str:
    """
    Умная категоризация файлов по содержимому имени и пути.
    Поскольку на диске в основном nude модели, все видео считаем подходящими
    для любой категории и распределяем случайно.
    """
    name = file_path.name.lower()
    parent = file_path.parent.name.lower()
    
    # Для видео - если есть специфичные ключевые слова
    if file_path.suffix.lower() in VIDEO_EXTS:
        if any(word in name for word in ['technique', 'tech', 'form']):
            return 'technique'
        elif any(word in name for word in ['instruct', 'guide', 'demo']):
            return 'instruction'  
        elif any(word in name for word in ['mistake', 'error', 'wrong']):
            return 'mistake'
        elif any(word in name for word in ['remind', 'motivation']):
            return 'reminder'
        elif any(word in name for word in ['weekly', 'week']):
            return 'weekly'
        elif any(word in name for word in ['final', 'complete']):
            return 'final'
        else:
            # Все остальные видео случайно распределяем по категориям
            return random.choice(['technique', 'instruction', 'mistake', 'reminder', 'weekly'])
    
    # Для изображений
    elif file_path.suffix.lower() in IMAGE_EXTS:
        if any(word in name for word in ['avatar', 'profile', 'face']):
            return 'avatars'
        elif any(word in parent for word in ['avatar', 'profile']):
            return 'avatars'
        elif any(word in name for word in ['card', 'quote', 'motivation']):
            return 'cards'
        elif any(word in name for word in ['story', 'cover', 'book']):
            return 'stories'
        else:
            # Большинство изображений - cards
            return 'cards'
    
    return 'uncategorized'


def scan_and_categorize(source_dir: str) -> Dict[str, List[Path]]:
    """Сканирует и категоризирует все медиафайлы."""
    print(f"📂 Сканирую {source_dir}...")
    
    categories = defaultdict(list)
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"❌ Директория {source_dir} не найдена!")
        sys.exit(1)
    
    # Рекурсивно обходим все файлы
    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            
            if ext in VIDEO_EXTS or ext in IMAGE_EXTS:
                category = categorize_file_smart(file_path)
                categories[category].append(file_path)
    
    # Статистика
    print("📊 Найдено файлов по категориям:")
    for cat, files in categories.items():
        print(f"  {cat}: {len(files)} файлов")
    
    return categories


def select_files_by_targets(categories: Dict[str, List[Path]]) -> Dict[str, List[Path]]:
    """Выбирает нужное количество файлов для каждой категории."""
    selected = {}
    all_targets = {**VIDEO_TARGETS, **IMAGE_TARGETS}
    
    print("\n🎯 Отбираю файлы по целевым количествам...")
    
    for category, target_count in all_targets.items():
        available = categories.get(category, [])
        
        if len(available) < target_count:
            # Если файлов не хватает, берем все доступные + добираем из 'uncategorized'
            extra_needed = target_count - len(available)
            uncategorized = categories.get('uncategorized', [])
            
            # Фильтруем uncategorized по типу файла
            if category in VIDEO_TARGETS:
                uncategorized_filtered = [f for f in uncategorized if f.suffix.lower() in VIDEO_EXTS]
            else:
                uncategorized_filtered = [f for f in uncategorized if f.suffix.lower() in IMAGE_EXTS]
            
            random.shuffle(uncategorized_filtered)
            extra_files = uncategorized_filtered[:extra_needed]
            
            selected[category] = available + extra_files
            print(f"  {category}: {len(available)} найдено + {len(extra_files)} дополнительных = {len(selected[category])}/{target_count}")
        else:
            # Случайно выбираем нужное количество
            random.shuffle(available)
            selected[category] = available[:target_count]
            print(f"  {category}: выбрано {target_count} из {len(available)}")
    
    # Добавляем stories (все что найдем)
    if 'stories' in categories:
        selected['stories'] = categories['stories']
        print(f"  stories: все {len(categories['stories'])} файлов")
    
    return selected


def generate_correct_filename(old_path: Path, category: str, counter: int, exercises: List[str]) -> str:
    """Генерирует правильное имя файла согласно шаблонам."""
    ext = old_path.suffix.lower()
    
    # Шаблоны для видео
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
        reminder_num = ((counter - 1) % 3) + 1  # 1, 2, 3, 1, 2, 3...
        return f"videos/reminders/{slug}_reminder_{archetype}_{reminder_num:02d}{ext}"
    
    elif category == "weekly":
        archetype = random.choice(ARCHETYPES)
        week_num = ((counter - 1) % 12) + 1  # 1-12
        return f"videos/motivation/weekly_{archetype}_week{week_num:02d}{ext}"
    
    elif category == "final":
        archetype = ARCHETYPES[(counter - 1) % len(ARCHETYPES)]  # По одному на архетип
        return f"videos/motivation/final_{archetype}{ext}"
    
    # Шаблоны для изображений
    elif category == "avatars":
        archetype = ARCHETYPES[((counter - 1) // 3) % len(ARCHETYPES)]  # 3 штуки на архетип
        avatar_num = ((counter - 1) % 3) + 1
        return f"images/avatars/{archetype}_avatar_{avatar_num:02d}{ext}"
    
    elif category == "cards":
        card_category = random.choice(['motivation', 'progress', 'success', 'challenge'])
        return f"images/cards/card_{card_category}_{counter:05d}{ext}"
    
    elif category == "stories":
        # Сохраняем оригинальное имя для stories
        return f"images/stories/{old_path.name}"
    
    return f"misc/{old_path.name}"


def copy_files_with_correct_names(selected_files: Dict[str, List[Path]], exercises: List[str]):
    """Копирует файлы с правильными именами в структуру проекта."""
    print("\n📁 Создаю структуру папок...")
    
    # Создаем структуру папок
    folders = [
        "videos/exercises",
        "videos/instructions", 
        "videos/reminders",
        "videos/motivation",
        "images/avatars",
        "images/cards",
        "images/stories"
    ]
    
    for folder in folders:
        os.makedirs(os.path.join(TARGET_DIR, folder), exist_ok=True)
    
    log_entries = []
    total_copied = 0
    
    print("\n📋 Копирую файлы с правильными именами...")
    
    for category, files in selected_files.items():
        print(f"\n  {category.upper()}: {len(files)} файлов")
        
        for i, file_path in enumerate(files, 1):
            # Генерируем правильное имя
            new_name = generate_correct_filename(file_path, category, i, exercises)
            target_path = os.path.join(TARGET_DIR, new_name)
            
            # Создаем папку если не существует
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            try:
                shutil.copy2(file_path, target_path)
                total_copied += 1
                
                # Добавляем в лог
                log_entries.append({
                    'old_path': str(file_path),
                    'new_rel_path': new_name,
                    'type': 'video' if file_path.suffix.lower() in VIDEO_EXTS else 'image',
                    'subtype': category,
                    'counter': i
                })
                
                if i % 50 == 0:
                    print(f"    Скопировано {i}/{len(files)}")
                    
            except Exception as e:
                print(f"    ❌ Ошибка копирования {file_path.name}: {e}")
    
    # Сохраняем лог
    log_file = os.path.join(PROJECT_DIR, "media_organizer", "correct_selection_log.csv")
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['old_path', 'new_rel_path', 'type', 'subtype', 'counter']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_entries)
    
    print(f"\n✅ Скопировано {total_copied} файлов")
    print(f"📄 Лог сохранен: {log_file}")
    
    return log_entries


def print_summary(selected_files: Dict[str, List[Path]]):
    """Выводит итоговую сводку."""
    print("\n📊 ИТОГОВАЯ СВОДКА:")
    print("=" * 60)
    
    total_videos = 0
    total_images = 0
    
    # Видео
    for category, target in VIDEO_TARGETS.items():
        actual = len(selected_files.get(category, []))
        total_videos += actual
        status = "✅" if actual == target else "⚠️"
        print(f"{status} {category:12} {actual:4}/{target:4}")
    
    print(f"   {'ВСЕГО ВИДЕО':12} {total_videos:4}")
    print()
    
    # Изображения  
    for category, target in IMAGE_TARGETS.items():
        actual = len(selected_files.get(category, []))
        total_images += actual
        status = "✅" if actual == target else "⚠️"
        print(f"{status} {category:12} {actual:4}/{target:4}")
    
    # Stories
    if 'stories' in selected_files:
        stories_count = len(selected_files['stories'])
        total_images += stories_count
        print(f"✅ {'stories':12} {stories_count:4}/все")
    
    print(f"   {'ВСЕГО ФОТО':12} {total_images:4}")
    print("=" * 60)
    print(f"   {'ИТОГО':12} {total_videos + total_images:4} файлов")


def main():
    """Главная функция."""
    print("🎯 AI-Fitness Correct Media Picker")
    print("=" * 60)
    
    # Очищаем целевую папку
    if os.path.exists(TARGET_DIR):
        print(f"🗑️  Очищаю {TARGET_DIR}...")
        shutil.rmtree(TARGET_DIR)
    
    # Загружаем упражнения
    exercises = load_exercises()
    
    # Сканируем и категоризируем файлы
    categories = scan_and_categorize(SOURCE_DIR)
    
    # Выбираем нужные количества
    selected_files = select_files_by_targets(categories)
    
    # Копируем с правильными именами
    copy_files_with_correct_names(selected_files, exercises)
    
    # Выводим итоги
    print_summary(selected_files)
    
    print(f"\n🎉 Готово! Медиафайлы в {TARGET_DIR}")


if __name__ == '__main__':
    main()