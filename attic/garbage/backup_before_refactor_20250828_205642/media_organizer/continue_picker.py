#!/usr/bin/env python3
"""
ПРОДОЛЖЕНИЕ копирования медиафайлов с места остановки
"""

import csv
import os
import random
import shutil
from pathlib import Path

# Параметры
SOURCE_DIR = "/Volumes/fitnes ai/"
TARGET_DIR = "/Users/alexbel/Desktop/Проекты/AI Fitness Coach/selected_media"
EXERCISES_FILE = "/Users/alexbel/Desktop/Проекты/AI Fitness Coach/media_organizer/exercises.csv"
ARCHETYPES = ["wise_mentor", "best_mate", "pro_coach"]

# Целевые количества
TARGETS = {
    "instruction": 441,    # продолжаем с 224
    "reminder": 1323,      # начинаем с 0
    "weekly": 36,          # начинаем с 0
    "final": 3,            # начинаем с 0
    "avatars": 9,          # начинаем с 0
    "cards": 600,          # начинаем с 0
}

def load_exercises():
    exercises = []
    with open(EXERCISES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exercises.append(row['slug'])
    return exercises

def collect_remaining_videos():
    """Собирает все оставшиеся видео"""
    print("📂 Собираю оставшиеся видео с диска...")
    
    videos = []
    for path in Path(SOURCE_DIR).rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.mp4', '.mov', '.avi', '.mkv', '.webm'}:
            videos.append(path)
    
    random.shuffle(videos)
    print(f"📹 Найдено {len(videos)} видео для продолжения")
    return videos

def collect_images():
    """Собирает все изображения"""
    print("📂 Собираю изображения с диска...")
    
    images = []
    for path in Path(SOURCE_DIR).rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
            images.append(path)
    
    random.shuffle(images)
    print(f"📷 Найдено {len(images)} изображений")
    return images

def get_current_counts():
    """Определяет текущее количество скопированных файлов"""
    counts = {}
    
    # Проверяем videos/instructions
    counts['instruction'] = len(list(Path(TARGET_DIR, "videos/instructions").glob("*")))
    
    # Проверяем videos/reminders
    counts['reminder'] = len(list(Path(TARGET_DIR, "videos/reminders").glob("*"))) if Path(TARGET_DIR, "videos/reminders").exists() else 0
    
    # Проверяем videos/motivation
    motivation_path = Path(TARGET_DIR, "videos/motivation")
    if motivation_path.exists():
        counts['weekly'] = len(list(motivation_path.glob("*weekly*")))
        counts['final'] = len(list(motivation_path.glob("*final*")))
    else:
        counts['weekly'] = 0
        counts['final'] = 0
    
    # Проверяем images
    avatars_path = Path(TARGET_DIR, "images/avatars")
    cards_path = Path(TARGET_DIR, "images/cards")
    counts['avatars'] = len(list(avatars_path.glob("*"))) if avatars_path.exists() else 0
    counts['cards'] = len(list(cards_path.glob("*"))) if cards_path.exists() else 0
    
    return counts

def generate_filename(category, counter, exercises):
    """Генерирует правильное имя файла"""
    
    if category == "instruction":
        exercise = exercises[counter % len(exercises)]
        archetype = ARCHETYPES[counter % len(ARCHETYPES)]
        return f"videos/instructions/{exercise}_instruction_{archetype}_m01"
    
    elif category == "reminder":
        # 147 упражнений × 3 архетипа × 3 варианта = 1323
        exercise_idx = counter % len(exercises)
        archetype_idx = (counter // len(exercises)) % len(ARCHETYPES)
        reminder_num = ((counter // (len(exercises) * len(ARCHETYPES))) % 3) + 1
        
        exercise = exercises[exercise_idx]
        archetype = ARCHETYPES[archetype_idx]
        
        return f"videos/reminders/{exercise}_reminder_{archetype}_{reminder_num:02d}"
    
    elif category == "weekly":
        week_num = (counter % 12) + 1
        archetype = ARCHETYPES[counter % len(ARCHETYPES)]
        return f"videos/motivation/weekly_{archetype}_week{week_num:02d}"
    
    elif category == "final":
        archetype = ARCHETYPES[counter % len(ARCHETYPES)]
        return f"videos/motivation/final_{archetype}"
    
    elif category == "avatars":
        archetype = ARCHETYPES[counter // 3]
        variant = (counter % 3) + 1
        return f"images/avatars/{archetype}_avatar_{variant:02d}"
    
    elif category == "cards":
        card_category = random.choice(['motivation', 'progress', 'success', 'challenge'])
        return f"images/cards/card_{card_category}_{counter+1:05d}"
    
    return "misc/unknown"

def continue_copying():
    """Продолжает копирование с места остановки"""
    
    exercises = load_exercises()
    current_counts = get_current_counts()
    
    print("\n🔄 ПРОДОЛЖАЮ КОПИРОВАНИЕ С ТЕКУЩЕГО СОСТОЯНИЯ:")
    for category, current in current_counts.items():
        target = TARGETS[category]
        remaining = target - current
        print(f"  {category}: {current}/{target} (осталось {remaining})")
    
    # Собираем медиафайлы
    all_videos = collect_remaining_videos()
    all_images = collect_images()
    
    video_idx = 0
    image_idx = 0
    
    # Продолжаем копирование видео
    video_categories = ["instruction", "reminder", "weekly", "final"]
    
    for category in video_categories:
        current_count = current_counts[category]
        target_count = TARGETS[category]
        remaining = target_count - current_count
        
        if remaining <= 0:
            print(f"✅ {category}: уже готово ({current_count}/{target_count})")
            continue
            
        print(f"\n📹 {category}: копирую {remaining} оставшихся видео...")
        
        # Создаем папку если не существует
        if category == "instruction":
            folder = "videos/instructions"
        elif category == "reminder":
            folder = "videos/reminders" 
        else:  # weekly, final
            folder = "videos/motivation"
            
        os.makedirs(os.path.join(TARGET_DIR, folder), exist_ok=True)
        
        for i in range(remaining):
            if video_idx >= len(all_videos):
                print(f"❌ Закончились видео! Скопировано {i}")
                break
                
            counter = current_count + i
            source_file = all_videos[video_idx]
            filename_base = generate_filename(category, counter, exercises)
            target_file = filename_base + source_file.suffix
            target_path = os.path.join(TARGET_DIR, target_file)
            
            try:
                shutil.copy2(source_file, target_path)
                video_idx += 1
                
                if (i + 1) % 100 == 0:
                    print(f"    {i + 1}/{remaining} скопировано")
                    
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
                video_idx += 1
        
        final_count = len(list(Path(TARGET_DIR, folder).glob("*")))
        print(f"✅ {category}: завершено ({final_count}/{target_count})")
    
    # Копируем изображения
    image_categories = ["avatars", "cards"]
    
    for category in image_categories:
        current_count = current_counts[category]
        target_count = TARGETS[category]
        remaining = target_count - current_count
        
        if remaining <= 0:
            print(f"✅ {category}: уже готово")
            continue
            
        print(f"\n📷 {category}: копирую {remaining} изображений...")
        
        folder = f"images/{category}"
        os.makedirs(os.path.join(TARGET_DIR, folder), exist_ok=True)
        
        for i in range(remaining):
            if image_idx >= len(all_images):
                print(f"❌ Закончились изображения! Скопировано {i}")
                break
                
            counter = current_count + i
            source_file = all_images[image_idx]
            filename_base = generate_filename(category, counter, exercises)
            target_file = filename_base + source_file.suffix
            target_path = os.path.join(TARGET_DIR, target_file)
            
            try:
                shutil.copy2(source_file, target_path)
                image_idx += 1
                
                if (i + 1) % 100 == 0:
                    print(f"    {i + 1}/{remaining} скопировано")
                    
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
                image_idx += 1
        
        final_count = len(list(Path(TARGET_DIR, folder).glob("*")))
        print(f"✅ {category}: завершено ({final_count}/{target_count})")

def verify_final_results():
    """Проверяет финальные результаты"""
    print("\n📊 ФИНАЛЬНАЯ ПРОВЕРКА:")
    print("=" * 50)
    
    all_targets = {
        "technique": 147,
        "instruction": 441, 
        "mistake": 147,
        "reminder": 1323,
        "weekly": 36,
        "final": 3,
        "avatars": 9,
        "cards": 600
    }
    
    total_actual = 0
    total_target = sum(all_targets.values())
    
    for category, target in all_targets.items():
        if category == "technique":
            actual = len(list(Path(TARGET_DIR, "videos/exercises").glob("*technique*")))
        elif category == "mistake":
            actual = len(list(Path(TARGET_DIR, "videos/exercises").glob("*mistake*")))
        elif category == "instruction":
            actual = len(list(Path(TARGET_DIR, "videos/instructions").glob("*")))
        elif category == "reminder":
            actual = len(list(Path(TARGET_DIR, "videos/reminders").glob("*")))
        elif category in ["weekly", "final"]:
            actual = len(list(Path(TARGET_DIR, "videos/motivation").glob(f"*{category}*")))
        else:  # avatars, cards
            actual = len(list(Path(TARGET_DIR, f"images/{category}").glob("*")))
        
        total_actual += actual
        status = "✅" if actual == target else "❌"
        print(f"{status} {category:12} {actual:4}/{target:4}")
    
    print("=" * 50)
    print(f"   {'ИТОГО':12} {total_actual:4}/{total_target:4}")
    
    # Размер
    size_gb = sum(f.stat().st_size for f in Path(TARGET_DIR).rglob('*') if f.is_file()) / (1024**3)
    print(f"   {'РАЗМЕР':12} {size_gb:.1f} GB")

def main():
    print("🔄 ПРОДОЛЖЕНИЕ КОПИРОВАНИЯ МЕДИАФАЙЛОВ")
    print("=" * 50)
    
    continue_copying()
    verify_final_results()
    
    print(f"\n🎉 ГОТОВО! Все файлы в {TARGET_DIR}")

if __name__ == '__main__':
    main()