#!/usr/bin/env python3
"""
Финальный отборщик видео упражнений из папки exercises
Берем видео 1-5 минут для всех 144 упражнений
"""

import os
import shutil
import json
import pandas as pd
from pathlib import Path

def get_file_size_mb(file_path):
    """Получить размер файла в мегабайтах"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0

def is_suitable_for_exercise(size_mb):
    """Проверить подходит ли видео для упражнения (1-5 минут)"""
    # Приблизительная оценка: 1-5 минут = 5-50 MB
    return 5 <= size_mb <= 50

def collect_exercise_videos():
    """Собрать все подходящие видео из папки exercises"""
    
    exercise_folder = "/Volumes/Z9/материалы для ai fitnes/exercises"
    
    print(f"🔍 Сканируем папку exercises: {exercise_folder}")
    
    suitable_videos = []
    total_scanned = 0
    
    # Рекурсивно обходим все подпапки
    for root, dirs, files in os.walk(exercise_folder):
        for file in files:
            if file.lower().endswith('.mp4'):
                file_path = os.path.join(root, file)
                size_mb = get_file_size_mb(file_path)
                total_scanned += 1
                
                if is_suitable_for_exercise(size_mb):
                    # Определяем относительный путь от exercises
                    rel_path = os.path.relpath(root, exercise_folder)
                    
                    suitable_videos.append({
                        "file_path": file_path,
                        "file_name": file,
                        "folder": rel_path if rel_path != "." else "root",
                        "size_mb": round(size_mb, 2),
                        "estimated_duration": f"{size_mb/10:.1f} мин"  # Приблизительно
                    })
                
                if total_scanned % 100 == 0:
                    print(f"  Просканировано: {total_scanned}, найдено подходящих: {len(suitable_videos)}")
    
    print(f"✅ Сканирование завершено:")
    print(f"  Всего видео: {total_scanned}")
    print(f"  Подходящих (1-5 мин): {len(suitable_videos)}")
    
    return suitable_videos

def load_exercise_database():
    """Загрузить базу упражнений"""
    
    excel_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MODERN_EXERCISES_DATABASE_2025.xlsx'
    
    try:
        df = pd.read_excel(excel_file, sheet_name='All_Modern_Exercises')
        exercises = df.to_dict('records')
        print(f"📋 Загружено {len(exercises)} упражнений из базы")
        return exercises
    except Exception as e:
        print(f"❌ Ошибка загрузки упражнений: {e}")
        return []

def create_full_exercise_mapping(exercises, available_videos):
    """Создать полный маппинг всех 144 упражнений"""
    
    print(f"🎯 Создаем маппинг для {len(exercises)} упражнений...")
    print(f"📊 Доступно {len(available_videos)} подходящих видео")
    
    if len(available_videos) < len(exercises):
        print(f"⚠️ ВНИМАНИЕ: Видео меньше чем упражнений!")
        print(f"   Нужно: {len(exercises)}")
        print(f"   Есть: {len(available_videos)}")
        print(f"   Недостает: {len(exercises) - len(available_videos)}")
    
    # Сортируем видео по размеру (предпочитаем средние размеры ~15-25MB)
    available_videos.sort(key=lambda x: abs(x["size_mb"] - 20))
    
    exercise_mapping = []
    
    for i, exercise in enumerate(exercises):
        # Берем видео по порядку (лучшие сначала)
        if i < len(available_videos):
            video = available_videos[i]
        else:
            # Если видео закончились, используем повторно (циклично)
            video = available_videos[i % len(available_videos)]
            print(f"🔄 Повторное использование видео для упражнения {i+1}")
        
        new_name = f"{exercise['slug']}_technique_mod1.mp4"
        
        exercise_mapping.append({
            "exercise_id": exercise.get('id', i+1),
            "exercise_slug": exercise["slug"],
            "exercise_name": exercise.get("name_en", f"Exercise {i+1}"),
            "exercise_name_ru": exercise.get("name_ru", f"Упражнение {i+1}"),
            "category": exercise.get("category", "unknown"),
            "category_ru": exercise.get("category_ru", "Неизвестно"),
            "original_path": video["file_path"],
            "original_name": video["file_name"],
            "original_folder": video["folder"],
            "new_name": new_name,
            "size_mb": video["size_mb"],
            "estimated_duration": video["estimated_duration"],
            "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/exercises/{new_name}",
            "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/exercises/{new_name}",
            "video_reused": i >= len(available_videos)
        })
    
    print(f"✅ Маппинг создан для всех {len(exercise_mapping)} упражнений")
    
    # Статистика повторного использования
    reused_count = sum(1 for item in exercise_mapping if item.get("video_reused", False))
    if reused_count > 0:
        print(f"🔄 Повторно использовано {reused_count} видео")
    
    return exercise_mapping

def create_additional_video_types(exercises, available_videos):
    """Создать дополнительные типы видео (инструкции, напоминания)"""
    
    print(f"🎬 Создаем дополнительные типы видео...")
    
    # Разделяем видео по размерам для разных типов
    small_videos = [v for v in available_videos if 5 <= v["size_mb"] <= 15]  # Для напоминаний
    medium_videos = [v for v in available_videos if 10 <= v["size_mb"] <= 25]  # Для инструкций
    
    archetypes = ["bro", "sergeant", "intellectual"]
    
    instruction_mapping = []
    reminder_mapping = []
    
    # Инструкции: 3 архетипа × 144 упражнения = 432 видео
    video_index = 0
    for exercise in exercises:
        for archetype in archetypes:
            if video_index < len(medium_videos):
                video = medium_videos[video_index % len(medium_videos)]
            else:
                video = available_videos[video_index % len(available_videos)]
            
            new_name = f"{exercise['slug']}_instruction_{archetype}_mod1.mp4"
            
            instruction_mapping.append({
                "exercise_slug": exercise["slug"],
                "exercise_name": exercise.get("name_en", ""),
                "archetype": archetype,
                "type": "instruction",
                "original_path": video["file_path"],
                "original_name": video["file_name"],
                "new_name": new_name,
                "size_mb": video["size_mb"],
                "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/instructions/{new_name}",
                "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/instructions/{new_name}"
            })
            video_index += 1
    
    # Напоминания: 3 архетипа × 3 напоминания × 144 упражнения = 1296 видео
    video_index = 0
    for exercise in exercises:
        for archetype in archetypes:
            for reminder_num in range(1, 4):  # 3 напоминания на упражнение
                if video_index < len(small_videos):
                    video = small_videos[video_index % len(small_videos)]
                else:
                    video = available_videos[video_index % len(available_videos)]
                
                new_name = f"{exercise['slug']}_reminder_{archetype}_{reminder_num}.mp4"
                
                reminder_mapping.append({
                    "exercise_slug": exercise["slug"],
                    "exercise_name": exercise.get("name_en", ""),
                    "archetype": archetype,
                    "reminder_number": reminder_num,
                    "type": "reminder",
                    "original_path": video["file_path"],
                    "original_name": video["file_name"],
                    "new_name": new_name,
                    "size_mb": video["size_mb"],
                    "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/reminders/{new_name}",
                    "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/reminders/{new_name}"
                })
                video_index += 1
    
    print(f"✅ Создано:")
    print(f"  📋 Инструкций: {len(instruction_mapping)}")
    print(f"  💬 Напоминаний: {len(reminder_mapping)}")
    
    return instruction_mapping, reminder_mapping

def copy_all_videos(exercise_mapping, instruction_mapping, reminder_mapping, motivational_mapping):
    """Копирование всех видео по категориям"""
    
    # Создаем все необходимые папки
    folders = ["exercises", "instructions", "reminders", "weekly", "final"]
    for folder in folders:
        os.makedirs(f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/{folder}", exist_ok=True)
    
    all_mappings = [
        ("Упражения", exercise_mapping),
        ("Инструкции", instruction_mapping),
        ("Напоминания", reminder_mapping),
        ("Мотивационные", motivational_mapping)
    ]
    
    total_success = 0
    total_errors = 0
    
    for category_name, mapping in all_mappings:
        if not mapping:
            continue
            
        print(f"\n📁 Копируем {category_name}: {len(mapping)} файлов...")
        
        category_success = 0
        category_errors = 0
        
        for i, item in enumerate(mapping):
            try:
                source = item["original_path"]
                target = item["target_path"]
                
                # Копируем файл
                shutil.copy2(source, target)
                category_success += 1
                total_success += 1
                
                # Показываем прогресс каждые 50 файлов
                if (i + 1) % 50 == 0 or (i + 1) == len(mapping):
                    print(f"  Прогресс: {i+1}/{len(mapping)} ({(i+1)/len(mapping)*100:.1f}%)")
                    
            except Exception as e:
                print(f"❌ Ошибка копирования {item.get('original_name', 'unknown')}: {e}")
                category_errors += 1
                total_errors += 1
        
        print(f"✅ {category_name}: {category_success} успешно, {category_errors} ошибок")
    
    print(f"\n🎉 ИТОГО: {total_success} успешно, {total_errors} ошибок")
    return total_success, total_errors

def save_complete_mapping(exercise_mapping, instruction_mapping, reminder_mapping, motivational_mapping):
    """Сохранение полного маппинга"""
    
    # Полный результат
    complete_result = {
        "summary": {
            "total_exercises": len(exercise_mapping),
            "total_instructions": len(instruction_mapping),
            "total_reminders": len(reminder_mapping),
            "total_motivational": len(motivational_mapping),
            "grand_total": len(exercise_mapping) + len(instruction_mapping) + len(reminder_mapping) + len(motivational_mapping)
        },
        "exercises": exercise_mapping,
        "instructions": instruction_mapping,
        "reminders": reminder_mapping,
        "motivational": motivational_mapping
    }
    
    # Сохраняем полный JSON
    json_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/COMPLETE_VIDEO_MAPPING.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(complete_result, f, ensure_ascii=False, indent=2)
    
    # Создаем отдельные CSV для каждого типа
    files_created = []
    
    if exercise_mapping:
        df = pd.DataFrame(exercise_mapping)
        csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/ALL_EXERCISE_VIDEOS.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8')
        files_created.append(csv_file)
    
    if instruction_mapping:
        df = pd.DataFrame(instruction_mapping)
        csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/ALL_INSTRUCTION_VIDEOS.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8')
        files_created.append(csv_file)
    
    if reminder_mapping:
        df = pd.DataFrame(reminder_mapping)
        csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/ALL_REMINDER_VIDEOS.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8')
        files_created.append(csv_file)
    
    # Создаем конфигурацию для ChatGPT
    chatgpt_config = {
        "system_info": {
            "version": "2.0",
            "phase": "Complete System - All Video Types",
            "total_videos": complete_result["summary"]["grand_total"]
        },
        "video_types": {
            "technique": {
                "count": len(exercise_mapping),
                "pattern": "{exercise_slug}_technique_mod1.mp4",
                "folder": "exercises"
            },
            "instruction": {
                "count": len(instruction_mapping),
                "pattern": "{exercise_slug}_instruction_{archetype}_mod1.mp4",
                "folder": "instructions"
            },
            "reminder": {
                "count": len(reminder_mapping),
                "pattern": "{exercise_slug}_reminder_{archetype}_{number}.mp4",
                "folder": "reminders"
            },
            "weekly": {
                "pattern": "weekly_{archetype}_week{number}.mp4",
                "folder": "weekly"
            },
            "final": {
                "pattern": "final_{archetype}.mp4",
                "folder": "final"
            }
        },
        "exercises_by_slug": {item["exercise_slug"]: item for item in exercise_mapping},
        "archetypes": ["bro", "sergeant", "intellectual"],
        "base_url": "https://ai-fitness-media.r2.cloudflarestorage.com/videos/"
    }
    
    config_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/COMPLETE_CHATGPT_CONFIG.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(chatgpt_config, f, ensure_ascii=False, indent=2)
    
    files_created.extend([json_file, config_file])
    
    print(f"💾 Сохранены файлы:")
    for file in files_created:
        print(f"  📄 {file}")
    
    return complete_result

def main():
    """Основная функция"""
    
    print("🎬 ПОЛНЫЙ ОТБОР ВИДЕО ДЛЯ AI FITNESS COACH")
    print("=" * 60)
    
    # 1. Собираем все подходящие видео из папки exercises
    print("\n📊 Шаг 1: Сбор видео из папки exercises...")
    available_videos = collect_exercise_videos()
    
    if not available_videos:
        print("❌ Не найдено подходящих видео!")
        return
    
    # 2. Загружаем базу упражнений
    print("\n📋 Шаг 2: Загрузка базы упражнений...")
    exercises = load_exercise_database()
    
    if not exercises:
        print("❌ Не удалось загрузить упражнения!")
        return
    
    # 3. Создаем маппинг для техники упражнений (144 видео)
    print("\n🎯 Шаг 3: Маппинг техники упражнений...")
    exercise_mapping = create_full_exercise_mapping(exercises, available_videos)
    
    # 4. Создаем дополнительные типы видео
    print("\n🎬 Шаг 4: Создание инструкций и напоминаний...")
    instruction_mapping, reminder_mapping = create_additional_video_types(exercises, available_videos)
    
    # 5. Загружаем существующий маппинг мотивационных видео
    print("\n📥 Шаг 5: Загрузка мотивационных видео...")
    try:
        motivational_df = pd.read_csv('/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MOTIVATIONAL_VIDEOS.csv')
        motivational_mapping = motivational_df.to_dict('records')
        print(f"✅ Загружено {len(motivational_mapping)} мотивационных видео")
    except:
        print("⚠️ Мотивационные видео не найдены, пропускаем")
        motivational_mapping = []
    
    # 6. Сохраняем полный маппинг
    print("\n💾 Шаг 6: Сохранение полного маппинга...")
    complete_result = save_complete_mapping(exercise_mapping, instruction_mapping, reminder_mapping, motivational_mapping)
    
    # 7. Копируем все файлы
    print("\n📁 Шаг 7: Копирование всех файлов...")
    print("⚠️ ВНИМАНИЕ: Это займет много времени!")
    
    print("🚀 Начинаем копирование...")
    total_success, total_errors = copy_all_videos(
        exercise_mapping, 
        instruction_mapping, 
        reminder_mapping, 
        motivational_mapping
    )
    
    # Итоговая статистика
    print(f"\n🎉 ЗАВЕРШЕНО!")
    print(f"📊 Статистика:")
    print(f"  💪 Упражнения (техника): {len(exercise_mapping)}")
    print(f"  📋 Инструкции: {len(instruction_mapping)}")
    print(f"  💬 Напоминания: {len(reminder_mapping)}")
    print(f"  🎬 Мотивационные: {len(motivational_mapping)}")
    print(f"  🎯 ВСЕГО ВИДЕО: {complete_result['summary']['grand_total']}")
    print(f"")
    print(f"📁 Копирование: {total_success} успешно, {total_errors} ошибок")
    print(f"💾 Размер системы: ~{sum(item['size_mb'] for item in exercise_mapping + instruction_mapping + reminder_mapping)/1024:.1f} GB")

if __name__ == '__main__':
    main()