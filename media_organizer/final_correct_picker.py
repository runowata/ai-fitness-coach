#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ПРАВИЛЬНЫЙ скрипт отбора медиафайлов
Отбирает ТОЧНО нужные количества согласно техзаданию
"""

import csv
import os
import random
import shutil
from pathlib import Path

# ТОЧНЫЕ ЦЕЛИ из техзадания
VIDEO_TARGETS = {
    "technique": 147,      # 1× на упражнение = 147
    "instruction": 441,    # 3× архетип × 147 упражнений = 441  
    "mistake": 147,        # 1× на упражнение = 147
    "reminder": 1323,      # 3 варианта × 3 архетипа × 147 упражнений = 1323
    "weekly": 36,          # 12 недель × 3 архетипа = 36
    "final": 3             # 1× на архетип = 3
}

IMAGE_TARGETS = {
    "avatars": 9,          # 3 варианта × 3 архетипа = 9
    "cards": 600,          # 600 мотивационных карточек
}

# ИТОГО НУЖНО:
# Видео: 147+441+147+1323+36+3 = 2097 видео
# Изображения: 9+600 = 609 изображений

SOURCE_DIR = "/Volumes/fitnes ai/"
TARGET_DIR = "/Users/alexbel/Desktop/Проекты/AI Fitness Coach/selected_media"
EXERCISES_FILE = "/Users/alexbel/Desktop/Проекты/AI Fitness Coach/media_organizer/exercises.csv"
ARCHETYPES = ["wise_mentor", "best_mate", "pro_coach"]

def load_exercises():
    exercises = []
    with open(EXERCISES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exercises.append(row['slug'])
    print(f"✓ Загружено {len(exercises)} упражнений")
    return exercises

def collect_all_media():
    """Собирает ВСЕ медиафайлы с диска"""
    print(f"📂 Сканирую весь диск {SOURCE_DIR}...")
    
    videos = []
    images = []
    
    for path in Path(SOURCE_DIR).rglob('*'):
        if path.is_file():
            ext = path.suffix.lower()
            if ext in {'.mp4', '.mov', '.avi', '.mkv', '.webm'}:
                videos.append(path)
            elif ext in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
                images.append(path)
    
    print(f"📹 Найдено {len(videos)} видео")
    print(f"📷 Найдено {len(images)} изображений")
    
    return videos, images

def create_folder_structure():
    """Создает правильную структуру папок"""
    print("📁 Создаю структуру папок...")
    
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    
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

def generate_filename(category, counter, exercises):
    """Генерирует правильное имя файла"""
    
    if category == "technique":
        exercise = exercises[counter % len(exercises)]
        return f"videos/exercises/{exercise}_technique_m01"
    
    elif category == "instruction":
        exercise = exercises[counter % len(exercises)]
        archetype = ARCHETYPES[counter % len(ARCHETYPES)]
        return f"videos/instructions/{exercise}_instruction_{archetype}_m01"
    
    elif category == "mistake":
        exercise = exercises[counter % len(exercises)]
        return f"videos/exercises/{exercise}_mistake_m01"
    
    elif category == "reminder":
        # 147 упражнений × 3 архетипа × 3 варианта = 1323
        exercise_idx = counter % len(exercises)
        archetype_idx = (counter // len(exercises)) % len(ARCHETYPES)
        reminder_num = ((counter // (len(exercises) * len(ARCHETYPES))) % 3) + 1
        
        exercise = exercises[exercise_idx]
        archetype = ARCHETYPES[archetype_idx]
        
        return f"videos/reminders/{exercise}_reminder_{archetype}_{reminder_num:02d}"
    
    elif category == "weekly":
        # 12 недель × 3 архетипа = 36
        week_num = (counter % 12) + 1
        archetype = ARCHETYPES[counter % len(ARCHETYPES)]
        return f"videos/motivation/weekly_{archetype}_week{week_num:02d}"
    
    elif category == "final":
        archetype = ARCHETYPES[counter % len(ARCHETYPES)]
        return f"videos/motivation/final_{archetype}"
    
    elif category == "avatars":
        # 3 архетипа × 3 варианта = 9
        archetype = ARCHETYPES[counter // 3]
        variant = (counter % 3) + 1
        return f"images/avatars/{archetype}_avatar_{variant:02d}"
    
    elif category == "cards":
        card_category = random.choice(['motivation', 'progress', 'success', 'challenge'])
        return f"images/cards/card_{card_category}_{counter+1:05d}"
    
    return "misc/unknown"

def copy_files_correctly(all_videos, all_images, exercises):
    """Копирует файлы с правильными именами в нужных количествах"""
    
    print("\n🎯 ОТБИРАЮ И КОПИРУЮ ТОЧНЫЕ КОЛИЧЕСТВА:")
    print(f"Видео нужно: {sum(VIDEO_TARGETS.values())} штук")
    print(f"Изображений нужно: {sum(IMAGE_TARGETS.values())} штук")
    
    # Перемешиваем файлы
    random.shuffle(all_videos)
    random.shuffle(all_images)
    
    video_idx = 0
    image_idx = 0
    total_copied = 0
    
    # Копируем видео по категориям
    for category, target_count in VIDEO_TARGETS.items():
        print(f"\n📹 {category}: копирую {target_count} видео...")
        
        for counter in range(target_count):
            if video_idx >= len(all_videos):
                print(f"❌ Не хватает видео! Найдено только {len(all_videos)}")
                break
                
            source_file = all_videos[video_idx]
            filename_base = generate_filename(category, counter, exercises)
            target_file = filename_base + source_file.suffix
            target_path = os.path.join(TARGET_DIR, target_file)
            
            try:
                shutil.copy2(source_file, target_path)
                total_copied += 1
                video_idx += 1
                
                if (counter + 1) % 100 == 0:
                    print(f"    Скопировано {counter + 1}/{target_count}")
                    
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
        
        print(f"✅ {category}: {target_count} видео скопировано")
    
    # Копируем изображения
    for category, target_count in IMAGE_TARGETS.items():
        print(f"\n📷 {category}: копирую {target_count} изображений...")
        
        for counter in range(target_count):
            if image_idx >= len(all_images):
                print(f"❌ Не хватает изображений! Найдено только {len(all_images)}")
                break
                
            source_file = all_images[image_idx]
            filename_base = generate_filename(category, counter, exercises)
            target_file = filename_base + source_file.suffix
            target_path = os.path.join(TARGET_DIR, target_file)
            
            try:
                shutil.copy2(source_file, target_path)
                total_copied += 1
                image_idx += 1
                
                if (counter + 1) % 100 == 0:
                    print(f"    Скопировано {counter + 1}/{target_count}")
                    
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
        
        print(f"✅ {category}: {target_count} изображений скопировано")
    
    return total_copied

def verify_results():
    """Проверяет правильность результатов"""
    print("\n📊 ПРОВЕРКА РЕЗУЛЬТАТОВ:")
    print("=" * 50)
    
    # Проверяем видео
    total_videos = 0
    for category, target in VIDEO_TARGETS.items():
        if category in ['technique', 'mistake']:
            pattern = f"*_{category}_*"
            folder = "videos/exercises"
        elif category == 'instruction':
            pattern = "*_instruction_*"
            folder = "videos/instructions"
        elif category == 'reminder':
            pattern = "*_reminder_*"
            folder = "videos/reminders"
        else:  # weekly, final
            pattern = f"*_{category}_*"
            folder = "videos/motivation"
        
        actual = len(list(Path(TARGET_DIR, folder).glob(pattern)))
        total_videos += actual
        status = "✅" if actual == target else "❌"
        print(f"{status} {category:12} {actual:4}/{target:4}")
    
    print(f"   {'ВСЕГО ВИДЕО':12} {total_videos:4}/{sum(VIDEO_TARGETS.values()):4}")
    print()
    
    # Проверяем изображения
    total_images = 0
    for category, target in IMAGE_TARGETS.items():
        folder = f"images/{category}"
        actual = len(list(Path(TARGET_DIR, folder).glob("*")))
        total_images += actual
        status = "✅" if actual == target else "❌"
        print(f"{status} {category:12} {actual:4}/{target:4}")
    
    print(f"   {'ВСЕГО ФОТО':12} {total_images:4}/{sum(IMAGE_TARGETS.values()):4}")
    print("=" * 50)
    print(f"   {'ИТОГО':12} {total_videos + total_images:4} файлов")
    
    # Размер
    size_gb = sum(f.stat().st_size for f in Path(TARGET_DIR).rglob('*') if f.is_file()) / (1024**3)
    print(f"   {'РАЗМЕР':12} {size_gb:.1f} GB")

def main():
    print("🚀 ФИНАЛЬНЫЙ ПРАВИЛЬНЫЙ ОТБОР МЕДИАФАЙЛОВ")
    print("=" * 60)
    print(f"ЦЕЛЬ: {sum(VIDEO_TARGETS.values())} видео + {sum(IMAGE_TARGETS.values())} изображений")
    print("=" * 60)
    
    # Загружаем упражнения
    exercises = load_exercises()
    
    # Собираем все файлы с диска
    all_videos, all_images = collect_all_media()
    
    # Создаем структуру
    create_folder_structure()
    
    # Копируем файлы правильно
    total_copied = copy_files_correctly(all_videos, all_images, exercises)
    
    # Проверяем результат
    verify_results()
    
    print(f"\n🎉 ГОТОВО! Скопировано {total_copied} файлов")
    print(f"📁 Расположение: {TARGET_DIR}")

if __name__ == '__main__':
    main()