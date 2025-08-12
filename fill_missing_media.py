#!/usr/bin/env python3
"""
fill_missing_media.py
Заменяет слишком большие видео и дозаполняет медиатеку до целевых объёмов.
"""

import os
import csv
import shutil
import hashlib
import random
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.cwd()
TARGET_MEDIA = PROJECT_ROOT / "selected_media"
SRC_DISK = Path("/Volumes/fitnes ai")
LOG_FILE = PROJECT_ROOT / "media_fill_log.csv"

# Целевые количества
TARGET = {
    "videos/exercises/explain": 147,
    "videos/reminders": 441,
    "videos/intros": 15,
    "videos/weekly": 5,
    "videos/closing": 10,
    "photos/quotes": 1000,
    "photos/workout": 500,
    "photos/progress": 500,
}

# Ограничения
MAX_VIDEO_SEC = 7 * 60  # 7 минут
MAX_VIDEO_SIZE = 600 * 1024**2  # 600 МБ
MAX_TOTAL_SIZE = 10 * 1024**3  # 10 ГБ
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def sha256_hash(file_path):
    """Вычисляет SHA256 хеш файла."""
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def video_duration_sec(file_path):
    """Получает длительность видео через ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0.0
    except Exception:
        return 0.0

def ensure_dirs():
    """Создает необходимые папки."""
    for category in TARGET.keys():
        (TARGET_MEDIA / category).mkdir(parents=True, exist_ok=True)

def scan_current_files():
    """Сканирует текущие файлы, находит нарушающие ограничения."""
    current_counts = {}
    current_hashes = set()
    files_to_remove = []
    
    for category in TARGET.keys():
        category_path = TARGET_MEDIA / category
        files = list(category_path.glob("*")) if category_path.exists() else []
        
        valid_files = []
        for file_path in files:
            if not file_path.is_file():
                continue
                
            file_hash = sha256_hash(file_path)
            if file_hash:
                current_hashes.add(file_hash)
            
            # Проверяем видео на ограничения
            if category.startswith("videos/") and file_path.suffix.lower() in VIDEO_EXTS:
                size = file_path.stat().st_size
                duration = video_duration_sec(file_path)
                
                if size > MAX_VIDEO_SIZE or duration > MAX_VIDEO_SEC:
                    files_to_remove.append((file_path, category))
                    continue
            
            valid_files.append(file_path)
        
        current_counts[category] = len(valid_files)
    
    return current_counts, current_hashes, files_to_remove

def find_candidates():
    """Находит все подходящие файлы на внешнем диске."""
    if not SRC_DISK.exists():
        return []
    
    candidates = []
    print("Сканирование внешнего диска...")
    
    file_count = 0
    video_count = 0
    photo_count = 0
    
    for file_path in SRC_DISK.rglob("*"):
        if not file_path.is_file():
            continue
        
        file_count += 1
        if file_count % 1000 == 0:
            print(f"  Обработано файлов: {file_count}, найдено: видео={video_count}, фото={photo_count}")
        
        ext = file_path.suffix.lower()
        size = file_path.stat().st_size
        
        # Видео файлы
        if ext in VIDEO_EXTS:
            if size <= MAX_VIDEO_SIZE:
                duration = video_duration_sec(file_path)
                if duration <= MAX_VIDEO_SEC and duration > 0:
                    candidates.append(("video", file_path, size))
                    video_count += 1
                    if video_count >= 500:  # Лимитируем для ускорения
                        break
        
        # Фото файлы
        elif ext in PHOTO_EXTS:
            candidates.append(("photo", file_path, size))
            photo_count += 1
            if photo_count >= 2500:  # Лимитируем для ускорения
                break
        
        # Остановимся если нашли достаточно
        if video_count >= 500 and photo_count >= 2500:
            break
    
    print(f"  Финал: обработано {file_count} файлов, найдено: видео={video_count}, фото={photo_count}")
    random.shuffle(candidates)
    return candidates

def generate_filename(category, src_path, counters):
    """Генерирует имя файла по категории."""
    ext = src_path.suffix.lower()
    
    if category == "videos/exercises/explain":
        slug = src_path.stem.lower().replace(" ", "-")[:20]
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        return f"{slug}_explain_m01{ext}"
    
    elif category == "videos/reminders":
        counters[category] = counters.get(category, 0) + 1
        return f"reminder_{counters[category]:03d}{ext}"
    
    elif category == "videos/intros":
        counters[category] = counters.get(category, 0) + 1
        return f"intro_{counters[category]:02d}{ext}"
    
    elif category == "videos/weekly":
        counters[category] = counters.get(category, 0) + 1
        return f"weekly_{counters[category]:02d}{ext}"
    
    elif category == "videos/closing":
        counters[category] = counters.get(category, 0) + 1
        return f"closing_{counters[category]:02d}{ext}"
    
    elif category == "photos/quotes":
        counters[category] = counters.get(category, 0) + 1
        return f"card_quotes_{counters[category]:04d}.jpg"
    
    elif category == "photos/workout":
        counters[category] = counters.get(category, 0) + 1
        return f"card_workout_{counters[category]:04d}.jpg"
    
    elif category == "photos/progress":
        counters[category] = counters.get(category, 0) + 1
        return f"card_progress_{counters[category]:04d}.jpg"
    
    return f"file_{counters.get('default', 0)}{ext}"

def log_action(action, category, src, dst, size_mb):
    """Записывает действие в лог."""
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            action,
            category,
            str(src),
            str(dst),
            f"{size_mb:.2f}"
        ])

def main():
    print("🚀 Заполнение медиатеки до целевых объёмов")
    print("=" * 60)
    
    # Инициализация лога
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "action", "category", "src", "dst", "size_MB"])
    
    ensure_dirs()
    
    # Сканируем текущие файлы
    print("📊 Анализ текущих файлов...")
    current_counts, current_hashes, files_to_remove = scan_current_files()
    
    print(f"Найдено {len(files_to_remove)} файлов для удаления (превышают лимиты)")
    
    # Удаляем файлы, нарушающие ограничения
    for file_path, category in files_to_remove:
        size_mb = file_path.stat().st_size / (1024**2)
        log_action("remove", category, file_path, "", size_mb)
        file_path.unlink()
        print(f"  🗑️  Удален: {file_path.name}")
    
    # Пересчитываем после удаления
    current_counts, current_hashes, _ = scan_current_files()
    
    print("\n📋 Текущее состояние:")
    for category, target in TARGET.items():
        current = current_counts.get(category, 0)
        print(f"  {category:25} {current:3}/{target:3}")
    
    # Находим кандидатов
    candidates = find_candidates()
    print(f"\n🔍 Найдено {len(candidates)} кандидатов на внешнем диске")
    
    # Заполняем категории
    total_added_size = 0
    counters = {}
    stats = {}
    
    for category, target_count in TARGET.items():
        current_count = current_counts.get(category, 0)
        needed = target_count - current_count
        
        if needed <= 0:
            stats[category] = {"added": 0, "size_mb": 0}
            continue
        
        print(f"\n⚙️  {category}: нужно {needed} файлов")
        
        category_path = TARGET_MEDIA / category
        added_count = 0
        added_size = 0
        
        # Определяем тип файлов для категории
        file_type = "video" if category.startswith("videos/") else "photo"
        
        for cand_type, src_path, size in candidates[:]:
            if added_count >= needed:
                break
            
            if total_added_size + size > MAX_TOTAL_SIZE:
                print(f"    ⚠️  Достигнут лимит 10 ГБ, остановлено")
                break
            
            if cand_type != file_type:
                continue
            
            # Проверяем дубликаты
            file_hash = sha256_hash(src_path)
            if not file_hash or file_hash in current_hashes:
                continue
            
            # Генерируем имя и копируем
            new_name = generate_filename(category, src_path, counters)
            dst_path = category_path / new_name
            
            # Проверяем конфликт имен
            counter = 1
            while dst_path.exists():
                name_parts = new_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name = f"{name_parts[0]}_{counter:02d}.{name_parts[1]}"
                else:
                    new_name = f"{new_name}_{counter:02d}"
                dst_path = category_path / new_name
                counter += 1
            
            try:
                shutil.copy2(src_path, dst_path)
                size_mb = size / (1024**2)
                
                log_action("add", category, src_path, dst_path, size_mb)
                current_hashes.add(file_hash)
                candidates.remove((cand_type, src_path, size))
                
                added_count += 1
                added_size += size
                total_added_size += size
                
                print(f"    ✓ {src_path.name} → {new_name}")
                
            except Exception as e:
                print(f"    ❌ Ошибка копирования {src_path.name}: {e}")
        
        stats[category] = {
            "added": added_count,
            "size_mb": added_size / (1024**2)
        }
    
    # Итоговая сводка
    print("\n" + "=" * 80)
    print("📊 ИТОГОВАЯ СВОДКА")
    print("-" * 80)
    print(f"{'Категория':25} {'Есть/Цель':10} {'Не хватает':10} {'Добавлено МБ':12}")
    print("-" * 80)
    
    total_size_mb = 0
    for category, target in TARGET.items():
        current = current_counts.get(category, 0) + stats[category]["added"]
        missing = max(0, target - current)
        added_mb = stats[category]["size_mb"]
        total_size_mb += added_mb
        
        print(f"{category:25} {current:3}/{target:3}     {missing:6}     {added_mb:8.1f}")
    
    print("-" * 80)
    print(f"{'ИТОГО добавлено:':47} {total_size_mb:8.1f} МБ")
    print(f"{'Лог сохранен:':47} {LOG_FILE.name}")
    print("=" * 80)

if __name__ == "__main__":
    main()