#!/usr/bin/env python3
"""
Заполняет все недостающие медиа-файлы любыми подходящими файлами с внешнего диска.
Создает временные заглушки с правильными названиями для корректной работы системы.
"""

import csv
import random
import shutil
import time
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent
SELECTED_MEDIA = PROJECT_ROOT / "selected_media"
SRC_DISK = Path("/Volumes/fitnes ai")
LOG_FILE = PROJECT_ROOT / "placeholders_log.csv"

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

def get_all_source_files():
    """Собирает ВСЕ подходящие файлы с внешнего диска."""
    if not SRC_DISK.exists():
        return [], []
    
    print("🔍 Scanning external disk for ALL usable files...")
    
    video_files = []
    photo_files = []
    
    # Сканируем все видео файлы
    video_patterns = ["**/*.mp4", "**/*.mov", "**/*.avi", "**/*.MP4", "**/*.MOV"]
    for pattern in video_patterns:
        try:
            for file_path in SRC_DISK.rglob(pattern):
                if file_path.is_file() and file_path.stat().st_size > 50000:  # Больше 50KB
                    video_files.append(file_path)
        except Exception:
            continue
    
    # Сканируем все фото файлы
    photo_patterns = ["**/*.jpg", "**/*.jpeg", "**/*.png", "**/*.gi", "**/*.webp", 
                      "**/*.JPG", "**/*.JPEG", "**/*.PNG"]
    for pattern in photo_patterns:
        try:
            for file_path in SRC_DISK.rglob(pattern):
                if file_path.is_file() and file_path.stat().st_size > 5000:  # Больше 5KB
                    photo_files.append(file_path)
        except Exception:
            continue
    
    # Перемешиваем для случайности
    random.shuffle(video_files)
    random.shuffle(photo_files)
    
    print(f"  Found {len(video_files)} video files")
    print(f"  Found {len(photo_files)} photo files")
    
    return video_files, photo_files

def generate_exercise_slugs():
    """Генерирует список из 147 exercise slugs."""
    base_exercises = [
        "push-ups", "pull-ups", "squats", "lunges", "burpees", "plank", "deadlifts",
        "bench-press", "shoulder-press", "rows", "dips", "chin-ups", "jumping-jacks",
        "mountain-climbers", "bicycle-crunches", "leg-raises", "russian-twists",
        "wall-sits", "tricep-extensions", "bicep-curls", "lateral-raises", "front-raises",
        "calf-raises", "hip-thrusts", "glute-bridges", "side-lunges", "jump-squats",
        "pike-push-ups", "diamond-push-ups", "wide-grip-pull-ups", "close-grip-push-ups",
        "incline-push-ups", "decline-push-ups", "single-leg-deadlifts", "bulgarian-split-squats",
        "step-ups", "box-jumps", "broad-jumps", "high-knees", "butt-kicks", "leg-curls",
        "leg-extensions", "chest-flyes", "reverse-flyes", "upright-rows", "shrugs",
        "arnold-press", "clean-and-press", "thrusters", "kettlebell-swings",
        "goblet-squats", "farmer-walks", "bear-crawls", "crab-walks", "inchworms"
    ]
    
    # Расширяем список до 147 элементов
    extended_exercises = []
    for i in range(147):
        if i < len(base_exercises):
            extended_exercises.append(base_exercises[i])
        else:
            # Создаем вариации
            base_idx = i % len(base_exercises)
            variation = (i // len(base_exercises)) + 1
            extended_exercises.append(f"{base_exercises[base_idx]}-v{variation}")
    
    return extended_exercises

def create_placeholders(category, needed_count, source_files, target_dir):
    """Создает временные файлы-заглушки с правильными именами."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if needed_count <= 0 or not source_files:
        return 0
    
    created_count = 0
    source_idx = 0
    
    for i in range(needed_count):
        if source_idx >= len(source_files):
            source_idx = 0  # Начинаем сначала, если файлы кончились
        
        src_file = source_files[source_idx]
        source_idx += 1
        
        # Генерируем правильное имя в зависимости от категории
        ext = src_file.suffix.lower()
        if ext in ['.jpeg', '.png', '.gi', '.webp']:
            ext = '.jpg'  # Унифицируем для фото
        
        if category == "photos/quotes":
            new_name = f"card_quotes_{i+1:04d}{ext}"
            
        elif category == "photos/workout":
            new_name = f"card_workout_{i+1:04d}{ext}"
            
        elif category == "photos/progress":
            new_name = f"card_progress_{i+1:04d}{ext}"
            
        elif category == "videos/exercises/explain":
            # Используем сгенерированные exercise slugs
            exercise_slugs = generate_exercise_slugs()
            slug = exercise_slugs[i] if i < len(exercise_slugs) else f"exercise-{i+1}"
            new_name = f"{slug}_explain_m01{ext}"
            
        elif category == "videos/reminders":
            # Генерируем reminder файлы для разных упражнений и архетипов
            exercise_slugs = generate_exercise_slugs()
            archetypes = ["m01", "m02", "w01"]
            
            # Распределяем по упражнениям и архетипам
            exercises_per_arch = len(exercise_slugs)  # 147
            arch_idx = i // exercises_per_arch
            exercise_idx = i % exercises_per_arch
            
            if arch_idx >= len(archetypes):
                arch_idx = arch_idx % len(archetypes)
            
            slug = exercise_slugs[exercise_idx] if exercise_idx < len(exercise_slugs) else f"exercise-{exercise_idx+1}"
            arch = archetypes[arch_idx]
            new_name = f"{slug}_reminder_{arch}{ext}"
            
        elif category == "videos/intros":
            coaches = ["power", "endurance", "balance"]
            archs = ["m01", "m02"]
            
            # Комбинируем coaches и archs для получения 15 файлов
            combo_idx = i % (len(coaches) * len(archs))
            coach_idx = combo_idx // len(archs)
            arch_idx = combo_idx % len(archs)
            
            coach = coaches[coach_idx] if coach_idx < len(coaches) else "general"
            arch = archs[arch_idx]
            
            extra = f"_{(i // (len(coaches) * len(archs))) + 1}" if i >= len(coaches) * len(archs) else ""
            new_name = f"{coach}_intro_{arch}{extra}{ext}"
            
        elif category == "videos/weekly":
            coaches = ["power", "endurance", "balance", "general", "beginner"]
            coach = coaches[i] if i < len(coaches) else f"coach-{i+1}"
            new_name = f"weekly_{coach}{ext}"
            
        elif category == "videos/closing":
            names = ["celebration", "reflection", "motivation", "success", "journey", 
                    "transformation", "strength", "progress", "achievement", "victory"]
            name = names[i] if i < len(names) else f"closing-{i+1}"
            new_name = f"closing_{name}{ext}"
        
        else:
            new_name = f"placeholder_{i+1:04d}{ext}"
        
        # Убеждаемся, что имя уникально
        target_path = target_dir / new_name
        counter = 1
        while target_path.exists():
            name_parts = new_name.rsplit('.', 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{counter:02d}.{name_parts[1]}"
            else:
                new_name = f"{new_name}_{counter:02d}"
            target_path = target_dir / new_name
            counter += 1
        
        # Копируем файл
        try:
            shutil.copy2(src_file, target_path)
            log_action(category, str(src_file), str(target_path.relative_to(PROJECT_ROOT)))
            created_count += 1
            
            if created_count % 50 == 0:
                print(f"    Created {created_count}/{needed_count} placeholders...")
                
        except Exception as e:
            print(f"    Error copying {src_file.name}: {e}")
            # Создаем пустой файл как последнюю попытку
            try:
                target_path.touch()
                created_count += 1
            except Exception:
                pass
    
    return created_count

def log_action(category, src_path, dst_path):
    """Записывает действие в лог."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, category, src_path, dst_path])

def main():
    print("🎯 CREATING PLACEHOLDERS FOR COMPLETE MEDIA LIBRARY")
    print("=" * 70)
    print("This will create temporary files with correct names for system testing.")
    print("Replace these files with proper content later.")
    print("=" * 70)
    
    # Инициализируем лог
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "category", "src_path", "dst_path"])
    
    # Проверяем внешний диск
    if not SRC_DISK.exists():
        print(f"❌ External disk not found: {SRC_DISK}")
        return 1
    
    # Получаем все доступные файлы
    video_files, photo_files = get_all_source_files()
    
    if not video_files and not photo_files:
        print("❌ No usable files found on external disk")
        return 1
    
    # Считаем текущее состояние
    current_counts = count_current_files()
    
    print("\nCurrent vs Target:")
    print("-" * 50)
    total_needed = 0
    
    for category, target in TARGET.items():
        current = current_counts.get(category, 0)
        needed = max(0, target - current)
        total_needed += needed
        
        status = "✅" if needed == 0 else f"⚠️  need {needed}"
        print(f"{category:25} {current:3}/{target:3} {status}")
    
    if total_needed == 0:
        print("\n🎉 ALL COMPLETE! No placeholders needed.")
        return 0
    
    print(f"\nTotal placeholders needed: {total_needed}")
    print("\n🔄 Creating placeholders...")
    print("=" * 70)
    
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
    
    # Создаем плейсхолдеры для каждой категории
    total_created = 0
    results = {}
    
    for category, target_count in TARGET.items():
        current_count = current_counts.get(category, 0)
        needed = target_count - current_count
        
        if needed <= 0:
            results[category] = {"created": 0, "final": current_count}
            continue
        
        print(f"\n📂 Creating {needed} placeholders for {category}")
        
        # Выбираем подходящие исходные файлы
        if category.startswith("photos/"):
            source_files = photo_files
        else:
            source_files = video_files
        
        if not source_files:
            print(f"    ❌ No source files available for {category}")
            results[category] = {"created": 0, "final": current_count}
            continue
        
        # Создаем плейсхолдеры
        target_dir = target_dirs[category]
        created = create_placeholders(category, needed, source_files, target_dir)
        
        total_created += created
        results[category] = {"created": created, "final": current_count + created}
        
        print(f"    ✅ Created {created}/{needed} placeholders")
    
    # Финальная сводка
    print("\n" + "=" * 70)
    print("🎉 PLACEHOLDER CREATION COMPLETE")
    print("=" * 70)
    
    all_complete = True
    for category, target in TARGET.items():
        stats = results.get(category, {"created": 0, "final": current_counts.get(category, 0)})
        created = stats["created"]
        final = stats["final"]
        
        if final >= target:
            status = "✅ COMPLETE"
        else:
            status = f"⚠️  {target - final} still missing"
            all_complete = False
        
        print(f"{category:25} +{created:3} → {final:3}/{target:3} {status}")
    
    print("-" * 70)
    print(f"Total placeholders created: {total_created}")
    print(f"Status: {'🎉 LIBRARY COMPLETE!' if all_complete else '⚠️ Some items still missing'}")
    print(f"Log saved to: {LOG_FILE.name}")
    print("\n💡 Remember: These are TEMPORARY files for system testing.")
    print("   Replace with proper content when ready!")
    
    return 0

if __name__ == "__main__":
    exit(main())