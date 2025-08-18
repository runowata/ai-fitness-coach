#!/usr/bin/env python3
"""
Пакетное копирование видео с прогрессом
Создает полную систему из 1872 видео: 144 техники + 432 инструкции + 1296 напоминаний
"""

import os
import shutil
import json
import pandas as pd
from datetime import datetime

def load_suitable_videos():
    """Загрузить список подходящих видео"""
    
    # Быстро собираем все подходящие видео
    exercise_folder = "/Volumes/Z9/материалы для ai fitnes/exercises"
    suitable_videos = []
    
    print(f"📂 Собираем подходящие видео...")
    
    for root, dirs, files in os.walk(exercise_folder):
        for file in files:
            if file.lower().endswith('.mp4'):
                file_path = os.path.join(root, file)
                try:
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    if 5 <= size_mb <= 50:  # 1-5 минут
                        suitable_videos.append({
                            "file_path": file_path,
                            "file_name": file,
                            "size_mb": round(size_mb, 2)
                        })
                except:
                    continue
    
    print(f"✅ Найдено {len(suitable_videos)} подходящих видео")
    
    # Сортируем по размеру (предпочитаем средние)
    suitable_videos.sort(key=lambda x: abs(x["size_mb"] - 20))
    
    return suitable_videos

def load_exercises():
    """Загрузить упражнения"""
    
    excel_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MODERN_EXERCISES_DATABASE_2025.xlsx'
    
    try:
        df = pd.read_excel(excel_file, sheet_name='All_Modern_Exercises')
        exercises = df.to_dict('records')
        print(f"📋 Загружено {len(exercises)} упражнений")
        return exercises
    except Exception as e:
        print(f"❌ Ошибка загрузки упражнений: {e}")
        return []

def create_video_assignments(exercises, suitable_videos):
    """Создать назначения видео для всех типов"""
    
    print(f"🎯 Создаем назначения видео...")
    
    archetypes = ["bro", "sergeant", "intellectual"]
    
    assignments = {
        "technique": [],      # 144 видео
        "instruction": [],    # 432 видео (144 × 3)
        "reminder": []        # 1296 видео (144 × 3 × 3)
    }
    
    video_index = 0
    
    # 1. ТЕХНИКА УПРАЖНЕНИЙ (144 видео)
    for i, exercise in enumerate(exercises):
        video = suitable_videos[video_index % len(suitable_videos)]
        
        assignments["technique"].append({
            "exercise_slug": exercise["slug"],
            "exercise_name": exercise.get("name_en", f"Exercise {i+1}"),
            "exercise_name_ru": exercise.get("name_ru", f"Упражнение {i+1}"),
            "type": "technique",
            "original_path": video["file_path"],
            "original_name": video["file_name"],
            "new_name": f"{exercise['slug']}_technique_mod1.mp4",
            "size_mb": video["size_mb"],
            "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/exercises/{exercise['slug']}_technique_mod1.mp4",
            "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/exercises/{exercise['slug']}_technique_mod1.mp4"
        })
        video_index += 1
    
    # 2. ИНСТРУКЦИИ (432 видео: 144 × 3 архетипа)
    for exercise in exercises:
        for archetype in archetypes:
            video = suitable_videos[video_index % len(suitable_videos)]
            
            assignments["instruction"].append({
                "exercise_slug": exercise["slug"],
                "exercise_name": exercise.get("name_en", ""),
                "archetype": archetype,
                "type": "instruction",
                "original_path": video["file_path"],
                "original_name": video["file_name"],
                "new_name": f"{exercise['slug']}_instruction_{archetype}_mod1.mp4",
                "size_mb": video["size_mb"],
                "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/instructions/{exercise['slug']}_instruction_{archetype}_mod1.mp4",
                "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/instructions/{exercise['slug']}_instruction_{archetype}_mod1.mp4"
            })
            video_index += 1
    
    # 3. НАПОМИНАНИЯ (1296 видео: 144 × 3 архетипа × 3 напоминания)
    for exercise in exercises:
        for archetype in archetypes:
            for reminder_num in range(1, 4):
                video = suitable_videos[video_index % len(suitable_videos)]
                
                assignments["reminder"].append({
                    "exercise_slug": exercise["slug"],
                    "exercise_name": exercise.get("name_en", ""),
                    "archetype": archetype,
                    "reminder_number": reminder_num,
                    "type": "reminder",
                    "original_path": video["file_path"],
                    "original_name": video["file_name"],
                    "new_name": f"{exercise['slug']}_reminder_{archetype}_{reminder_num}.mp4",
                    "size_mb": video["size_mb"],
                    "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/reminders/{exercise['slug']}_reminder_{archetype}_{reminder_num}.mp4",
                    "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/reminders/{exercise['slug']}_reminder_{archetype}_{reminder_num}.mp4"
                })
                video_index += 1
    
    print(f"✅ Назначения созданы:")
    print(f"  💪 Техника: {len(assignments['technique'])}")
    print(f"  📋 Инструкции: {len(assignments['instruction'])}")
    print(f"  💬 Напоминания: {len(assignments['reminder'])}")
    print(f"  🎯 ВСЕГО: {sum(len(v) for v in assignments.values())}")
    
    return assignments

def batch_copy_videos(assignments, batch_size=50):
    """Копирование видео пакетами с прогрессом"""
    
    # Создаем папки
    folders = ["exercises", "instructions", "reminders"]
    for folder in folders:
        folder_path = f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/{folder}"
        os.makedirs(folder_path, exist_ok=True)
        print(f"📁 Создана папка: {folder}")
    
    total_files = sum(len(videos) for videos in assignments.values())
    copied_count = 0
    error_count = 0
    start_time = datetime.now()
    
    print(f"\n🚀 Начинаем копирование {total_files} файлов пакетами по {batch_size}...")
    
    for category, videos in assignments.items():
        print(f"\n📂 Копируем {category}: {len(videos)} файлов...")
        
        category_copied = 0
        category_errors = 0
        
        # Копируем пакетами
        for i in range(0, len(videos), batch_size):
            batch = videos[i:i+batch_size]
            batch_copied = 0
            batch_errors = 0
            
            for video in batch:
                try:
                    source = video["original_path"]
                    target = video["target_path"]
                    
                    if not os.path.exists(source):
                        print(f"⚠️ Исходный файл не найден: {source}")
                        batch_errors += 1
                        continue
                    
                    # Копируем файл
                    shutil.copy2(source, target)
                    batch_copied += 1
                    
                except Exception as e:
                    print(f"❌ Ошибка: {video['original_name']} - {e}")
                    batch_errors += 1
            
            category_copied += batch_copied
            category_errors += batch_errors
            copied_count += batch_copied
            error_count += batch_errors
            
            # Показываем прогресс
            progress = (copied_count + error_count) / total_files * 100
            batch_num = (i // batch_size) + 1
            total_batches = (len(videos) + batch_size - 1) // batch_size
            
            elapsed = datetime.now() - start_time
            eta = elapsed * (total_files / (copied_count + error_count)) - elapsed if (copied_count + error_count) > 0 else elapsed
            
            print(f"  📦 Пакет {batch_num}/{total_batches}: +{batch_copied} ✅, +{batch_errors} ❌ | "
                  f"Общий прогресс: {progress:.1f}% | ETA: {eta}")
        
        print(f"✅ {category}: {category_copied} успешно, {category_errors} ошибок")
    
    total_time = datetime.now() - start_time
    print(f"\n🎉 КОПИРОВАНИЕ ЗАВЕРШЕНО!")
    print(f"⏱️  Время: {total_time}")
    print(f"✅ Успешно: {copied_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📊 Успешность: {copied_count/(copied_count+error_count)*100:.1f}%")
    
    return copied_count, error_count

def save_final_config(assignments):
    """Сохранить финальную конфигурацию"""
    
    # Объединяем все назначения
    all_videos = []
    for category, videos in assignments.items():
        all_videos.extend(videos)
    
    # Создаем полную конфигурацию
    final_config = {
        "system_info": {
            "version": "3.0 - Complete System",
            "created": datetime.now().isoformat(),
            "total_videos": len(all_videos),
            "categories": {cat: len(videos) for cat, videos in assignments.items()}
        },
        "video_structure": {
            "technique": {
                "count": len(assignments["technique"]),
                "pattern": "{exercise_slug}_technique_mod1.mp4",
                "folder": "exercises",
                "description": "Демонстрация правильной техники выполнения"
            },
            "instruction": {
                "count": len(assignments["instruction"]),
                "pattern": "{exercise_slug}_instruction_{archetype}_mod1.mp4",
                "folder": "instructions",
                "description": "Мотивирующие инструкции от тренеров"
            },
            "reminder": {
                "count": len(assignments["reminder"]),
                "pattern": "{exercise_slug}_reminder_{archetype}_{number}.mp4",
                "folder": "reminders",
                "description": "Короткие подбадривания во время выполнения"
            }
        },
        "archetypes": {
            "bro": "Дружелюбный тренер-приятель",
            "sergeant": "Строгий тренер-сержант",
            "intellectual": "Мудрый тренер-интеллектуал"
        },
        "cloudflare_base": "https://ai-fitness-media.r2.cloudflarestorage.com/videos/",
        "exercises_index": {video["exercise_slug"]: video for video in assignments["technique"]},
        "chatgpt_integration": {
            "get_technique": "exercises/{exercise_slug}_technique_mod1.mp4",
            "get_instruction": "instructions/{exercise_slug}_instruction_{archetype}_mod1.mp4",
            "get_reminder": "reminders/{exercise_slug}_reminder_{archetype}_{1-3}.mp4"
        }
    }
    
    # Сохраняем конфигурацию
    config_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/FINAL_COMPLETE_CONFIG.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(final_config, f, ensure_ascii=False, indent=2)
    
    # Сохраняем CSV файлы
    csv_files = []
    for category, videos in assignments.items():
        if videos:
            df = pd.DataFrame(videos)
            csv_file = f'/Users/alexbel/Desktop/AI Fitness Coach/media_lists/FINAL_{category.upper()}_VIDEOS.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8')
            csv_files.append(csv_file)
    
    print(f"💾 Конфигурация сохранена:")
    print(f"  🔧 {config_file}")
    for csv_file in csv_files:
        print(f"  📊 {csv_file}")
    
    return final_config

def main():
    """Основная функция"""
    
    print("🎬 ПОЛНАЯ СИСТЕМА ВИДЕО AI FITNESS COACH")
    print("=" * 60)
    print(f"🎯 Цель: создать 1872 видео (144 техника + 432 инструкции + 1296 напоминаний)")
    print()
    
    # 1. Загружаем подходящие видео
    print("📂 Шаг 1: Загрузка подходящих видео...")
    suitable_videos = load_suitable_videos()
    
    if len(suitable_videos) < 144:
        print(f"❌ Недостаточно видео! Нужно минимум 144, найдено {len(suitable_videos)}")
        return
    
    # 2. Загружаем упражнения
    print("\n📋 Шаг 2: Загрузка упражнений...")
    exercises = load_exercises()
    
    if not exercises:
        print("❌ Не удалось загрузить упражнения!")
        return
    
    # 3. Создаем назначения
    print("\n🎯 Шаг 3: Создание назначений видео...")
    assignments = create_video_assignments(exercises, suitable_videos)
    
    # 4. Сохраняем конфигурацию
    print("\n💾 Шаг 4: Сохранение конфигурации...")
    final_config = save_final_config(assignments)
    
    # 5. Копируем файлы
    print("\n📁 Шаг 5: Копирование файлов...")
    print("⚠️ ВНИМАНИЕ: Копирование 1872 файлов займет 30-60 минут!")
    
    copied, errors = batch_copy_videos(assignments, batch_size=25)
    
    # Финальная статистика
    total_size_gb = sum(video["size_mb"] for videos in assignments.values() for video in videos) / 1024
    
    print(f"\n🎉 СИСТЕМА ГОТОВА!")
    print(f"📊 Создано видео:")
    print(f"  💪 Техника упражнений: {len(assignments['technique'])}")
    print(f"  📋 Инструкции: {len(assignments['instruction'])}")
    print(f"  💬 Напоминания: {len(assignments['reminder'])}")
    print(f"  🎯 ВСЕГО: {final_config['system_info']['total_videos']}")
    print(f"")
    print(f"💾 Размер системы: ~{total_size_gb:.1f} GB")
    print(f"✅ Скопировано: {copied}")
    print(f"❌ Ошибок: {errors}")
    print(f"📈 Успешность: {copied/(copied+errors)*100:.1f}%")
    print(f"")
    print(f"🔗 Готово для загрузки на Cloudflare R2!")
    print(f"🤖 Готово для интеграции с ChatGPT!")

if __name__ == '__main__':
    main()