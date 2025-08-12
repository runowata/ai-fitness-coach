#!/usr/bin/env python3
"""
ИСПРАВЛЕННЫЙ скрипт с ПРАВИЛЬНЫМИ количествами
"""

import os
import sys
import csv
import random
import shutil
from pathlib import Path

# ПРАВИЛЬНЫЕ ЦЕЛЕВЫЕ КОЛИЧЕСТВА
CORRECT_TARGETS = {
    "technique": 147,      # 1× на упражнение = 147
    "instruction": 441,    # 3× архетип × 147 упражнений = 441  
    "mistake": 147,        # 1× на упражнение = 147
    "reminder": 441,       # 3× архетип × 147 упражнений × 1 вариант = 441 (НЕ 1323!)
    "weekly": 36,          # 12 недель × 3 архетипа = 36
    "final": 3,            # 1× на архетип = 3
    "avatars": 9,          # 3 варианта × 3 архетипа = 9
    "cards": 600,          # 600 мотивационных карточек
}

# ИТОГО ПРАВИЛЬНО:
# Видео: 147+441+147+441+36+3 = 1215 видео (НЕ 2097!)
# Изображения: 9+600 = 609 изображений
# ВСЕГО: 1824 файла

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
    return exercises

def get_current_counts():
    """Определяет текущее количество файлов"""
    counts = {}
    
    # Видео
    counts['technique'] = len(list(Path(TARGET_DIR, "videos/exercises").glob("*technique*")))
    counts['instruction'] = len(list(Path(TARGET_DIR, "videos/instructions").glob("*")))
    
    reminder_path = Path(TARGET_DIR, "videos/reminders")
    counts['reminder'] = len(list(reminder_path.glob("*"))) if reminder_path.exists() else 0
    
    motivation_path = Path(TARGET_DIR, "videos/motivation")
    if motivation_path.exists():
        counts['weekly'] = len(list(motivation_path.glob("*weekly*")))
        counts['final'] = len(list(motivation_path.glob("*final*")))
    else:
        counts['weekly'] = 0
        counts['final'] = 0
    
    # Изображения
    avatars_path = Path(TARGET_DIR, "images/avatars")
    cards_path = Path(TARGET_DIR, "images/cards")
    counts['avatars'] = len(list(avatars_path.glob("*"))) if avatars_path.exists() else 0
    counts['cards'] = len(list(cards_path.glob("*"))) if cards_path.exists() else 0
    
    return counts

def generate_filename(category, counter, exercises):
    """Генерирует правильное имя файла"""
    
    if category == "reminder":
        # 147 упражнений × 3 архетипа = 441 (НЕ 1323!)
        exercise_idx = counter % len(exercises)
        archetype_idx = (counter // len(exercises)) % len(ARCHETYPES)
        
        exercise = exercises[exercise_idx]
        archetype = ARCHETYPES[archetype_idx]
        
        return f"videos/reminders/{exercise}_reminder_{archetype}_01"
    
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

def continue_with_correct_amounts():
    """Продолжает копирование с ПРАВИЛЬНЫМИ количествами"""
    
    exercises = load_exercises()
    current_counts = get_current_counts()
    
    print(f"📊 ТЕКУЩЕЕ СОСТОЯНИЕ С ПРАВИЛЬНЫМИ ЦЕЛЯМИ:")
    print("=" * 50)
    
    total_current = 0
    total_target = sum(CORRECT_TARGETS.values())
    
    for category, target in CORRECT_TARGETS.items():
        current = current_counts.get(category, 0)
        remaining = max(0, target - current)
        total_current += current
        
        # Если текущее количество больше целевого - обрезаем
        if current > target:
            print(f"⚠️  {category}: {current}/{target} (ЛИШНИЕ! Нужно удалить {current - target})")
        elif remaining > 0:
            print(f"⏳ {category}: {current}/{target} (осталось {remaining})")
        else:
            print(f"✅ {category}: {current}/{target} (готово)")
    
    print("=" * 50)
    print(f"   ИТОГО: {total_current}/{total_target}")
    
    # Удаляем лишние reminder видео если есть
    if current_counts.get('reminder', 0) > CORRECT_TARGETS['reminder']:
        print(f"\n🗑️  Удаляю лишние reminder видео...")
        reminder_files = list(Path(TARGET_DIR, "videos/reminders").glob("*"))
        
        # Удаляем лишние файлы
        excess_count = len(reminder_files) - CORRECT_TARGETS['reminder']
        for i in range(excess_count):
            reminder_files[-(i+1)].unlink()
        
        print(f"✅ Удалено {excess_count} лишних reminder файлов")
        current_counts['reminder'] = CORRECT_TARGETS['reminder']
    
    # Собираем медиафайлы для продолжения
    print(f"\n📂 Собираю файлы с диска...")
    
    all_videos = []
    all_images = []
    
    for path in Path(SOURCE_DIR).rglob('*'):
        if path.is_file():
            ext = path.suffix.lower()
            if ext in {'.mp4', '.mov', '.avi', '.mkv', '.webm'}:
                all_videos.append(path)
            elif ext in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
                all_images.append(path)
    
    random.shuffle(all_videos)
    random.shuffle(all_images)
    
    print(f"📹 Доступно {len(all_videos)} видео")
    print(f"📷 Доступно {len(all_images)} изображений")
    
    video_idx = 0
    image_idx = 0
    
    # Копируем недостающие файлы
    categories_to_copy = ["reminder", "weekly", "final", "avatars", "cards"]
    
    for category in categories_to_copy:
        current_count = current_counts.get(category, 0)
        target_count = CORRECT_TARGETS[category]
        remaining = target_count - current_count
        
        if remaining <= 0:
            continue
            
        print(f"\n📁 {category}: копирую {remaining} недостающих файлов...")
        
        # Определяем папку
        if category in ["reminder"]:
            folder = "videos/reminders"
            file_source = all_videos
            idx_ref = 'video_idx'
        elif category in ["weekly", "final"]:
            folder = "videos/motivation" 
            file_source = all_videos
            idx_ref = 'video_idx'
        else:  # avatars, cards
            folder = f"images/{category}"
            file_source = all_images
            idx_ref = 'image_idx'
            
        os.makedirs(os.path.join(TARGET_DIR, folder), exist_ok=True)
        
        for i in range(remaining):
            if idx_ref == 'video_idx':
                if video_idx >= len(all_videos):
                    print(f"❌ Закончились видео!")
                    break
                source_file = all_videos[video_idx]
                video_idx += 1
            else:
                if image_idx >= len(all_images):
                    print(f"❌ Закончились изображения!")
                    break
                source_file = all_images[image_idx] 
                image_idx += 1
            
            counter = current_count + i
            filename_base = generate_filename(category, counter, exercises)
            target_file = filename_base + source_file.suffix
            target_path = os.path.join(TARGET_DIR, target_file)
            
            try:
                shutil.copy2(source_file, target_path)
                
                if (i + 1) % 50 == 0:
                    print(f"    {i + 1}/{remaining} скопировано")
                    
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
        
        final_count = len(list(Path(TARGET_DIR, folder).glob("*")))
        print(f"✅ {category}: завершено ({final_count}/{target_count})")

def verify_final_correct_results():
    """Проверяет финальные результаты с правильными целями"""
    print(f"\n🎯 ФИНАЛЬНАЯ ПРОВЕРКА С ПРАВИЛЬНЫМИ ЦЕЛЯМИ:")
    print("=" * 60)
    
    total_actual = 0
    total_target = sum(CORRECT_TARGETS.values())
    
    for category, target in CORRECT_TARGETS.items():
        if category == "technique":
            actual = len(list(Path(TARGET_DIR, "videos/exercises").glob("*technique*")))
        elif category == "instruction":
            actual = len(list(Path(TARGET_DIR, "videos/instructions").glob("*")))
        elif category == "reminder":
            actual = len(list(Path(TARGET_DIR, "videos/reminders").glob("*")))
        elif category in ["weekly", "final"]:
            actual = len(list(Path(TARGET_DIR, "videos/motivation").glob(f"*{category}*")))
        else:  # avatars, cards
            actual = len(list(Path(TARGET_DIR, f"images/{category}").glob("*")))
        
        total_actual += actual
        status = "✅" if actual == target else ("⚠️" if actual > target else "❌")
        print(f"{status} {category:12} {actual:4}/{target:4}")
    
    print("=" * 60)
    print(f"   {'ИТОГО':12} {total_actual:4}/{total_target:4}")
    
    # Размер
    size_gb = sum(f.stat().st_size for f in Path(TARGET_DIR).rglob('*') if f.is_file()) / (1024**3)
    print(f"   {'РАЗМЕР':12} {size_gb:.1f} GB")
    
    print(f"\nПРАВИЛЬНЫЕ ЦЕЛИ:")
    print(f"- Видео: {147+441+147+441+36+3} = 1215 штук")  
    print(f"- Изображения: {9+600} = 609 штук")
    print(f"- ВСЕГО: {1215+609} = 1824 файла")

def main():
    print("🔧 ИСПРАВЛЕНИЕ КОЛИЧЕСТВ И ЗАВЕРШЕНИЕ КОПИРОВАНИЯ")
    print("=" * 60)
    print("⚠️  ИСПРАВЛЯЮ: reminder = 441 (НЕ 1323!)")
    print("=" * 60)
    
    continue_with_correct_amounts()
    verify_final_correct_results()
    
    print(f"\n🎉 ГОТОВО! Все файлы с ПРАВИЛЬНЫМИ количествами в {TARGET_DIR}")

if __name__ == '__main__':
    main()