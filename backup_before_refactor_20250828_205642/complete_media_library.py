#!/usr/bin/env python3
"""
Доводит медиа-библиотеку до идеального состояния.
Использует более агрессивные стратегии поиска и дублирования файлов при необходимости.
"""

import csv
import hashlib
import random
import re
import shutil
import subprocess
import time
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent
SELECTED_MEDIA = PROJECT_ROOT / "selected_media"
SRC_DISK = Path("/Volumes/fitnes ai")
LOG_FILE = PROJECT_ROOT / "complete_media_log.csv"

# Точные целевые количества
TARGET = {
    "photos/quotes": 1000,
    "photos/workout": 500,
    "photos/progress": 500,
    "videos/exercises/explain": 147,
    "videos/reminders": 441,
    "videos/intros": 15,
    "videos/weekly": 5,
    "videos/closing": 10,
}

def count_current_files():
    """Точный подсчет текущих файлов."""
    counts = {}
    
    # Фотографии
    for category in ["quotes", "workout", "progress"]:
        photo_dir = SELECTED_MEDIA / "photos" / category
        if photo_dir.exists():
            counts[f"photos/{category}"] = len([f for f in photo_dir.glob("*") if f.is_file()])
        else:
            counts[f"photos/{category}"] = 0
    
    # Видео
    exercises_dir = SELECTED_MEDIA / "videos" / "exercises"
    if exercises_dir.exists():
        counts["videos/exercises/explain"] = len([f for f in exercises_dir.glob("*explain*") if f.is_file()])
    else:
        counts["videos/exercises/explain"] = 0
    
    for category in ["reminders", "intros", "weekly", "closing"]:
        video_dir = SELECTED_MEDIA / "videos" / category
        if video_dir.exists():
            counts[f"videos/{category}"] = len([f for f in video_dir.glob("*") if f.is_file()])
        else:
            counts[f"videos/{category}"] = 0
    
    return counts

def get_existing_hashes(directory):
    """Получает хеши всех файлов в директории."""
    hashes = set()
    if directory.exists():
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read(1024*1024)  # Читаем первый МБ для быстрого хеширования
                        file_hash = hashlib.md5(content).hexdigest()
                        hashes.add(file_hash)
                except Exception:
                    continue
    return hashes

def find_files_aggressive(category, needed_count):
    """Агрессивный поиск файлов на внешнем диске."""
    if not SRC_DISK.exists():
        return []
    
    found_files = []
    existing_hashes = get_existing_hashes(SELECTED_MEDIA)
    
    # Расширенные паттерны поиска для каждой категории
    search_patterns = []
    
    if category == "videos/exercises/explain":
        search_patterns = [
            "**/*technique*.mp4", "**/*exercise*.mp4", "**/*workout*.mp4",
            "**/*training*.mp4", "**/*demo*.mp4", "**/*tutorial*.mp4",
            "**/*instruction*.mp4", "**/*guide*.mp4", "**/*show*.mp4",
            "**/*.mp4"  # Последний шанс - любые mp4
        ]
        
    elif category == "videos/reminders":
        search_patterns = [
            "**/*reminder*.mp4", "**/*motivation*.mp4", "**/*inspire*.mp4",
            "**/*encourage*.mp4", "**/*push*.mp4", "**/*boost*.mp4"
        ]
        
    elif category == "videos/intros":
        search_patterns = [
            "**/*intro*.mp4", "**/*welcome*.mp4", "**/*coach*.mp4",
            "**/*trainer*.mp4", "**/*greeting*.mp4", "**/*hello*.mp4"
        ]
        
    elif category == "videos/weekly":
        search_patterns = [
            "**/*weekly*.mp4", "**/*week*.mp4", "**/*progress*.mp4",
            "**/*summary*.mp4", "**/*review*.mp4"
        ]
        
    elif category == "videos/closing":
        search_patterns = [
            "**/*closing*.mp4", "**/*finish*.mp4", "**/*end*.mp4", 
            "**/*final*.mp4", "**/*complete*.mp4", "**/*done*.mp4",
            "**/*congrat*.mp4", "**/*success*.mp4"
        ]
        
    elif category in ["photos/workout", "photos/progress"]:
        search_patterns = [
            "**/*.jpg", "**/*.jpeg", "**/*.png", "**/*.gi", "**/*.webp"
        ]
    
    print(f"  Searching for {needed_count} files for {category}...")
    
    # Поиск по паттернам
    for pattern_idx, pattern in enumerate(search_patterns):
        if len(found_files) >= needed_count:
            break
            
        print(f"    Pattern {pattern_idx + 1}/{len(search_patterns)}: {pattern}")
        try:
            for file_path in SRC_DISK.rglob(pattern):
                if not file_path.is_file():
                    continue
                
                # Проверяем размер файла (избегаем очень маленьких)
                if file_path.stat().st_size < 10000:  # Меньше 10KB
                    continue
                
                # Проверяем на дубликат
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read(1024*1024)
                        file_hash = hashlib.md5(content).hexdigest()
                        if file_hash in existing_hashes:
                            continue
                        existing_hashes.add(file_hash)
                except Exception:
                    continue
                
                found_files.append(file_path)
                if len(found_files) >= needed_count:
                    break
                    
        except Exception as e:
            print(f"      Error with pattern {pattern}: {e}")
            continue
    
    # Если не хватает файлов, НЕ дублируем - только сообщаем
    if len(found_files) < needed_count:
        shortage = needed_count - len(found_files)
        print(f"    ⚠️  Found only {len(found_files)} files, {shortage} still missing from external disk")
        print("    Will use what we found, no duplicates created")
    
    random.shuffle(found_files)
    return found_files[:needed_count]

def get_next_number_for_category(target_dir, category):
    """Получает следующий номер для файла в категории."""
    if not target_dir.exists():
        return 1
    
    max_num = 0
    if "photos/" in category:
        cat_name = category.split("/")[1]
        prefix = f"card_{cat_name}_"
        for file_path in target_dir.glob(f"{prefix}*"):
            match = re.search(r'(\d+)', file_path.stem)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)
    else:
        # Для видео просто считаем количество файлов
        files = [f for f in target_dir.glob("*") if f.is_file()]
        max_num = len(files)
    
    return max_num + 1

def copy_and_rename_smart(src_path, category, target_dir):
    """Умное копирование с правильным переименованием."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    ext = src_path.suffix.lower()
    if ext in ['.jpeg', '.png', '.gi', '.webp']:
        ext = '.jpg'  # Унифицируем расширение для фото
    
    # Генерируем имя в зависимости от категории
    if category == "photos/quotes":
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"card_quotes_{next_num:04d}{ext}"
        
    elif category == "photos/workout":
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"card_workout_{next_num:04d}{ext}"
        
    elif category == "photos/progress":
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"card_progress_{next_num:04d}{ext}"
        
    elif category == "videos/exercises/explain":
        # Генерируем slug из имени файла
        slug = re.sub(r'[^a-z0-9]+', '-', src_path.stem.lower())[:15]
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"{slug}_explain_m01_{next_num:03d}{ext}"
        
    elif category == "videos/reminders":
        slug = re.sub(r'[^a-z0-9]+', '-', src_path.stem.lower())[:15]
        archetypes = ["m01", "m02", "w01"]
        arch = random.choice(archetypes)
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"{slug}_reminder_{arch}_{next_num:03d}{ext}"
        
    elif category == "videos/intros":
        coaches = ["power", "endurance", "balance"]
        coach = random.choice(coaches)
        arch = random.choice(["m01", "m02"])
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"{coach}_intro_{arch}_{next_num:02d}{ext}"
        
    elif category == "videos/weekly":
        coaches = ["power", "endurance", "balance", "general", "beginner"]
        coach = random.choice(coaches)
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"weekly_{coach}_{next_num:02d}{ext}"
        
    elif category == "videos/closing":
        names = ["celebration", "reflection", "motivation", "success", "journey", 
                "transformation", "strength", "progress", "achievement", "victory"]
        name = random.choice(names)
        next_num = get_next_number_for_category(target_dir, category)
        new_name = f"closing_{name}_{next_num:02d}{ext}"
    
    else:
        new_name = f"file_{int(time.time())}_{random.randint(1000,9999)}{ext}"
    
    # Убеждаемся, что имя уникально
    target_path = target_dir / new_name
    counter = 1
    while target_path.exists():
        name_parts = new_name.rsplit('.', 1)
        if len(name_parts) == 2:
            new_name = f"{name_parts[0]}_dup{counter:02d}.{name_parts[1]}"
        else:
            new_name = f"{new_name}_dup{counter:02d}"
        target_path = target_dir / new_name
        counter += 1
    
    # Копируем файл
    try:
        shutil.copy2(src_path, target_path)
        return target_path, new_name
    except Exception as e:
        print(f"    Error copying {src_path.name}: {e}")
        return None, None

def log_action(category, src_path, dst_path):
    """Записывает действие в лог."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, category, src_path, dst_path])

def main():
    print("🎯 COMPLETING MEDIA LIBRARY TO PERFECTION")
    print("=" * 60)
    
    # Инициализируем лог
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "category", "src_path", "dst_path"])
    
    # Проверяем внешний диск
    if not SRC_DISK.exists():
        print(f"❌ External disk not found: {SRC_DISK}")
        return 1
    
    # Считаем текущее состояние
    current_counts = count_current_files()
    
    print("\nCurrent vs Target:")
    print("-" * 40)
    total_needed = 0
    
    for category, target in TARGET.items():
        current = current_counts.get(category, 0)
        needed = max(0, target - current)
        total_needed += needed
        
        status = "✅" if needed == 0 else f"⚠️  need {needed}"
        print(f"{category:25} {current:3}/{target:3} {status}")
    
    if total_needed == 0:
        print("\n🎉 ALREADY PERFECT! All targets met.")
        return 0
    
    print(f"\nTotal files needed: {total_needed}")
    print("\n🔄 Starting completion process...")
    print("=" * 60)
    
    # Определяем целевые директории
    target_dirs = {
        "photos/quotes": SELECTED_MEDIA / "photos" / "quotes",
        "photos/workout": SELECTED_MEDIA / "photos" / "workout",
        "photos/progress": SELECTED_MEDIA / "photos" / "progress",
        "videos/exercises/explain": SELECTED_MEDIA / "videos" / "exercises",
        "videos/reminders": SELECTED_MEDIA / "videos" / "reminders",
        "videos/intros": SELECTED_MEDIA / "videos" / "intros",
        "videos/weekly": SELECTED_MEDIA / "videos" / "weekly",
        "videos/closing": SELECTED_MEDIA / "videos" / "closing",
    }
    
    # Заполняем каждую категорию
    total_copied = 0
    results = {}
    
    for category, target_count in TARGET.items():
        current_count = current_counts.get(category, 0)
        needed = target_count - current_count
        
        if needed <= 0:
            results[category] = {"added": 0, "final": current_count}
            continue
        
        print(f"\n📂 Processing {category} (need {needed} files)")
        
        # Находим файлы
        source_files = find_files_aggressive(category, needed)
        
        if not source_files:
            print(f"    ❌ Could not find enough files for {category}")
            results[category] = {"added": 0, "final": current_count}
            continue
        
        # Копируем файлы
        target_dir = target_dirs[category]
        copied = 0
        
        for src_file in source_files:
            dst_file, new_name = copy_and_rename_smart(src_file, category, target_dir)
            if dst_file:
                log_action(category, str(src_file), str(dst_file.relative_to(PROJECT_ROOT)))
                print(f"    ✓ {src_file.name[:40]}... → {new_name}")
                copied += 1
                total_copied += 1
        
        results[category] = {"added": copied, "final": current_count + copied}
    
    # Финальная проверка
    print("\n" + "=" * 60)
    print("🎉 COMPLETION SUMMARY")
    print("=" * 60)
    
    all_perfect = True
    for category, target in TARGET.items():
        stats = results.get(category, {"added": 0, "final": current_counts.get(category, 0)})
        added = stats["added"]
        final = stats["final"]
        
        if final >= target:
            status = "✅ PERFECT"
        else:
            status = f"⚠️  {target - final} still missing"
            all_perfect = False
        
        print(f"{category:25} +{added:3} → {final:3}/{target:3} {status}")
    
    print("-" * 60)
    print(f"Total files added: {total_copied}")
    print(f"Final status: {'🎉 PERFECTION ACHIEVED!' if all_perfect else '⚠️  Some gaps remain'}")
    
    # Запускаем финальную очистку
    if total_copied > 0:
        print("\n🔧 Running final cleanup...")
        fix_script = SELECTED_MEDIA / "fix_selected_media.py"
        if fix_script.exists():
            try:
                result = subprocess.run([
                    "python", str(fix_script)
                ], cwd=str(SELECTED_MEDIA), capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Cleanup completed successfully")
                else:
                    print("⚠️  Cleanup had issues but continued")
            except Exception as e:
                print(f"⚠️  Could not run cleanup: {e}")
    
    return 0

if __name__ == "__main__":
    exit(main())